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


def _longest_run(active_days: set[date]) -> int:
    if not active_days:
        return 0
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
    return longest


def _streaks(active_days: set[date], today: date) -> tuple[int, int]:
    """Return (current_streak, longest_streak) over UTC days with ≥1 first-AC.

    current_streak counts contiguous active days ending today or yesterday
    (so a quiet UTC today does not instantly zero an overnight streak).
    """
    if not active_days:
        return 0, 0

    longest = _longest_run(active_days)
    current = 0
    cursor = today if today in active_days else today - timedelta(days=1)
    while cursor in active_days:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _weekday_name(d: date) -> str:
    return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[d.weekday()]


def build_solving_stats(
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Richer solving metrics derived only from available CF payloads."""
    now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    today = now_utc.date()
    first = first_accepted_timestamps(submissions)

    # Per-problem attempt counts before first AC (chronological within each identity).
    by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sub in submissions:
        by_problem[problem_identity(sub)].append(sub)

    attempts_before_ac: list[int] = []
    hardest: dict[str, Any] | None = None
    for key, rows in by_problem.items():
        rows_sorted = sorted(rows, key=lambda s: int(s.get("creationTimeSeconds") or 0))
        attempts = 0
        solved_row = None
        for sub in rows_sorted:
            attempts += 1
            if sub.get("verdict") == V_AC:
                solved_row = sub
                attempts_before_ac.append(attempts)
                break
        if solved_row is None:
            continue
        problem = solved_row.get("problem") or {}
        rating = problem.get("rating")
        if isinstance(rating, int) and (hardest is None or rating > int(hardest["rating"])):
            hardest = {
                "problemKey": key,
                "name": problem.get("name") or "",
                "rating": rating,
                "contestId": problem.get("contestId"),
                "index": problem.get("index"),
            }

    avg_attempts = (
        round(sum(attempts_before_ac) / len(attempts_before_ac), 2) if attempts_before_ac else None
    )

    # Activity peaks by first-AC day.
    first_by_day: dict[date, int] = defaultdict(int)
    first_by_month: dict[str, int] = defaultdict(int)
    first_by_weekday: dict[str, int] = defaultdict(int)
    for ts in first.values():
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        first_by_day[d] += 1
        first_by_month[_month_key(d)] += 1
        first_by_weekday[_weekday_name(d)] += 1

    most_active_day = None
    if first_by_day:
        day, count = max(first_by_day.items(), key=lambda kv: (kv[1], kv[0].isoformat()))
        most_active_day = {"date": day.isoformat(), "uniqueSolved": count}

    most_active_month = None
    if first_by_month:
        month, count = max(first_by_month.items(), key=lambda kv: (kv[1], kv[0]))
        most_active_month = {"month": month, "uniqueSolved": count}

    most_active_weekday = None
    if first_by_weekday:
        weekday, count = max(first_by_weekday.items(), key=lambda kv: (kv[1], kv[0]))
        most_active_weekday = {"weekday": weekday, "uniqueSolved": count}

    year_start = date(today.year, 1, 1)
    month_start = date(today.year, today.month, 1)
    active_days = set(first_by_day)
    year_days = {d for d in active_days if d >= year_start}
    month_days = {d for d in active_days if d >= month_start}

    rating_history = build_rating_history(rating_rows or [])
    rating_progress = None
    if rating_history:
        rating_progress = {
            "fromRating": rating_history[0]["oldRating"],
            "toRating": rating_history[-1]["newRating"],
            "delta": rating_history[-1]["newRating"] - rating_history[0]["oldRating"],
            "contests": len(rating_history),
        }

    year_cut = int((now_utc - timedelta(days=365)).timestamp())
    month_cut = int((now_utc - timedelta(days=30)).timestamp())
    current_streak, longest_streak = _streaks(active_days, today)

    return {
        "solvedAllTime": len(first),
        "solvedLastYear": sum(1 for ts in first.values() if ts >= year_cut),
        "solvedLastMonth": sum(1 for ts in first.values() if ts >= month_cut),
        "avgAttemptsBeforeAC": avg_attempts,
        "hardestSolved": hardest,
        "mostActiveDay": most_active_day,
        "mostActiveMonth": most_active_month,
        "mostActiveWeekday": most_active_weekday,
        "currentStreakDays": current_streak,
        "longestStreakDays": longest_streak,
        "longestStreakThisYear": _longest_run(year_days),
        "longestStreakThisMonth": _longest_run(month_days),
        "ratingProgress": rating_progress,
    }


def build_activity_summary(
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    solving = build_solving_stats(submissions, rating_rows, now=now_utc)
    ok_count = sum(1 for s in submissions if s.get("verdict") == V_AC)
    return {
        **solving,
        "submissionsAllTime": len(submissions),
        "acceptedSubmissions": ok_count,
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
    summary = build_activity_summary(submissions, rating_rows)
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


def build_public_profile(user: dict[str, Any]) -> dict[str, Any]:
    """Map Codeforces user.info into the public analyze profile shape."""
    handle = user.get("handle") or ""
    first_name = (user.get("firstName") or "").strip()
    last_name = (user.get("lastName") or "").strip()
    real_name = " ".join(part for part in (first_name, last_name) if part)

    avatar = (user.get("avatar") or "").strip()
    title_photo = (user.get("titlePhoto") or "").strip()
    placeholder = any(
        marker in (avatar or title_photo).lower()
        for marker in ("no-avatar", "no-title")
    )

    last_online = user.get("lastOnlineTimeSeconds")
    registration = user.get("registrationTimeSeconds")
    online = False
    if isinstance(last_online, int):
        # Codeforces typically treats ~5 minutes as "online".
        online = (datetime.now(timezone.utc).timestamp() - last_online) <= 5 * 60

    return {
        "handle": handle,
        "firstName": first_name,
        "lastName": last_name,
        "realName": real_name,
        "rating": user.get("rating", 0) or 0,
        "maxRating": user.get("maxRating", 0) or 0,
        "rank": user.get("rank") or "unrated",
        "maxRank": user.get("maxRank") or "unrated",
        "country": user.get("country") or "",
        "city": user.get("city") or "",
        "organization": user.get("organization") or "",
        "contribution": int(user["contribution"]) if isinstance(user.get("contribution"), int) else 0,
        "friendOfCount": int(user["friendOfCount"]) if isinstance(user.get("friendOfCount"), int) else 0,
        "avatarUrl": "" if placeholder else (title_photo or avatar),
        "avatarThumbnailUrl": "" if placeholder else (avatar or title_photo),
        "registrationTimeSeconds": int(registration) if isinstance(registration, int) else None,
        "lastOnlineTimeSeconds": int(last_online) if isinstance(last_online, int) else None,
        "online": online,
        "profileUrl": f"https://codeforces.com/profile/{handle}" if handle else "",
    }
