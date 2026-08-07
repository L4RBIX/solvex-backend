"""Tests for all-time solved accounting and Codeforces profile history aggregates."""

from __future__ import annotations

from datetime import datetime, timezone

from contestiq_api.legacy_compat import legacy_analysis
from contestiq_api.profile_history import (
    build_activity,
    build_activity_summary,
    build_codeforces_history,
    build_rating_history,
    problem_identity,
    unique_accepted_problem_ids,
)


def _sub(
    sid: int,
    contest_id: int | None,
    index: str,
    verdict: str,
    *,
    ts: int,
    name: str = "P",
    rating: int | None = 1200,
    tags: list[str] | None = None,
    problemset_name: str | None = None,
):
    problem: dict = {"index": index, "name": name, "tags": tags or ["dp"]}
    if contest_id is not None:
        problem["contestId"] = contest_id
    if rating is not None:
        problem["rating"] = rating
    if problemset_name is not None:
        problem["problemsetName"] = problemset_name
    return {
        "id": sid,
        "contestId": contest_id,
        "problem": problem,
        "programmingLanguage": "C++17",
        "verdict": verdict,
        "creationTimeSeconds": ts,
    }


def test_unique_accepted_counts_each_problem_once():
    subs = [
        _sub(1, 1, "A", "WRONG_ANSWER", ts=100),
        _sub(2, 1, "A", "OK", ts=110),
        _sub(3, 1, "A", "OK", ts=120),  # repeat OK must not inflate
        _sub(4, 1, "B", "OK", ts=130),
        _sub(5, 2, "A", "TIME_LIMIT_EXCEEDED", ts=140),
    ]
    assert unique_accepted_problem_ids(subs) == {"1:A", "1:B"}


def test_non_ok_verdicts_excluded_from_solved():
    subs = [
        _sub(1, 10, "A", "WRONG_ANSWER", ts=1),
        _sub(2, 10, "B", "CHALLENGED", ts=2),
        _sub(3, 10, "C", "OK", ts=3),
    ]
    assert unique_accepted_problem_ids(subs) == {"10:C"}


def test_unusual_and_catalog_unsupported_ids_still_count():
    """Gym / problemset-only IDs count toward all-time solved."""
    subs = [
        _sub(1, 101853, "C", "OK", ts=10, name="Gym"),
        _sub(
            2,
            None,
            "A",
            "OK",
            ts=11,
            name="Acmsguru 1",
            problemset_name="acmsguru",
        ),
        _sub(3, 2254, "C2", "OK", ts=12, name="Unusual index"),
    ]
    ids = unique_accepted_problem_ids(subs)
    assert "101853:C" in ids
    assert "2254:C2" in ids
    assert problem_identity(subs[1]) == "acmsguru:A:Acmsguru 1"
    assert len(ids) == 3


def test_legacy_unique_solved_matches_all_time_and_keeps_recommendations_catalog_shaped():
    user = {
        "handle": "fixture",
        "rating": 1400,
        "maxRating": 1600,
        "rank": "specialist",
        "maxRank": "expert",
    }
    # Include an unsupported-looking gym solve plus normal rated solves.
    subs = [
        _sub(1, 101853, "C", "OK", ts=50, name="Gym Only", rating=None, tags=["graphs"]),
        _sub(2, 1, "A", "WRONG_ANSWER", ts=60, name="DP 1", tags=["dp"]),
        _sub(3, 1, "A", "OK", ts=70, name="DP 1", tags=["dp"]),
        _sub(4, 1, "A", "OK", ts=80, name="DP 1", tags=["dp"]),
        _sub(5, 2, "A", "OK", ts=90, name="DP 2", tags=["dp"]),
        _sub(6, 3, "A", "WRONG_ANSWER", ts=100, name="DP 3", tags=["dp"]),
        _sub(7, 3, "A", "WRONG_ANSWER", ts=110, name="DP 3", tags=["dp"]),
        _sub(8, 10, "B", "OK", ts=120, name="Greedy 10", tags=["greedy"], rating=1100),
        _sub(9, 11, "B", "OK", ts=130, name="Greedy 11", tags=["greedy"], rating=1100),
        _sub(10, 12, "B", "OK", ts=140, name="Greedy 12", tags=["greedy"], rating=1100),
    ]
    subs.reverse()
    result = legacy_analysis(user, subs, rating_history=[])
    assert result["summary"]["uniqueSolved"] == 6
    assert result["codeforcesHistory"]["summary"]["solvedAllTime"] == 6
    # Catalog / practice eligibility stays separate: recommendation rows that
    # name a concrete problem still use contestId+index, and the gym-only
    # unrated solve is counted in all-time solved without being required as a
    # recommendation candidate.
    assert all("contestId" in p and "index" in p for p in result["recommendedProblems"])
    assert not any(p.get("contestId") == 101853 for p in result["recommendedProblems"])


