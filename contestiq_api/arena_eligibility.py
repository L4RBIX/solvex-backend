"""Arena catalog eligibility for recommendation / training CTAs.

Codeforces Div1/Div2/Technocup mirrors share a statement but use different
``contestId:index`` identities. Submissions may store the non-problemset
mirror (e.g. ``651C``) while SolveX's catalog only imports
``problemset.problems`` keys (e.g. ``650A``).

Any surface that emits ``Solve in Arena`` must resolve to a catalog key first.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from contestiq_core.codeforces.normalizer import stable_problem_key

CatalogLookup = Callable[[str], dict[str, Any] | None]
CatalogByName = Callable[[str, Any], list[dict[str, Any]]]


def arena_problem_id(contest_id: Any, index: Any) -> str | None:
    try:
        cid = int(contest_id)
    except (TypeError, ValueError):
        return None
    if not isinstance(index, str):
        return None
    normalized = index.strip().upper()
    if cid <= 0 or not normalized or not normalized.isalnum():
        return None
    return f"{cid}{normalized}"


def _contest_start_map(contests: list[dict[str, Any]] | None) -> dict[int, int]:
    starts: dict[int, int] = {}
    for row in contests or []:
        try:
            starts[int(row["id"])] = int(row["startTimeSeconds"])
        except (KeyError, TypeError, ValueError):
            continue
    return starts


def resolve_arena_catalog_problem(
    *,
    contest_id: Any,
    index: Any,
    name: str | None = None,
    rating: Any = None,
    contests: list[dict[str, Any]] | None = None,
    lookup: CatalogLookup | None = None,
    by_name: CatalogByName | None = None,
) -> dict[str, Any] | None:
    """Return the catalog problem row for an Arena CTA, or None if unavailable.

    Resolution order:
    1. Direct ``contestId+index`` catalog hit.
    2. Same-name (+rating) catalog rows whose contest shares ``startTimeSeconds``
       with the submission contest (Div1/Div2/Technocup mirrors).
    3. Unique same-name (+rating) catalog row when only one exists.
    """
    if lookup is None:
        from contestiq_api.cfdata import store

        lookup = store.get_problem
    if by_name is None:
        from contestiq_api.cfdata import store

        by_name = store.find_problems_by_name_rating

    direct_id = arena_problem_id(contest_id, index)
    if direct_id:
        hit = lookup(direct_id)
        if hit is not None:
            return hit

    normalized_name = (name or "").strip().lower()
    if not normalized_name:
        return None

    matches = by_name(normalized_name, rating) or []
    if not matches:
        # Rating on submission objects is sometimes missing while the catalog
        # row is rated — retry by name only.
        matches = by_name(normalized_name, None) or []
        if rating is not None:
            matches = [
                row
                for row in matches
                if row.get("rating") is None or row.get("rating") == rating
            ] or matches

    if not matches:
        return None

    try:
        source_cid = int(contest_id) if contest_id is not None else None
    except (TypeError, ValueError):
        source_cid = None

    starts = _contest_start_map(contests)
    source_start = starts.get(source_cid) if source_cid is not None else None
    if source_start is not None:
        mirrored: list[dict[str, Any]] = []
        for row in matches:
            try:
                row_cid = int(row["contest_id"])
            except (KeyError, TypeError, ValueError):
                continue
            if starts.get(row_cid) == source_start:
                mirrored.append(row)
        if len(mirrored) == 1:
            return mirrored[0]
        if len(mirrored) > 1:
            # Prefer exact rating match among mirrors.
            rated = [row for row in mirrored if row.get("rating") == rating]
            return (rated or mirrored)[0]

    if len(matches) == 1:
        return matches[0]
    if rating is not None:
        rated = [row for row in matches if row.get("rating") == rating]
        if len(rated) == 1:
            return rated[0]
    return None


def attach_arena_identity(
    item: dict[str, Any],
    *,
    contests: list[dict[str, Any]] | None = None,
    lookup: CatalogLookup | None = None,
    by_name: CatalogByName | None = None,
) -> dict[str, Any] | None:
    """Rewrite a recommendation/queue row onto a catalog identity.

    Returns None when the row named a concrete problem that is not Arena-capable.
    Focus-only rows (no contestId/index) pass through unchanged.
    """
    if item.get("contestId") is None or not item.get("index"):
        return {**item, "arenaAvailable": False}

    resolved = resolve_arena_catalog_problem(
        contest_id=item.get("contestId"),
        index=item.get("index"),
        name=item.get("name") or item.get("problemName"),
        rating=item.get("rating"),
        contests=contests,
        lookup=lookup,
        by_name=by_name,
    )
    if resolved is None:
        return None

    problem_key = resolved.get("problem_key") or stable_problem_key(
        {
            "contestId": resolved.get("contest_id"),
            "index": resolved.get("problem_index"),
            "name": resolved.get("name"),
        }
    )
    return {
        **item,
        "contestId": resolved.get("contest_id"),
        "index": resolved.get("problem_index"),
        "name": item.get("name") or resolved.get("name"),
        "problemName": item.get("problemName") or resolved.get("name"),
        "rating": item.get("rating") if item.get("rating") is not None else resolved.get("rating"),
        "problemKey": problem_key,
        "arenaAvailable": True,
    }


def filter_arena_capable_items(
    items: list[dict[str, Any]],
    *,
    contests: list[dict[str, Any]] | None = None,
    lookup: CatalogLookup | None = None,
    by_name: CatalogByName | None = None,
    keep_focus_only: bool = True,
) -> list[dict[str, Any]]:
    """Keep focus-only rows; rewrite or drop concrete problems lacking Arena catalog rows."""
    out: list[dict[str, Any]] = []
    for item in items:
        has_concrete = item.get("contestId") is not None and bool(item.get("index"))
        rewritten = attach_arena_identity(
            item,
            contests=contests,
            lookup=lookup,
            by_name=by_name,
        )
        if rewritten is None:
            continue
        if not has_concrete and not keep_focus_only:
            continue
        out.append(rewritten)
    return out


def select_arena_recommendations(
    candidates: list[dict[str, Any]],
    *,
    limit: int = 8,
    contests: list[dict[str, Any]] | None = None,
    lookup: CatalogLookup | None = None,
    by_name: CatalogByName | None = None,
) -> list[dict[str, Any]]:
    """Prefer Arena-capable rewrites until ``limit`` slots are filled."""
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        rewritten = attach_arena_identity(
            item,
            contests=contests,
            lookup=lookup,
            by_name=by_name,
        )
        if rewritten is None or not rewritten.get("arenaAvailable"):
            continue
        key = str(rewritten.get("problemKey") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        selected.append(rewritten)
        if len(selected) >= limit:
            break
    return selected
