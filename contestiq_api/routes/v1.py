"""Versioned API v1 boundary.

These are the stable, contract-first endpoints. Analysis work is recorded in
the persistent backend_jobs store; execution is synchronous in-process for now
(real async workers arrive with the Phase 02 data platform).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from contestiq_api import jobs
from contestiq_api.errors import APIError
from contestiq_api.legacy_compat import legacy_analysis
from contestiq_api.metadata import response_metadata
from contestiq_api.rate_limit import check_analyze_rate_limit
from contestiq_api.routes.health import health as legacy_health
from contestiq_api.service import analyze_codeforces_handle, get_saved_analysis, validate_handle
from contestiq_api.settings import get_settings
from contestiq_api.versions import ANALYSIS_VERSION, PROBLEM_CATALOG_VERSION, TAXONOMY_VERSION
from contestiq_core.codeforces.client import CodeforcesAPIError, fetch_user_info, fetch_user_status

router = APIRouter(prefix="/api/v1")

ANALYSIS_JOB_TYPE = "analysis"


class AnalysisRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)
    force_refresh: bool = False
    idempotency_key: str | None = Field(default=None, max_length=128)


@router.get("/health")
async def health_v1():
    legacy = await legacy_health()
    return {
        **legacy,
        "service": "solvex-api",
        "api_version": "v1",
        "analysis_version": ANALYSIS_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "problem_catalog_version": PROBLEM_CATALOG_VERSION,
    }


def _analysis_source(analysis: dict[str, Any]) -> str:
    raw = str(analysis.get("data_quality_summary", {}).get("source", ""))
    if "offline" in raw:
        return "offline_sample"
    return "codeforces_public_api"


def _job_response(job: dict[str, Any], analysis: dict[str, Any] | None, reused: bool) -> dict[str, Any]:
    meta = response_metadata(
        source=_analysis_source(analysis) if analysis else "codeforces_public_api",
        warnings=list(analysis.get("warnings", [])) if analysis else [],
        data_cutoff_time=analysis.get("created_at") if analysis else None,
    )
    return {**meta, "job": jobs.public_job(job), "reused": reused}


def _run_analysis_job(job: dict[str, Any]) -> dict[str, Any]:
    """Execute an analysis job inline and record its terminal state."""
    handle = job["input"]["handle"]
    force_refresh = bool(job["input"].get("force_refresh", False))
    jobs.mark_running(job["id"])
    try:
        analysis = analyze_codeforces_handle(handle, debug=False, force_refresh=force_refresh)
    except APIError as exc:
        jobs.mark_finished(job["id"], "failed", error_message=f"{exc.error_code}: {exc.message}")
        raise
    except Exception as exc:
        jobs.mark_finished(job["id"], "failed", error_message=str(exc))
        raise APIError("ANALYSIS_FAILED", f"Analysis failed for handle {handle}.", 500) from exc

    status = "stale_cache_used" if analysis.get("from_cache") else "success"
    jobs.mark_finished(job["id"], status, result_ref=f"analysis/{validate_handle(handle).lower()}")
    refreshed = jobs.get_job(job["id"])
    assert refreshed is not None
    return refreshed


@router.post("/analysis/request")
def request_analysis(
    payload: AnalysisRequest,
    request: Request,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
):
    handle = validate_handle(payload.handle)
    idempotency_key = payload.idempotency_key or idempotency_key_header

    # Client-supplied idempotency key wins: retries never duplicate side effects.
    if idempotency_key:
        existing = jobs.find_job_by_idempotency_key(idempotency_key)
        if existing is not None:
            analysis = _saved_or_none(handle)
            return _job_response(existing, analysis, reused=True)

    # An active job for the same handle is reused rather than duplicated.
    active = jobs.find_active_job(ANALYSIS_JOB_TYPE, {"handle": handle})
    if active is not None:
        return _job_response(active, _saved_or_none(handle), reused=True)

    # Without force_refresh, a completed job whose analysis is still current is reused.
    if not payload.force_refresh:
        latest = jobs.find_latest_job(
            ANALYSIS_JOB_TYPE, {"handle": handle}, statuses={"success", "stale_cache_used"}
        )
        analysis = _saved_or_none(handle)
        if latest is not None and analysis is not None and analysis.get("model_version") == ANALYSIS_VERSION:
            return _job_response(latest, analysis, reused=True)

    settings = get_settings()
    rate_key = request.client.host if request.client and request.client.host else handle
    check_analyze_rate_limit(rate_key, settings.rate_limit_analyze_seconds)

    job = jobs.create_job(
        ANALYSIS_JOB_TYPE,
        {"handle": handle, "force_refresh": payload.force_refresh},
        idempotency_key=idempotency_key,
    )
    if job["status"] != "queued":  # idempotency race returned an existing job
        return _job_response(job, _saved_or_none(handle), reused=True)

    job = _run_analysis_job(job)
    return _job_response(job, _saved_or_none(handle), reused=False)


def _saved_or_none(handle: str) -> dict[str, Any] | None:
    try:
        return get_saved_analysis(handle, include_debug=False)
    except APIError:
        return None


@router.get("/analysis/jobs/{job_id}")
def analysis_job_status(job_id: str):
    job = jobs.get_job(job_id)
    if job is None or job["job_type"] != ANALYSIS_JOB_TYPE:
        raise APIError("JOB_NOT_FOUND", f"No analysis job found with id {job_id}.", 404)
    handle = job["input"].get("handle", "")
    analysis = _saved_or_none(handle) if handle else None
    return _job_response(job, analysis, reused=False)


@router.get("/analysis/latest/{handle}")
def latest_analysis(handle: str):
    cleaned = validate_handle(handle)
    analysis = get_saved_analysis(cleaned, include_debug=False)
    meta = response_metadata(
        source=_analysis_source(analysis),
        warnings=list(analysis.get("warnings", [])),
        data_cutoff_time=analysis.get("created_at"),
    )
    return {**meta, "handle": cleaned, "analysis": analysis}


@router.get("/compat/analyze/{handle}")
def compat_legacy_analysis(handle: str):
    """Temporary adapter serving the legacy frontend AnalysisResult shape.

    Exists so the Next.js /api/analyze route can proxy here instead of running
    its own TypeScript analysis. Remove once the UI consumes /api/v1 directly.
    """
    cleaned = validate_handle(handle)
    try:
        user = fetch_user_info(cleaned)
        submissions = fetch_user_status(cleaned)
    except CodeforcesAPIError as exc:
        message = str(exc)
        lowered = message.lower()
        if "429" in message or "rate limited" in lowered:
            raise APIError(
                "CODEFORCES_RATE_LIMITED",
                "Codeforces is rate-limiting requests. Please wait 1–2 minutes and try again.",
                429,
            ) from exc
        if "not found" in lowered:
            raise APIError("CODEFORCES_HANDLE_NOT_FOUND", f"Codeforces handle was not found: {cleaned}", 404) from exc
        raise APIError("CODEFORCES_UNAVAILABLE", "Codeforces API is temporarily unavailable. Try again later.", 502) from exc

    result = legacy_analysis(user, submissions)
    meta = response_metadata(source="codeforces_public_api", warnings=[], data_cutoff_time=None)
    # Legacy shape stays at the top level for the existing UI; v1 metadata rides along.
    return {**result, "_meta": meta}
