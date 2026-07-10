"""Onboarding/retention product events (Phase 10).

track() records behavioral milestones for launch metrics. Events whose type
starts with `first_` are recorded at most once per subject (enforced by a
partial unique index). Payloads carry no code, tokens, or hidden material.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from contestiq_api.cfdata import store

EVENT_TYPES = {
    "first_analysis_completed",
    "first_queue_generated",
    "daily_queue_generated",
    "plan_started",
    "feedback_submitted",
    "weekly_report_generated",
    "verification_attempted",
    "premium_conversion",
    # Phase G4 friend duels — only completed/won count for XP (no farm from abandoned creates).
    "duel_created",
    "duel_joined",
    "duel_started",
    "duel_completed",
    "duel_won",
    # Phase G4.1 live duel room — telemetry only, zero XP (hints must never earn XP).
    "duel_ready",
    "duel_arena_opened",
    "duel_hint_used",
}


def subject_for_handle_action(handle: str, user: dict[str, Any] | None) -> str:
    """Attribute a handle-scoped action without treating the handle as auth.

    Only a bearer-authenticated verified owner earns account activity. Public
    visitors still produce legacy/public telemetry, which is excluded from
    the owner's post-verification private history by ``events_for_account``.
    """
    from contestiq_api import handles

    canonical = store.canonical_handle(handle)
    if user and user.get("user_id") and handles.owner_user_id_for_handle(canonical) == user["user_id"]:
        return f"user:{user['user_id']}"
    return f"handle:{canonical}"


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


def events_for_subjects(subjects: list[str]) -> list[dict[str, Any]]:
    """Union of events for several subject aliases (e.g. `handle:x` and `user:y`
    both belonging to the same learner), ordered chronologically.

    Used by gamification (Phase G1) to replay a learner's full meaningful-action
    history without introducing any new tables — product_events stays the
    single source of truth.
    """
    if not subjects:
        return []
    placeholders = ", ".join("?" for _ in subjects)
    with store.connect() as conn:
        rows = conn.execute(
            f"SELECT event_type, subject, properties, created_at FROM product_events"
            f" WHERE subject IN ({placeholders}) ORDER BY created_at",
            subjects,
        ).fetchall()
    return [{**dict(row), "properties": json.loads(row["properties"])} for row in rows]


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def events_for_account(user_id: str) -> list[dict[str, Any]]:
    """Return private account activity plus a bounded legacy-handle history.

    A verified handle permits safe reconciliation of telemetry that predates
    verification. It does *not* make future public handle events trustworthy:
    anyone may still run public analysis for that handle. Account-owned
    actions after verification are recorded under ``user:<id>`` instead.
    """
    from contestiq_api import handles

    user_subject = f"user:{user_id}"
    binding = handles.verified_binding_for_user(user_id)
    subjects = [user_subject]
    handle_subject: str | None = None
    cutoff: datetime | None = None
    if binding:
        handle_subject = f"handle:{binding['handle']}"
        subjects.append(handle_subject)
        cutoff = _parse_time(binding["verified_at"])

    events = events_for_subjects(subjects)
    bounded = [
        event
        for event in events
        if event.get("subject") != handle_subject
        or cutoff is None
        or _parse_time(event["created_at"]) <= cutoff
    ]

    # first_* uniqueness was historically enforced per subject. Once two
    # proven aliases are reconciled, keep only the earliest milestone so a
    # handle→account transition cannot award the same onboarding XP twice.
    result: list[dict[str, Any]] = []
    seen_first: set[str] = set()
    for event in bounded:
        event_type = str(event.get("event_type") or "")
        if event_type.startswith("first_"):
            if event_type in seen_first:
                continue
            seen_first.add(event_type)
        result.append(event)
    return result
