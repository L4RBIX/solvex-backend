"""Contest → Arena → Pack → Learning pipeline (automatic)."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.contests.lifecycle import refresh_contest_lifecycles, refresh_problem_lifecycle
from contestiq_api.contests.similar import compute_similar_problems

logger = logging.getLogger(__name__)


def _now() -> str:
    return store._now()


def _record_event(contest_id: int, event_type: str, detail: dict[str, Any] | None = None) -> None:
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO contest_pipeline_events (event_id, contest_id, event_type, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), contest_id, event_type, json.dumps(detail or {}, ensure_ascii=False), _now()),
        )


def process_finished_contest(contest_id: int) -> dict[str, Any]:
    """Run the zero-day import pipeline for one finished contest."""
    from contestiq_api.cfdata import statement_ingest
    from contestiq_api.cfdata import sync as cf_sync
    from contestiq_api.cfdata import taxonomy
    from contestiq_api.practice_packs import batch as pack_batch
    from contestiq_api.practice_packs.jobs import enqueue_pack_jobs
    from contestiq_api.practice_packs.oracles import ORACLE_REGISTRY

    with store.connect() as conn:
        conn.execute(
            """
            UPDATE cf_contests
            SET pipeline_status = 'running', pipeline_started_at = COALESCE(pipeline_started_at, ?),
                pipeline_error = NULL, updated_at = ?
            WHERE contest_id = ?
            """,
            (_now(), _now(), contest_id),
        )
    _record_event(contest_id, "pipeline_started")

    result: dict[str, Any] = {"contest_id": contest_id, "steps": {}}
    try:
        # 1) Catalog import (problemset sync brings new problems).
        sync_result = cf_sync.sync_problemset(force=True)
        result["steps"]["catalog_sync"] = {
            "status": sync_result.get("status"),
            "new_problems": ((sync_result.get("catalog_sync") or {}).get("new_problems")),
        }

        with store.connect() as conn:
            problems = conn.execute(
                """
                SELECT problem_key, rating, tags FROM problems
                WHERE contest_id = ?
                ORDER BY problem_index
                """,
                (contest_id,),
            ).fetchall()
        problem_ids = [r["problem_key"] for r in problems]
        result["steps"]["problems"] = len(problem_ids)

        for pid in problem_ids:
            refresh_problem_lifecycle(pid)

        # 2) Statement ingest priority for this contest.
        if problem_ids:
            queued = statement_ingest.enqueue_statement_ingestion(
                problem_ids,
                reason=f"contest_{contest_id}_finished",
                only_missing=True,
            )
            result["steps"]["statement_enqueue"] = queued

        # 3) Learning metadata (skill map) for contest problems.
        if problem_ids:
            skill = taxonomy.build_problem_skill_map(problem_ids)
            result["steps"]["skill_map"] = skill

        # 4) Similar problems.
        similar_counts = 0
        for pid in problem_ids:
            compute_similar_problems(pid, limit=8)
            similar_counts += 1
        result["steps"]["similar_computed"] = similar_counts

        # 5) Pack factory — only oracle-registry problems (fail-closed).
        pack_ids = [r["problem_key"] for r in problems if r["problem_key"] in ORACLE_REGISTRY]
        if pack_ids:
            enq = enqueue_pack_jobs(
                pack_ids,
                support_class="AUTO_HIGH_CONFIDENCE",
                priority_score=90.0,
            )
            result["steps"]["pack_enqueue"] = {"inserted": enq, "candidates": len(pack_ids)}
            run = pack_batch.run_batch(limit=min(25, len(pack_ids)), worker_id="contest-pipeline")
            result["steps"]["pack_run"] = {
                "claimed": run.get("claimed"),
                "activated": run.get("activated"),
                "review_required": run.get("review_required"),
                "rejected": run.get("rejected"),
            }

        lifecycles = refresh_contest_lifecycles(contest_id)
        result["steps"]["lifecycle"] = {
            "problems": len(lifecycles),
            "by_stage": _count_stages(lifecycles),
        }

        with store.connect() as conn:
            conn.execute(
                """
                UPDATE cf_contests
                SET pipeline_status = 'complete', pipeline_completed_at = ?, updated_at = ?
                WHERE contest_id = ?
                """,
                (_now(), _now(), contest_id),
            )
        _record_event(contest_id, "pipeline_complete", result["steps"])
        result["status"] = "complete"
    except Exception as exc:
        logger.exception("contest pipeline failed contest_id=%s", contest_id)
        with store.connect() as conn:
            conn.execute(
                """
                UPDATE cf_contests
                SET pipeline_status = 'failed', pipeline_error = ?, updated_at = ?
                WHERE contest_id = ?
                """,
                (str(exc)[:500], _now(), contest_id),
            )
        _record_event(contest_id, "pipeline_failed", {"error": str(exc)[:500]})
        result["status"] = "failed"
        result["error"] = str(exc)[:500]
    return result


def _count_stages(lifecycles: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in lifecycles:
        stage = str(item.get("stage") or "UNKNOWN")
        out[stage] = out.get(stage, 0) + 1
    return out


def tick_contest_pipelines(*, limit: int = 3) -> dict[str, Any]:
    """Process queued contest pipelines (and retry recent failures once)."""
    with store.connect() as conn:
        queued = conn.execute(
            """
            SELECT contest_id FROM cf_contests
            WHERE pipeline_status = 'queued'
            ORDER BY COALESCE(start_time, 0) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        # Soft retry failures from last day.
        failed = conn.execute(
            """
            SELECT contest_id FROM cf_contests
            WHERE pipeline_status = 'failed'
              AND updated_at > datetime('now', '-1 day')
            ORDER BY updated_at ASC
            LIMIT 1
            """,
        ).fetchall()

    ids = [int(r["contest_id"]) for r in queued] + [int(r["contest_id"]) for r in failed]
    results = []
    for contest_id in ids[:limit]:
        results.append(process_finished_contest(contest_id))
    return {"processed": len(results), "results": results}


def refresh_open_contest_readiness(*, limit_contests: int = 15) -> dict[str, Any]:
    """Recompute lifecycle for recent finished contests (statement/pack progress)."""
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT contest_id FROM cf_contests
            WHERE phase = 'FINISHED' AND is_gym = 0
            ORDER BY COALESCE(start_time, 0) DESC
            LIMIT ?
            """,
            (limit_contests,),
        ).fetchall()
    refreshed = 0
    for row in rows:
        refresh_contest_lifecycles(int(row["contest_id"]))
        refreshed += 1
    return {"contests": refreshed}
