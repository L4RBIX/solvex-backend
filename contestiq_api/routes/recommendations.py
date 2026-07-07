"""v1 recommendation and training-plan endpoints (Phase 05; entitlement-gated since Phase 06)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from contestiq_api import entitlements
from contestiq_api.cfdata import planner, profiles
from contestiq_api.errors import APIError
from contestiq_api.metadata import response_metadata
from contestiq_api.service import validate_handle

router = APIRouter(prefix="/api/v1")


class DailyQueueRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)
    queue_date: str | None = None
    size: int = Field(default=4, ge=3, le=5)
    force: bool = False


class PlanRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)
    start_date: str | None = None
    force: bool = False


class FeedbackRequest(BaseModel):
    feedback_type: str
    comment: str | None = Field(default=None, max_length=2000)


def _with_metadata(payload: dict) -> dict:
    meta = response_metadata(source="codeforces_public_api", warnings=payload.get("warnings", []))
    return {**meta, **payload}


@router.post("/recommendations/daily")
def daily_queue(payload: DailyQueueRequest, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    import time

    from contestiq_api import metrics

    handle = validate_handle(payload.handle)
    profiles.build_profiles(handle)  # refresh from latest analysis snapshot
    started = time.monotonic()
    result = planner.build_daily_queue(
        handle, queue_date=payload.queue_date, size=payload.size, force=payload.force
    )
    metrics.observe("recommendation_generation_latency_ms", (time.monotonic() - started) * 1000)
    if not result.get("items"):
        metrics.inc("empty_queue_total")
    else:
        from contestiq_api import product_events

        product_events.track("first_queue_generated", f"handle:{handle.lower()}")
    return entitlements.shape_queue_response(_with_metadata(result), ctx)


@router.get("/recommendations/today")
def today_queue(handle: str = Query(min_length=3, max_length=24),
                ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    cleaned = validate_handle(handle)
    result = planner.get_today_queue(cleaned)
    if result is None:
        raise APIError(
            "QUEUE_NOT_FOUND",
            "No daily queue exists for today. Create one with POST /api/v1/recommendations/daily.",
            404,
        )
    return entitlements.shape_queue_response(_with_metadata(result), ctx)


@router.post("/plans/7-day")
def plan_7_day(payload: PlanRequest, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    from contestiq_api import product_events

    handle = validate_handle(payload.handle)
    profiles.build_profiles(handle)
    plan = planner.build_plan(handle, "7_day", start_date=payload.start_date, force=payload.force)
    if plan.get("days"):
        product_events.track("plan_started", f"handle:{handle.lower()}", {"plan_type": "7_day"})
    return entitlements.shape_plan_response(_with_metadata(plan), ctx)


@router.post("/plans/14-day")
def plan_14_day(payload: PlanRequest, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    entitlements.require_feature(ctx, "plan_14_day")
    handle = validate_handle(payload.handle)
    profiles.build_profiles(handle)
    plan = planner.build_plan(handle, "14_day", start_date=payload.start_date, force=payload.force)
    return entitlements.shape_plan_response(_with_metadata(plan), ctx)


@router.get("/plans/{plan_id}")
def plan_by_id(plan_id: str, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    plan = planner.get_plan(plan_id)
    if plan is None:
        raise APIError("PLAN_NOT_FOUND", f"No training plan found with id {plan_id}.", 404)
    return entitlements.shape_plan_response(_with_metadata(plan), ctx)


@router.get("/weekly-report/{handle}")
def weekly_report(handle: str, ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    """Premium feature: weekly progress report comparing analysis snapshots."""
    from contestiq_api import weekly

    entitlements.require_feature(ctx, "weekly_report")
    cleaned = validate_handle(handle)
    report = weekly.get_weekly_report(cleaned)
    if report is None:
        report = weekly.generate_weekly_report(cleaned)
    if report.get("status") == "no_analysis_runs":
        raise APIError("ANALYSIS_REQUIRED", "Run a weakness analysis before requesting a weekly report.", 404)
    return _with_metadata(report)


@router.post("/recommendations/{item_id}/feedback")
def item_feedback(item_id: str, payload: FeedbackRequest, request: Request = None):
    from contestiq_api.throttle import throttle

    if request is not None:
        throttle(request, "recommendation_feedback")
    if payload.feedback_type not in profiles.FEEDBACK_TYPES:
        raise APIError(
            "INVALID_FEEDBACK_TYPE",
            f"feedback_type must be one of: {', '.join(sorted(profiles.FEEDBACK_TYPES))}",
            422,
        )
    result = profiles.record_feedback(item_id, payload.feedback_type, payload.comment)
    if result.get("status") == "item_not_found":
        raise APIError("ITEM_NOT_FOUND", f"No recommendation or plan item found with id {item_id}.", 404)
    from contestiq_api import product_events

    product_events.track("feedback_submitted", f"item:{item_id}", {"feedback_type": payload.feedback_type})
    return result
