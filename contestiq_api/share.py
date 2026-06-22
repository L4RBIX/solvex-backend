from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from contestiq_api import MODEL_VERSION
from contestiq_api.errors import APIError
from contestiq_api.service import public_analysis, validate_handle
from contestiq_api.storage import load_analysis, load_share, save_share
from contestiq_api.workspace import update_workspace_share

PUBLIC_REPORT_FIELDS = {
    "handle",
    "analysis_id",
    "created_at",
    "model_version",
    "profile_summary",
    "weakness_map_user",
    "daily_queue",
    "warnings",
    "safe_interpretation",
    "caveats",
}

SAFE_INTERPRETATION = (
    "Shareable training report based on public Codeforces history. "
    "This is not a verification result."
)

CAVEATS = [
    "Codeforces data does not reveal the true solving process.",
    "This report does not verify skill, identity, or independent solving.",
    "This is a training aid, not proof of ability.",
]


def _sanitize_public_text(value: Any) -> Any:
    if isinstance(value, str):
        return (
            value.replace("public outcome/history data", "public history data")
            .replace("outcome/history data", "history data")
            .replace("public outcome history", "public history")
            .replace("outcome history", "history")
            .replace("outcomes", "results")
            .replace("outcome", "result")
        )
    if isinstance(value, list):
        return [_sanitize_public_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_public_text(item) for key, item in value.items()}
    return value


def build_public_report(analysis: dict[str, Any]) -> dict[str, Any]:
    public = public_analysis(deepcopy(analysis), include_debug=False)
    report = {
        "handle": public.get("handle"),
        "analysis_id": public.get("analysis_id"),
        "created_at": public.get("created_at"),
        "model_version": public.get("model_version"),
        "profile_summary": public.get("profile_summary", {}),
        "weakness_map_user": public.get("weakness_map_user", {"likely_needs_work": [], "watchlist": [], "limited_evidence": []}),
        "daily_queue": public.get("daily_queue", {}),
        "warnings": public.get("warnings", []),
        "safe_interpretation": SAFE_INTERPRETATION,
        "caveats": CAVEATS,
    }
    return _sanitize_public_text({key: report[key] for key in PUBLIC_REPORT_FIELDS})


def create_share_for_handle(handle: str) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    analysis = load_analysis(cleaned)
    if analysis is None:
        raise APIError("ANALYSIS_NOT_FOUND", f"No saved analysis found for handle {cleaned}.", 404)
    share_id = uuid.uuid4().hex[:16]
    record = {
        "share_id": share_id,
        "handle": cleaned,
        "analysis_id": analysis.get("analysis_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_version": MODEL_VERSION,
        "public_report": build_public_report(analysis),
    }
    save_share(share_id, record)
    update_workspace_share(cleaned, share_id, analysis)
    return {
        "status": "created",
        "share_id": share_id,
        "handle": cleaned,
        "analysis_id": analysis.get("analysis_id"),
        "public_url_path": f"/api/share/{share_id}",
    }


def get_share_report(share_id: str) -> dict[str, Any]:
    record = load_share(share_id)
    if record is None:
        raise APIError("SHARE_NOT_FOUND", "Share report not found.", 404)
    return {
        "status": "available",
        "share_id": record["share_id"],
        "report_type": "shareable_training_report",
        "public_report": record["public_report"],
    }


def _skill_lines(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["* none"]
    return [f"* {row.get('display_name') or row.get('skill_id')} — {row.get('explanation', '')}" for row in rows]


def share_markdown(share_id: str) -> str:
    response = get_share_report(share_id)
    report = response["public_report"]
    weakness = report.get("weakness_map_user", {})
    queue = report.get("daily_queue", {})
    lines = [
        "# ContestIQ Shareable Training Report",
        "",
        "This report is based only on public Codeforces history. It is not a verification result.",
        "",
        "## Profile",
        "",
        f"* Handle: {report.get('handle')}",
        f"* Model version: {report.get('model_version')}",
        f"* Analysis date: {report.get('created_at')}",
        "",
        "## Weakness Map",
        "",
        "### Likely Needs Work",
        *_skill_lines(weakness.get("likely_needs_work", [])),
        "",
        "### Watchlist",
        *_skill_lines(weakness.get("watchlist", [])),
        "",
        "### Limited Evidence",
        *_skill_lines(weakness.get("limited_evidence", [])),
        "",
        "## Daily Queue",
        "",
    ]
    items = queue.get("items", [])
    if items:
        for item in items:
            lines.append(
                f"* {item.get('slot_type')} / {item.get('anchor_skill')} / "
                f"{item.get('problem_name')} / rating {item.get('rating')}"
            )
    else:
        lines.append("* none")
    lines.extend(["", "## Caveats", ""])
    lines.extend([f"* {caveat}" for caveat in CAVEATS])
    return "\n".join(lines)
