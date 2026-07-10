"""Weekly progress reports (Phase 10, premium feature).

Compares the latest analysis run against the previous one via
user_skill_history and produces a safe, evidence-bound summary. One report
per (handle, ISO week); regeneration within the same week replaces it.
The batch job iterates every handle that has analysis runs.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Any

from contestiq_api import product_events
from contestiq_api.cfdata import store, weakness

STATUS_ORDER = {  # higher = healthier; used only to describe direction of change
    "likely_weakness": 0,
    "possible_weakness": 1,
    "underexposed": 2,
    "insufficient_evidence": 2,
    "calibration_needed": 2,
    "historical_weakness_recent_improvement": 3,
    "maintenance_needed": 4,
    "likely_strength": 5,
    "strength": 6,
}


def _week_start(today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    return (today - dt.timedelta(days=today.weekday())).isoformat()


def _runs_for(handle: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT run_id, created_at, episode_count, global_rating FROM analysis_runs"
            " WHERE handle = ? ORDER BY created_at DESC LIMIT 2",
            (store.canonical_handle(handle),),
        ).fetchall()
    return [dict(row) for row in rows]


def generate_weekly_report(
    handle: str,
    week_start: str | None = None,
    *,
    event_subject: str | None = None,
) -> dict[str, Any]:
    canonical = store.canonical_handle(handle)
    week = week_start or _week_start()
    runs = _runs_for(canonical)
    if not runs:
        return {"handle": canonical, "status": "no_analysis_runs",
                "note": "Run a weakness analysis first."}

    latest = weakness.get_run(runs[0]["run_id"])
    assert latest is not None
    previous = weakness.get_run(runs[1]["run_id"]) if len(runs) > 1 else None

    improvements, regressions, unchanged_weak = [], [], []
    if previous is not None:
        prev_by_skill = {s["skill_id"]: s for s in previous["skills"]}
        for skill in latest["skills"]:
            prev = prev_by_skill.get(skill["skill_id"])
            if prev is None:
                continue
            now_rank = STATUS_ORDER.get(skill["status"], 2)
            prev_rank = STATUS_ORDER.get(prev["status"], 2)
            entry = {
                "skill_id": skill["skill_id"],
                "from_status": prev["status"],
                "to_status": skill["status"],
                "severity_change": skill["severity"] - prev["severity"],
            }
            if now_rank > prev_rank:
                improvements.append(entry)
            elif now_rank < prev_rank:
                regressions.append(entry)
            elif skill["status"] in ("likely_weakness", "possible_weakness"):
                unchanged_weak.append(entry)

    weak = [s for s in latest["skills"] if s["status"] in ("likely_weakness", "possible_weakness")]
    weak.sort(key=lambda s: (-s["severity"], s["skill_id"]))
    content = {
        "handle": canonical,
        "week_start": week,
        "status": "available" if previous is not None else "first_report_baseline",
        "latest_analysis_run_id": latest["run_id"],
        "previous_analysis_run_id": previous["run_id"] if previous else None,
        "episode_count": latest["episode_count"],
        "episode_count_change": (latest["episode_count"] - previous["episode_count"]) if previous else None,
        "improvements": improvements,
        "regressions": regressions,
        "still_needs_work": unchanged_weak,
        "next_week_focus": [
            {"skill_id": s["skill_id"], "status": s["status"], "severity": s["severity"]} for s in weak[:3]
        ],
        "safe_interpretation": (
            "Changes describe evidence from public Codeforces history between two analysis "
            "snapshots. They are friction signals, not claims about mastery or effort."
        ),
    }

    report_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO weekly_reports (report_id, handle, week_start, content, created_at) VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(handle, week_start) DO UPDATE SET content = excluded.content, created_at = excluded.created_at",
            (report_id, canonical, week, json.dumps(content, ensure_ascii=False), store._now()),
        )
    product_events.track(
        "weekly_report_generated",
        event_subject or f"handle:{canonical}",
        {"week_start": week},
    )
    return content


def get_weekly_report(handle: str, week_start: str | None = None) -> dict[str, Any] | None:
    canonical = store.canonical_handle(handle)
    week = week_start or _week_start()
    with store.connect() as conn:
        row = conn.execute(
            "SELECT content FROM weekly_reports WHERE handle = ? AND week_start = ?", (canonical, week)
        ).fetchone()
    return json.loads(row["content"]) if row else None


def generate_all_weekly_reports() -> dict[str, Any]:
    """Batch job: one report per handle with analysis runs. Idempotent per week."""
    with store.connect() as conn:
        handles = [row["handle"] for row in conn.execute(
            "SELECT DISTINCT handle FROM analysis_runs ORDER BY handle").fetchall()]
    generated = 0
    for handle in handles:
        result = generate_weekly_report(handle)
        if result.get("status") != "no_analysis_runs":
            generated += 1
    return {"week_start": _week_start(), "handles_seen": len(handles), "reports_generated": generated}
