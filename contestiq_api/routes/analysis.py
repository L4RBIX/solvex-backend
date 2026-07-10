from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from contestiq_api import auth, entitlements, handles
from contestiq_api.errors import APIError
from contestiq_api.models import AnalyzeRequest
from contestiq_api.progress_report import analysis_history, generate_weekly_report, weekly_report_markdown
from contestiq_api.rate_limit import check_analyze_rate_limit
from contestiq_api.service import (
    analyze_codeforces_handle,
    daily_queue_only,
    get_saved_analysis,
    progress_for_handle,
    validate_handle,
    weakness_map_only,
)
from contestiq_api.settings import get_settings

router = APIRouter()


def _rate_limit_key(request: Request, payload: AnalyzeRequest) -> str:
    if request.client and request.client.host:
        return request.client.host
    return validate_handle(payload.handle)


@router.post("/api/analyze")
def analyze(payload: AnalyzeRequest, request: Request):
    settings = get_settings()
    check_analyze_rate_limit(_rate_limit_key(request, payload), settings.rate_limit_analyze_seconds)
    return analyze_codeforces_handle(
        payload.handle,
        debug=payload.debug,
        force_refresh=payload.force_refresh,
    )


@router.get("/api/analysis/{handle}/weakness-map")
def weakness_map(handle: str):
    return weakness_map_only(handle)


@router.get("/api/analysis/{handle}/daily-queue")
def daily_queue(handle: str):
    return daily_queue_only(handle)


@router.get("/api/analysis/{handle}/debug")
def debug_analysis(handle: str):
    if not get_settings().enable_debug_endpoint:
        raise APIError("DEBUG_ENDPOINT_DISABLED", "Debug endpoint is disabled in this environment.", 403)
    return get_saved_analysis(handle, include_debug=True)


@router.get("/api/analysis/{handle}/history")
def history(handle: str):
    return analysis_history(handle)


@router.get("/api/analysis/{handle}/weekly-report")
def weekly_report(
    handle: str,
    user: dict[str, Any] = Depends(auth.require_user),
    ctx: dict[str, Any] = Depends(entitlements.plan_context),
):
    cleaned = _require_weekly_report_access(handle, user, ctx)
    report = generate_weekly_report(cleaned)
    _track_weekly_report_view(user)
    return report


@router.get("/api/analysis/{handle}/weekly-report.md", response_class=PlainTextResponse)
def weekly_report_md(
    handle: str,
    user: dict[str, Any] = Depends(auth.require_user),
    ctx: dict[str, Any] = Depends(entitlements.plan_context),
):
    cleaned = _require_weekly_report_access(handle, user, ctx)
    report = weekly_report_markdown(cleaned)
    _track_weekly_report_view(user)
    return report


def _track_weekly_report_view(user: dict[str, Any]) -> None:
    from contestiq_api import product_events

    product_events.track("weekly_report_generated", f"user:{user['user_id']}")


def _require_weekly_report_access(
    handle: str,
    user: dict[str, Any],
    ctx: dict[str, Any],
) -> str:
    """Authorize the legacy report surface without making analysis private."""
    cleaned = validate_handle(handle)
    if handles.owner_user_id_for_handle(cleaned) != user["user_id"]:
        raise APIError(
            "HANDLE_NOT_VERIFIED",
            "Verify ownership of this Codeforces handle before viewing its weekly report.",
            403,
        )
    entitlements.require_feature(ctx, "weekly_report")
    return cleaned


@router.get("/api/analysis/{handle}/progress")
def progress(handle: str):
    return progress_for_handle(handle)


@router.get("/api/analysis/{handle}")
def analysis(handle: str):
    return get_saved_analysis(handle, include_debug=False)
