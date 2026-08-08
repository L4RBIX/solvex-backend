"""Public contest APIs for the zero-day pipeline."""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Query

from contestiq_api.cfdata import store
from contestiq_api.contests.lifecycle import readiness_payload, refresh_problem_lifecycle
from contestiq_api.contests.practice import contest_practice
from contestiq_api.contests.similar import list_similar
from contestiq_api.errors import APIError

router = APIRouter(prefix="/api/v1/contests", tags=["contests"])


def _contest_dict(row: Any) -> dict[str, Any]:
    start = row["start_time"]
    duration = row["duration_seconds"]
    end = int(start) + int(duration) if start is not None and duration is not None else None
    return {
        "contest_id": row["contest_id"],
        "name": row["name"],
        "type": row["type"],
        "phase": row["phase"],
        "duration_seconds": duration,
        "start_time": start,
        "end_time": end,
        "is_gym": bool(row["is_gym"]),
        "finished_at": row["finished_at"],
        "pipeline_status": row["pipeline_status"],
        "pipeline_started_at": row["pipeline_started_at"],
        "pipeline_completed_at": row["pipeline_completed_at"],
        "pipeline_error": row["pipeline_error"],
        "website_url": row["website_url"] or f"https://codeforces.com/contest/{row['contest_id']}",
        "is_new": bool(
            row["phase"] == "FINISHED"
            and end is not None
            and (time.time() - end) < 48 * 3600
        ),
    }


@router.get("")
def list_contests(
    limit: int = Query(default=40, ge=1, le=100),
    phase: str | None = Query(default=None),
):
    clauses = ["is_gym = 0"]
    params: list[Any] = []
    if phase:
        clauses.append("phase = ?")
        params.append(phase.upper())
    where = " AND ".join(clauses)
    with store.connect() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM cf_contests
            WHERE {where}
            ORDER BY COALESCE(start_time, 0) DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    return {"contests": [_contest_dict(r) for r in rows]}


@router.get("/{contest_id}")
def get_contest(contest_id: int):
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM cf_contests WHERE contest_id = ?",
            (contest_id,),
        ).fetchone()
        if row is None:
            raise APIError("CONTEST_NOT_FOUND", f"Contest {contest_id} not found.", 404)
        problems = conn.execute(
            """
            SELECT problem_key, problem_index, name, rating, tags
            FROM problems WHERE contest_id = ?
            ORDER BY problem_index
            """,
            (contest_id,),
        ).fetchall()

    items = []
    stage_counts: dict[str, int] = {}
    for p in problems:
        life = refresh_problem_lifecycle(p["problem_key"])
        ready = readiness_payload(life)
        stage = ready["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        items.append(
            {
                "problem_id": p["problem_key"],
                "index": p["problem_index"],
                "name": p["name"],
                "rating": p["rating"],
                "tags": json.loads(p["tags"] or "[]"),
                "readiness": ready,
                "lifecycle": life,
                "similar_count": len(list_similar(p["problem_key"], limit=10)),
                "official_url": f"https://codeforces.com/contest/{contest_id}/problem/{p['problem_index']}",
                "arena_href": f"/arena?problem={p['problem_key']}&source=contest&contest={contest_id}",
            }
        )

    contest = _contest_dict(row)
    contest["problems"] = items
    contest["readiness_summary"] = {
        "problem_count": len(items),
        "arena_ready": sum(1 for i in items if i["readiness"]["arena"] == "ready"),
        "submit_ready": sum(1 for i in items if i["readiness"]["submit"] == "ready"),
        "submit_generating": sum(1 for i in items if i["readiness"]["submit"] == "generating"),
        "unsupported": sum(1 for i in items if i["readiness"]["arena"] == "unsupported"),
        "by_stage": stage_counts,
    }
    return contest


@router.get("/{contest_id}/practice")
def get_contest_practice(
    contest_id: int,
    handle: str = Query(min_length=1, max_length=64),
):
    with store.connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM cf_contests WHERE contest_id = ?",
            (contest_id,),
        ).fetchone()
    if exists is None:
        raise APIError("CONTEST_NOT_FOUND", f"Contest {contest_id} not found.", 404)
    return contest_practice(contest_id, handle)


@router.get("/{contest_id}/events")
def contest_events(contest_id: int, limit: int = Query(default=30, ge=1, le=100)):
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT event_id, event_type, detail, created_at
            FROM contest_pipeline_events
            WHERE contest_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (contest_id, limit),
        ).fetchall()
    return {
        "contest_id": contest_id,
        "events": [
            {
                "event_id": r["event_id"],
                "event_type": r["event_type"],
                "detail": json.loads(r["detail"] or "{}"),
                "created_at": r["created_at"],
            }
            for r in rows
        ],
    }
