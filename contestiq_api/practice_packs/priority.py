"""Coverage prioritization for practice-pack expansion."""

from __future__ import annotations

from typing import Any

# Lower rating bands first for beginner coverage.
_RATING_WEIGHT = {
    800: 100,
    900: 95,
    1000: 90,
    1100: 85,
    1200: 80,
    1300: 75,
}

_PREFERRED_TAGS = {
    "implementation",
    "math",
    "greedy",
    "strings",
    "brute force",
    "sortings",
    "constructive algorithms",  # often still unique-answer Div2 A; mild boost only
    "binary search",
    "two pointers",
    "data structures",
    "dfs and similar",
    "graphs",
    "trees",
    "combinatorics",
    "number theory",
    "bitmasks",
}

_DEPRIORITIZE_TAGS = {
    "interactive",
    "geometry",
    "fft",
    "flows",
    "graph matchings",
    "2-sat",
    "chinese remainder theorem",
    "schedules",
    "matrices",
    "string suffix structures",
    "probabilities",
}


def rating_band(rating: int | None) -> int | None:
    if rating is None:
        return None
    # Snap to nearest published CF band used in prioritization.
    for band in (800, 900, 1000, 1100, 1200, 1300):
        if abs(rating - band) <= 50 or rating == band:
            if 800 <= rating <= 1300:
                # Prefer exact band when present.
                if rating in _RATING_WEIGHT:
                    return rating
                return min(_RATING_WEIGHT, key=lambda b: abs(b - rating))
    if 800 <= rating <= 1300:
        return min(_RATING_WEIGHT, key=lambda b: abs(b - rating))
    return None


def priority_score(
    *,
    rating: int | None,
    solved_count: int = 0,
    tags: list[str] | None = None,
    usage_score: float = 0.0,
    has_oracle: bool = False,
    already_submit_capable: bool = False,
) -> float:
    """Higher is better. Does not activate packs by itself."""
    if already_submit_capable:
        return -1e9
    tags = tags or []
    tagset = {t.lower() for t in tags}
    if tagset & {t.lower() for t in _DEPRIORITIZE_TAGS}:
        return -1e6

    band = rating_band(rating)
    score = float(_RATING_WEIGHT.get(band, 20 if rating and rating < 800 else 10))

    # Popularity: log-ish via sqrt, capped.
    sc = max(0, int(solved_count))
    score += min(80.0, (sc**0.5) / 3.0)

    preferred = tagset & {t.lower() for t in _PREFERRED_TAGS}
    score += 4.0 * len(preferred)

    # Mild constructive deprioritization vs pure implementation/math.
    if "constructive algorithms" in tagset and not (
        tagset & {"implementation", "math", "greedy", "strings"}
    ):
        score -= 15.0

    score += max(0.0, float(usage_score)) * 10.0

    if has_oracle:
        score += 50.0  # ready to build immediately
    return score


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["priority_score"] = priority_score(
            rating=item.get("rating"),
            solved_count=int(item.get("solved_count") or 0),
            tags=list(item.get("tags") or []),
            usage_score=float(item.get("usage_score") or 0),
            has_oracle=bool(item.get("has_oracle")),
            already_submit_capable=bool(item.get("already_submit_capable")),
        )
        ranked.append(item)
    ranked.sort(key=lambda r: (-float(r["priority_score"]), str(r.get("problem_id") or "")))
    return ranked
