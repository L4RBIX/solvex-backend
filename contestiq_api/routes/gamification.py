"""v1 gamification endpoints (Phase G1): XP, levels, streak, daily goal, badges.

Everything here is read-derived from `product_events` (Phase 10) — there is no
gamification-owned table. A subject is resolved from the `handle` query param
(the CF handle the learner is training with — matches how analysis, queues,
and plans already identify anonymous/free learners) and/or the bearer token
(premium/verification actions, which are tracked per `user_id`). Both are
optional and this endpoint never raises for a caller with neither: it simply
returns an empty "anonymous" snapshot, so a missing handle can never break the
/analyze page.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, entitlements, gamification, metrics, product_events
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle

router = APIRouter(prefix="/api/v1/gamification")

_EMPTY_SUBJECT = "anonymous"


def _timed(name: str):
    started = time.monotonic()

    def finish(ok: bool) -> None:
        metrics.observe(f"gamification_{name}_latency_ms", (time.monotonic() - started) * 1000)
        if not ok:
            metrics.inc("gamification_errors_total")
            metrics.inc(f"gamification_{name}_errors_total")

    return finish


def resolve_subject(request: Request, handle: str | None) -> dict[str, Any]:
    """Resolve one or more product_events subject aliases for the caller.

    - `handle` (query param) maps to the `handle:<cf handle>` alias used by
      analysis/queue/plan/weekly-report events.
    - A bearer token (if present) maps to the `user:<user_id>` alias used by
      verification/premium events, and — if that user account has a linked
      handle and none was passed explicitly — also contributes the matching
      `handle:` alias so both event styles merge into one learner.
    """
    ctx = entitlements.plan_context(request)
    aliases: list[str] = []
    primary: str | None = None

    cleaned_handle: str | None = None
    if handle:
        cleaned_handle = validate_handle(handle)
        alias = f"handle:{store.canonical_handle(cleaned_handle)}"
        aliases.append(alias)
        primary = alias

    user = ctx.get("user")
    user_id = user.get("user_id") if user else None
    if user_id:
        user_alias = f"user:{user_id}"
        aliases.append(user_alias)
        if primary is None:
            primary = user_alias
        if cleaned_handle is None:
            stored_handle = user.get("handle")
            if stored_handle:
                handle_alias = f"handle:{store.canonical_handle(stored_handle)}"
                if handle_alias not in aliases:
                    aliases.append(handle_alias)
                if primary is None:
                    primary = handle_alias

    plan = ctx["plan"]
    if not aliases:
        return {"aliases": [], "subject": _EMPTY_SUBJECT, "plan": plan}
    return {"aliases": aliases, "subject": primary, "plan": plan}


def _snapshot_for(request: Request, handle: str | None) -> dict[str, Any]:
    resolved = resolve_subject(request, handle)
    events = product_events.events_for_subjects(resolved["aliases"])
    return gamification.build_snapshot(resolved["subject"], resolved["plan"], events)


@router.get("/me")
def gamification_me(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    finish = _timed("me")
    try:
        snapshot = _snapshot_for(request, handle)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return snapshot


@router.get("/streak")
def gamification_streak(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    finish = _timed("streak")
    try:
        snapshot = _snapshot_for(request, handle)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "streak": snapshot["streak"]}


@router.get("/daily-goal")
def gamification_daily_goal(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    finish = _timed("daily_goal")
    try:
        snapshot = _snapshot_for(request, handle)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "daily_goal": snapshot["daily_goal"]}


@router.get("/badges")
def gamification_badges(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    finish = _timed("badges")
    try:
        snapshot = _snapshot_for(request, handle)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "badges": snapshot["badges"]}


@router.get("/activity")
def gamification_activity(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    """Recent XP breakdown (Phase G2 transparency): the last few meaningful
    events with the XP each one actually awarded, including 0-XP entries when
    the daily cap (or the once-per-day-per-type rule) applied."""
    finish = _timed("activity")
    try:
        snapshot = _snapshot_for(request, handle)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"subject": snapshot["subject"], "recent_xp_events": snapshot["recent_xp_events"]}


@router.get("/quests")
def gamification_quests(request: Request, handle: str | None = Query(default=None, min_length=3, max_length=24)):
    """Daily + weekly quests (Phase G2). Progress UI only — quests never award
    XP themselves, so they cannot double-count or bypass the daily cap."""
    finish = _timed("quests")
    try:
        snapshot = _snapshot_for(request, handle)
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
    admin surface."""
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
        snapshot = gamification.build_snapshot(primary or _EMPTY_SUBJECT, plan, events)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)

    auth.audit(admin["actor"], "gamification_recompute", primary, {"handle": payload.handle, "user_id": payload.user_id})
    return snapshot
