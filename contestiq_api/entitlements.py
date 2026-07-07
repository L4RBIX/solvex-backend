"""Entitlement plans, feature gates, usage limits, and response shaping (Phase 06).

The paywall is backend-owned: premium endpoints resolve the caller's plan
server-side and shape/deny the response. Anonymous callers are free-tier.

Entitlement matrix (None = unlimited):

feature                      free   premium_student  team   event  admin
weak_skills_visible          3      None             None   None   None
daily_queue_items            2      None             None   None   None
plan_preview_days            1      None             None   None   None
plan_14_day                  no     yes              yes    no     yes
weekly_report                no     yes              yes    yes    yes
verification_attempts_week   1      10               10     None   None
analysis_runs_per_day        3      50               50     50     None
coach_dashboard              no     no               yes    no     yes
event_dashboard              no     no               no     yes    yes
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import Request

from contestiq_api import auth
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError

PLANS = ("free", "premium_student", "team", "event", "admin")
PLAN_PRIORITY = {"admin": 4, "team": 3, "event": 2, "premium_student": 1, "free": 0}

PLAN_FEATURES: dict[str, dict[str, Any]] = {
    "free": {
        "weak_skills_visible": 3,
        "daily_queue_items": 2,
        "plan_preview_days": 1,
        "plan_14_day": False,
        "weekly_report": False,
        "verification_attempts_per_week": 1,
        "analysis_runs_per_day": 3,
        "coach_dashboard": False,
        "event_dashboard": False,
        "shareable_badges": False,
    },
    "premium_student": {
        "weak_skills_visible": None,
        "daily_queue_items": None,
        "plan_preview_days": None,
        "plan_14_day": True,
        "weekly_report": True,
        "verification_attempts_per_week": 10,
        "analysis_runs_per_day": 50,
        "coach_dashboard": False,
        "event_dashboard": False,
        "shareable_badges": True,
    },
    "team": {
        "weak_skills_visible": None,
        "daily_queue_items": None,
        "plan_preview_days": None,
        "plan_14_day": True,
        "weekly_report": True,
        "verification_attempts_per_week": 10,
        "analysis_runs_per_day": 50,
        "coach_dashboard": True,
        "event_dashboard": False,
        "shareable_badges": True,
    },
    "event": {
        "weak_skills_visible": None,
        "daily_queue_items": None,
        "plan_preview_days": None,
        "plan_14_day": False,
        "weekly_report": True,
        "verification_attempts_per_week": None,
        "analysis_runs_per_day": 50,
        "coach_dashboard": False,
        "event_dashboard": True,
        "shareable_badges": False,
    },
    "admin": {
        "weak_skills_visible": None,
        "daily_queue_items": None,
        "plan_preview_days": None,
        "plan_14_day": True,
        "weekly_report": True,
        "verification_attempts_per_week": None,
        "analysis_runs_per_day": None,
        "coach_dashboard": True,
        "event_dashboard": True,
        "shareable_badges": True,
    },
}


def grant_entitlement(
    user_id: str,
    plan: str,
    source: str,
    granted_by: str,
    reference: str | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    if plan not in PLANS or plan == "free":
        raise APIError("INVALID_PLAN", f"plan must be one of: {', '.join(p for p in PLANS if p != 'free')}", 422)
    grant_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO entitlement_grants (grant_id, user_id, plan, source, reference, granted_by, granted_at, expires_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (grant_id, user_id, plan, source, reference, granted_by, store._now(), expires_at),
        )
    from contestiq_api import product_events

    product_events.track("premium_conversion", f"user:{user_id}", {"plan": plan, "source": source})
    return {"grant_id": grant_id, "user_id": user_id, "plan": plan, "source": source, "expires_at": expires_at}


def revoke_entitlement(user_id: str, plan: str) -> int:
    with store.connect() as conn:
        cursor = conn.execute(
            "UPDATE entitlement_grants SET revoked_at = ? WHERE user_id = ? AND plan = ? AND revoked_at IS NULL",
            (store._now(), user_id, plan),
        )
    return cursor.rowcount


def active_grants(user_id: str) -> list[dict[str, Any]]:
    now = store._now()
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM entitlement_grants WHERE user_id = ? AND revoked_at IS NULL"
            " AND (expires_at IS NULL OR expires_at > ?) ORDER BY granted_at DESC",
            (user_id, now),
        ).fetchall()
    return [dict(row) for row in rows]


def effective_plan(user: dict[str, Any] | None) -> str:
    if user is None:
        return "free"
    if user.get("role") == "admin":
        return "admin"
    grants = active_grants(user["user_id"])
    best = "free"
    for grant in grants:
        if PLAN_PRIORITY.get(grant["plan"], 0) > PLAN_PRIORITY[best]:
            best = grant["plan"]
    return best


def plan_context(request: Request) -> dict[str, Any]:
    """FastAPI dependency: resolve caller → (user, plan, features, usage subject)."""
    settings_admin = request.headers.get("X-Admin-Key")
    if settings_admin:
        try:
            admin = auth.require_admin(request)
            return {"user": admin, "plan": "admin", "features": PLAN_FEATURES["admin"], "subject": "admin"}
        except APIError:
            pass  # fall through to normal resolution
    user = auth.current_user(request)
    plan = effective_plan(user)
    subject = f"user:{user['user_id']}" if user else f"anon:{request.client.host if request.client else 'unknown'}"
    return {"user": user, "plan": plan, "features": PLAN_FEATURES[plan], "subject": subject}


def require_feature(ctx: dict[str, Any], feature: str) -> None:
    if not ctx["features"].get(feature):
        raise APIError(
            "PREMIUM_REQUIRED",
            f"The '{feature}' feature requires a premium plan. Current plan: {ctx['plan']}.",
            402,
        )


# ─── Usage limits ────────────────────────────────────────────────────────────


def check_and_count_usage(ctx: dict[str, Any], feature: str, window: str = "day") -> None:
    """Increment usage for the caller; raise 429 once past the plan limit."""
    limit = ctx["features"].get(feature)
    if limit is None:
        return  # unlimited
    if window == "week":
        today = dt.date.today()
        window_start = (today - dt.timedelta(days=today.weekday())).isoformat()
    else:
        window_start = dt.date.today().isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO usage_limits (subject, feature, window_start, used) VALUES (?, ?, ?, 0)"
            " ON CONFLICT(subject, feature, window_start) DO NOTHING",
            (ctx["subject"], feature, window_start),
        )
        row = conn.execute(
            "SELECT used FROM usage_limits WHERE subject = ? AND feature = ? AND window_start = ?",
            (ctx["subject"], feature, window_start),
        ).fetchone()
        if row["used"] >= limit:
            raise APIError(
                "USAGE_LIMIT_EXCEEDED",
                f"The '{feature}' limit for the {ctx['plan']} plan ({limit}/{window}) is exhausted.",
                429,
            )
        conn.execute(
            "UPDATE usage_limits SET used = used + 1 WHERE subject = ? AND feature = ? AND window_start = ?",
            (ctx["subject"], feature, window_start),
        )


def usage_summary(subject: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT feature, window_start, used FROM usage_limits WHERE subject = ? ORDER BY window_start DESC LIMIT 50",
            (subject,),
        ).fetchall()
    return [dict(row) for row in rows]


# ─── Response shaping (backend paywall) ──────────────────────────────────────

WEAKNESS_PRIORITY_STATUSES = (
    "likely_weakness",
    "possible_weakness",
    "historical_weakness_recent_improvement",
    "underexposed",
)


def shape_weakness_response(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Free tier sees the top 3 weak skills; the rest are counted, not shown."""
    limit = ctx["features"]["weak_skills_visible"]
    if limit is None:
        return payload
    skills = payload.get("skills", [])
    weak = [s for s in skills if s["status"] in WEAKNESS_PRIORITY_STATUSES]
    weak.sort(key=lambda s: (-s["severity"], -s["confidence"], s["skill_id"]))
    visible = weak[:limit]
    if len(visible) < limit:
        rest = [s for s in skills if s not in visible]
        rest.sort(key=lambda s: (-s["severity"], s["skill_id"]))
        visible = visible + rest[: limit - len(visible)]
    shown_ids = {s["skill_id"] for s in visible}
    return {
        **payload,
        "skills": [s for s in skills if s["skill_id"] in shown_ids],
        "locked_skills_count": len(skills) - len(shown_ids),
        "plan": ctx["plan"],
        "upgrade_hint": "Premium unlocks the full weakness map.",
    }


def shape_queue_response(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    limit = ctx["features"]["daily_queue_items"]
    items = payload.get("items", [])
    if limit is None or len(items) <= limit:
        return payload
    locked = [
        {"slot": item["slot"], "mode": item["mode"], "locked": True}
        for item in items[limit:]
    ]
    return {
        **payload,
        "items": items[:limit] + locked,
        "plan": ctx["plan"],
        "upgrade_hint": "Premium unlocks the full daily queue.",
    }


def shape_plan_response(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    preview_days = ctx["features"]["plan_preview_days"]
    if preview_days is None:
        return payload
    days = []
    for day in payload.get("days", []):
        if day["day_number"] <= preview_days:
            days.append(day)
        else:
            days.append({
                "day_number": day["day_number"],
                "theme": day["theme"],
                "locked": True,
                "item_count": len(day.get("items", [])),
                "items": [],
            })
    return {**payload, "days": days, "plan": ctx["plan"], "upgrade_hint": "Premium unlocks the full plan."}
