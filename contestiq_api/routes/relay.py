"""Persistent statement-fetch relay API (pull jobs, submit HTML, heartbeat)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from contestiq_api import relay_auth
from contestiq_api.cfdata import store
from contestiq_api.cfdata import statement_html
from contestiq_api.cfdata import statement_ingest
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

router = APIRouter(prefix="/api/v1/relay/statements", tags=["statement-relay"])

_PROBLEM_ID_RE = re.compile(r"^([1-9]\d*)([A-Za-z][A-Za-z0-9]*)$")
_MAX_HTML_BYTES = 2_000_000


class HeartbeatRequest(BaseModel):
    version: str | None = None
    note: str | None = Field(default=None, max_length=200)


class JobResultRequest(BaseModel):
    http_status: int | None = None
    final_url: str | None = Field(default=None, max_length=500)
    html: str | None = Field(default=None, max_length=_MAX_HTML_BYTES)
    error: str | None = Field(default=None, max_length=500)
    failure_class: str | None = Field(default=None, max_length=32)
    fetched_at: str | None = None


def _classify_fetch_failure(http_status: int | None, html: str | None, error: str | None) -> str:
    text = (html or "")[:4000].lower()
    if http_status in {403, 401} or statement_html.is_cloudflare_or_challenge_page(html or ""):
        return "blocked"
    if http_status in {429, 500, 502, 503, 504} or (error and "timeout" in error.lower()):
        return "retryable"
    if http_status == 404 or statement_html.is_error_or_login_page(html or ""):
        return "permanent"
    if error:
        return "retryable"
    if http_status and http_status >= 400:
        return "retryable"
    if text and "problem-statement" not in text:
        return "retryable"
    return "retryable"


@router.post("/heartbeat")
def relay_heartbeat(
    payload: HeartbeatRequest,
    relay: dict[str, Any] = Depends(relay_auth.require_relay),
):
    store.upsert_relay_heartbeat(
        relay["relay_id"],
        version=payload.version,
        note=payload.note,
    )
    return {"ok": True, "relay_id": relay["relay_id"], "observability": store.statement_relay_observability()}


@router.get("/jobs/next")
def next_statement_job(
    limit: int = 1,
    relay: dict[str, Any] = Depends(relay_auth.require_relay),
):
    settings = get_settings()
    limit = max(1, min(int(limit or 1), 5))
    # Keep the queue primed for missing statements.
    store.enqueue_statement_ingest(store.list_non_display_ready_problem_ids()[:200], reason="relay_prime")
    jobs = store.lease_next_statement_jobs(
        limit=limit,
        relay_id=relay["relay_id"],
        lease_seconds=int(settings.statement_relay_lease_seconds or 600),
    )
    if not jobs:
        return {"job": None, "jobs": [], "observability": store.statement_relay_observability()}
    return {
        "job": jobs[0],
        "jobs": jobs,
        "observability": store.statement_relay_observability(),
    }


@router.post("/jobs/{problem_id}/result")
def submit_statement_job_result(
    problem_id: str,
    payload: JobResultRequest,
    relay: dict[str, Any] = Depends(relay_auth.require_relay),
):
    if _PROBLEM_ID_RE.fullmatch(problem_id.strip()) is None:
        raise APIError("INVALID_PROBLEM_ID", "Invalid problem id.", 400)

    html = payload.html
    if html is not None and len(html.encode("utf-8", errors="ignore")) > _MAX_HTML_BYTES:
        raise APIError("HTML_TOO_LARGE", "HTML payload exceeds size limit.", 413)

    failure_class = payload.failure_class
    if not failure_class:
        if html and payload.http_status == 200:
            failure_class = None
        else:
            failure_class = _classify_fetch_failure(payload.http_status, html, payload.error)

    content_hash = None
    if html:
        content_hash = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()

    accepted = store.record_statement_job_result(
        problem_id,
        relay_id=relay["relay_id"],
        ok=bool(html) and (payload.http_status in (None, 200)),
        html=html,
        http_status=payload.http_status,
        final_url=payload.final_url,
        error=payload.error,
        failure_class=failure_class,
        content_hash=content_hash,
    )
    if not accepted.get("accepted"):
        raise APIError("JOB_RESULT_REJECTED", accepted.get("reason") or "rejected", 409)

    # Successful HTML → authoritative backend parse/validate/upsert.
    if html and (payload.http_status in (None, 200)):
        try:
            store.claim_statement_ingest_batch(
                limit=1,
                problem_ids=[problem_id],
                leased_by=relay["relay_id"],
            )
            outcome = statement_ingest.ingest_one(problem_id, html=html)
            status = outcome.get("status") or "failed"
            store.finish_statement_ingest(
                problem_id,
                status=status if status != "skipped" else "succeeded",
                detail=None,
            )
            store.upsert_relay_heartbeat(
                relay["relay_id"],
                successful_fetch=status in {"succeeded", "partial", "asset_required"},
                failed=status == "failed",
                blocked=False,
            )
            return {
                "accepted": True,
                "ingest": outcome,
                "observability": store.statement_relay_observability(),
            }
        except Exception as exc:
            attempts = store.bump_statement_ingest_failure(
                problem_id,
                error=str(exc)[:500],
                next_attempt_at=_next_attempt_iso(accepted.get("attempts") or 1),
            )
            store.finish_statement_ingest(
                problem_id,
                status="retrying" if attempts < get_settings().statement_ingest_max_attempts else "failed",
                detail=str(exc)[:500],
            )
            store.upsert_relay_heartbeat(relay["relay_id"], failed=True)
            return {
                "accepted": True,
                "ingest": {"status": "failed", "error": str(exc)[:500]},
                "observability": store.statement_relay_observability(),
            }

    # Fetch-level failure path.
    attempts = int(accepted.get("attempts") or 1)
    if failure_class == "blocked":
        store.bump_statement_ingest_failure(
            problem_id,
            error=(payload.error or f"blocked HTTP {payload.http_status}")[:500],
            next_attempt_at=_next_attempt_iso(attempts, blocked=True),
        )
        store.upsert_relay_heartbeat(relay["relay_id"], blocked=True)
        final_status = "retrying"
    elif failure_class == "permanent":
        store.finish_statement_ingest(
            problem_id,
            status="failed",
            detail=(payload.error or "permanent fetch failure")[:500],
        )
        store.upsert_relay_heartbeat(relay["relay_id"], failed=True)
        final_status = "failed"
    else:
        store.bump_statement_ingest_failure(
            problem_id,
            error=(payload.error or f"retryable HTTP {payload.http_status}")[:500],
            next_attempt_at=_next_attempt_iso(attempts),
        )
        store.upsert_relay_heartbeat(relay["relay_id"], failed=True)
        final_status = "retrying"

    return {
        "accepted": True,
        "ingest": {"status": final_status, "failure_class": failure_class},
        "observability": store.statement_relay_observability(),
    }


def _next_attempt_iso(attempts: int, *, blocked: bool = False) -> str:
    from datetime import datetime, timedelta, timezone

    # 5m, 15m, 1h, 6h, 24h (+ longer when blocked)
    table = {1: 300, 2: 900, 3: 3600, 4: 21600}
    seconds = float(table.get(int(attempts), 86400))
    if blocked:
        seconds = max(seconds, 3600.0)
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