def test_rating_history_sorted_chronologically_with_deltas():
    rows = [
        {
            "contestId": 2,
            "contestName": "Later",
            "handle": "u",
            "rank": 100,
            "ratingUpdateTimeSeconds": 200,
            "oldRating": 1500,
            "newRating": 1550,
        },
        {
            "contestId": 1,
            "contestName": "Earlier",
            "handle": "u",
            "rank": 200,
            "ratingUpdateTimeSeconds": 100,
            "oldRating": 1400,
            "newRating": 1500,
        },
    ]
    events = build_rating_history(rows)
    assert [e["contestId"] for e in events] == [1, 2]
    assert events[0]["delta"] == 100
    assert events[1]["delta"] == 50


def test_activity_aggregation_by_utc_day():
    # Two OK on same UTC day for different problems + one WA + next-day OK.
    subs = [
        _sub(1, 1, "A", "OK", ts=1_700_000_000),  # 2023-11-14 UTC
        _sub(2, 1, "A", "OK", ts=1_700_000_100),  # repeat same problem
        _sub(3, 1, "B", "WRONG_ANSWER", ts=1_700_000_200),
        _sub(4, 1, "C", "OK", ts=1_700_000_300),
        _sub(5, 2, "A", "OK", ts=1_700_086_400),  # +1 day
    ]
    activity = build_activity(subs)
    by_date = {row["date"]: row for row in activity}
    day1 = datetime.fromtimestamp(1_700_000_000, tz=timezone.utc).date().isoformat()
    day2 = datetime.fromtimestamp(1_700_086_400, tz=timezone.utc).date().isoformat()
    assert by_date[day1]["uniqueSolved"] == 2
    assert by_date[day1]["acceptedSubmissions"] == 3
    assert by_date[day1]["submissions"] == 4
    assert by_date[day2]["uniqueSolved"] == 1


def test_yearly_monthly_counters_and_streaks():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    # first-AC days: today, yesterday, and 40 days ago
    t_today = int(datetime(2026, 8, 7, 1, tzinfo=timezone.utc).timestamp())
    t_yest = int(datetime(2026, 8, 6, 1, tzinfo=timezone.utc).timestamp())
    t_old = int(datetime(2026, 6, 28, 1, tzinfo=timezone.utc).timestamp())
    t_ancient = int(datetime(2024, 1, 1, 1, tzinfo=timezone.utc).timestamp())
    subs = [
        _sub(1, 1, "A", "OK", ts=t_today),
        _sub(2, 1, "B", "OK", ts=t_yest),
        _sub(3, 1, "C", "OK", ts=t_old),
        _sub(4, 1, "D", "OK", ts=t_ancient),
    ]
    summary = build_activity_summary(subs, now=now)
    assert summary["solvedAllTime"] == 4
    assert summary["solvedLastMonth"] == 2  # today + yesterday
    assert summary["solvedLastYear"] == 3  # excludes ancient
    assert summary["currentStreakDays"] == 2
    assert summary["longestStreakDays"] >= 2
    assert summary["longestStreakThisYear"] >= 2
    assert summary["longestStreakThisMonth"] == 2
    assert summary["mostActiveMonth"] is not None
    assert summary["timezone"] == "UTC"


def test_public_profile_maps_avatar_and_metadata():
    from contestiq_api.profile_history import build_public_profile

    profile = build_public_profile(
        {
            "handle": "tourist",
            "firstName": "Gennady",
            "lastName": "Korotkevich",
            "country": "Belarus",
            "city": "Gomel",
            "organization": "ITMO",
            "contribution": 55,
            "friendOfCount": 10,
            "rating": 3800,
            "maxRating": 4000,
            "rank": "legendary grandmaster",
            "maxRank": "legendary grandmaster",
            "avatar": "https://userpic.codeforces.org/422/avatar/x.jpg",
            "titlePhoto": "https://userpic.codeforces.org/422/title/x.jpg",
            "registrationTimeSeconds": 1_200_000_000,
            "lastOnlineTimeSeconds": int(datetime.now(timezone.utc).timestamp()),
        }
    )
    assert profile["realName"] == "Gennady Korotkevich"
    assert profile["avatarUrl"].endswith("title/x.jpg")
    assert profile["city"] == "Gomel"
    assert profile["online"] is True
    assert profile["profileUrl"].endswith("/tourist")

    blank = build_public_profile(
        {
            "handle": "nobody",
            "avatar": "https://userpic.codeforces.org/no-avatar.jpg",
            "titlePhoto": "https://userpic.codeforces.org/no-title.jpg",
        }
    )
    assert blank["avatarUrl"] == ""
    assert blank["online"] is False


def test_build_codeforces_history_empty_rating_for_unrated():
    user = {"handle": "newbie", "rank": "newbie"}
    history = build_codeforces_history(user, [], [])
    assert history["ratingHistory"] == []
    assert history["summary"]["solvedAllTime"] == 0
    assert history["summary"]["currentRating"] is None
