from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contestiq_api.storage import list_snapshots, safe_handle

WORKSPACE_FILE = Path("api_cache") / "workspace" / "saved_handles.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_workspace() -> dict[str, dict[str, Any]]:
    if not WORKSPACE_FILE.exists():
        return {}
    try:
        data = json.loads(WORKSPACE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        return {str(key): value for key, value in data.items() if isinstance(value, dict)}
    return {}


def _write_workspace(records: dict[str, dict[str, Any]]) -> None:
    WORKSPACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _record_key(handle: str) -> str:
    return safe_handle(handle)


def _base_record(handle: str, notes: str | None = None) -> dict[str, Any]:
    timestamp = _now()
    record: dict[str, Any] = {
        "handle": handle,
        "created_at": timestamp,
        "updated_at": timestamp,
        "latest_analysis_id": None,
        "latest_analysis_created_at": None,
        "latest_queue_mode": None,
        "latest_model_version": None,
        "latest_share_id": None,
    }
    if notes is not None:
        record["notes"] = notes
    return record


def _apply_analysis(record: dict[str, Any], analysis: dict[str, Any]) -> None:
    record["latest_analysis_id"] = analysis.get("analysis_id")
    record["latest_analysis_created_at"] = analysis.get("created_at")
    record["latest_queue_mode"] = analysis.get("daily_queue", {}).get("queue_mode")
    record["latest_model_version"] = analysis.get("model_version")


def save_workspace_handle(handle: str, notes: str | None = None) -> dict[str, Any]:
    records = _read_workspace()
    key = _record_key(handle)
    record = records.get(key, _base_record(handle, notes=notes))
    record["handle"] = handle
    record["updated_at"] = _now()
    if notes is not None:
        record["notes"] = notes
    records[key] = record
    _write_workspace(records)
    return dict(record)


def upsert_workspace_analysis(handle: str, analysis: dict[str, Any]) -> dict[str, Any]:
    records = _read_workspace()
    key = _record_key(handle)
    record = records.get(key, _base_record(handle))
    record["handle"] = handle
    record["updated_at"] = _now()
    _apply_analysis(record, analysis)
    records[key] = record
    _write_workspace(records)
    return dict(record)


def update_workspace_share(handle: str, share_id: str, analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    records = _read_workspace()
    key = _record_key(handle)
    record = records.get(key, _base_record(handle))
    record["handle"] = handle
    record["updated_at"] = _now()
    record["latest_share_id"] = share_id
    if analysis is not None:
        _apply_analysis(record, analysis)
    records[key] = record
    _write_workspace(records)
    return dict(record)


def list_workspace_handles() -> dict[str, Any]:
    items = sorted(
        _read_workspace().values(),
        key=lambda row: row.get("updated_at", ""),
        reverse=True,
    )
    return {
        "status": "available",
        "count": len(items),
        "items": items,
    }


def delete_workspace_handle(handle: str) -> dict[str, Any]:
    records = _read_workspace()
    key = _record_key(handle)
    records.pop(key, None)
    _write_workspace(records)
    return {
        "status": "deleted",
        "handle": handle,
    }


def workspace_dashboard() -> dict[str, Any]:
    items = []
    for record in list_workspace_handles()["items"]:
        snapshots = list_snapshots(record["handle"])
        items.append(
            {
                "handle": record["handle"],
                "latest_queue_mode": record.get("latest_queue_mode"),
                "latest_analysis_id": record.get("latest_analysis_id"),
                "latest_share_id": record.get("latest_share_id"),
                "has_weekly_report": len(snapshots) >= 2,
                "has_history": bool(snapshots),
            }
        )
    return {
        "status": "available",
        "handles_count": len(items),
        "items": items,
        "safe_interpretation": "Workspace data is local and based on saved analyses. It is not verification.",
    }
