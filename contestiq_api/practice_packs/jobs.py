"""Practice pack job queue with leases/retries for batch generation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from contestiq_api.cfdata import store


def _now() -> str:
    return store._now()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def enqueue_pack_jobs(
    problem_ids: list[str],
    *,
    support_class: str | None = None,
    priority_score: float | None = None,
) -> int:
    """Insert pending jobs for problems not already terminal/active."""
    inserted = 0
    now = _now()
    with store.connect() as conn:
        for problem_id in problem_ids:
            job_id = f"ppj_{problem_id}_{uuid.uuid4().hex[:8]}"
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO practice_pack_jobs (
                        job_id, problem_id, status, support_class, attempt_count,
                        last_error, quality_report, created_at, updated_at,
                        priority_score, leased_until, leased_by, next_attempt_at
                    ) VALUES (?, ?, 'pending', ?, 0, NULL, '{}', ?, ?, ?, NULL, NULL, ?)
                    """,
                    (
                        job_id,
                        problem_id,
                        support_class,
                        now,
                        now,
                        priority_score,
                        now,
                    ),
                )
                if conn.total_changes:
                    inserted += 1
            except Exception:
                # Older SQLite schema without lease columns — minimal insert.
                conn.execute(
                    """
                    INSERT OR IGNORE INTO practice_pack_jobs (
                        job_id, problem_id, status, support_class, attempt_count,
                        last_error, quality_report, created_at, updated_at
                    ) VALUES (?, ?, 'pending', ?, 0, NULL, '{}', ?, ?)
                    """,
                    (job_id, problem_id, support_class, now, now),
                )
                if conn.total_changes:
                    inserted += 1
    return inserted


def reclaim_expired_leases(*, now_iso: str | None = None) -> int:
    now = now_iso or _now()
    with store.connect() as conn:
        cur = conn.execute(
            """
            UPDATE practice_pack_jobs
            SET status = CASE WHEN attempt_count > 0 THEN 'retrying' ELSE 'pending' END,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = ?
            WHERE status = 'processing'
              AND leased_until IS NOT NULL
              AND leased_until <= ?
            """,
            (now, now),
        )
        return int(cur.rowcount or 0)


def claim_pack_jobs(
    *,
    limit: int = 25,
    worker_id: str,
    lease_seconds: int = 600,
    now_iso: str | None = None,
) -> list[dict[str, Any]]:
    now = now_iso or _now()
    reclaim_expired_leases(now_iso=now)
    try:
        base = datetime.fromisoformat(now.replace("Z", "+00:00"))
    except ValueError:
        base = datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    lease_until = (base + timedelta(seconds=int(lease_seconds))).isoformat()

    claimed: list[dict[str, Any]] = []
    with store.connect() as conn:
        try:
            rows = conn.execute(
                """
                SELECT job_id, problem_id, status, attempt_count, support_class, priority_score
                FROM practice_pack_jobs
                WHERE status IN ('pending', 'retrying')
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                  AND (leased_until IS NULL OR leased_until <= ?)
                ORDER BY COALESCE(priority_score, 0) DESC, updated_at ASC
                LIMIT ?
                """,
                (now, now, int(limit)),
            ).fetchall()
        except Exception:
            rows = conn.execute(
                """
                SELECT job_id, problem_id, status, attempt_count, support_class
                FROM practice_pack_jobs
                WHERE status IN ('pending', 'retrying')
                ORDER BY updated_at ASC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

        for row in rows:
            conn.execute(
                """
                UPDATE practice_pack_jobs
                SET status = 'processing',
                    attempt_count = attempt_count + 1,
                    leased_until = ?,
                    leased_by = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (lease_until, worker_id, now, row["job_id"]),
            )
            claimed.append(dict(row))
    return claimed


def complete_pack_job(
    job_id: str,
    *,
    status: str,
    quality_report: dict[str, Any] | None = None,
    last_error: str | None = None,
    worker_id: str | None = None,
) -> None:
    now = _now()
    with store.connect() as conn:
        if worker_id:
            row = conn.execute(
                "SELECT leased_by FROM practice_pack_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row and row["leased_by"] and row["leased_by"] != worker_id:
                return
        conn.execute(
            """
            UPDATE practice_pack_jobs
            SET status = ?,
                quality_report = ?,
                last_error = ?,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = ?,
                next_attempt_at = CASE
                    WHEN ? IN ('pending', 'retrying') THEN ?
                    ELSE next_attempt_at
                END
            WHERE job_id = ?
            """,
            (
                status,
                _canonical(quality_report or {}),
                last_error,
                now,
                status,
                now,
                job_id,
            ),
        )


def job_status_counts() -> dict[str, int]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS c FROM practice_pack_jobs GROUP BY status"
        ).fetchall()
    return {str(r["status"]): int(r["c"]) for r in rows}
