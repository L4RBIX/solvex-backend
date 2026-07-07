"""Append-only, server-sequenced, hash-chained session event ledger.

Rows are inserted, never updated. Each event's hash covers the previous
event's hash plus its own canonical content, so any tampering breaks
verify_chain(). Sequencing happens server-side under a single connection.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from typing import Any

from contestiq_api.cfdata import store

_APPEND_RETRIES = 8

EVENT_TYPES = {
    "session_started",
    "problem_revealed",
    "code_snapshot",
    "run_attempt_created",
    "judge0_submission_created",
    "judge0_result_received",
    "hidden_tests_started",
    "hidden_tests_completed",
    "badge_decision_created",
    "badge_issued",
    "badge_not_issued",
    "manual_review_requested",
}


def _canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _event_hash(prev_hash: str | None, record: dict[str, Any]) -> str:
    return hashlib.sha256(((prev_hash or "genesis") + _canonical(record)).encode("utf-8")).hexdigest()


def append(
    session_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    actor_type: str = "server",
    source_trust: str = "server",
    redaction_level: str = "none",
    occurred_at: str | None = None,
    trace_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    assert event_type in EVENT_TYPES, f"unknown event type {event_type}"
    event_id = str(uuid.uuid4())
    received_at = store._now()
    payload = payload or {}
    # seq is part of the hashed record, so it must be known before insert;
    # concurrent appends race on UNIQUE(session_id, seq) and retry.
    last_error: Exception | None = None
    for _ in range(_APPEND_RETRIES):
        try:
            with store.connect() as conn:
                row = conn.execute(
                    "SELECT seq, event_hash FROM session_events WHERE session_id = ? ORDER BY seq DESC LIMIT 1",
                    (session_id,),
                ).fetchone()
                seq = (row["seq"] + 1) if row else 1
                prev_hash = row["event_hash"] if row else None
                record = {
                    "event_id": event_id,
                    "session_id": session_id,
                    "seq": seq,
                    "event_type": event_type,
                    "actor_type": actor_type,
                    "source_trust": source_trust,
                    "occurred_at": occurred_at,
                    "received_at": received_at,
                    "payload": payload,
                    "payload_redaction_level": redaction_level,
                }
                event_hash = _event_hash(prev_hash, record)
                conn.execute(
                    "INSERT INTO session_events (event_id, session_id, seq, event_type, actor_type, source_trust,"
                    " occurred_at, received_at, payload, payload_redaction_level, prev_event_hash, event_hash,"
                    " trace_id, request_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        event_id, session_id, seq, event_type, actor_type, source_trust,
                        occurred_at, received_at, json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        redaction_level, prev_hash, event_hash, trace_id, request_id,
                    ),
                )
            return {**record, "prev_event_hash": prev_hash, "event_hash": event_hash}
        except sqlite3.IntegrityError as exc:
            last_error = exc  # another writer took this seq; recompute and retry
    raise RuntimeError(f"Could not append session event after {_APPEND_RETRIES} retries") from last_error


def list_events(session_id: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM session_events WHERE session_id = ? ORDER BY seq", (session_id,)
        ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event["payload"] = json.loads(event["payload"])
        events.append(event)
    return events


def verify_chain(session_id: str) -> bool:
    prev_hash: str | None = None
    for event in list_events(session_id):
        record = {
            "event_id": event["event_id"],
            "session_id": event["session_id"],
            "seq": event["seq"],
            "event_type": event["event_type"],
            "actor_type": event["actor_type"],
            "source_trust": event["source_trust"],
            "occurred_at": event["occurred_at"],
            "received_at": event["received_at"],
            "payload": event["payload"],
            "payload_redaction_level": event["payload_redaction_level"],
        }
        if event["prev_event_hash"] != prev_hash:
            return False
        if _event_hash(prev_hash, record) != event["event_hash"]:
            return False
        prev_hash = event["event_hash"]
    return True
