"""Batch worker: prioritize → build → gate → activate/review/reject."""

from __future__ import annotations

import logging
import time
from typing import Any

from contestiq_api.practice_packs.classify import classify_problem
from contestiq_api.practice_packs.jobs import (
    claim_pack_jobs,
    complete_pack_job,
    enqueue_pack_jobs,
    job_status_counts,
)
from contestiq_api.practice_packs.oracles import ORACLE_REGISTRY, build_candidate_pack
from contestiq_api.practice_packs.pipeline import upsert_practice_pack
from contestiq_api.practice_packs.priority import priority_score, rank_candidates
from contestiq_api.practice_packs.quality_score import AUTO_ACTIVATE_MIN, REVIEW_MIN
from contestiq_api.cfdata import store

logger = logging.getLogger(__name__)


def _problem_meta(problem_id: str) -> dict[str, Any]:
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT p.problem_key, p.rating, p.tags, ps.solved_count,
                   st.display_ready, st.is_interactive, st.io_mode, st.availability_status
            FROM problems p
            LEFT JOIN problem_statistics ps ON ps.problem_key = p.problem_key
            LEFT JOIN problem_statements st ON st.problem_id = p.problem_key
            WHERE p.problem_key = ?
            """,
            (problem_id,),
        ).fetchone()
    if row is None:
        return {"problem_id": problem_id}
    import json

    tags = row["tags"]
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    return {
        "problem_id": row["problem_key"],
        "rating": row["rating"],
        "tags": tags or [],
        "solved_count": int(row["solved_count"] or 0),
        "display_ready": bool(row["display_ready"]),
        "is_interactive": bool(row["is_interactive"]),
        "io_mode": row["io_mode"],
        "availability_status": row["availability_status"],
        "has_oracle": problem_id in ORACLE_REGISTRY,
    }


def enqueue_registry_candidates(*, limit: int | None = None) -> dict[str, Any]:
    """Enqueue oracle-registry problems that are not yet submit-capable."""
    from contestiq_api.practice_packs.pipeline import submit_capable_problem_ids

    capable = submit_capable_problem_ids()
    rows: list[dict[str, Any]] = []
    for pid in ORACLE_REGISTRY:
        if pid in capable:
            continue
        meta = _problem_meta(pid)
        meta["already_submit_capable"] = False
        meta["has_oracle"] = True
        meta["priority_score"] = priority_score(
            rating=meta.get("rating"),
            solved_count=int(meta.get("solved_count") or 0),
            tags=list(meta.get("tags") or []),
            has_oracle=True,
        )
        meta["support_class"] = classify_problem(
            is_interactive=bool(meta.get("is_interactive")),
            io_mode=meta.get("io_mode"),
            availability_status=meta.get("availability_status"),
            has_oracle=True,
            display_ready=bool(meta.get("display_ready")),
            rating=meta.get("rating"),
            tags=list(meta.get("tags") or []),
        )
        rows.append(meta)
    ranked = rank_candidates(rows)
    if limit is not None:
        ranked = ranked[: int(limit)]
    inserted = enqueue_pack_jobs(
        [r["problem_id"] for r in ranked],
        support_class="AUTO_HIGH_CONFIDENCE",
    )
    # Attach priority scores where schema allows (best-effort per row).
    with store.connect() as conn:
        for r in ranked:
            try:
                conn.execute(
                    "UPDATE practice_pack_jobs SET priority_score = ?, support_class = ? WHERE problem_id = ?",
                    (r.get("priority_score"), r.get("support_class"), r["problem_id"]),
                )
            except Exception:
                break
    return {"enqueued": inserted, "candidates": len(ranked), "job_counts": job_status_counts()}


def process_pack_job(problem_id: str, *, job_id: str, worker_id: str) -> dict[str, Any]:
    if problem_id not in ORACLE_REGISTRY:
        complete_pack_job(
            job_id,
            status="unsupported",
            last_error="no oracle registry entry",
            worker_id=worker_id,
        )
        return {"problem_id": problem_id, "status": "unsupported"}

    started = time.perf_counter()
    try:
        pack = build_candidate_pack(problem_id)
    except Exception as exc:  # noqa: BLE001
        complete_pack_job(
            job_id,
            status="rejected",
            last_error=str(exc),
            quality_report={"passed": False, "failures": [str(exc)]},
            worker_id=worker_id,
        )
        return {"problem_id": problem_id, "status": "rejected", "error": str(exc)}

    quality = pack.get("quality_report") or {}
    score = float(quality.get("quality_score") or 0)
    recommendation = quality.get("recommendation")
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    if not quality.get("passed"):
        complete_pack_job(
            job_id,
            status="rejected",
            quality_report=quality,
            last_error="quality gate failed",
            worker_id=worker_id,
        )
        return {
            "problem_id": problem_id,
            "status": "rejected",
            "quality_score": score,
            "elapsed_ms": elapsed_ms,
        }

    if recommendation == "auto_activate" or (
        recommendation is None and score >= AUTO_ACTIVATE_MIN and quality.get("passed")
    ):
        pack["review_state"] = "reviewed"
        ok = upsert_practice_pack(pack, activate=True)
        status = "active" if ok else "rejected"
        complete_pack_job(
            job_id,
            status=status if ok else "rejected",
            quality_report=quality,
            last_error=None if ok else "upsert failed",
            worker_id=worker_id,
        )
        return {
            "problem_id": problem_id,
            "status": status,
            "quality_score": score,
            "mutation_score": pack.get("mutation_score"),
            "elapsed_ms": elapsed_ms,
        }

    if recommendation == "review_required" or score >= REVIEW_MIN:
        pack["review_state"] = "review_required"
        upsert_practice_pack(pack, activate=False)
        complete_pack_job(
            job_id,
            status="review_required",
            quality_report=quality,
            worker_id=worker_id,
        )
        return {
            "problem_id": problem_id,
            "status": "review_required",
            "quality_score": score,
            "elapsed_ms": elapsed_ms,
        }

    complete_pack_job(
        job_id,
        status="rejected",
        quality_report=quality,
        last_error="quality_score below review threshold",
        worker_id=worker_id,
    )
    return {
        "problem_id": problem_id,
        "status": "rejected",
        "quality_score": score,
        "elapsed_ms": elapsed_ms,
    }


def run_batch(
    *,
    limit: int = 25,
    worker_id: str = "pack-batch-worker",
    lease_seconds: int = 600,
) -> dict[str, Any]:
    claimed = claim_pack_jobs(limit=limit, worker_id=worker_id, lease_seconds=lease_seconds)
    results = []
    for job in claimed:
        results.append(
            process_pack_job(
                job["problem_id"],
                job_id=job["job_id"],
                worker_id=worker_id,
            )
        )
    summary = {
        "claimed": len(claimed),
        "activated": sum(1 for r in results if r.get("status") == "active"),
        "review_required": sum(1 for r in results if r.get("status") == "review_required"),
        "rejected": sum(1 for r in results if r.get("status") == "rejected"),
        "unsupported": sum(1 for r in results if r.get("status") == "unsupported"),
        "results": results,
        "job_counts": job_status_counts(),
    }
    logger.info(
        "practice_pack_batch claimed=%s activated=%s review=%s rejected=%s",
        summary["claimed"],
        summary["activated"],
        summary["review_required"],
        summary["rejected"],
    )
    return summary
