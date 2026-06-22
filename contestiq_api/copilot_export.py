"""Admin utility: export consented Copilot interactions as JSONL for dataset use.

Usage (from project root):
    python -m contestiq_api.copilot_export --output dataset.jsonl

Only exports rows where consent_for_training = TRUE.
Anonymizes user_id, removing personal identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from typing import Any

import httpx

from contestiq_api.settings import get_settings

logger = logging.getLogger(__name__)


def _anonymize_user_id(user_id: str | None) -> str | None:
    """One-way hash so the export is linkable within a session but not back to the user."""
    if not user_id:
        return None
    return "anon_" + hashlib.sha256(user_id.encode()).hexdigest()[:16]


def _anonymize_session_id(session_id: str) -> str:
    return "sess_" + hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _fetch_all(url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    limit = 1000
    while True:
        resp = httpx.get(url, headers=headers, params={"offset": offset, "limit": limit})
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return rows


def export_consented_copilot_dataset(output_path: str = "copilot_dataset.jsonl") -> int:
    """
    Export all consented Copilot sessions to JSONL.

    Returns the number of session records written.
    Raises RuntimeError if Supabase is not configured.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set to export data.")

    base = settings.supabase_url.rstrip("/") + "/rest/v1"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }

    # Fetch all sessions that have at least one consented message
    sessions_url = f"{base}/copilot_sessions"
    all_sessions = _fetch_all(sessions_url, headers)

    # Fetch all consented messages grouped by session_id
    msgs_url = f"{base}/copilot_messages?consent_for_training=eq.true&select=*&order=created_at.asc"
    all_messages = _fetch_all(msgs_url, {**headers, "Prefer": "count=none"})

    msgs_by_session: dict[str, list[dict]] = {}
    for msg in all_messages:
        sid = msg.get("session_id", "")
        msgs_by_session.setdefault(sid, []).append(msg)

    # Fetch all consented snapshots (most recent per session)
    snaps_url = f"{base}/copilot_context_snapshots?consent_for_training=eq.true&select=*&order=created_at.desc"
    all_snaps = _fetch_all(snaps_url, {**headers, "Prefer": "count=none"})
    snap_by_session: dict[str, dict] = {}
    for snap in all_snaps:
        sid = snap.get("session_id", "")
        if sid not in snap_by_session:  # keep most recent (already ordered desc)
            snap_by_session[sid] = snap

    written = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for session in all_sessions:
            sid = session.get("id", "")
            messages = msgs_by_session.get(sid, [])
            if not messages:
                continue  # skip sessions with no consented messages

            snap = snap_by_session.get(sid, {})
            anon_sid = _anonymize_session_id(sid)

            record: dict[str, Any] = {
                "session_id": anon_sid,
                "problem": {
                    "contest_id": session.get("contest_id"),
                    "index": session.get("problem_index"),
                    "title": None,  # not stored in sessions table
                    "tags": [],
                    "rating": None,
                },
                "language": session.get("language"),
                "messages": [
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                    if m["role"] in ("user", "assistant")
                ],
                "context": {
                    "source_code": snap.get("source_code"),
                    "last_status": snap.get("last_status"),
                    "last_compile_output": snap.get("last_compile_output"),
                    "last_stderr": snap.get("last_stderr"),
                    "last_stdout": snap.get("last_stdout"),
                    "recent_events": snap.get("recent_events") or [],
                },
                "metadata": {
                    "mode": messages[-1].get("mode") if messages else None,
                    "help_level": messages[-1].get("help_level") if messages else None,
                },
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    logger.info("exported %d sessions to %s", written, output_path)
    return written


def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Export consented Copilot dataset to JSONL")
    parser.add_argument("--output", default="copilot_dataset.jsonl", help="Output file path")
    args = parser.parse_args()

    try:
        count = export_consented_copilot_dataset(args.output)
        print(f"Exported {count} sessions to {args.output}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main()
