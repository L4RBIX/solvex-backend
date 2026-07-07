"""Persistent backend job store.

Local persistence is SQLite (stdlib, zero-dependency) so tests and dev runs
work without external services. The canonical Postgres/Supabase schema for
production lives in db/migrations/007_backend_jobs.sql — keep both in sync.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contestiq_api.settings import get_settings

JOB_STATUSES = {"queued", "running", "success", "failed", "cancelled", "stale_cache_used"}
ACTIVE_STATUSES = {"queued", "running"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS backend_jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    input TEXT NOT NULL,
    result_ref TEXT,
    error_message TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_backend_jobs_type_status ON backend_jobs (job_type, status);
CREATE INDEX IF NOT EXISTS idx_backend_jobs_created_at ON backend_jobs (created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    job = dict(row)
    job["input"] = json.loads(job["input"])
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM backend_jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def find_job_by_idempotency_key(key: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM backend_jobs WHERE idempotency_key = ?", (key,)).fetchone()
    return _row_to_job(row) if row else None


def find_active_job(job_type: str, input_match: dict[str, Any]) -> dict[str, Any] | None:
    """Most recent queued/running job of this type whose input contains input_match."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM backend_jobs WHERE job_type = ? AND status IN ('queued', 'running') ORDER BY created_at DESC",
            (job_type,),
        ).fetchall()
    for row in rows:
        job = _row_to_job(row)
        if all(job["input"].get(key) == value for key, value in input_match.items()):
            return job
    return None


def find_latest_job(job_type: str, input_match: dict[str, Any], statuses: set[str] | None = None) -> dict[str, Any] | None:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM backend_jobs WHERE job_type = ? ORDER BY created_at DESC",
            (job_type,),
        ).fetchall()
    for row in rows:
        job = _row_to_job(row)
        if statuses is not None and job["status"] not in statuses:
            continue
        if all(job["input"].get(key) == value for key, value in input_match.items()):
            return job
    return None


def create_job(job_type: str, input: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
    """Insert a queued job. If idempotency_key already exists, return that job instead."""
    job_id = str(uuid.uuid4())
    with _connect() as conn:
        try:
            conn.execute(
                "INSERT INTO backend_jobs (id, job_type, status, input, idempotency_key, created_at) VALUES (?, ?, 'queued', ?, ?, ?)",
                (job_id, job_type, json.dumps(input, ensure_ascii=False), idempotency_key, _now()),
            )
        except sqlite3.IntegrityError:
            existing = find_job_by_idempotency_key(idempotency_key) if idempotency_key else None
            if existing is not None:
                return existing
            raise
    job = get_job(job_id)
    assert job is not None
    return job


def mark_running(job_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE backend_jobs SET status = 'running', started_at = ? WHERE id = ?",
            (_now(), job_id),
        )


def mark_finished(job_id: str, status: str, result_ref: str | None = None, error_message: str | None = None) -> None:
    if status not in JOB_STATUSES - ACTIVE_STATUSES:
        raise ValueError(f"Invalid terminal job status: {status}")
    with _connect() as conn:
        conn.execute(
            "UPDATE backend_jobs SET status = ?, result_ref = ?, error_message = ?, completed_at = ? WHERE id = ?",
            (status, result_ref, error_message, _now(), job_id),
        )


def public_job(job: dict[str, Any]) -> dict[str, Any]:
    """Job payload safe to return to clients (input is echoed as submitted, no internals)."""
    return {
        "job_id": job["id"],
        "job_type": job["job_type"],
        "status": job["status"],
        "input": job["input"],
        "result_ref": job["result_ref"],
        "error_message": job["error_message"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
    }
