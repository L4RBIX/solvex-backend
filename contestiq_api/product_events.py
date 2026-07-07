"""Onboarding/retention product events (Phase 10).

track() records behavioral milestones for launch metrics. Events whose type
starts with `first_` are recorded at most once per subject (enforced by a
partial unique index). Payloads carry no code, tokens, or hidden material.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from contestiq_api.cfdata import store

EVENT_TYPES = {
    "first_analysis_completed",
    "first_queue_generated",
    "plan_started",
    "feedback_submitted",
    "weekly_report_generated",
    "verification_attempted",
    "premium_conversion",
}


def track(event_type: str, subject: str, properties: dict[str, Any] | None = None) -> bool:
    """Record an event. Returns False when a first_* event already exists."""
    assert event_type in EVENT_TYPES, f"unknown product event {event_type}"
    try:
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO product_events (event_id, event_type, subject, properties, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), event_type, subject,
                 json.dumps(properties or {}, ensure_ascii=False), store._now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False  # first_* event already recorded for this subject


def count(event_type: str) -> int:
    with store.connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM product_events WHERE event_type = ?", (event_type,)
        ).fetchone()[0]


def events_for(subject: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT event_type, properties, created_at FROM product_events WHERE subject = ? ORDER BY created_at",
            (subject,),
        ).fetchall()
    return [{**dict(row), "properties": json.loads(row["properties"])} for row in rows]
