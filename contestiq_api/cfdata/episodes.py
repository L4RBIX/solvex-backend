"""Problem episode builder.

Raw submissions must never be scored independently: every (handle, problem)
pair collapses into ONE deterministic diagnostic episode. Rebuilding from the
same normalized submissions always produces identical rows (same episode_id,
same episode_hash), so rebuilds are idempotent.

Timestamps are epoch seconds in the SQLite mirror (matching
cf_submissions_normalized); the Postgres schema uses timestamptz.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter
from typing import Any

from contestiq_api.cfdata import store

EPISODE_NAMESPACE = uuid.UUID("6f6c7665-7858-4570-a973-6f6465733031")  # stable, arbitrary

AC_VERDICT = "OK"
# An AC this long after the first attempt is weaker evidence: the solve
# likely happened in a separate sitting, possibly after external input.
DELAYED_AC_SECONDS = 72 * 3600

GLOBAL_DEFAULT_RATING = 1200  # mirrors contestiq_core.config.DEFAULT_OVERALL_RATING

RATING_BANDS = ("consolidation", "on_level", "stretch", "out_of_band", "unknown_difficulty")

_CONTEXT_BY_PARTICIPANT = {
    "CONTESTANT": "contest",
    "OUT_OF_COMPETITION": "contest",
    "VIRTUAL": "virtual",
    "PRACTICE": "practice",
}


def episode_id_for(handle: str, problem_id: str) -> str:
    return str(uuid.uuid5(EPISODE_NAMESPACE, f"{store.canonical_handle(handle)}:{problem_id}"))


def rating_band(rating_gap: int | None) -> str:
    if rating_gap is None:
        return "unknown_difficulty"
    if rating_gap <= -200:
        return "consolidation"
    if rating_gap <= 150:
        return "on_level"
    if rating_gap <= 400:
        return "stretch"
    return "out_of_band"


def _user_rating_at(rating_history: list[dict[str, Any]], at_time: int | None, current_rating: int | None) -> tuple[int, str]:
    """Latest contest rating before the episode start; else current rating; else global default."""
    if at_time is not None:
        before = [row for row in rating_history if (row.get("rating_update_time") or 0) <= at_time]
        if before:
            latest = max(before, key=lambda row: row.get("rating_update_time") or 0)
            if latest.get("new_rating") is not None:
                return int(latest["new_rating"]), "rating_history"
    if current_rating is not None:
        return int(current_rating), "current_rating"
    return GLOBAL_DEFAULT_RATING, "global_default"


def _episode_hash(handle: str, problem_id: str, submissions: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {
            "handle": store.canonical_handle(handle),
            "problem_id": problem_id,
            "submissions": [
                [row["submission_id"], row.get("verdict"), row.get("creation_time"), row.get("passed_test_count")]
                for row in submissions
            ],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_episode(
    handle: str,
    problem_id: str,
    submissions: list[dict[str, Any]],
    rating_history: list[dict[str, Any]],
    current_rating: int | None,
    problem_rating_fallback: int | None = None,
) -> dict[str, Any]:
    """Collapse one problem's normalized submissions (any order) into one episode."""
    ordered = sorted(submissions, key=lambda row: (row.get("creation_time") or 0, row["submission_id"]))
    first = ordered[0]
    last = ordered[-1]

    first_ac = next((row for row in ordered if row.get("verdict") == AC_VERDICT), None)
    if first_ac is not None:
        before_ac = ordered[: ordered.index(first_ac)]
        failed_before_ac = sum(1 for row in before_ac if row.get("verdict") != AC_VERDICT)
    else:
        failed_before_ac = sum(1 for row in ordered if row.get("verdict") != AC_VERDICT)

    if first_ac is None:
        final_status = "abandoned"
    elif failed_before_ac == 0:
        final_status = "clean_solve"
    elif (first_ac.get("creation_time") or 0) - (first.get("creation_time") or 0) > DELAYED_AC_SECONDS:
        final_status = "delayed_ac"
    else:
        final_status = "solved_with_friction"

    types = Counter(row.get("participant_type") for row in ordered if row.get("participant_type"))
    participant_primary = min(
        types.items(), key=lambda kv: (-kv[1], kv[0])
    )[0] if types else None
    # Context reflects the first encounter with the problem, which is the
    # diagnostically interesting moment (a contest fail solved later in
    # practice is still a contest episode).
    context_type = _CONTEXT_BY_PARTICIPANT.get(first.get("participant_type") or "", "other")

    problem_rating = next((row.get("problem_rating") for row in ordered if row.get("problem_rating") is not None), None)
    if problem_rating is None:
        problem_rating = problem_rating_fallback

    user_rating, anchor_source = _user_rating_at(rating_history, first.get("creation_time"), current_rating)
    rating_gap = (problem_rating - user_rating) if problem_rating is not None else None

    return {
        "episode_id": episode_id_for(handle, problem_id),
        "user_id": None,
        "handle": store.canonical_handle(handle),
        "problem_id": problem_id,
        "first_submission_id": first["submission_id"],
        "first_attempt_at": first.get("creation_time"),
        "first_ac_submission_id": first_ac["submission_id"] if first_ac else None,
        "first_ac_at": first_ac.get("creation_time") if first_ac else None,
        "last_submission_at": last.get("creation_time"),
        "total_submissions": len(ordered),
        "failed_before_ac": failed_before_ac,
        "final_status": final_status,
        "eventual_ac": 1 if first_ac is not None else 0,
        "participant_type_primary": participant_primary,
        "context_type": context_type,
        "problem_rating": problem_rating,
        "user_rating_at_time": user_rating,
        "rating_anchor_source": anchor_source,
        "rating_gap": rating_gap,
        "rating_band": rating_band(rating_gap),
        "verdict_sequence": json.dumps([row.get("verdict") for row in ordered], ensure_ascii=False),
        "passed_test_progression": json.dumps([row.get("passed_test_count") for row in ordered], ensure_ascii=False),
        "episode_hash": _episode_hash(handle, problem_id, ordered),
    }


