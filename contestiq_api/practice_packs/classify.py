"""Practice pack support classification (prioritization only — never auto-activates)."""

from __future__ import annotations

from typing import Any

AUTO_HIGH_CONFIDENCE = "AUTO_HIGH_CONFIDENCE"
AUTO_POSSIBLE = "AUTO_POSSIBLE"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
UNSUPPORTED = "UNSUPPORTED"

# Back-compat aliases used by older tests/callers.
AUTO_PACK_POSSIBLE = AUTO_POSSIBLE
REVIEW_PACK_POSSIBLE = REVIEW_REQUIRED

_HIGH_CONF_TAGS = {
    "implementation",
    "math",
    "greedy",
    "strings",
    "brute force",
    "sortings",
    "binary search",
    "two pointers",
    "number theory",
    "combinatorics",
    "bitmasks",
}

_HARD_TAGS = {
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
}


def classify_problem(
    *,
    is_interactive: bool = False,
    io_mode: str | None = None,
    availability_status: str | None = None,
    has_oracle: bool = False,
    display_ready: bool = False,
    rating: int | None = None,
    tags: list[str] | None = None,
) -> str:
    if is_interactive:
        return UNSUPPORTED
    if (io_mode or "stdio") == "file":
        return UNSUPPORTED
    if availability_status in {"asset_required"}:
        return UNSUPPORTED

    tagset = {t.lower() for t in (tags or [])}
    if tagset & _HARD_TAGS:
        return UNSUPPORTED

    stdio_ok = io_mode in {None, "stdio"}
    if not display_ready or not stdio_ok:
        return UNSUPPORTED

    beginner = rating is not None and 800 <= int(rating) <= 1300
    preferred = bool(tagset & _HIGH_CONF_TAGS) or not tagset

    if has_oracle and beginner and preferred:
        return AUTO_HIGH_CONFIDENCE
    if has_oracle:
        return AUTO_POSSIBLE
    if beginner and preferred:
        return REVIEW_REQUIRED
    return REVIEW_REQUIRED


def classify_from_statement_row(
    row: dict[str, Any] | None,
    *,
    has_oracle: bool,
    rating: int | None = None,
    tags: list[str] | None = None,
) -> str:
    if row is None:
        return UNSUPPORTED
    return classify_problem(
        is_interactive=bool(row.get("is_interactive")),
        io_mode=row.get("io_mode"),
        availability_status=row.get("availability_status"),
        has_oracle=has_oracle,
        display_ready=bool(row.get("display_ready")),
        rating=rating if rating is not None else row.get("rating"),
        tags=tags if tags is not None else row.get("tags"),
    )
