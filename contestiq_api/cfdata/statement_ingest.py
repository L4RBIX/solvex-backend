"""Automatic statement ingestion into the existing problem_statements store.

Flow:
  missing/pending stubs (catalog sync)
    → statement_ingest_queue
    → fetch official CF HTML
    → parse/validate
    → problem_import.apply_statement_content (_classify + _upsert_statement)
    → display_ready / asset_required / partial / failed

Does not create a second statement system. Never ingests editorials or
solutions. Never marks Arena capability directly — that stays derived from
display_ready via is_arena_solvable.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from contestiq_api.cfdata import store
from contestiq_api.cfdata import statement_fetch
from contestiq_api.cfdata import statement_html
from contestiq_api.cfdata.problem_import import apply_statement_content
from contestiq_api.settings import get_settings

logger = logging.getLogger("solvex.api")

_PROBLEM_ID_RE = re.compile(r"^([1-9]\d*)([A-Za-z][A-Za-z0-9]*)$")
SOURCE_NAME = statement_html.SOURCE_DATASET
BATCH_PREFIX = "cf-html-ingest"


def split_problem_id(problem_id: str) -> tuple[int, str]:
    match = _PROBLEM_ID_RE.fullmatch((problem_id or "").strip())
    if match is None:
        raise ValueError(f"invalid problem_id: {problem_id!r}")
    return int(match.group(1)), match.group(2).upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


def _backoff_seconds(attempts: int) -> float:
    # 1→2m, 2→15m, 3→1h, 4→6h, 5+→24h
    table = {1: 120, 2: 900, 3: 3600, 4: 21600}
    return float(table.get(attempts, 86400))


def enqueue_statement_ingestion(
    problem_ids: list[str] | None = None,
    *,
    reason: str = "manual",
    only_missing: bool = True,
) -> dict[str, Any]:
    """Enqueue problem IDs for statement fetch. Defaults to all non-display-ready."""
    if problem_ids is None:
        problem_ids = store.list_non_display_ready_problem_ids() if only_missing else sorted(
            store.list_problem_keys()
        )
    # Newest contests first.
    ordered = sorted(
        {pid for pid in problem_ids if pid},
        key=_problem_sort_key,
        reverse=True,
    )
    enqueued = store.enqueue_statement_ingest(ordered, reason=reason)
    return {"requested": len(ordered), "enqueued_or_reset": enqueued, "reason": reason}


def _problem_sort_key(problem_id: str) -> tuple[int, str]:
    try:
        contest_id, index = split_problem_id(problem_id)
        return contest_id, index
    except ValueError:
        return 0, problem_id


def ingest_one(
    problem_id: str,
    *,
    html: str | None = None,
    transport: statement_fetch.HtmlTransport | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Ingest a single problem statement. ``html`` injects a fixture (tests/offline)."""
    contest_id, index = split_problem_id(problem_id)
    started = time.monotonic()
    catalog = store.get_problem(problem_id) or {
        "problem_id": problem_id,
        "contest_id": contest_id,
        "index": index,
        "name": problem_id,
    }
    # Align catalog_row keys with archive shape used by _classify.
    catalog_row = {
        "problem_id": problem_id,
        "contest_id": int(catalog.get("contest_id") or contest_id),
        "index": str(catalog.get("problem_index") or catalog.get("index") or index),
        "name": catalog.get("name") or problem_id,
        "rating": catalog.get("rating"),
        "tags": catalog.get("tags") or [],
    }

    existing = store.get_problem_statement(problem_id)
    if (
        existing
        and bool(existing.get("display_ready"))
        and not force
        and (existing.get("source_dataset") or "") != SOURCE_NAME
        and not str(existing.get("content_hash") or "").startswith("pending-")
        and existing.get("availability_status") not in {"missing", "partial"}
    ):
        return {
            "problem_id": problem_id,
            "status": "skipped",
            "reason": "already_display_ready",
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        }

    fetch_meta: dict[str, Any] = {}
    if html is None:
        result = statement_fetch.fetch_problem_html(
            contest_id, index, transport=transport
        )
        html = result.text
        fetch_meta = {"http_status": result.status_code, "url": result.url}

    parsed = statement_html.parse_codeforces_problem_html(
        html,
        expected_contest_id=contest_id,
        expected_index=index,
    )

    # Extra validation gate before classify/upsert.
    content = parsed.content
    if not (content.get("description") or "").strip():
        raise statement_html.StatementParseError("empty description after parse")
    # Reject obvious editorial contamination in the statement body.
    desc_head = (content.get("description") or "")[:300].lower()
    if desc_head.startswith("editorial") or "solution:" == desc_head[:9]:
        raise statement_html.StatementParseError("editorial contamination rejected")

    batch_id = f"{BATCH_PREFIX}-{_iso()[:13]}"
    applied = apply_statement_content(
        problem_id,
        catalog_row,
        content,
        batch_id=batch_id,
        source_name=SOURCE_NAME,
        force=force,
    )

    status = _queue_status_from_payload(applied.get("payload") or {})
    return {
        "problem_id": problem_id,
        "status": status,
        "availability_status": (applied.get("payload") or {}).get("availability_status"),
        "display_ready": bool((applied.get("payload") or {}).get("display_ready")),
        "solve_ready": bool((applied.get("payload") or {}).get("solve_ready")),
        "picture_count": parsed.picture_count,
        "warnings": parsed.warnings,
        "action": applied.get("action"),
        "fetch": fetch_meta,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
    }


