"""Private weekly leaderboards (Phase G3).

Invite-only groups where members compete on real training activity for the
current ISO week. Scores are computed live from product_events via the same
gamification XP rules — no separate score table, no global leaderboard, no
PvP duels, no public profiles.

Security: every function here takes a real `user_id` (from a validated
bearer token — see auth.require_user_subject), NEVER a caller-supplied
handle/subject/alias. Membership lookups are always `WHERE user_id = ?`.
Invite codes are stored hashed (sha256); the plaintext is returned exactly
once when created. A Codeforces handle is public data and carries no
authorization weight — it is attached only for display/scoring convenience
when the caller has a verified one (contestiq_api.handles).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import uuid
from typing import Any

from contestiq_api import auth, entitlements, gamification, handles, product_events
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.identity import account_display_name

INVITE_DAYS_DEFAULT = 30
OWNER_ROLE = "owner"
MEMBER_ROLE = "member"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def _plan_for_member(member: dict[str, Any]) -> str:
    if member.get("user_id"):
        user = auth.get_user(member["user_id"])
        if user is not None:
            return entitlements.effective_plan(user)
    return "free"


def _public_group(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "leaderboard_id": row["leaderboard_id"],
        "name": row["name"],
        "visibility": row["visibility"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
    }


def create_group(
    caller: dict[str, Any],
    name: str,
    display_name: str | None = None,
) -> dict[str, Any]:
    leaderboard_id = str(uuid.uuid4())
    now = store._now()
    owner_subject = caller["subject"]
    owner_user_id = caller.get("user_id")
    owner_handle = caller.get("handle")
    if owner_handle:
        owner_handle = store.canonical_handle(owner_handle)
    display_name = account_display_name(caller)

    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO leaderboard_groups
                (leaderboard_id, name, owner_subject, owner_user_id, visibility, active, created_at)
            VALUES (?, ?, ?, ?, 'private', 1, ?)
            """,
            (leaderboard_id, name.strip(), owner_subject, owner_user_id, now),
        )
        conn.execute(
            """
            INSERT INTO leaderboard_members
                (leaderboard_id, member_subject, user_id, handle, display_name, member_role, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (leaderboard_id, owner_subject, owner_user_id, owner_handle, display_name, OWNER_ROLE, now),
        )

    invite = create_invite(leaderboard_id, created_by=owner_subject)
    return {
        **_public_group({
            "leaderboard_id": leaderboard_id,
            "name": name.strip(),
            "visibility": "private",
            "active": 1,
            "created_at": now,
            "owner_subject": owner_subject,
        }),
        "invite_code": invite["invite_code"],
        "invite_expires_at": invite.get("expires_at"),
    }


def create_invite(
    leaderboard_id: str,
    created_by: str,
    expires_in_days: int = INVITE_DAYS_DEFAULT,
) -> dict[str, Any]:
    group = get_group(leaderboard_id)
    if group is None or not group["active"]:
        raise APIError("LEADERBOARD_NOT_FOUND", "Leaderboard not found.", 404)

    code = secrets.token_urlsafe(12)
    invite_id = str(uuid.uuid4())
    expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=expires_in_days)).isoformat()
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO leaderboard_invites
                (invite_id, leaderboard_id, invite_code_hash, created_by, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (invite_id, leaderboard_id, _hash_code(code), created_by, now, expires),
        )
    return {
        "invite_id": invite_id,
        "leaderboard_id": leaderboard_id,
        "invite_code": code,
        "expires_at": expires,
    }


def get_group(leaderboard_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM leaderboard_groups WHERE leaderboard_id = ?", (leaderboard_id,)
        ).fetchone()
    return dict(row) if row else None


def get_member(leaderboard_id: str, member_subject: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM leaderboard_members WHERE leaderboard_id = ? AND member_subject = ?",
            (leaderboard_id, member_subject),
        ).fetchone()
    return dict(row) if row else None


def is_member(leaderboard_id: str, user_id: str) -> dict[str, Any] | None:
    if not user_id:
        return None
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM leaderboard_members WHERE leaderboard_id = ? AND user_id = ? ORDER BY joined_at ASC LIMIT 1",
            (leaderboard_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def require_member(leaderboard_id: str, user_id: str) -> dict[str, Any]:
    member = is_member(leaderboard_id, user_id)
    if member is None:
        raise APIError("FORBIDDEN", "You are not a member of this leaderboard.", 403)
    return member


def list_groups_for_caller(user_id: str) -> list[dict[str, Any]]:
    if not user_id:
        return []
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT g.leaderboard_id, g.name, g.visibility, g.active, g.created_at, g.owner_subject,
                   m.member_role, m.joined_at
            FROM leaderboard_groups g
            JOIN leaderboard_members m ON m.leaderboard_id = g.leaderboard_id
            WHERE m.user_id = ? AND g.active = 1
            ORDER BY g.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [
        {
            "leaderboard_id": row["leaderboard_id"],
            "name": row["name"],
            "visibility": row["visibility"],
            "member_role": row["member_role"],
            "joined_at": row["joined_at"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def join_group(
    caller: dict[str, Any],
    invite_code: str,
    display_name: str | None = None,
) -> dict[str, Any]:
    with store.connect() as conn:
        invite = conn.execute(
            "SELECT * FROM leaderboard_invites WHERE invite_code_hash = ?",
            (_hash_code(invite_code),),
        ).fetchone()
    if invite is None:
        raise APIError("INVITE_INVALID", "Invite code is not valid.", 404)
    invite = dict(invite)
    if invite.get("revoked_at"):
        raise APIError("INVITE_REVOKED", "This invite has been revoked.", 410)
    if invite.get("expires_at") and store._now() > invite["expires_at"]:
        raise APIError("INVITE_EXPIRED", "This invite has expired.", 410)

    leaderboard_id = invite["leaderboard_id"]
    group = get_group(leaderboard_id)
    if group is None or not group["active"]:
        raise APIError("LEADERBOARD_NOT_FOUND", "Leaderboard not found.", 404)

    member_subject = caller["subject"]
    existing = get_member(leaderboard_id, member_subject)
    if existing is not None:
        return {
            "leaderboard_id": leaderboard_id,
            "name": group["name"],
            "member_role": existing["member_role"],
            "already_member": True,
        }

    user_id = caller.get("user_id")
    handle = caller.get("handle")
    if handle:
        handle = store.canonical_handle(handle)
    display_name = account_display_name(caller)

    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO leaderboard_members
                (leaderboard_id, member_subject, user_id, handle, display_name, member_role, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (leaderboard_id, member_subject, user_id, handle, display_name, MEMBER_ROLE, now),
        )
    return {
        "leaderboard_id": leaderboard_id,
        "name": group["name"],
        "member_role": MEMBER_ROLE,
        "already_member": False,
    }


def _rank_entries(members: list[dict[str, Any]], week_start: dt.date) -> list[dict[str, Any]]:
    """`user_id` is kept on each entry so the caller can robustly find the
    viewer's own row (see weekly_standings) — it is always stripped before
    any entry is returned over HTTP (never leak other members' user_ids)."""
    scored: list[dict[str, Any]] = []
    for member in members:
        if member.get("user_id"):
            events = product_events.events_for_account(member["user_id"])
        else:
            # Pre-fix handle-only membership cannot be safely attributed to
            # any account. Preserve the row for audit/display, but freeze its
            # score at zero: new anonymous public analysis events must not be
            # able to change a private leaderboard. Explicitly rejoin with a
            # bearer-token account after support reconciliation.
            events = []
        plan = _plan_for_member(member)
        stats = gamification.compute_weekly_stats(events, plan, week_start)
        scored.append({
            "user_id": member.get("user_id"),
            "display_name": member["display_name"],
            "handle": member.get("handle"),
            "joined_at": member["joined_at"],
            "weekly_xp": stats["weekly_xp"],
            "level": stats["level"],
            "active_days": stats["active_days"],
            "daily_goals_completed": stats["daily_goals_completed"],
            "feedback_count": stats["feedback_count"],
            "queues_generated": stats["queues_generated"],
            "weekly_report_viewed": stats["weekly_report_viewed"],
            "verification_attempts": stats["verification_attempts"],
            "badges_earned_this_week": stats["badges_earned_this_week"],
            "duels_completed": stats.get("duels_completed", 0),
            "duels_won": stats.get("duels_won", 0),
        })

    scored.sort(
        key=lambda e: (
            -e["weekly_xp"],
            -e["active_days"],
            -e["feedback_count"],
            e["joined_at"],
        ),
    )
    for rank, entry in enumerate(scored, start=1):
        entry["rank"] = rank
        entry.pop("joined_at", None)
    return scored


def _strip_internal(entry: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in entry.items() if k != "user_id"}


def weekly_standings(
    leaderboard_id: str,
    viewer_user_id: str,
    week_start: dt.date | None = None,
) -> dict[str, Any]:
    require_member(leaderboard_id, viewer_user_id)
    group = get_group(leaderboard_id)
    assert group is not None

    today = dt.datetime.now(dt.timezone.utc).date()
    start = week_start or gamification.week_start_for(today)

    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM leaderboard_members WHERE leaderboard_id = ? ORDER BY joined_at",
            (leaderboard_id,),
        ).fetchall()
    members = [dict(row) for row in rows]
    entries = _rank_entries(members, start)

    viewer_entry_internal = next((e for e in entries if e.get("user_id") == viewer_user_id), None)
    viewer_rank = viewer_entry_internal["rank"] if viewer_entry_internal else None
    viewer_entry = _strip_internal(viewer_entry_internal) if viewer_entry_internal else None

    return {
        "leaderboard_id": leaderboard_id,
        "name": group["name"],
        "visibility": group["visibility"],
        "week_start": start.isoformat(),
        "viewer_rank": viewer_rank,
        "viewer_entry": viewer_entry,
        "entries": [_strip_internal(e) for e in entries],
    }


def viewer_weekly_me(
    leaderboard_id: str,
    viewer_user_id: str,
) -> dict[str, Any]:
    standings = weekly_standings(leaderboard_id, viewer_user_id)
    entry = standings.get("viewer_entry")
    if entry is None:
        raise APIError("VIEWER_NOT_RANKED", "No weekly activity found for you yet.", 404)
    return {
        "leaderboard_id": leaderboard_id,
        "week_start": standings["week_start"],
        "rank": standings["viewer_rank"],
        **entry,
    }
