"""Organization event screening (Phase 08).

Flow: organizer creates an event with skill requirements → generates expiring
applicant links → an applicant opens their link, which mints a scoped shadow
user (token shown once) and starts a standard SkillTrace session → results
land in the organizer dashboard as sanitized summaries. Full reports require
org membership and every open/export is audited.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from contestiq_api import auth
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.skilltrace import sessions as st

LINK_DAYS_DEFAULT = 7
EVENT_DAYS_DEFAULT = 30

STATUS_RANK = {"completed": 0, "started": 1, "invited": 2, "expired": 3}
DECISION_RANK = {"issued": 0, "manual_review": 1, "not_issued": 2, None: 3}


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_org(user: dict[str, Any], name: str) -> dict[str, Any]:
    org_id = str(uuid.uuid4())
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO organizations (org_id, name, owner_user_id, created_at) VALUES (?, ?, ?, ?)",
            (org_id, name, user["user_id"], now),
        )
        conn.execute(
            "INSERT INTO organization_members (org_id, user_id, member_role, joined_at) VALUES (?, ?, 'owner', ?)",
            (org_id, user["user_id"], now),
        )
    return {"org_id": org_id, "name": name, "role": "owner"}


def require_org_member(org_id: str, user: dict[str, Any]) -> dict[str, Any]:
    if user.get("role") == "admin":
        return {"org_id": org_id, "user_id": user.get("user_id"), "member_role": "owner"}
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM organization_members WHERE org_id = ? AND user_id = ?",
            (org_id, user["user_id"]),
        ).fetchone()
    if row is None:
        raise APIError("FORBIDDEN", "You do not have access to this organization.", 403)
    return dict(row)


def get_event(event_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM org_events WHERE event_id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


def require_event_access(event_id: str, user: dict[str, Any]) -> dict[str, Any]:
    event = get_event(event_id)
    if event is None:
        raise APIError("EVENT_NOT_FOUND", f"No event found with id {event_id}.", 404)
    require_org_member(event["org_id"], user)
    return event


def create_event(
    org_id: str,
    created_by: str,
    name: str,
    requirements: list[dict[str, Any]],
    expires_in_days: int = EVENT_DAYS_DEFAULT,
) -> dict[str, Any]:
    if not requirements:
        raise APIError("REQUIREMENTS_REQUIRED", "An event needs at least one skill requirement.", 422)
    event_id = str(uuid.uuid4())
    expires = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO org_events (event_id, org_id, name, event_status, expires_at, created_by, created_at)"
            " VALUES (?, ?, ?, 'active', ?, ?, ?)",
            (event_id, org_id, name, expires, created_by, store._now()),
        )
        for req in requirements:
            conn.execute(
                "INSERT INTO event_requirements (event_id, skill_id, level, min_evidence_label) VALUES (?, ?, ?, ?)",
                (event_id, req["skill_id"], req.get("level"),
                 req.get("min_evidence_label", "sufficient_process_evidence")),
            )
    return {"event_id": event_id, "org_id": org_id, "name": name, "expires_at": expires,
            "requirements": requirements}


def _event_expired(event: dict[str, Any]) -> bool:
    return event["event_status"] != "active" or store._now() > event["expires_at"]


def create_applicant_link(event: dict[str, Any], display_name: str | None, email: str | None,
                          expires_in_days: int = LINK_DAYS_DEFAULT) -> dict[str, Any]:
    if _event_expired(event):
        raise APIError("EVENT_EXPIRED", "This event is no longer active.", 410)
    applicant_id = str(uuid.uuid4())
    link_id = str(uuid.uuid4())
    token = secrets.token_hex(16)
    now = store._now()
    # Link lifetime is capped by the event window: scoped AND expiring.
    link_expiry = min(
        (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat(),
        event["expires_at"],
    )
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO event_applicants (applicant_id, event_id, display_name, email, applicant_status, created_at)"
            " VALUES (?, ?, ?, ?, 'invited', ?)",
            (applicant_id, event["event_id"], display_name, email, now),
        )
        conn.execute(
            "INSERT INTO event_verification_links (link_id, event_id, applicant_id, token_hash, expires_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (link_id, event["event_id"], applicant_id, _hash(token), link_expiry, now),
        )
    return {"applicant_id": applicant_id, "link_token": token, "expires_at": link_expiry}


def start_applicant_session(token: str, request_id: str | None) -> dict[str, Any]:
    """Applicant opens their link: mint a scoped shadow user and start the session."""
    with store.connect() as conn:
        link = conn.execute(
            "SELECT * FROM event_verification_links WHERE token_hash = ?", (_hash(token),)
        ).fetchone()
    if link is None:
        raise APIError("LINK_NOT_FOUND", "Applicant link is not valid.", 404)
    link = dict(link)
    if link["used_at"] is not None:
        raise APIError("LINK_USED", "This applicant link has already been used.", 409)
    if store._now() > link["expires_at"]:
        raise APIError("LINK_EXPIRED", "This applicant link has expired.", 410)
    event = get_event(link["event_id"])
    assert event is not None
    if _event_expired(event):
        raise APIError("EVENT_EXPIRED", "This event is no longer active.", 410)

    with store.connect() as conn:
        requirement = conn.execute(
            "SELECT * FROM event_requirements WHERE event_id = ? ORDER BY skill_id LIMIT 1",
            (link["event_id"],),
        ).fetchone()
    if requirement is None:
        raise APIError("EVENT_MISCONFIGURED", "Event has no skill requirements.", 500)

    # Shadow user: throwaway identity scoped to this applicant; its token drives
    # the standard verification endpoints (snapshot/run/submit).
    shadow = auth.create_user(handle=None, email=None, role="user")
    session = st.start_session(
        {"user_id": shadow["user_id"], "handle": None},
        requirement["skill_id"], requirement["level"], request_id,
    )
    with store.connect() as conn:
        conn.execute(
            "UPDATE event_verification_links SET used_at = ? WHERE link_id = ?",
            (store._now(), link["link_id"]),
        )
        conn.execute(
            "UPDATE event_applicants SET applicant_status = 'started', shadow_user_id = ?, session_id = ?"
            " WHERE applicant_id = ?",
            (shadow["user_id"], session["session_id"], link["applicant_id"]),
        )
    return {
        "applicant_id": link["applicant_id"],
        "event_name": event["name"],
        "api_token": shadow["api_token"],  # shown exactly once, scoped to this session's user
        "session": session,
    }


def _applicant_result(applicant: dict[str, Any]) -> dict[str, Any]:
    """Sanitized screening summary: no code, no ledger, no session internals."""
    decision, label, pass_rate, badge = None, None, None, None
    completed_at = applicant["completed_at"]
    if applicant["session_id"]:
        with store.connect() as conn:
            row = conn.execute(
                "SELECT decision, process_evidence_label, hidden_pass_rate FROM badge_decisions WHERE session_id = ?",
                (applicant["session_id"],),
            ).fetchone()
            badge_row = conn.execute(
                "SELECT badge_public_id FROM public_badges WHERE session_id = ?", (applicant["session_id"],)
            ).fetchone()
            session = conn.execute(
                "SELECT session_status, completed_at FROM verification_sessions WHERE session_id = ?",
                (applicant["session_id"],),
            ).fetchone()
        if row is not None:
            decision, label, pass_rate = row["decision"], row["process_evidence_label"], row["hidden_pass_rate"]
        if badge_row is not None:
            badge = badge_row["badge_public_id"]
        if session is not None and session["session_status"] == "completed":
            completed_at = session["completed_at"]
    status = applicant["applicant_status"]
    if decision is not None:
        status = "completed"
    return {
        "applicant_id": applicant["applicant_id"],
        "display_name": applicant["display_name"],
        "status": status,
        "decision": decision,
        "evidence_label": label,
        "hidden_pass_rate": pass_rate,
        "badge_public_id": badge,
        "completed_at": completed_at,
    }


def event_dashboard(event: dict[str, Any]) -> dict[str, Any]:
    with store.connect() as conn:
        applicants = [dict(row) for row in conn.execute(
            "SELECT * FROM event_applicants WHERE event_id = ? ORDER BY created_at", (event["event_id"],)
        ).fetchall()]
        requirements = [dict(row) for row in conn.execute(
            "SELECT * FROM event_requirements WHERE event_id = ?", (event["event_id"],)
        ).fetchall()]
    results = [_applicant_result(a) for a in applicants]
    results.sort(key=lambda r: (
        STATUS_RANK.get(r["status"], 9),
        DECISION_RANK.get(r["decision"], 3),
        -(r["hidden_pass_rate"] or 0.0),
        r["applicant_id"],
    ))
    return {
        "event_id": event["event_id"],
        "name": event["name"],
        "event_status": "expired" if _event_expired(event) else event["event_status"],
        "expires_at": event["expires_at"],
        "requirements": requirements,
        "applicants": results,
        "applicant_count": len(results),
        "interpretation": (
            "Rankings summarize verification outcomes and process-evidence strength. "
            "They are not accusations and not general certificates of ability."
        ),
    }


def applicant_report(event: dict[str, Any], applicant_id: str, exported_by: str) -> dict[str, Any]:
    with store.connect() as conn:
        applicant = conn.execute(
            "SELECT * FROM event_applicants WHERE applicant_id = ? AND event_id = ?",
            (applicant_id, event["event_id"]),
        ).fetchone()
    if applicant is None:
        raise APIError("APPLICANT_NOT_FOUND", "No such applicant in this event.", 404)
    applicant = dict(applicant)
    if not applicant["session_id"]:
        raise APIError("REPORT_NOT_READY", "The applicant has not started a verification session.", 409)
    with store.connect() as conn:
        report = conn.execute(
            "SELECT * FROM private_reports WHERE session_id = ?", (applicant["session_id"],)
        ).fetchone()
    if report is None:
        raise APIError("REPORT_NOT_READY", "The applicant's verification is not finished yet.", 409)

    export_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO event_report_exports (export_id, event_id, applicant_id, exported_by, export_format, created_at)"
            " VALUES (?, ?, ?, ?, 'json', ?)",
            (export_id, event["event_id"], applicant_id, exported_by, store._now()),
        )
    auth.audit(exported_by, "event_report_export", applicant_id,
               {"event_id": event["event_id"], "export_id": export_id})
    return {
        "export_id": export_id,
        "applicant_id": applicant_id,
        "display_name": applicant["display_name"],
        "report": json.loads(dict(report)["content"]),
    }
