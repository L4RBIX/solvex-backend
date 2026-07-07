"""v1 weakness-analysis endpoints (Phase 04; entitlement-gated since Phase 06)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from contestiq_api import entitlements
from contestiq_api.cfdata import episodes as cf_episodes
from contestiq_api.cfdata import weakness
from contestiq_api.errors import APIError
from contestiq_api.metadata import response_metadata
from contestiq_api.service import validate_handle

router = APIRouter(prefix="/api/v1/weakness")


def _with_metadata(payload: dict) -> dict:
    meta = response_metadata(
        source="codeforces_public_api",
        warnings=payload.get("run_warnings", []),
        data_cutoff_time=payload.get("data_cutoff_time"),
    )
    return {**meta, **payload}


@router.post("/{handle}/analyze")
def analyze(handle: str, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    import time

    from contestiq_api import metrics

    cleaned = validate_handle(handle)
    entitlements.check_and_count_usage(ctx, "analysis_runs_per_day")
    started = time.monotonic()
    # Episodes are the engine's input; rebuilding first keeps them consistent
    # with the latest synced submissions (deterministic + idempotent).
    cf_episodes.rebuild_episodes(cleaned)
    payload = weakness.analyze_handle_weakness(cleaned)
    metrics.observe("analysis_latency_ms", (time.monotonic() - started) * 1000)
    metrics.inc("analysis_runs_total")
    from contestiq_api import product_events

    product_events.track("first_analysis_completed", f"handle:{cleaned.lower()}", {"run_id": payload["run_id"]})
    return entitlements.shape_weakness_response(_with_metadata(payload), ctx)


@router.get("/{handle}/latest")
def latest(handle: str, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    cleaned = validate_handle(handle)
    run_id = weakness.latest_run_id(cleaned)
    if run_id is None:
        raise APIError("ANALYSIS_RUN_NOT_FOUND", f"No weakness analysis run found for {cleaned}.", 404)
    payload = weakness.get_run(run_id)
    assert payload is not None
    return entitlements.shape_weakness_response(_with_metadata(payload), ctx)


@router.get("/runs/{run_id}")
def run(run_id: str, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    payload = weakness.get_run(run_id)
    if payload is None:
        raise APIError("ANALYSIS_RUN_NOT_FOUND", f"No weakness analysis run found with id {run_id}.", 404)
    return entitlements.shape_weakness_response(_with_metadata(payload), ctx)
