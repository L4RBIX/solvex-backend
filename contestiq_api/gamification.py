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

# Human-readable labels for the XP activity breakdown (Phase G2 transparency).
# These are the only event details ever exposed to the client — raw
# product_event payloads (`properties`) are never included in any response.
EVENT_LABELS: dict[str, str] = {
    "first_analysis_completed": "Completed first analysis",
    "first_queue_generated": "Generated first queue",
    "daily_queue_generated": "Generated today's queue",
    "feedback_submitted": "Submitted problem feedback",
    "weekly_report_generated": "Viewed weekly report",
    "verification_attempted": "Attempted SkillTrace verification",
    "premium_conversion": "Upgraded to premium",
    "plan_started": "Started a training plan",
}

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

# Categories: onboarding | consistency | verification | premium.
# Rarity: common | uncommon | rare. Purely descriptive labels for the widget —
# no mastery claim, no social comparison, no public profile attached.
BADGE_DEFS: tuple[dict[str, str], ...] = (
    {"id": "first_analysis", "name": "First Diagnosis", "description": "Completed your first SolveX analysis.",
     "category": "onboarding", "rarity": "common"},
    {"id": "first_queue", "name": "Queued Up", "description": "Generated your first daily training queue.",
     "category": "onboarding", "rarity": "common"},
    {"id": "feedback_loop", "name": "Feedback Loop", "description": "Submitted your first problem feedback.",
     "category": "onboarding", "rarity": "common"},
    {"id": "three_day_streak", "name": "3-Day Streak", "description": "Trained on 3 consecutive days.",
     "category": "consistency", "rarity": "uncommon"},
    {"id": "seven_day_streak", "name": "7-Day Streak", "description": "Trained on 7 consecutive days.",
     "category": "consistency", "rarity": "rare"},
    {"id": "first_weekly_report", "name": "First Weekly Report", "description": "Generated your first weekly progress report.",
     "category": "consistency", "rarity": "uncommon"},
    {"id": "first_verification_attempt", "name": "Put To The Test", "description": "Attempted your first SkillTrace verification.",
     "category": "verification", "rarity": "uncommon"},
    {"id": "beta_premium", "name": "Beta Premium", "description": "Upgraded to a premium SolveX plan.",
     "category": "premium", "rarity": "rare"},
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


# ─── Recent XP events (Phase G2 transparency) ────────────────────────────────
#
# Per-event XP attribution replays history with the same two rules as
# compute_xp_total (each event type earns at most once per UTC day; the day
# total is capped by plan), so the per-event awards always sum to xp_total.
# Only event_type / label / xp / timestamp are exposed — never the raw
# product_event `properties` payload, which may carry internal identifiers.

RECENT_XP_EVENTS_LIMIT = 10


def compute_recent_xp_events(
    events: list[dict[str, Any]], daily_cap: int, limit: int = RECENT_XP_EVENTS_LIMIT
) -> list[dict[str, Any]]:
    day_types: dict[dt.date, set[str]] = {}
    day_totals: dict[dt.date, int] = {}
    attributed: list[dict[str, Any]] = []
    for event in _meaningful(events):  # chronological replay
        day = _event_date(event)
        etype = event["event_type"]
        awarded_types = day_types.setdefault(day, set())
        raw = XP_RULES[etype]
        if etype in awarded_types:
            # Repeating the same action within a day never re-awards XP —
            # this is the anti-farming rule, not the daily cap.
            awarded, cap_applied = 0, False
        else:
            remaining = max(0, daily_cap - day_totals.get(day, 0))
            awarded = min(raw, remaining)
            cap_applied = awarded < raw
            awarded_types.add(etype)
            day_totals[day] = day_totals.get(day, 0) + awarded
        attributed.append({
            "event_type": etype,
            "label": EVENT_LABELS.get(etype, etype),
            "xp_awarded": awarded,
            "occurred_at": event["created_at"],
            "daily_cap_applied": cap_applied,
        })
    return list(reversed(attributed[-limit:]))  # most recent first


# ─── Quests (Phase G2) ────────────────────────────────────────────────────────
#
# Quests are progress UI only: they are derived from the same product_events
# and award no XP themselves, so they can never double-count or bypass the
# daily cap. Completion is judged per UTC day / ISO week (Monday start).

DAILY_QUEST_DEFS: tuple[tuple[str, str, frozenset[str]], ...] = (
    ("complete_analysis_today", "Complete an analysis", frozenset({"first_analysis_completed"})),
    ("generate_queue_today", "Generate today's queue", frozenset({"first_queue_generated", "daily_queue_generated"})),
    ("submit_feedback_today", "Give feedback on one recommendation", frozenset({"feedback_submitted"})),
    ("view_weekly_report_today", "View weekly report", frozenset({"weekly_report_generated"})),
    ("start_plan_today", "Start a training plan", frozenset({"plan_started"})),
    ("attempt_verification_today", "Attempt SkillTrace verification", frozenset({"verification_attempted"})),
)

_QUEUE_EVENT_TYPES = frozenset({"first_queue_generated", "daily_queue_generated"})


def compute_daily_quests(events: list[dict[str, Any]], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    first_ts_today: dict[str, str] = {}
    for event in _meaningful(events):
        if _event_date(event) == today:
            first_ts_today.setdefault(event["event_type"], event["created_at"])

    quests = []
    completed_count = 0
    for quest_id, label, qualifying in DAILY_QUEST_DEFS:
        completed_at = min((first_ts_today[t] for t in qualifying if t in first_ts_today), default=None)
        completed = completed_at is not None
        if completed:
            completed_count += 1
        quests.append({"id": quest_id, "label": label, "completed": completed, "completed_at": completed_at})

    return {
        "date": today.isoformat(),
        "completed_count": completed_count,
        "total_count": len(DAILY_QUEST_DEFS),
        "quests": quests,
    }


def week_start_for(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())  # ISO week, Monday start


def compute_weekly_quests(events: list[dict[str, Any]], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    start = week_start_for(today)
    end = start + dt.timedelta(days=7)
    week_events = [e for e in _meaningful(events) if start <= _event_date(e) < end]

    active_days = {_event_date(e) for e in week_events}
    # Distinct days (not raw event count) so regenerating one day's queue
    # repeatedly cannot complete a "3 queues" quest.
    queue_days = {_event_date(e) for e in week_events if e["event_type"] in _QUEUE_EVENT_TYPES}
    feedback_count = sum(1 for e in week_events if e["event_type"] == "feedback_submitted")
    report_done = any(e["event_type"] == "weekly_report_generated" for e in week_events)
    verification_done = any(e["event_type"] == "verification_attempted" for e in week_events)

    raw_quests: tuple[tuple[str, str, int, int], ...] = (
        ("active_3_days_this_week", "Train on 3 different days this week", len(active_days), 3),
        ("complete_3_queues_this_week", "Generate 3 daily queues this week", len(queue_days), 3),
        ("submit_3_feedback_this_week", "Give feedback on 3 recommendations", feedback_count, 3),
        ("complete_weekly_report", "View weekly report", 1 if report_done else 0, 1),
        ("attempt_one_verification", "Attempt one SkillTrace verification", 1 if verification_done else 0, 1),
    )

    quests = []
    completed_count = 0
    for quest_id, label, progress, target in raw_quests:
        completed = progress >= target
        if completed:
            completed_count += 1
        quests.append({
            "id": quest_id,
            "label": label,
            "completed": completed,
            "progress": min(progress, target),
            "target": target,
        })

    return {
        "week_start": start.isoformat(),
        "completed_count": completed_count,
        "total_count": len(raw_quests),
        "quests": quests,
    }


# ─── Milestones (Phase G2) ────────────────────────────────────────────────────


def compute_milestones(
    xp_total: int,
    streak: dict[str, Any],
    daily_goal: dict[str, Any],
    weekly_quests: dict[str, Any],
) -> list[dict[str, Any]]:
    """Small forward-looking targets derived from already-computed state.
    Ordered by usefulness; the widget shows only the first few."""
    milestones: list[dict[str, Any]] = []

    level = level_for_xp(xp_total)
    milestones.append({
        "id": "next_level",
        "label": f"Reach Level {level + 1}",
        "progress": xp_total,
        "target": level_threshold(level + 1),
    })

    current_streak = int(streak.get("current", 0))
    if current_streak < 3:
        milestones.append({"id": "next_streak_badge", "label": "Reach a 3-day streak", "progress": current_streak, "target": 3})
    elif current_streak < 7:
        milestones.append({"id": "next_streak_badge", "label": "Reach a 7-day streak", "progress": current_streak, "target": 7})

    if not daily_goal.get("completed"):
        milestones.append({
            "id": "next_daily_goal",
            "label": "Complete today's daily goal",
            "progress": daily_goal.get("completed_count", 0),
            "target": daily_goal.get("required_count", DAILY_GOAL_REQUIRED_COUNT),
        })

    next_weekly = next((q for q in weekly_quests.get("quests", []) if not q["completed"]), None)
    if next_weekly is not None:
        milestones.append({
            "id": "next_weekly_quest",
            "label": next_weekly["label"],
            "progress": next_weekly["progress"],
            "target": next_weekly["target"],
        })

    return milestones


def resolve_daily_cap(plan: str) -> int:
    return DAILY_XP_CAP.get(plan, DEFAULT_DAILY_XP_CAP)


def compute_weekly_stats(
    events: list[dict[str, Any]],
    plan: str,
    week_start: dt.date | None = None,
) -> dict[str, Any]:
    """Derive one member's ISO-week training stats from product_events.

    Used by private weekly leaderboards (Phase G3). Reuses the same XP rules,
    daily caps, and meaningful-event filter as G1/G2 — page visits and other
    non-training events never enter product_events, so they cannot inflate scores.
    """
    today = dt.datetime.now(dt.timezone.utc).date()
    start = week_start or week_start_for(today)
    end = start + dt.timedelta(days=7)
    daily_cap = resolve_daily_cap(plan)
    meaningful = _meaningful(events)
    week_events = [e for e in meaningful if start <= _event_date(e) < end]

    by_day: dict[dt.date, set[str]] = {}
    for event in week_events:
        by_day.setdefault(_event_date(event), set()).add(event["event_type"])

    weekly_xp = 0
    daily_goals_completed = 0
    for day, types in by_day.items():
        day_raw = sum(XP_RULES[t] for t in types)
        weekly_xp += min(day_raw, daily_cap)
        completed_categories = sum(1 for _gid, _label, qualifying in GOAL_ITEM_DEFS if types & qualifying)
        if completed_categories >= DAILY_GOAL_REQUIRED_COUNT:
            daily_goals_completed += 1

    active_days = len(by_day)
    queues_generated = sum(1 for e in week_events if e["event_type"] in _QUEUE_EVENT_TYPES)
    feedback_count = sum(1 for e in week_events if e["event_type"] == "feedback_submitted")
    weekly_report_viewed = any(e["event_type"] == "weekly_report_generated" for e in week_events)
    verification_attempts = sum(1 for e in week_events if e["event_type"] == "verification_attempted")

    all_time_xp = compute_xp_total(meaningful, daily_cap)
    badges = compute_badges(meaningful)
    badges_earned_this_week = sum(
        1 for b in badges
        if start.isoformat() <= str(b.get("earned_at", ""))[:10] < end.isoformat()
    )

    return {
        "week_start": start.isoformat(),
        "weekly_xp": weekly_xp,
        "active_days": active_days,
        "queues_generated": queues_generated,
        "feedback_count": feedback_count,
        "weekly_report_viewed": weekly_report_viewed,
        "verification_attempts": verification_attempts,
        "daily_goals_completed": daily_goals_completed,
        "badges_earned_this_week": badges_earned_this_week,
        "level": level_for_xp(all_time_xp),
    }


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
    streak = compute_streak(meaningful, today)
    daily_goal = compute_daily_goal(meaningful, today)
    weekly_quests = compute_weekly_quests(meaningful, today)
    return {
        "subject": subject,
        "plan": plan,
        "xp_total": xp_total,
        "level": level_for_xp(xp_total),
        "level_progress": level_progress(xp_total),
        "streak": streak,
        "daily_goal": daily_goal,
        "badges": compute_badges(meaningful),
        # Phase G2 additions (purely additive — G1 fields above are unchanged):
        "recent_xp_events": compute_recent_xp_events(meaningful, daily_cap),
        "daily_quests": compute_daily_quests(meaningful, today),
        "weekly_quests": weekly_quests,
        "milestones": compute_milestones(xp_total, streak, daily_goal, weekly_quests),
    }
