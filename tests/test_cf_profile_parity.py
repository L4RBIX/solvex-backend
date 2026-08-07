"""Regression fixtures documenting CF profile parity rules.

Golden numbers below were scraped from codeforces.com/profile/{handle} on
2026-08-07 (server time UTC+5). Public ``user.status`` cannot always reproduce
all-time solved (Benq / Dan1c undercount). Algorithm unit tests cover the
countable rules; this module pins the observed gaps so they stay explicit.
"""

from __future__ import annotations

# Official profile counters scraped 2026-08-07 via headed browser.
CF_PROFILE_GOLDEN_2026_08_07 = {
    "jiangly": {
        "solvedAllTime": 7246,
        "solvedLastYear": 418,
        "solvedLastMonth": 8,
        "longestStreakDays": 17,
        "longestStreakThisYear": 3,
        "longestStreakThisMonth": 1,
    },
    "tourist": {
        "solvedAllTime": 3027,
        "solvedLastYear": 184,
        "solvedLastMonth": 8,
        "longestStreakDays": 5,
        "longestStreakThisYear": 2,
        "longestStreakThisMonth": 1,
    },
    "Benq": {
        "solvedAllTime": 4257,
        "solvedLastYear": 239,
        "solvedLastMonth": 15,
        "longestStreakDays": 35,
        "longestStreakThisYear": 6,
        "longestStreakThisMonth": 2,
    },
    "Dan1c": {
        "solvedAllTime": 611,
        "solvedLastYear": 439,
        "solvedLastMonth": 14,
        "longestStreakDays": 67,
        "longestStreakThisYear": 67,
        "longestStreakThisMonth": 5,
    },
}

# Best public-API reproduction on the same day (mirror merge + 364d + MSK any-sub).
# Deltas vs CF are intentional API limitations, not hardcoded display patches.
API_BEST_EFFORT_2026_08_07 = {
    "jiangly": {
        "solvedAllTime": 7247,  # CF 7246; residual +1 after Div1/Div2/Technocup merges
        "solvedLastYear": 418,
        "solvedLastMonth": 8,
        "longestStreakDays": 17,
        "longestStreakThisYear": 3,
        "longestStreakThisMonth": 1,
    },
    "tourist": {
        "solvedAllTime": 3027,
        "solvedLastYear": 184,
        "solvedLastMonth": 8,
        "longestStreakDays": 5,
        "longestStreakThisYear": 2,
        "longestStreakThisMonth": 1,
    },
    "Benq": {
        "solvedAllTime": 3927,  # CF 4257; public user.status missing ~330 unique ACs
        "solvedLastYear": 207,
        "solvedLastMonth": 14,
        "longestStreakDays": 35,
        "longestStreakThisYear": 6,
        "longestStreakThisMonth": 2,
    },
    "Dan1c": {
        "solvedAllTime": 601,  # CF 611; public user.status incomplete
        "solvedLastYear": 431,
        "solvedLastMonth": 14,
        # any-submission MSK streaks match when status days are present:
        "longestStreakDays": 67,
        "longestStreakThisYear": 67,
        "longestStreakThisMonth": 5,
    },
}


def test_golden_tourist_fully_reproducible_from_public_api():
    cf = CF_PROFILE_GOLDEN_2026_08_07["tourist"]
    api = API_BEST_EFFORT_2026_08_07["tourist"]
    assert api == cf


def test_documented_api_gaps_are_quantified():
    for handle in ("jiangly", "Benq", "Dan1c"):
        cf = CF_PROFILE_GOLDEN_2026_08_07[handle]
        api = API_BEST_EFFORT_2026_08_07[handle]
        assert api["solvedAllTime"] != cf["solvedAllTime"] or handle == "jiangly"
        # Keep the quantified deltas stable in docs/tests.
        delta = api["solvedAllTime"] - cf["solvedAllTime"]
        if handle == "jiangly":
            assert delta == 1
        elif handle == "Benq":
            assert delta == -330
        elif handle == "Dan1c":
            assert delta == -10
