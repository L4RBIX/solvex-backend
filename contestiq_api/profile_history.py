"""Codeforces profile history aggregates for the public analysis page.

Counting rules are reverse-engineered to match the official profile
``_UserActivityFrame`` counters as closely as the public API allows:

* **Solved** = unique accepted problems, with Div1/Div2/Technocup *mirror*
  contests (identical ``startTimeSeconds``) collapsed when the user has an OK
  on the same problem name+rating in more than one of those contests.
* **Last year / last month** solved windows are rolling **364** and **30**
  days (CF’s “last year” is 52 weeks, not 365 days).
* **Streaks** use Moscow time (UTC+3) and count calendar days with *any*
  submission (any verdict), matching CF’s “in a row” counters.

All-time solved still cannot always equal the website for every handle: the
public ``user.status`` feed is incomplete for some users (observed undercounts
for Benq / Dan1c). When the API is complete, tourist matches exactly and
jiangly is within +1 after mirror merging.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Hashable

V_AC = "OK"

# Official profile “last year” is 52 weeks, not a 365-day civil year.
LAST_YEAR_DAYS = 364
LAST_MONTH_DAYS = 30
MOSCOW = timezone(timedelta(hours=3))


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


def _problem_tuple(sub: dict[str, Any]) -> tuple[Any, ...]:
    problem = sub.get("problem") or {}
    contest_id = problem.get("contestId")
    if contest_id is None:
        contest_id = sub.get("contestId")
    index = problem.get("index")
    if contest_id is not None and index:
        return ("cid", contest_id, index)
    problemset = problem.get("problemsetName") or "problemset"
    name = problem.get("name") or "unknown"
    return ("ps", problemset, index or "x", name)


def _contest_start_index(
    contests: list[dict[str, Any]] | None,
) -> dict[int, list[int]]:
    """Map startTimeSeconds → contest ids that share that exact start."""
    by_start: dict[int, list[int]] = defaultdict(list)
    for row in contests or []:
        try:
            cid = int(row["id"])
            start = int(row["startTimeSeconds"])
        except (KeyError, TypeError, ValueError):
            continue
        by_start[start].append(cid)
    return {start: ids for start, ids in by_start.items() if len(ids) >= 2}


def _mirror_parent_map(
    submissions: list[dict[str, Any]],
    contests: list[dict[str, Any]] | None,
) -> dict[tuple[Any, ...], tuple[Any, ...]]:
    """Union-find parents for OK problems that are contest mirrors of each other.

    Two solves merge when:
    - their contests share an identical startTimeSeconds, and
    - normalized name + rating match, and
    - the contest ids differ (never merge E1/E2 inside one contest).
    """
    parent: dict[tuple[Any, ...], tuple[Any, ...]] = {}

    def find(x: tuple[Any, ...]) -> tuple[Any, ...]:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: tuple[Any, ...], b: tuple[Any, ...]) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # Earliest OK row per raw identity (for name/rating).
    first: dict[tuple[Any, ...], dict[str, Any]] = {}
    for sub in sorted(
        (s for s in submissions if s.get("verdict") == V_AC),
        key=lambda s: int(s.get("creationTimeSeconds") or 0),
    ):
        key = _problem_tuple(sub)
        if key not in first:
            first[key] = sub

    by_start = _contest_start_index(contests)
    if not by_start:
        return {k: k for k in first}

    for ids in by_start.values():
        idset = set(ids)
        by_nr: dict[tuple[str, Any], list[tuple[Any, ...]]] = defaultdict(list)
        for key, sub in first.items():
            if key[0] != "cid" or key[1] not in idset:
                continue
            problem = sub.get("problem") or {}
            name = (problem.get("name") or "").strip().lower()
            if not name:
                continue
            by_nr[(name, problem.get("rating"))].append(key)
        for keys in by_nr.values():
            by_contest: dict[Any, list[tuple[Any, ...]]] = defaultdict(list)
            for key in keys:
                by_contest[key[1]].append(key)
            if len(by_contest) < 2:
                continue
            reps = [rows[0] for rows in by_contest.values()]
            base = reps[0]
            for other in reps[1:]:
                union(base, other)

    return {k: find(k) for k in first}


def unique_accepted_problem_ids(
    submissions: list[dict[str, Any]],
    contests: list[dict[str, Any]] | None = None,
) -> set[str]:
    first = first_accepted_timestamps(submissions, contests)
    return set(first)


def _utc_day(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()


def _moscow_day(ts: int) -> date:
    return datetime.fromtimestamp(int(ts), tz=MOSCOW).date()


def first_accepted_timestamps(
    submissions: list[dict[str, Any]],
    contests: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Earliest OK creationTimeSeconds per canonical (mirror-merged) identity."""
    parents = _mirror_parent_map(submissions, contests)
    first: dict[Hashable, int] = {}
    display: dict[Hashable, str] = {}
    for sub in sorted(
        (s for s in submissions if s.get("verdict") == V_AC),
        key=lambda s: int(s.get("creationTimeSeconds") or 0),
    ):
        raw = _problem_tuple(sub)
        root = parents.get(raw, raw)
        ts = int(sub.get("creationTimeSeconds") or 0)
        if root not in first:
            first[root] = ts
            display[root] = problem_identity(sub)
    return {display[root]: ts for root, ts in first.items()}


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
    """Return (current_streak, longest_streak).

    current_streak counts contiguous active days ending today or yesterday
    (so a quiet local today does not instantly zero an overnight streak).
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


def submission_active_days_moscow(submissions: list[dict[str, Any]]) -> set[date]:
    """Moscow calendar days with at least one submission (any verdict)."""
    days: set[date] = set()
    for sub in submissions:
        ts = sub.get("creationTimeSeconds")
        if ts is None:
            continue
        days.add(_moscow_day(int(ts)))
    return days


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _weekday_name(d: date) -> str:
    return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[
        d.weekday()
    ]


def build_solving_stats(
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    contests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Richer solving metrics aligned with Codeforces profile counters."""
    now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    now_msk = now_utc.astimezone(MOSCOW)
    today_msk = now_msk.date()
    first = first_accepted_timestamps(submissions, contests)

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

    # Activity peaks by first-AC day (UTC — heatmap / “most active” helpers).
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

    rating_history = build_rating_history(rating_rows or [])
    rating_progress = None
    if rating_history:
        rating_progress = {
            "fromRating": rating_history[0]["oldRating"],
            "toRating": rating_history[-1]["newRating"],
            "delta": rating_history[-1]["newRating"] - rating_history[0]["oldRating"],
            "contests": len(rating_history),
        }

    year_cut = int((now_utc - timedelta(days=LAST_YEAR_DAYS)).timestamp())
    month_cut = int((now_utc - timedelta(days=LAST_MONTH_DAYS)).timestamp())

    active_days = submission_active_days_moscow(submissions)
    year_days = {d for d in active_days if d >= today_msk - timedelta(days=LAST_YEAR_DAYS)}
    month_days = {d for d in active_days if d >= today_msk - timedelta(days=LAST_MONTH_DAYS)}
    current_streak, longest_streak = _streaks(active_days, today_msk)

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
        # CF labels these “for the last year/month” (rolling), not calendar YTD.
        "longestStreakThisYear": _longest_run(year_days),
        "longestStreakThisMonth": _longest_run(month_days),
        "ratingProgress": rating_progress,
    }


def build_activity_summary(
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    contests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    solving = build_solving_stats(submissions, rating_rows, now=now_utc, contests=contests)
    ok_count = sum(1 for s in submissions if s.get("verdict") == V_AC)
    return {
        **solving,
        "submissionsAllTime": len(submissions),
        "acceptedSubmissions": ok_count,
        "activityMetric": "unique_first_accepted",
        "streakMetric": "any_submission_moscow",
        "solvedWindowDays": {"lastYear": LAST_YEAR_DAYS, "lastMonth": LAST_MONTH_DAYS},
        "timezone": "Europe/Moscow",
        # Honest limitation: anonymous user.status is public activity only.
        "solvedCountBasis": "public_user_status",
        "solvedCountLimitation": (
            "Matches Codeforces public activity from user.status. Profiles that "
            "include private group/mashup solves on the website can show a higher "
            "all-time total than the public API can reconstruct."
        ),
    }


def build_codeforces_history(
    user: dict[str, Any],
    submissions: list[dict[str, Any]],
    rating_rows: list[dict[str, Any]] | None = None,
    contests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rating_history = build_rating_history(rating_rows or [])
    activity = build_activity(submissions)
    summary = build_activity_summary(submissions, rating_rows, contests=contests)
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
