from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from contestiq_api.service import validate_handle
from contestiq_api.storage import list_snapshots as storage_list_snapshots

SAFE_INTERPRETATION_AVAILABLE = (
    "The latest snapshot shows changes in public friction signals and training focus. "
    "This is based only on Codeforces public outcome/history data and should be treated "
    "as a training aid, not verification."
)
SAFE_INTERPRETATION_NOT_ENOUGH = "ContestIQ needs at least two saved analyses to build a weekly report."

CAVEATS = [
    "Codeforces data does not reveal true solving process.",
    "This report is not verification.",
    "This suggests a training focus, not a diagnosis of ability.",
]


def _parse_created_at(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def list_snapshots(handle: str) -> list[dict[str, Any]]:
    validate_handle(handle)
    return storage_list_snapshots(handle)


def _bucket_items(snapshot: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    return list(snapshot.get("weakness_map_user", {}).get(bucket, []))


def _bucket_ids(snapshot: dict[str, Any], bucket: str) -> set[str]:
    return {row.get("skill_id") for row in _bucket_items(snapshot, bucket) if row.get("skill_id")}


def summarize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    weakness = snapshot.get("weakness_map_user", {})
    queue = snapshot.get("daily_queue", {})
    return {
        "analysis_id": snapshot.get("analysis_id"),
        "created_at": snapshot.get("created_at"),
        "model_version": snapshot.get("model_version"),
        "queue_mode": queue.get("queue_mode"),
        "likely_needs_work_count": len(weakness.get("likely_needs_work", [])),
        "watchlist_count": len(weakness.get("watchlist", [])),
        "limited_evidence_count": len(weakness.get("limited_evidence", [])),
    }


def extract_public_skill_ids(weakness_map_user: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "likely_needs_work": {row.get("skill_id") for row in weakness_map_user.get("likely_needs_work", []) if row.get("skill_id")},
        "watchlist": {row.get("skill_id") for row in weakness_map_user.get("watchlist", []) if row.get("skill_id")},
        "limited_evidence": {row.get("skill_id") for row in weakness_map_user.get("limited_evidence", []) if row.get("skill_id")},
    }


def extract_current_training_focus(daily_queue: dict[str, Any]) -> list[dict[str, Any]]:
    focus = []
    for item in daily_queue.get("items", []):
        focus.append(
            {
                "slot_type": item.get("slot_type"),
                "anchor_skill": item.get("anchor_skill"),
                "problem_key": item.get("problem_key"),
                "problem_name": item.get("problem_name"),
                "rating": item.get("rating"),
            }
        )
    return focus


def _focus_skills(snapshot: dict[str, Any]) -> set[str]:
    queue_skills = {
        item.get("anchor_skill")
        for item in snapshot.get("daily_queue", {}).get("items", [])
        if item.get("anchor_skill")
    }
    watchlist = _bucket_ids(snapshot, "watchlist")
    return queue_skills | watchlist


def compare_snapshots(baseline: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    return {
        "queue_mode_latest": latest.get("daily_queue", {}).get("queue_mode"),
        "queue_mode_previous": baseline.get("daily_queue", {}).get("queue_mode"),
        "queue_mode_changed": baseline.get("daily_queue", {}).get("queue_mode") != latest.get("daily_queue", {}).get("queue_mode"),
        "watchlist_added": sorted(_bucket_ids(latest, "watchlist") - _bucket_ids(baseline, "watchlist")),
        "watchlist_removed": sorted(_bucket_ids(baseline, "watchlist") - _bucket_ids(latest, "watchlist")),
        "limited_evidence_added": sorted(_bucket_ids(latest, "limited_evidence") - _bucket_ids(baseline, "limited_evidence")),
        "limited_evidence_removed": sorted(_bucket_ids(baseline, "limited_evidence") - _bucket_ids(latest, "limited_evidence")),
        "likely_needs_work_added": sorted(_bucket_ids(latest, "likely_needs_work") - _bucket_ids(baseline, "likely_needs_work")),
        "likely_needs_work_removed": sorted(_bucket_ids(baseline, "likely_needs_work") - _bucket_ids(latest, "likely_needs_work")),
        "repeated_focus_skills": sorted(_focus_skills(baseline) & _focus_skills(latest)),
        "current_training_focus": extract_current_training_focus(latest.get("daily_queue", {})),
    }


def analysis_history(handle: str) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    snapshots = list_snapshots(cleaned)
    if not snapshots:
        return {"handle": cleaned, "status": "not_found", "count": 0, "items": []}
    items = [summarize_snapshot(snapshot) for snapshot in sorted(snapshots, key=lambda row: row.get("created_at", ""), reverse=True)]
    return {"handle": cleaned, "status": "available", "count": len(items), "items": items}


def _select_baseline(snapshots: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    sorted_snapshots = sorted(snapshots, key=lambda row: row.get("created_at", ""))
    latest = sorted_snapshots[-1]
    latest_time = _parse_created_at(latest.get("created_at"))
    window_start = latest_time - timedelta(days=7)
    in_window = [snapshot for snapshot in sorted_snapshots if _parse_created_at(snapshot.get("created_at")) >= window_start]
    if len(in_window) >= 2:
        return in_window[0], latest
    return sorted_snapshots[-2], latest


def generate_weekly_report(handle: str) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    snapshots = list_snapshots(cleaned)
    if len(snapshots) < 2:
        latest = snapshots[-1] if snapshots else None
        return {
            "handle": cleaned,
            "status": "not_enough_history",
            "latest_analysis_id": latest.get("analysis_id") if latest else None,
            "baseline_analysis_id": None,
            "period": {
                "baseline_created_at": None,
                "latest_created_at": latest.get("created_at") if latest else None,
            },
            "summary": {
                "queue_mode_latest": latest.get("daily_queue", {}).get("queue_mode") if latest else None,
                "queue_mode_previous": None,
                "queue_mode_changed": False,
                "watchlist_added": [],
                "watchlist_removed": [],
                "limited_evidence_added": [],
                "limited_evidence_removed": [],
                "likely_needs_work_added": [],
                "likely_needs_work_removed": [],
                "repeated_focus_skills": [],
                "current_training_focus": [],
            },
            "safe_interpretation": SAFE_INTERPRETATION_NOT_ENOUGH,
            "caveats": CAVEATS,
        }
    baseline, latest = _select_baseline(snapshots)
    return {
        "handle": cleaned,
        "status": "available",
        "latest_analysis_id": latest.get("analysis_id"),
        "baseline_analysis_id": baseline.get("analysis_id"),
        "period": {
            "baseline_created_at": baseline.get("created_at"),
            "latest_created_at": latest.get("created_at"),
        },
        "summary": compare_snapshots(baseline, latest),
        "safe_interpretation": SAFE_INTERPRETATION_AVAILABLE,
        "caveats": CAVEATS,
    }


def weekly_report_markdown(handle: str) -> str:
    report = generate_weekly_report(handle)
    summary = report["summary"]
    lines = [
        "# ContestIQ Weekly Training Report",
        "",
        "This report is based only on public Codeforces history and ContestIQ snapshots. It is not a verification result.",
        "",
        "## Summary",
        "",
        f"* Status: {report['status']}",
        f"* Latest queue mode: {summary.get('queue_mode_latest')}",
        f"* Previous queue mode: {summary.get('queue_mode_previous')}",
        f"* Queue mode changed: {summary.get('queue_mode_changed')}",
        f"* Watchlist added: {', '.join(summary.get('watchlist_added', [])) or 'none'}",
        f"* Watchlist removed: {', '.join(summary.get('watchlist_removed', [])) or 'none'}",
        f"* Limited evidence changes: +{len(summary.get('limited_evidence_added', []))} / -{len(summary.get('limited_evidence_removed', []))}",
        "",
        "## Current Training Focus",
        "",
    ]
    focus = summary.get("current_training_focus", [])
    if focus:
        for item in focus:
            lines.append(f"* {item.get('anchor_skill')} — {item.get('slot_type')} ({item.get('problem_name')})")
    else:
        lines.append("* none")
    lines.extend(["", "## Caveats", ""])
    lines.extend([f"* {caveat}" for caveat in report["caveats"]])
    return "\n".join(lines)
