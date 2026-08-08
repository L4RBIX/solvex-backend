"""Similar-problem recommendations (tag/rating heuristic; ML-ready table)."""

from __future__ import annotations

import json
from typing import Any

from contestiq_api.cfdata import store


def compute_similar_problems(problem_id: str, *, limit: int = 8) -> list[dict[str, Any]]:
    with store.connect() as conn:
        src = conn.execute(
            "SELECT problem_key, contest_id, rating, tags FROM problems WHERE problem_key = ?",
            (problem_id,),
        ).fetchone()
        if src is None:
            return []
        tags = json.loads(src["tags"] or "[]")
        rating = src["rating"]
        contest_id = src["contest_id"]
        # Candidate pool: nearby rating band.
        if rating is None:
            candidates = conn.execute(
                """
                SELECT problem_key, contest_id, rating, tags FROM problems
                WHERE problem_key != ?
                ORDER BY updated_at DESC LIMIT 400
                """,
                (problem_id,),
            ).fetchall()
        else:
            candidates = conn.execute(
                """
                SELECT problem_key, contest_id, rating, tags FROM problems
                WHERE problem_key != ?
                  AND rating IS NOT NULL
                  AND rating BETWEEN ? AND ?
                ORDER BY ABS(rating - ?) ASC
                LIMIT 500
                """,
                (problem_id, int(rating) - 300, int(rating) + 300, int(rating)),
            ).fetchall()

    tag_set = {str(t).lower() for t in tags}
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in candidates:
        other_tags = {str(t).lower() for t in json.loads(row["tags"] or "[]")}
        overlap = tag_set & other_tags
        if not overlap and rating is None:
            continue
        score = 0.0
        reasons: list[str] = []
        if overlap:
            jaccard = len(overlap) / max(1, len(tag_set | other_tags))
            score += 4.0 * jaccard
            reasons.append(f"tags:{','.join(sorted(overlap)[:4])}")
        if rating is not None and row["rating"] is not None:
            delta = abs(int(row["rating"]) - int(rating))
            score += max(0.0, 3.0 - delta / 100.0)
            reasons.append(f"rating_delta:{delta}")
        if contest_id is not None and row["contest_id"] == contest_id:
            score -= 1.5  # prefer practice outside same contest
            reasons.append("same_contest_penalty")
        if score <= 0.5:
            continue
        scored.append(
            (
                score,
                {
                    "problem_id": row["problem_key"],
                    "score": round(score, 4),
                    "reasons": reasons,
                    "rating": row["rating"],
                    "tags": list(other_tags),
                },
            )
        )

    scored.sort(key=lambda x: -x[0])
    top = [item for _, item in scored[:limit]]
    now = store._now()
    with store.connect() as conn:
        conn.execute("DELETE FROM problem_similar WHERE problem_id = ?", (problem_id,))
        for item in top:
            conn.execute(
                """
                INSERT INTO problem_similar (problem_id, similar_problem_id, score, reasons, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    problem_id,
                    item["problem_id"],
                    item["score"],
                    json.dumps(item["reasons"], ensure_ascii=False),
                    now,
                ),
            )
    return top


def list_similar(problem_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT s.similar_problem_id, s.score, s.reasons, p.name, p.rating, p.tags
            FROM problem_similar s
            JOIN problems p ON p.problem_key = s.similar_problem_id
            WHERE s.problem_id = ?
            ORDER BY s.score DESC
            LIMIT ?
            """,
            (problem_id, limit),
        ).fetchall()
    out = []
    for row in rows:
        out.append(
            {
                "problem_id": row["similar_problem_id"],
                "name": row["name"],
                "rating": row["rating"],
                "tags": json.loads(row["tags"] or "[]"),
                "score": row["score"],
                "reasons": json.loads(row["reasons"] or "[]"),
            }
        )
    return out
