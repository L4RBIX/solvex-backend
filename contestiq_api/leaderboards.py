"""Private weekly leaderboards (Phase G3).

Invite-only groups where members compete on real training activity for the
current ISO week. Scores are computed live from product_events via the same
gamification XP rules — no separate score table, no global leaderboard, no
PvP duels, no public profiles.

Authorization:
- Only members can view a group's weekly standings.
- Invite codes are stored hashed (sha256); the plaintext is returned exactly
  once when created.
- Creating a group requires an authenticated user OR an explicit handle
  (anonymous beta learners tracked as handle:<cf handle>).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import uuid
from typing import Any

from contestiq_api import auth, entitlements, gamification, product_events
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle

INVITE_DAYS_DEFAULT = 30
OWNER_ROLE = "owner"
MEMBER_ROLE = "member"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def _subject_aliases(member: dict[str, Any]) -> list[str]:
    aliases = [member["member_subject"]]
    if member.get("user_id"):
        user_alias = f"user:{member['user_id']}"
        if user_alias not in aliases:
            aliases.append(user_alias)
    if member.get("handle"):
        handle_alias = f"handle:{store.canonical_handle(member['handle'])}"
        if handle_alias not in aliases:
            aliases.append(handle_alias)
    return aliases


def _plan_for_member(member: dict[str, Any]) -> str:
    if member.get("user_id"):
        user = auth.get_user(member["user_id"])
        if user is not None:
            return entitlements.effective_plan(user)
    return "free"


def resolve_caller(
    user: dict[str, Any] | None,
    handle: str | None,
) -> dict[str, Any]:
    """Resolve caller identity into subject aliases for membership checks."""
    aliases: list[str] = []
    primary: str | None = None
    cleaned_handle: str | None = None

    if user is not None and user.get("user_id"):
        user_alias = f"user:{user['user_id']}"
        aliases.append(user_alias)
        primary = user_alias

    if handle:
        cleaned_handle = validate_handle(handle)
        alias = f"handle:{store.canonical_handle(cleaned_handle)}"
        if alias not in aliases:
            aliases.append(alias)
        if primary is None:
            primary = alias

    if user is not None and user.get("user_id") and primary is None:
        primary = f"user:{user['user_id']}"

    if user is not None and primary is None and user.get("handle"):
        handle_alias = f"handle:{store.canonical_handle(user['handle'])}"
        if handle_alias not in aliases:
            aliases.append(handle_alias)
        primary = handle_alias

    if not aliases:
        raise APIError("AUTH_REQUIRED", "Provide a handle or API token to use leaderboards.", 401)

    return {
        "aliases": aliases,
        "subject": primary,
        "user_id": user.get("user_id") if user else None,
        "handle": cleaned_handle or (user.get("handle") if user else None),
    }


def _public_group(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "leaderboard_id": row["leaderboard_id"],
        "name": row["name"],
        "visibility": row["visibility"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "owner_subject": row["owner_subject"],
    }


def create_group(
    caller: dict[str, Any],
    name: str,
    display_name: str,
) -> dict[str, Any]:
    leaderboard_id = str(uuid.uuid4())
    now = store._now()
    owner_subject = caller["subject"]
    owner_user_id = caller.get("user_id")
    owner_handle = caller.get("handle")
    if owner_handle:
        owner_handle = store.canonical_handle(owner_handle)
    elif owner_user_id:
        user = auth.get_user(owner_user_id)
        owner_handle = user.get("handle") if user else None

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
            (leaderboard_id, owner_subject, owner_user_id, owner_handle, display_name.strip(), OWNER_ROLE, now),
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


def is_member(leaderboard_id: str, subject_aliases: list[str]) -> dict[str, Any] | None:
    if not subject_aliases:
        return None
    placeholders = ", ".join("?" for _ in subject_aliases)
    with store.connect() as conn:
        row = conn.execute(
            f"SELECT * FROM leaderboard_members WHERE leaderboard_id = ? AND member_subject IN ({placeholders})"
            " ORDER BY joined_at ASC LIMIT 1",
            (leaderboard_id, *subject_aliases),
        ).fetchone()
    return dict(row) if row else None


def require_member(leaderboard_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    member = is_member(leaderboard_id, subject_aliases)
    if member is None:
        raise APIError("FORBIDDEN", "You are not a member of this leaderboard.", 403)
    return member


def list_groups_for_caller(subject_aliases: list[str]) -> list[dict[str, Any]]:
    if not subject_aliases:
        return []
    placeholders = ", ".join("?" for _ in subject_aliases)
    with store.connect() as conn:
        rows = conn.execute(
            f"""
            SELECT g.leaderboard_id, g.name, g.visibility, g.active, g.created_at, g.owner_subject,
                   m.member_role, m.joined_at
            FROM leaderboard_groups g
            JOIN leaderboard_members m ON m.leaderboard_id = g.leaderboard_id
            WHERE m.member_subject IN ({placeholders}) AND g.active = 1
            ORDER BY g.created_at DESC
            """,
            subject_aliases,
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
    display_name: str,
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
    elif user_id:
        user = auth.get_user(user_id)
        handle = user.get("handle") if user else None

    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO leaderboard_members
                (leaderboard_id, member_subject, user_id, handle, display_name, member_role, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (leaderboard_id, member_subject, user_id, handle, display_name.strip(), MEMBER_ROLE, now),
        )
    return {
        "leaderboard_id": leaderboard_id,
        "name": group["name"],
        "member_role": MEMBER_ROLE,
        "already_member": False,
    }


def _rank_entries(members: list[dict[str, Any]], week_start: dt.date) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for member in members:
        aliases = _subject_aliases(member)
        events = product_events.events_for_subjects(aliases)
        plan = _plan_for_member(member)
        stats = gamification.compute_weekly_stats(events, plan, week_start)
        scored.append({
            "display_name": member["display_name"],
            "handle": member.get("handle"),
            "member_subject": member["member_subject"],
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
        entry.pop("member_subject", None)
        entry.pop("joined_at", None)
    return scored


def weekly_standings(
    leaderboard_id: str,
    viewer_aliases: list[str],
    week_start: dt.date | None = None,
) -> dict[str, Any]:
    require_member(leaderboard_id, viewer_aliases)
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

    viewer_member = is_member(leaderboard_id, viewer_aliases)
    viewer_rank = None
    viewer_entry = None
    if viewer_member is not None:
        for entry in entries:
            if entry["display_name"] == viewer_member["display_name"] and (
                entry.get("handle") == viewer_member.get("handle")
                or viewer_member.get("handle") is None
            ):
                viewer_rank = entry["rank"]
                viewer_entry = entry
                break
        if viewer_rank is None:
            for entry in entries:
                if entry["display_name"] == viewer_member["display_name"]:
                    viewer_rank = entry["rank"]
                    viewer_entry = entry
                    break

    return {
        "leaderboard_id": leaderboard_id,
        "name": group["name"],
        "visibility": group["visibility"],
        "week_start": start.isoformat(),
        "viewer_rank": viewer_rank,
        "viewer_entry": viewer_entry,
        "entries": entries,
    }


def viewer_weekly_me(
    leaderboard_id: str,
    viewer_aliases: list[str],
) -> dict[str, Any]:
    standings = weekly_standings(leaderboard_id, viewer_aliases)
    entry = standings.get("viewer_entry")
    if entry is None:
        raise APIError("VIEWER_NOT_RANKED", "No weekly activity found for you yet.", 404)
    return {
        "leaderboard_id": leaderboard_id,
        "week_start": standings["week_start"],
        "rank": standings["viewer_rank"],
        **entry,
    }
