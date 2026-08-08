"""Poll Codeforces contest.list and enqueue finished contests."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from contestiq_api.cfdata import store
from contestiq_core.codeforces.client import fetch_contest_list

logger = logging.getLogger(__name__)


def _now() -> str:
    return store._now()


def _upsert_contest(raw: dict[str, Any], *, is_gym: bool = False) -> dict[str, Any]:
    contest_id = int(raw["id"])
    phase = str(raw.get("phase") or "UNKNOWN")
    start = raw.get("startTimeSeconds")
    duration = raw.get("durationSeconds")
    now = _now()
    finished_at = None
    # Codeforces marks finished contests as phase=FINISHED.
    if phase == "FINISHED":
        finished_at = now
        if start is not None and duration is not None:
            # Prefer deterministic finish time from CF metadata.
            finished_at = time.strftime(
                "%Y-%m-%dT%H:%M:%S+00:00",
                time.gmtime(int(start) + int(duration)),
            )

    with store.connect() as conn:
        existing = conn.execute(
            "SELECT phase, pipeline_status, finished_at FROM cf_contests WHERE contest_id = ?",
            (contest_id,),
        ).fetchone()
        prev_phase = existing["phase"] if existing else None
        conn.execute(
            """
            INSERT INTO cf_contests (
                contest_id, name, type, phase, frozen, duration_seconds, start_time,
                relative_time_seconds, prepared_by, website_url, description, difficulty,
                kind, icpc_region, country, city, season, is_gym, finished_at,
                pipeline_status, discovered_at, updated_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'idle', ?, ?, ?)
            ON CONFLICT(contest_id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                phase = excluded.phase,
                frozen = excluded.frozen,
                duration_seconds = excluded.duration_seconds,
                start_time = excluded.start_time,
                relative_time_seconds = excluded.relative_time_seconds,
                prepared_by = excluded.prepared_by,
                website_url = excluded.website_url,
                description = excluded.description,
                difficulty = excluded.difficulty,
                kind = excluded.kind,
                icpc_region = excluded.icpc_region,
                country = excluded.country,
                city = excluded.city,
                season = excluded.season,
                is_gym = excluded.is_gym,
                finished_at = COALESCE(cf_contests.finished_at, excluded.finished_at),
                updated_at = excluded.updated_at,
                raw_json = excluded.raw_json
            """,
            (
                contest_id,
                str(raw.get("name") or f"Contest {contest_id}"),
                raw.get("type"),
                phase,
                1 if raw.get("frozen") else 0,
                duration,
                start,
                raw.get("relativeTimeSeconds"),
                raw.get("preparedBy"),
                raw.get("websiteUrl"),
                raw.get("description"),
                raw.get("difficulty"),
                raw.get("kind"),
                raw.get("icpcRegion"),
                raw.get("country"),
                raw.get("city"),
                raw.get("season"),
                1 if is_gym else 0,
                finished_at,
                now,
                now,
                json.dumps(raw, ensure_ascii=False),
            ),
        )

    newly_finished = phase == "FINISHED" and prev_phase not in {None, "FINISHED"}
    # Also catch first-time discovery of already-finished contests that still need pipeline.
    first_seen_finished = phase == "FINISHED" and existing is None
    return {
        "contest_id": contest_id,
        "phase": phase,
        "newly_finished": newly_finished or False,
        "first_seen_finished": first_seen_finished,
        "prev_phase": prev_phase,
    }


def _record_event(contest_id: int, event_type: str, detail: dict[str, Any] | None = None) -> None:
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO contest_pipeline_events (event_id, contest_id, event_type, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                contest_id,
                event_type,
                json.dumps(detail or {}, ensure_ascii=False),
                _now(),
            ),
        )


def enqueue_contest_pipeline(contest_id: int, *, reason: str) -> bool:
    """Mark contest for pipeline processing if not already running/done."""
    with store.connect() as conn:
        row = conn.execute(
            "SELECT pipeline_status FROM cf_contests WHERE contest_id = ?",
            (contest_id,),
        ).fetchone()
        if row is None:
            return False
        status = row["pipeline_status"]
        if status in {"queued", "running", "complete"}:
            return False
        conn.execute(
            """
            UPDATE cf_contests
            SET pipeline_status = 'queued', pipeline_error = NULL, updated_at = ?
            WHERE contest_id = ?
            """,
            (_now(), contest_id),
        )
    _record_event(contest_id, "pipeline_queued", {"reason": reason})
    logger.info(json.dumps({"event": "contest_pipeline_queued", "contest_id": contest_id, "reason": reason}))
    return True


def poll_contests(*, gym: bool = False, max_age_seconds: int = 120) -> dict[str, Any]:
    """Fetch contest.list, upsert metadata, enqueue pipelines for newly finished contests."""
    contests = fetch_contest_list(gym=gym, use_cache=True, max_age_seconds=max_age_seconds) or []
    upserted = 0
    newly_finished: list[int] = []
    enqueued: list[int] = []

    # Process newest first (CF returns newest first typically).
    for raw in contests[:800]:
        try:
            info = _upsert_contest(raw, is_gym=gym)
        except Exception:
            logger.exception("contest upsert failed id=%s", raw.get("id"))
            continue
        upserted += 1
        if info["newly_finished"] or info["first_seen_finished"]:
            newly_finished.append(info["contest_id"])
            # Only auto-enqueue recent finished contests (last ~14 days) on first discovery
            # to avoid a thundering herd on cold start.
            start = raw.get("startTimeSeconds")
            duration = raw.get("durationSeconds") or 0
            end_ts = int(start) + int(duration) if start is not None else None
            recent = end_ts is None or (time.time() - end_ts) < 14 * 86400
            if info["newly_finished"] or (info["first_seen_finished"] and recent):
                if enqueue_contest_pipeline(info["contest_id"], reason="watcher_finished"):
                    enqueued.append(info["contest_id"])

    # Catch finished contests stuck in idle (e.g. missed transition).
    with store.connect() as conn:
        stuck = conn.execute(
            """
            SELECT contest_id, start_time, duration_seconds FROM cf_contests
            WHERE phase = 'FINISHED'
              AND pipeline_status = 'idle'
              AND is_gym = 0
              AND start_time IS NOT NULL
              AND (start_time + COALESCE(duration_seconds, 0)) > ?
            ORDER BY start_time DESC
            LIMIT 20
            """,
            (int(time.time()) - 14 * 86400,),
        ).fetchall()
    for row in stuck:
        if enqueue_contest_pipeline(int(row["contest_id"]), reason="watcher_backfill"):
            enqueued.append(int(row["contest_id"]))

    return {
        "upserted": upserted,
        "newly_finished": newly_finished[:50],
        "enqueued": enqueued,
        "fetched": len(contests),
    }
