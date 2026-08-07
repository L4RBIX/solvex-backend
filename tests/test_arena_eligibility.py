"""Regression tests for Arena catalog eligibility / Div1–Div2 mirror remapping."""

from __future__ import annotations

from contestiq_api.arena_eligibility import (
    attach_arena_identity,
    resolve_arena_catalog_problem,
    select_arena_recommendations,
)
from contestiq_api.legacy_compat import legacy_analysis


def _catalog():
    # Mirrors production: problemset stores Div1/Technocup keys, not Div2 mirrors.
    return {
        "650A": {
            "problem_key": "650A",
            "contest_id": 650,
            "problem_index": "A",
            "name": "Watchmen",
            "rating": 1600,
        },
        "1225D": {
            "problem_key": "1225D",
            "contest_id": 1225,
            "problem_index": "D",
            "name": "Power Products",
            "rating": 1800,
        },
        "1A": {
            "problem_key": "1A",
            "contest_id": 1,
            "problem_index": "A",
            "name": "Theatre Square",
            "rating": 1000,
        },
        "2228B": {
            "problem_key": "2228B",
            "contest_id": 2228,
            "problem_index": "B",
            "name": "Remilia Plays Soku",
            "rating": 1100,
        },
    }


DISPLAY_READY = {"650A", "1225D", "1A"}


def _lookup(key: str):
    return _catalog().get(key)


def _by_name(name: str, rating):
    rows = []
    for row in _catalog().values():
        if row["name"].lower() != name.lower():
            continue
        if rating is None or row.get("rating") == rating:
            rows.append(row)
    return rows


def _display_ready(problem_id: str) -> bool:
    return problem_id in DISPLAY_READY


CONTESTS = [
    {"id": 650, "startTimeSeconds": 1_450_000_000, "name": "Codeforces Round 345 (Div. 1)"},
    {"id": 651, "startTimeSeconds": 1_450_000_000, "name": "Codeforces Round 345 (Div. 2)"},
    {"id": 1246, "startTimeSeconds": 1_570_000_000, "name": "Codeforces Round 596 (Div. 1)"},
    {"id": 1225, "startTimeSeconds": 1_570_000_000, "name": "Technocup 2020 - Elimination Round 2"},
]


def test_651C_remaps_to_650A():
    resolved = resolve_arena_catalog_problem(
        contest_id=651,
        index="C",
        name="Watchmen",
        rating=1600,
        contests=CONTESTS,
        lookup=_lookup,
        by_name=_by_name,
    )
    assert resolved is not None
    assert resolved["problem_key"] == "650A"


def test_1246B_remaps_to_1225D():
    resolved = resolve_arena_catalog_problem(
        contest_id=1246,
        index="B",
        name="Power Products",
        rating=1800,
        contests=CONTESTS,
        lookup=_lookup,
        by_name=_by_name,
    )
    assert resolved is not None
    assert resolved["problem_key"] == "1225D"


def test_unavailable_catalog_problem_is_dropped():
    item = attach_arena_identity(
        {"name": "Missing", "contestId": 999999, "index": "A", "rating": 800},
        contests=CONTESTS,
        lookup=_lookup,
        by_name=_by_name,
        display_ready=_display_ready,
    )
    assert item is None


def test_2228B_catalog_hit_without_statement_is_not_arena_capable():
    """Regression: Remilia Plays Soku is in CF catalog but has no displayable statement."""
    item = attach_arena_identity(
        {
            "name": "Remilia Plays Soku",
            "contestId": 2228,
            "index": "B",
            "rating": 1100,
            "tags": ["games", "implementation"],
        },
        contests=CONTESTS,
        lookup=_lookup,
        by_name=_by_name,
        display_ready=_display_ready,
    )
    assert item is None


def test_select_recommendations_never_emits_mirror_ids():
    candidates = [
        {"name": "Watchmen", "contestId": 651, "index": "C", "rating": 1600, "tags": ["math"]},
        {"name": "Power Products", "contestId": 1246, "index": "B", "rating": 1800, "tags": ["math"]},
        {"name": "Theatre Square", "contestId": 1, "index": "A", "rating": 1000, "tags": ["math"]},
        {"name": "Ghost", "contestId": 999999, "index": "Z", "rating": 900, "tags": ["math"]},
        {"name": "Remilia Plays Soku", "contestId": 2228, "index": "B", "rating": 1100, "tags": ["games"]},
    ]
    selected = select_arena_recommendations(
        candidates,
        limit=8,
        contests=CONTESTS,
        lookup=_lookup,
        by_name=_by_name,
        display_ready=_display_ready,
    )
    ids = {f"{item['contestId']}{item['index']}" for item in selected}
    assert "651C" not in ids
    assert "1246B" not in ids
    assert "999999Z" not in ids
    assert "2228B" not in ids
    assert "650A" in ids
    assert "1225D" in ids
    assert "1A" in ids
    assert all(item.get("arenaAvailable") is True for item in selected)


def _sub(sid, contest_id, index, verdict, *, ts, name, rating, tags):
    return {
        "id": sid,
        "contestId": contest_id,
        "problem": {
            "contestId": contest_id,
            "index": index,
            "name": name,
            "rating": rating,
            "tags": tags,
        },
        "programmingLanguage": "C++17",
        "verdict": verdict,
        "creationTimeSeconds": ts,
    }


def test_legacy_analysis_rewrites_mirror_recommendations(monkeypatch):
    monkeypatch.setattr("contestiq_api.cfdata.store.get_problem", _lookup)
    monkeypatch.setattr("contestiq_api.cfdata.store.find_problems_by_name_rating", _by_name)
    monkeypatch.setattr(
        "contestiq_api.cfdata.store.is_problem_statement_display_ready",
        _display_ready,
    )

    user = {"handle": "fixture", "rating": 1600, "maxRating": 1700, "rank": "expert", "maxRank": "expert"}
    # Many WA attempts on mirror IDs so they become recommendation candidates.
    subs = []
    sid = 1
    for i in range(6):
        subs.append(
            _sub(
                sid,
                651,
                "C",
                "WRONG_ANSWER",
                ts=100 + i,
                name="Watchmen",
                rating=1600,
                tags=["math", "greedy"],
            )
        )
        sid += 1
    for i in range(6):
        subs.append(
            _sub(
                sid,
                1246,
                "B",
                "WRONG_ANSWER",
                ts=200 + i,
                name="Power Products",
                rating=1800,
                tags=["math", "number theory"],
            )
        )
        sid += 1
    # One easy solved problem so language/comfort stats work.
    subs.append(
        _sub(sid, 1, "A", "OK", ts=300, name="Theatre Square", rating=1000, tags=["math"])
    )

    result = legacy_analysis(user, list(reversed(subs)), [], contests=CONTESTS)
    rec_ids = [
        f"{p['contestId']}{p['index']}"
        for p in result["recommendedProblems"]
        if p.get("contestId") is not None
    ]
    assert "651C" not in rec_ids
    assert "1246B" not in rec_ids
    assert any(pid in rec_ids for pid in ("650A", "1225D"))
    assert all(p.get("arenaAvailable") is True for p in result["recommendedProblems"] if p.get("contestId"))

    queue_ids = [
        f"{p['contestId']}{p['index']}"
        for p in result["sevenDayQueue"]
        if p.get("contestId") is not None
    ]
    assert "651C" not in queue_ids
    assert "1246B" not in queue_ids
