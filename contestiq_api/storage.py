from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


API_CACHE_DIR = Path("api_cache") / "analyses"
SNAPSHOT_DIR = Path("api_cache") / "snapshots"
FEEDBACK_DIR = Path("api_cache") / "feedback"
SHARE_DIR = Path("api_cache") / "shares"


def safe_handle(handle: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", handle).strip("_").lower()


def analysis_path(handle: str) -> Path:
    API_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return API_CACHE_DIR / f"{safe_handle(handle)}.json"


def save_analysis(handle: str, analysis: dict[str, Any]) -> None:
    path = analysis_path(handle)
    path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")


def load_analysis(handle: str) -> dict[str, Any] | None:
    path = analysis_path(handle)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_path(handle: str, analysis_id: str) -> Path:
    path = SNAPSHOT_DIR / safe_handle(handle)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{analysis_id}.json"


def save_snapshot(handle: str, analysis: dict[str, Any]) -> None:
    snapshot_path(handle, analysis["analysis_id"]).write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_snapshots(handle: str) -> list[dict[str, Any]]:
    path = SNAPSHOT_DIR / safe_handle(handle)
    if not path.exists():
        return []
    snapshots = []
    for file_path in path.glob("*.json"):
        try:
            snapshots.append(json.loads(file_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return sorted(snapshots, key=lambda row: row.get("created_at", ""))


def append_jsonl(name: str, record: dict[str, Any]) -> None:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    path = FEEDBACK_DIR / name
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def share_path(share_id: str) -> Path:
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    return SHARE_DIR / f"{share_id}.json"


def save_share(share_id: str, record: dict[str, Any]) -> None:
    share_path(share_id).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def load_share(share_id: str) -> dict[str, Any] | None:
    path = share_path(share_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
