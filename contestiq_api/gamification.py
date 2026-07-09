"""Gamification (Phase G1): XP, levels, streaks, a daily goal, and badges.

Design principles (do not weaken these without re-reading the product spec):

- `product_events` (Phase 10) stays the single source of truth. Nothing here
  writes a new table; every number is *derived* by replaying a subject's
  meaningful-action history. That makes badges/streak/XP naturally idempotent:
  recomputing never double-counts and never double-fires a "first" badge.
- Only real learning actions count (see `MEANINGFUL_EVENT_TYPES`). Page
  visits, tab opens, refreshes, and failed backend calls are never recorded
  as product_events in the first place, so they structurally cannot leak in
  here — there is no "visited /analyze" event to accidentally reward.
- XP is capped per UTC calendar day so no single action (or repeatedly firing
  the same action) can be farmed past the plan's daily ceiling.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

# ─── Meaningful actions & XP rules (v1) ──────────────────────────────────────

XP_RULES: dict[str, int] = {
    "first_analysis_completed": 20,
    "first_queue_generated": 10,
    "daily_queue_generated": 5,
    "feedback_submitted": 5,
    "weekly_report_generated": 20,
    "verification_attempted": 25,
    "premium_conversion": 50,
    "plan_started": 15,
}

MEANINGFUL_EVENT_TYPES = frozenset(XP_RULES)

# Daily XP cap by plan. Team/event/admin share a single higher beta ceiling
# per the spec (no dedicated per-plan entitlement exists yet for XP).
DAILY_XP_CAP: dict[str, int] = {
    "free": 50,
    "premium_student": 150,
    "team": 200,
    "event": 200,
    "admin": 200,
}
DEFAULT_DAILY_XP_CAP = DAILY_XP_CAP["free"]

# ─── Level formula ────────────────────────────────────────────────────────────
#
# Levels 1-5 are hand-picked product thresholds:
#   L1=0, L2=100, L3=250, L4=500, L5=900
# The per-level XP *increments* (100, 150, 250, 400) fit the quadratic
#   increment(n) = 25*n*(n-1) + 100      (n = the level being left, 1-indexed)
# exactly for n=1..4. We reuse that same formula to deterministically extend
# thresholds past level 5 so the sequence keeps increasing forever without
# another hardcoded table. (Verified by tests/test_gamification.py.)

_MAX_LEVEL_LOOKAHEAD = 500  # generous ceiling; XP would need to be enormous to exceed this


def _level_increment(from_level: int) -> int:
    return 25 * from_level * (from_level - 1) + 100


def level_threshold(level: int) -> int:
    """Total XP required to *reach* `level` (level 1 requires 0 XP)."""
    if level < 1:
        raise ValueError("level must be >= 1")
    xp = 0
    for n in range(1, level):
        xp += _level_increment(n)
    return xp


def level_for_xp(xp_total: int) -> int:
    level = 1
    xp = 0
    while level < _MAX_LEVEL_LOOKAHEAD:
        next_xp = xp + _level_increment(level)
        if xp_total < next_xp:
            break
        xp = next_xp
        level += 1
    return level


def level_progress(xp_total: int) -> dict[str, Any]:
    level = level_for_xp(xp_total)
    current_level_xp = level_threshold(level)
    next_level_xp = level_threshold(level + 1)
    span = max(1, next_level_xp - current_level_xp)
    progress_percent = int(round((xp_total - current_level_xp) / span * 100))
    progress_percent = max(0, min(100, progress_percent))
    return {
        "current_level_xp": current_level_xp,
        "next_level_xp": next_level_xp,
        "progress_percent": progress_percent,
    }


# ─── Daily goal (v1) ──────────────────────────────────────────────────────────
#
# Complete once >= DAILY_GOAL_REQUIRED_COUNT distinct goal categories have a
# qualifying event on that UTC calendar day. Categories, not raw event counts,
# so repeating one action does not itself complete the goal.

DAILY_GOAL_REQUIRED_COUNT = 2

# (goal_id, label, event types that satisfy this goal item)
GOAL_ITEM_DEFS: tuple[tuple[str, str, frozenset[str]], ...] = (
    ("analysis_completed", "Complete an analysis", frozenset({"first_analysis_completed"})),
    ("queue_generated", "Generate today's queue", frozenset({"first_queue_generated", "daily_queue_generated"})),
    ("feedback_submitted", "Give feedback on a problem", frozenset({"feedback_submitted"})),
    ("weekly_report_generated", "View your weekly report", frozenset({"weekly_report_generated"})),
    ("verification_attempted", "Attempt a SkillTrace verification", frozenset({"verification_attempted"})),
    ("plan_started", "Start a training plan", frozenset({"plan_started"})),
)

# ─── Badges (v1) ──────────────────────────────────────────────────────────────

BADGE_DEFS: tuple[dict[str, str], ...] = (
    {"id": "first_analysis", "name": "First Diagnosis", "description": "Completed your first SolveX analysis."},
    {"id": "first_queue", "name": "Queued Up", "description": "Generated your first daily training queue."},
    {"id": "feedback_loop", "name": "Feedback Loop", "description": "Submitted your first problem feedback."},
    {"id": "three_day_streak", "name": "3-Day Streak", "description": "Trained on 3 consecutive days."},
    {"id": "seven_day_streak", "name": "7-Day Streak", "description": "Trained on 7 consecutive days."},
    {"id": "first_weekly_report", "name": "First Weekly Report", "description": "Generated your first weekly progress report."},
    {"id": "first_verification_attempt", "name": "Put To The Test", "description": "Attempted your first SkillTrace verification."},
    {"id": "beta_premium", "name": "Beta Premium", "description": "Upgraded to a premium SolveX plan."},
)

_BADGE_FIRST_EVENT: dict[str, str] = {
    "first_analysis": "first_analysis_completed",
    "first_queue": "first_queue_generated",
    "feedback_loop": "feedback_submitted",
    "first_weekly_report": "weekly_report_generated",
    "first_verification_attempt": "verification_attempted",
    "beta_premium": "premium_conversion",
}
_STREAK_BADGE_THRESHOLD: dict[str, int] = {
    "three_day_streak": 3,
    "seven_day_streak": 7,
}


def _event_date(event: dict[str, Any]) -> dt.date:
    return dt.date.fromisoformat(str(event["created_at"])[:10])


def _meaningful(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (e for e in events if e.get("event_type") in MEANINGFUL_EVENT_TYPES),
        key=lambda e: e["created_at"],
    )


def compute_xp_total(events: list[dict[str, Any]], daily_cap: int) -> int:
    """Sum daily-capped XP. Within a day, each event *type* contributes its
    XP at most once (repeating one action all day cannot out-earn the cap by
    itself); distinct action types on the same day still stack, up to the
    plan's daily cap."""
    by_day: dict[dt.date, set[str]] = {}
    for event in _meaningful(events):
        by_day.setdefault(_event_date(event), set()).add(event["event_type"])
    total = 0
    for _day, types in by_day.items():
        day_raw = sum(XP_RULES[t] for t in types)
        total += min(day_raw, daily_cap)
    return total