def _queue_status_from_payload(payload: dict[str, Any]) -> str:
    availability = payload.get("availability_status")
    if availability == "asset_required":
        return "asset_required"
    if availability == "partial":
        return "partial"
    if availability in {"complete_standard", "complete_interactive"} and payload.get("display_ready"):
        return "succeeded"
    if availability == "missing":
        return "failed"
    return "partial" if payload.get("display_ready") else "failed"


def process_statement_ingest_batch(
    *,
    limit: int | None = None,
    problem_ids: list[str] | None = None,
    transport: statement_fetch.HtmlTransport | None = None,
    force: bool = False,
    html_by_id: dict[str, str] | None = None,
    clock: Callable[[], datetime] = _now,
) -> dict[str, Any]:
    """Drain pending/retrying queue rows (newest first)."""
    settings = get_settings()
    limit = int(limit or settings.statement_ingest_batch_size or 25)
    started = time.monotonic()
    claimed = store.claim_statement_ingest_batch(
        limit=limit,
        problem_ids=problem_ids,
        now_iso=_iso(clock()),
    )

    counters = {
        "claimed": len(claimed),
        "succeeded": 0,
        "partial": 0,
        "asset_required": 0,
        "failed": 0,
        "retrying": 0,
        "skipped": 0,
    }
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for problem_id in claimed:
        try:
            html = (html_by_id or {}).get(problem_id)
            outcome = ingest_one(
                problem_id,
                html=html,
                transport=transport,
                force=force,
            )
            status = outcome.get("status") or "failed"
            if status == "skipped":
                counters["skipped"] += 1
                store.finish_statement_ingest(
                    problem_id,
                    status="succeeded",
                    detail="already_display_ready",
                    now_iso=_iso(clock()),
                )
            elif status in counters:
                counters[status] += 1
                store.finish_statement_ingest(
                    problem_id,
                    status=status,
                    detail=None,
                    now_iso=_iso(clock()),
                )
            else:
                counters["failed"] += 1
                store.finish_statement_ingest(
                    problem_id,
                    status="failed",
                    detail=f"unknown_status:{status}",
                    now_iso=_iso(clock()),
                )
            results.append(outcome)
        except Exception as exc:
            attempts = store.bump_statement_ingest_failure(
                problem_id,
                error=str(exc)[:500],
                next_attempt_at=_iso(clock() + timedelta(seconds=_backoff_seconds(
                    store.get_statement_ingest_attempts(problem_id)
                ))),
                now_iso=_iso(clock()),
            )
            max_attempts = int(settings.statement_ingest_max_attempts or 8)
            if attempts >= max_attempts:
                counters["failed"] += 1
                store.finish_statement_ingest(
                    problem_id,
                    status="failed",
                    detail=str(exc)[:500],
                    now_iso=_iso(clock()),
                )
                final_status = "failed"
            else:
                counters["retrying"] += 1
                final_status = "retrying"
            errors.append(f"{problem_id}: {exc}")
            results.append(
                {
                    "problem_id": problem_id,
                    "status": final_status,
                    "error": str(exc)[:500],
                }
            )
            logger.warning("statement_ingest failed for %s: %s", problem_id, exc)

    report = {
        "batch_id": str(uuid.uuid4()),
        **counters,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
        "queue": store.statement_ingest_queue_stats(),
        "coverage": store.arena_catalog_coverage_stats(),
        "errors": errors[:50],
        "results_sample": results[:20],
    }
    return report


def backfill_missing_statements(
    *,
    limit: int | None = None,
    min_contest_id: int | None = None,
    transport: statement_fetch.HtmlTransport | None = None,
    html_by_id: dict[str, str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Enqueue (optional filter) then process one or more batches until limit."""
    ids = store.list_non_display_ready_problem_ids()
    if min_contest_id is not None:
        filtered = []
        for pid in ids:
            try:
                contest_id, _ = split_problem_id(pid)
            except ValueError:
                continue
            if contest_id >= min_contest_id:
                filtered.append(pid)
        ids = filtered
    ids = sorted(ids, key=_problem_sort_key, reverse=True)
    if limit is not None:
        ids = ids[: int(limit)]
    enqueue_statement_ingestion(ids, reason="backfill")
    return process_statement_ingest_batch(
        limit=len(ids) or 1,
        problem_ids=ids,
        transport=transport,
        html_by_id=html_by_id,
        force=force,
    )