def rebuild_episodes(handle: str) -> dict[str, Any]:
    """Rebuild all episodes for a handle from cf_submissions_normalized. Idempotent."""
    canonical = store.canonical_handle(handle)
    with store.connect() as conn:
        submissions = [dict(row) for row in conn.execute(
            "SELECT * FROM cf_submissions_normalized WHERE handle = ?", (canonical,)
        ).fetchall()]
        rating_history = [dict(row) for row in conn.execute(
            "SELECT * FROM cf_user_rating_history WHERE handle = ?", (canonical,)
        ).fetchall()]
        user = conn.execute("SELECT rating FROM cf_users WHERE handle = ?", (canonical,)).fetchone()
        problem_ratings = {
            row["problem_key"]: row["rating"]
            for row in conn.execute("SELECT problem_key, rating FROM problems").fetchall()
        }
    current_rating = user["rating"] if user else None

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in submissions:
        grouped.setdefault(row["problem_key"], []).append(row)

    episodes = [
        build_episode(
            canonical,
            problem_id,
            rows,
            rating_history,
            current_rating,
            problem_rating_fallback=problem_ratings.get(problem_id),
        )
        for problem_id, rows in sorted(grouped.items())
    ]

    columns = list(episodes[0].keys()) if episodes else []
    with store.connect() as conn:
        conn.execute("DELETE FROM problem_episodes WHERE handle = ?", (canonical,))
        if episodes:
            placeholders = ", ".join(f":{col}" for col in columns)
            conn.executemany(
                f"INSERT INTO problem_episodes ({', '.join(columns)}) VALUES ({placeholders})",
                episodes,
            )

    return {
        "handle": canonical,
        "episodes": len(episodes),
        "from_submissions": len(submissions),
        "final_status_counts": dict(Counter(ep["final_status"] for ep in episodes)),
    }


def list_episodes(handle: str, limit: int = 200) -> list[dict[str, Any]]:
    canonical = store.canonical_handle(handle)
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM problem_episodes WHERE handle = ? ORDER BY last_submission_at DESC LIMIT ?",
            (canonical, limit),
        ).fetchall()
    episodes = []
    for row in rows:
        episode = dict(row)
        episode["eventual_ac"] = bool(episode["eventual_ac"])
        episode["verdict_sequence"] = json.loads(episode["verdict_sequence"])
        episode["passed_test_progression"] = json.loads(episode["passed_test_progression"])
        episodes.append(episode)
    return episodes


def get_episode(handle: str, problem_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM problem_episodes WHERE episode_id = ?",
            (episode_id_for(handle, problem_id),),
        ).fetchone()
    if row is None:
        return None
    episode = dict(row)
    episode["eventual_ac"] = bool(episode["eventual_ac"])
    episode["verdict_sequence"] = json.loads(episode["verdict_sequence"])
    episode["passed_test_progression"] = json.loads(episode["passed_test_progression"])
    return episode
