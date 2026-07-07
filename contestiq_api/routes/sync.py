"""v1 sync endpoints: trigger Codeforces syncs and inspect sync status.

Sync runs synchronously in-process for now (same trade-off as Phase 01
analysis jobs); the cf_sync_jobs table already gives async workers a home.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from contestiq_api.cfdata import sync as cf_sync
from contestiq_api.cfdata.client import (
    CodeforcesClientError,
    CodeforcesNotFoundError,
    CodeforcesRateLimitedError,
    CodeforcesUnavailableError,
)
from contestiq_api.errors import APIError
from contestiq_api.rate_limit import check_analyze_rate_limit
from contestiq_api.service import validate_handle
from contestiq_api.settings import get_settings

router = APIRouter(prefix="/api/v1/sync")


class SyncRequest(BaseModel):
    force_full: bool = False


class ProblemsetSyncRequest(BaseModel):
    force: bool = False


def _map_client_error(exc: CodeforcesClientError) -> APIError:
    if isinstance(exc, CodeforcesNotFoundError):
        return APIError(exc.error_code, str(exc), 404)
    if isinstance(exc, CodeforcesRateLimitedError):
        return APIError(exc.error_code, str(exc), 429)
    if isinstance(exc, CodeforcesUnavailableError):
        return APIError(exc.error_code, str(exc), 502)
    return APIError(exc.error_code, str(exc), 502)


@router.post("/codeforces/{handle}")
def request_handle_sync(handle: str, payload: SyncRequest | None = None, request: Request = None):
    cleaned = validate_handle(handle)
    settings = get_settings()
    rate_key = request.client.host if request and request.client and request.client.host else cleaned
    check_analyze_rate_limit(f"sync:{rate_key}", settings.rate_limit_analyze_seconds)
    force_full = bool(payload.force_full) if payload else False
    import time

    from contestiq_api import metrics

    started = time.monotonic()
    try:
        job = cf_sync.sync_handle(cleaned, force_full=force_full)
    except cf_sync.SyncInProgressError as exc:
        if exc.job is not None:
            return {"job": exc.job, "reused": True}
        raise APIError("SYNC_IN_PROGRESS", "A sync is already running for this handle.", 409) from exc
    except CodeforcesClientError as exc:
        metrics.inc("cf_sync_errors_total")
        raise _map_client_error(exc) from exc
    metrics.observe("cf_sync_duration_ms", (time.monotonic() - started) * 1000)
    if job.get("stats", {}).get("used_stale_cache"):
        metrics.inc("cf_sync_stale_cache_total")
    return {"job": job, "reused": job.get("status") in {"queued", "running"}}


@router.get("/codeforces/{handle}")
def handle_sync_status(handle: str):
    cleaned = validate_handle(handle)
    return cf_sync.sync_status(cleaned)


@router.post("/problemset")
def request_problemset_sync(payload: ProblemsetSyncRequest | None = None):
    force = bool(payload.force) if payload else False
    try:
        return cf_sync.sync_problemset(force=force)
    except CodeforcesClientError as exc:
        raise _map_client_error(exc) from exc
