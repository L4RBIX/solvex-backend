"""Teams: owner/coach/student roles, invites, assignments, coach dashboard.

Authorization model (backend-owned):
- every team object access resolves membership first (require_member);
- coaches and owners see the whole team; students see only themselves;
- coaches can only target users who are members of THAT team.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from contestiq_api.cfdata import store, weakness
from contestiq_api.entitlements import WEAKNESS_PRIORITY_STATUSES
from contestiq_api.errors import APIError

INVITE_DAYS_DEFAULT = 14
MANAGER_ROLES = ("owner", "coach")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_team(user: dict[str, Any], name: str) -> dict[str, Any]:
    team_id = str(uuid.uuid4())
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO teams (team_id, name, owner_user_id, created_at) VALUES (?, ?, ?, ?)",
            (team_id, name, user["user_id"], now),
        )
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, member_role, handle, joined_at) VALUES (?, ?, 'owner', ?, ?)",
            (team_id, user["user_id"], user.get("handle"), now),
        )
    return {"team_id": team_id, "name": name, "role": "owner"}


def get_member(team_id: str, user_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id)
        ).fetchone()
    return dict(row) if row else None


def require_member(team_id: str, user: dict[str, Any], roles: tuple[str, ...] = MANAGER_ROLES) -> dict[str, Any]:
    if user.get("role") == "admin":
        return {"team_id": team_id, "user_id": user.get("user_id"), "member_role": "owner"}
    member = get_member(team_id, user["user_id"])
    if member is None or member["member_role"] not in roles:
        raise APIError("FORBIDDEN", "You do not have access to this team.", 403)
    return member


def create_invite(team_id: str, created_by: str, member_role: str, expires_in_days: int = INVITE_DAYS_DEFAULT) -> dict[str, Any]:
    if member_role not in ("coach", "student"):
        raise APIError("INVALID_ROLE", "Invite role must be coach or student.", 422)
    token = secrets.token_hex(16)
    invite_id = str(uuid.uuid4())
    expires = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO team_invites (invite_id, team_id, token_hash, member_role, created_by, expires_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (invite_id, team_id, _hash(token), member_role, created_by, expires, store._now()),
        )
    return {"invite_id": invite_id, "team_id": team_id, "member_role": member_role,
            "invite_token": token, "expires_at": expires}


def accept_invite(user: dict[str, Any], token: str) -> dict[str, Any]:
    with store.connect() as conn:
        invite = conn.execute("SELECT * FROM team_invites WHERE token_hash = ?", (_hash(token),)).fetchone()
        if invite is None:
            raise APIError("INVITE_NOT_FOUND", "Invite token is not valid.", 404)
        invite = dict(invite)
        if invite["accepted_by"] is not None:
            raise APIError("INVITE_USED", "This invite has already been used.", 409)
        if store._now() > invite["expires_at"]:
            raise APIError("INVITE_EXPIRED", "This invite has expired.", 410)
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, member_role, handle, joined_at) VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(team_id, user_id) DO UPDATE SET member_role = excluded.member_role",
            (invite["team_id"], user["user_id"], invite["member_role"], user.get("handle"), store._now()),
        )
        conn.execute(
            "UPDATE team_invites SET accepted_by = ?, accepted_at = ? WHERE invite_id = ?",
            (user["user_id"], store._now(), invite["invite_id"]),
        )
    return {"team_id": invite["team_id"], "member_role": invite["member_role"]}


def list_students(team_id: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT tm.user_id, tm.member_role, tm.handle, tm.joined_at, u.email"
            " FROM team_members tm LEFT JOIN users u ON u.user_id = tm.user_id"
            " WHERE tm.team_id = ? ORDER BY tm.joined_at",
            (team_id,),
        ).fetchall()
    return [dict(row) for row in rows]


# ─── Assignments ─────────────────────────────────────────────────────────────


def create_assignment(team_id: str, assigned_by: str, payload: dict[str, Any]) -> dict[str, Any]:
    student = get_member(team_id, payload["student_user_id"])
    if student is None or student["member_role"] != "student":
        raise APIError("STUDENT_NOT_IN_TEAM", "The target user is not a student member of this team.", 404)
    kind = payload["kind"]
    if kind not in ("skill_focus", "problems", "verification"):
        raise APIError("INVALID_ASSIGNMENT_KIND", "kind must be skill_focus, problems, or verification.", 422)
    assignment_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO team_assignments (assignment_id, team_id, student_user_id, assigned_by, kind, skill_id,"
            " problem_ids, challenge_skill_id, due_date, notes, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                assignment_id, team_id, payload["student_user_id"], assigned_by, kind,
                payload.get("skill_id"), json.dumps(payload.get("problem_ids") or [], ensure_ascii=False),
                payload.get("challenge_skill_id"), payload.get("due_date"), payload.get("notes"), store._now(),
            ),
        )
    return {"assignment_id": assignment_id, "team_id": team_id, "kind": kind,
            "student_user_id": payload["student_user_id"]}


def list_assignments(team_id: str, student_user_id: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM team_assignments WHERE team_id = ?"
    params: list[Any] = [team_id]
    if student_user_id:
        query += " AND student_user_id = ?"
        params.append(student_user_id)
    query += " ORDER BY created_at DESC"
    with store.connect() as conn:
        rows = conn.execute(query, params).fetchall()
    assignments = []
    for row in rows:
        assignment = dict(row)
        assignment["problem_ids"] = json.loads(assignment["problem_ids"])
        assignments.append(assignment)
    return assignments


# ─── Dashboard ───────────────────────────────────────────────────────────────


def _student_summary(handle: str | None) -> dict[str, Any]:
    if not handle:
        return {"has_analysis": False, "reason": "no_handle_linked"}
    run_id = weakness.latest_run_id(handle)
    if run_id is None:
        return {"has_analysis": False, "reason": "no_analysis_run"}
    run = weakness.get_run(run_id)
    assert run is not None
    weak = [s for s in run["skills"] if s["status"] in WEAKNESS_PRIORITY_STATUSES]
    weak.sort(key=lambda s: (-s["severity"], s["skill_id"]))
    return {
        "has_analysis": True,
        "analysis_run_id": run["run_id"],
        "global_rating": run["global_rating"],
        "episode_count": run["episode_count"],
        "skill_count": len(run["skills"]),
        "weak_skill_count": len(weak),
        "top_weaknesses": [
            {"skill_id": s["skill_id"], "status": s["status"], "severity": s["severity"], "confidence": s["confidence"]}
            for s in weak[:3]
        ],
        "data_cutoff_time": run["data_cutoff_time"],
    }


def team_dashboard(team_id: str) -> dict[str, Any]:
    members = list_students(team_id)
    students = [m for m in members if m["member_role"] == "student"]
    entries = []
    now = store._now()
    with store.connect() as conn:
        for student in students:
            summary = _student_summary(student["handle"])
            previous = conn.execute(
                "SELECT summary, captured_at FROM team_student_snapshots WHERE team_id = ? AND user_id = ?"
                " ORDER BY captured_at DESC LIMIT 1",
                (team_id, student["user_id"]),
            ).fetchone()
            progress = None
            if previous is not None and summary.get("has_analysis"):
                prev_summary = json.loads(previous["summary"])
                if prev_summary.get("has_analysis"):
                    progress = {
                        "previous_captured_at": previous["captured_at"],
                        "weak_skill_count_change": summary["weak_skill_count"] - prev_summary.get("weak_skill_count", 0),
                        "global_rating_change": (summary.get("global_rating") or 0) - (prev_summary.get("global_rating") or 0),
                    }
            # Snapshot at most once per day per student.
            if previous is None or previous["captured_at"][:10] != now[:10]:
                conn.execute(
                    "INSERT INTO team_student_snapshots (snapshot_id, team_id, user_id, handle, analysis_run_id, summary, captured_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), team_id, student["user_id"], student["handle"],
                     summary.get("analysis_run_id"), json.dumps(summary, ensure_ascii=False), now),
                )
            entries.append({
                "user_id": student["user_id"],
                "handle": student["handle"],
                "summary": summary,
                "progress": progress,
                "open_assignments": len([
                    a for a in list_assignments(team_id, student["user_id"]) if a["assignment_status"] == "assigned"
                ]),
            })
    return {"team_id": team_id, "students": entries, "student_count": len(students)}
