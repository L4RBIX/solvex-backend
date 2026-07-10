"""v1 gamification endpoints (Phase G1): XP, levels, streak, daily goal, badges.

Everything here is read-derived from `product_events` (Phase 10) — there is
no gamification-owned table.

Security: every private endpoint below requires a bearer token and ALWAYS
returns the authenticated caller's own data — never a caller-supplied
`?handle=`. A Codeforces handle is public data and must never be trusted as
identity; the subject is `user:<id>` plus the caller's VERIFIED handle (if
any — see contestiq_api.handles), never an arbitrary query param.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from contestiq_api import auth, entitlements, gamification, metrics, product_events
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle

router = APIRouter(prefix="/api/v1/gamification")


def _timed(name: str):
    started = time.monotonic()

    def finish(ok: bool) -> None:
        metrics.observe(f"gamification_{name}_latency_ms", (time.monotonic() - started) * 1000)
        if not ok:
            metrics.inc("gamification_errors_total")
            metrics.inc(f"gamification_{name}_errors_total")

    return finish


def _snapshot_for(caller: dict[str, Any]) -> dict[str, Any]:
    user = auth.get_user(caller["user_id"])
    plan = entitlements.effective_plan(user)
    events = product_events.events_for_account(caller["user_id"])
    return gamification.build_snapshot(caller["subject"], plan, events)


@router.get("/me")
def gamification_me(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("me")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return snapshot


@router.get("/streak")
def gamification_streak(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("streak")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "streak": snapshot["streak"]}


@router.get("/daily-goal")
def gamification_daily_goal(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("daily_goal")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "daily_goal": snapshot["daily_goal"]}


@router.get("/badges")
def gamification_badges(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("badges")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "badges": snapshot["badges"]}


@router.get("/activity")
def gamification_activity(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    """Recent XP breakdown (Phase G2 transparency): the last few meaningful
    events with the XP each one actually awarded, including 0-XP entries when
    the daily cap (or the once-per-day-per-type rule) applied."""
    finish = _timed("activity")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "recent_xp_events": snapshot["recent_xp_events"]}


@router.get("/quests")
def gamification_quests(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    """Daily + weekly quests (Phase G2). Progress UI only — quests never award
    XP themselves, so they cannot double-count or bypass the daily cap."""
    finish = _timed("quests")
    try:
        snapshot = _snapshot_for(caller)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {
        "subject": snapshot["subject"],
        "daily_quests": snapshot["daily_quests"],
        "weekly_quests": snapshot["weekly_quests"],
        "milestones": snapshot["milestones"],
    }


class RecomputeRequest(BaseModel):
    handle: str | None = Field(default=None, min_length=3, max_length=24)
    user_id: str | None = None


@router.post("/recompute")
def gamification_recompute(payload: RecomputeRequest, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Admin-only manual recompute/inspection. Since gamification has no
    cache to invalidate (it always derives live from product_events), this
    simply replays a target subject's history on demand — useful for support
    ("why doesn't my badge show up?") without granting the browser any wider
    admin surface. Admin-supplied handle/user_id here is fine: it is not
    caller-controlled identity spoofing, it is an authenticated admin
    explicitly inspecting a specific account."""
    if not payload.handle and not payload.user_id:
        raise APIError("GAMIFICATION_TARGET_REQUIRED", "Provide a handle or user_id to recompute.", 422)

    finish = _timed("recompute")
    try:
        aliases: list[str] = []
        primary: str | None = None
        plan = "free"

        if payload.handle:
            cleaned = validate_handle(payload.handle)
            alias = f"handle:{store.canonical_handle(cleaned)}"
            aliases.append(alias)
            primary = alias
            linked_user = auth.get_user_by_handle(cleaned)
            if linked_user is not None:
                aliases.append(f"user:{linked_user['user_id']}")
                plan = entitlements.effective_plan(linked_user)

        if payload.user_id:
            target_user = auth.get_user(payload.user_id)
            if target_user is None:
                raise APIError("USER_NOT_FOUND", f"No user found with id {payload.user_id}.", 404)
            user_alias = f"user:{payload.user_id}"
            if user_alias not in aliases:
                aliases.append(user_alias)
            if primary is None:
                primary = user_alias
            plan = entitlements.effective_plan(target_user)
            if target_user.get("handle"):
                handle_alias = f"handle:{store.canonical_handle(target_user['handle'])}"
                if handle_alias not in aliases:
                    aliases.append(handle_alias)

        events = product_events.events_for_subjects(aliases)
        snapshot = gamification.build_snapshot(primary or "anonymous", plan, events)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)

    auth.audit(admin["actor"], "gamification_recompute", primary, {"handle": payload.handle, "user_id": payload.user_id})
    return snapshot
