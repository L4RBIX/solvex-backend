"""Codeforces profile history aggregates for the public analysis page.

Builds rating-change series and per-day activity from already-fetched
Codeforces payloads. All-time solved counts every unique problem identity with
at least one OK verdict — independent of catalog / recommendation eligibility.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

V_AC = "OK"


def problem_identity(sub: dict[str, Any]) -> str:
    """Stable unique-problem key for all-time solved accounting.

    Prefer contestId+index (including gym / unusual indexes). When contestId is
    absent, keep problemsetName+index+name so legitimate CF identities still
    count toward solved without collapsing into a single `0:…` bucket.
    """
    problem = sub.get("problem") or {}
    contest_id = problem.get("contestId")
    if contest_id is None:
        contest_id = sub.get("contestId")
    index = problem.get("index")
    if contest_id is not None and index:
        return f"{contest_id}:{index}"
    problemset = problem.get("problemsetName") or "problemset"
    name = problem.get("name") or "unknown"
    return f"{problemset}:{index or 'x'}:{name}"


def unique_accepted_problem_ids(submissions: list[dict[str, Any]]) -> set[str]:
    return {
        problem_identity(sub)
        for sub in submissions
        if sub.get("verdict") == V_AC
    }


def _utc_day(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()


def first_accepted_timestamps(submissions: list[dict[str, Any]]) -> dict[str, int]:
    """Earliest OK creationTimeSeconds per problem identity."""
    first: dict[str, int] = {}
    for sub in sorted(
        (s for s in submissions if s.get("verdict") == V_AC),
        key=lambda s: int(s.get("creationTimeSeconds") or 0),
    ):
        key = problem_identity(sub)
        ts = int(sub.get("creationTimeSeconds") or 0)
        if key not in first:
            first[key] = ts
    return first


def build_rating_history(rating_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in rating_rows:
        try:
            old_rating = int(row["oldRating"])
            new_rating = int(row["newRating"])
            ts = int(row["ratingUpdateTimeSeconds"])
        except (KeyError, TypeError, ValueError):
            continue
        events.append(
            {
                "contestId": row.get("contestId"),
                "contestName": row.get("contestName") or "",
                "ratingUpdateTimeSeconds": ts,
                "oldRating": old_rating,
                "newRating": new_rating,
                "delta": new_rating - old_rating,
            }
        )
    events.sort(key=lambda e: (e["ratingUpdateTimeSeconds"], e.get("contestId") or 0))
    return events


def build_activity(submissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate submissions and first-accepts per UTC calendar day."""
    by_day_subs: dict[str, int] = defaultdict(int)
    by_day_ok: dict[str, int] = defaultdict(int)
    first = first_accepted_timestamps(submissions)
    first_by_day: dict[str, set[str]] = defaultdict(set)
    for problem_id, ts in first.items():
        first_by_day[_utc_day(ts)].add(problem_id)

    for sub in submissions:
        ts = sub.get("creationTimeSeconds")
        if ts is None:
            continue
        day = _utc_day(int(ts))
        by_day_subs[day] += 1
        if sub.get("verdict") == V_AC:
            by_day_ok[day] += 1

    days = sorted(set(by_day_subs) | set(first_by_day))
    return [
        {
            "date": day,
            "submissions": by_day_subs.get(day, 0),
            "acceptedSubmissions": by_day_ok.get(day, 0),
            "uniqueSolved": len(first_by_day.get(day, ())),
        }
        for day in days
    ]


def _streaks(active_days: set[date], today: date) -> tuple[int, int]:
    """Return (current_streak, longest_streak) over UTC days with ≥1 first-AC.

    current_streak counts contiguous active days ending today or yesterday
    (so a quiet UTC today does not instantly zero an overnight streak).
    """
    if not active_days:
        return 0, 0

    longest = 0
    run = 0
    day = min(active_days)
    end = max(active_days)
    while day <= end:
        if day in active_days:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        day += timedelta(days=1)

    current = 0
    cursor = today if today in active_days else today - timedelta(days=1)
    while cursor in active_days:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def build_activity_summary(
    submissions: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    today = now_utc.date()
    first = first_accepted_timestamps(submissions)
    all_time = len(first)
    year_cut = int((now_utc - timedelta(days=365)).timestamp())
    month_cut = int((now_utc - timedelta(days=30)).timestamp())
    last_year = sum(1 for ts in first.values() if ts >= year_cut)
    last_month = sum(1 for ts in first.values() if ts >= month_cut)

    active_days = {
        datetime.fromtimestamp(ts, tz=timezone.utc).date() for ts in first.values()
    }
    current_streak, longest_streak = _streaks(active_days, today)

    ok_count = sum(1 for s in submissions if s.get("verdict") == V_AC)
    return {
        "solvedAllTime": all_time,
        "solvedLastYear": last_year,
        "solvedLastMonth": last_month,
        "submissionsAllTime": len(submissions),
        "acceptedSubmissions": ok_count,
        "currentStreakDays": current_streak,
        "longestStreakDays": longest_streak,
        "activityMetric": "unique_first_accepted",
        "timezone": "UTC",
    }


def build_codeforces_history(
    user: dict[str, Any],
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rating_history = build_rating_history(rating_rows or [])
    activity = build_activity(submissions)
    summary = build_activity_summary(submissions)
    current_rating = user.get("rating")
    max_rating = user.get("maxRating")
    return {
        "summary": {
            **summary,
            "currentRating": int(current_rating) if isinstance(current_rating, int) else None,
            "maxRating": int(max_rating) if isinstance(max_rating, int) else None,
        },
        "ratingHistory": rating_history,
        "activity": activity,
    }