def _active_dates(events: list[dict[str, Any]]) -> list[dt.date]:
    return sorted({_event_date(e) for e in _meaningful(events)})


def compute_streak(events: list[dict[str, Any]], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    active = _active_dates(events)
    if not active:
        return {"current": 0, "longest": 0, "last_active_date": None, "today_completed": False}

    active_set = set(active)
    longest = 0
    run = 0
    prev: dt.date | None = None
    for day in active:
        if prev is not None and (day - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = day

    today_completed = today in active_set
    anchor = today if today_completed else today - dt.timedelta(days=1)
    current = 0
    cursor = anchor
    while cursor in active_set:
        current += 1
        cursor -= dt.timedelta(days=1)
    if anchor not in active_set:
        current = 0

    return {
        "current": current,
        "longest": longest,
        "last_active_date": active[-1].isoformat(),
        "today_completed": today_completed,
    }


def compute_daily_goal(events: list[dict[str, Any]], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    today_types = {e["event_type"] for e in _meaningful(events) if _event_date(e) == today}

    items = []
    completed_count = 0
    for goal_id, label, qualifying in GOAL_ITEM_DEFS:
        completed = bool(today_types & qualifying)
        if completed:
            completed_count += 1
        items.append({"id": goal_id, "label": label, "completed": completed})

    return {
        "date": today.isoformat(),
        "completed": completed_count >= DAILY_GOAL_REQUIRED_COUNT,
        "completed_count": completed_count,
        "required_count": DAILY_GOAL_REQUIRED_COUNT,
        "items": items,
    }


def _streak_milestone_date(active_dates: list[dt.date], threshold: int) -> dt.date | None:
    run = 0
    prev: dt.date | None = None
    for day in active_dates:
        if prev is not None and (day - prev).days == 1:
            run += 1
        else:
            run = 1
        prev = day
        if run == threshold:
            return day
    return None


def compute_badges(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    meaningful = _meaningful(events)
    active_dates = _active_dates(meaningful)

    first_at: dict[str, str] = {}
    for event in meaningful:  # ascending order: first hit wins
        first_at.setdefault(event["event_type"], event["created_at"])

    day_first_event: dict[dt.date, str] = {}
    for event in meaningful:
        day = _event_date(event)
        day_first_event.setdefault(day, event["created_at"])

    earned: list[dict[str, Any]] = []
    for badge in BADGE_DEFS:
        badge_id = badge["id"]
        earned_at: str | None = None
        if badge_id in _BADGE_FIRST_EVENT:
            earned_at = first_at.get(_BADGE_FIRST_EVENT[badge_id])
        elif badge_id in _STREAK_BADGE_THRESHOLD:
            milestone_date = _streak_milestone_date(active_dates, _STREAK_BADGE_THRESHOLD[badge_id])
            if milestone_date is not None:
                earned_at = day_first_event.get(milestone_date)
        if earned_at is not None:
            earned.append({**badge, "earned_at": earned_at})
    return earned


def resolve_daily_cap(plan: str) -> int:
    return DAILY_XP_CAP.get(plan, DEFAULT_DAILY_XP_CAP)


def build_snapshot(
    subject: str,
    plan: str,
    events: list[dict[str, Any]],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Pure function: subject identity + plan + raw event history -> the full
    `/gamification/me` response contract. No secrets, no payment fields, no
    admin data, no other subjects' data — only this subject's derived state."""
    now = now or dt.datetime.now(dt.timezone.utc)
    today = now.date()
    daily_cap = resolve_daily_cap(plan)
    meaningful = _meaningful(events)

    xp_total = compute_xp_total(meaningful, daily_cap)
    return {
        "subject": subject,
        "plan": plan,
        "xp_total": xp_total,
        "level": level_for_xp(xp_total),
        "level_progress": level_progress(xp_total),
        "streak": compute_streak(meaningful, today),
        "daily_goal": compute_daily_goal(meaningful, today),
        "badges": compute_badges(meaningful),
    }
