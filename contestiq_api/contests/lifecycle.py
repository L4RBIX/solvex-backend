"""Per-problem zero-day readiness stages (fail-closed)."""

from __future__ import annotations

import json
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.practice_packs.oracles import ORACLE_REGISTRY

LIFECYCLE_STAGES = (
    "DISCOVERED",
    "CATALOG_IMPORTED",
    "STATEMENT_IMPORTED",
    "ARENA_READY",
    "LOCAL_TEST_READY",
    "PACK_GENERATION",
    "SUBMIT_READY",
    "FULLY_INDEXED",
    "UNSUPPORTED",
)

_STAGE_RANK = {name: i for i, name in enumerate(LIFECYCLE_STAGES)}


def _now() -> str:
    return store._now()


def ensure_lifecycle_row(problem_id: str, *, contest_id: int | None = None) -> None:
    now = _now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO problem_lifecycle (problem_id, contest_id, stage, discovered_at, updated_at)
            VALUES (?, ?, 'DISCOVERED', ?, ?)
            ON CONFLICT(problem_id) DO UPDATE SET
                contest_id = COALESCE(excluded.contest_id, problem_lifecycle.contest_id),
                updated_at = excluded.updated_at
            """,
            (problem_id, contest_id, now, now),
        )


def refresh_problem_lifecycle(problem_id: str) -> dict[str, Any]:
    """Recompute stage from live catalog/statement/pack/skill/similar state."""
    ensure_lifecycle_row(problem_id)
    now = _now()
    with store.connect() as conn:
        problem = conn.execute(
            "SELECT problem_key, contest_id, rating, tags FROM problems WHERE problem_key = ?",
            (problem_id,),
        ).fetchone()
        statement = conn.execute(
            """
            SELECT display_ready, solve_ready, is_interactive, io_mode, availability_status,
                   length(COALESCE(samples, '[]')) AS examples_len
            FROM problem_statements WHERE problem_id = ?
            """,
            (problem_id,),
        ).fetchone()
        pack = conn.execute(
            """
            SELECT pack_id, judge_tests, statement_summary, input_format, output_format, constraints_text
            FROM duel_problem_packs
            WHERE problem_id = ? AND active = 1
            ORDER BY version DESC LIMIT 1
            """,
            (problem_id,),
        ).fetchone()
        pack_job = conn.execute(
            "SELECT status FROM practice_pack_jobs WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
        skill = conn.execute(
            "SELECT 1 FROM problem_skill_map WHERE problem_id = ? LIMIT 1",
            (problem_id,),
        ).fetchone()
        similar = conn.execute(
            "SELECT COUNT(*) AS c FROM problem_similar WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
        existing = conn.execute(
            "SELECT * FROM problem_lifecycle WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()

    stamps = {
        "discovered_at": (existing["discovered_at"] if existing else None) or now,
        "catalog_imported_at": existing["catalog_imported_at"] if existing else None,
        "statement_imported_at": existing["statement_imported_at"] if existing else None,
        "arena_ready_at": existing["arena_ready_at"] if existing else None,
        "local_test_ready_at": existing["local_test_ready_at"] if existing else None,
        "pack_generation_at": existing["pack_generation_at"] if existing else None,
        "submit_ready_at": existing["submit_ready_at"] if existing else None,
        "fully_indexed_at": existing["fully_indexed_at"] if existing else None,
    }

    unsupported_reason = None
    stage = "DISCOVERED"
    support_class = None

    if problem is not None:
        stage = "CATALOG_IMPORTED"
        stamps["catalog_imported_at"] = stamps["catalog_imported_at"] or now
        contest_id = problem["contest_id"]
    else:
        contest_id = existing["contest_id"] if existing else None

    if statement is not None:
        if int(statement["is_interactive"] or 0):
            stage = "UNSUPPORTED"
            unsupported_reason = "interactive"
            support_class = "UNSUPPORTED"
        elif (statement["io_mode"] or "") == "file":
            stage = "UNSUPPORTED"
            unsupported_reason = "file_io"
            support_class = "UNSUPPORTED"
        elif (statement["availability_status"] or "") == "asset_required":
            stage = "UNSUPPORTED"
            unsupported_reason = "asset_required"
            support_class = "UNSUPPORTED"
        elif int(statement["display_ready"] or 0):
            stage = "STATEMENT_IMPORTED"
            stamps["statement_imported_at"] = stamps["statement_imported_at"] or now
            stage = "ARENA_READY"
            stamps["arena_ready_at"] = stamps["arena_ready_at"] or now
            # Samples present → local Run against statement samples is meaningful.
            if int(statement["examples_len"] or 0) > 2:
                stage = "LOCAL_TEST_READY"
                stamps["local_test_ready_at"] = stamps["local_test_ready_at"] or now

    submit_ready = False
    if pack is not None and stage != "UNSUPPORTED":
        from contestiq_api import duels

        tests = duels._normalize_judge_tests(pack["judge_tests"])
        if tests and duels._pack_has_complete_content(dict(pack)):
            submit_ready = True
            stage = "SUBMIT_READY"
            stamps["submit_ready_at"] = stamps["submit_ready_at"] or now

    if (
        not submit_ready
        and stage not in {"UNSUPPORTED", "DISCOVERED"}
        and (
            problem_id in ORACLE_REGISTRY
            or (pack_job is not None and pack_job["status"] in {"pending", "processing", "leased"})
        )
    ):
        # Prefer pack-generation signal once arena/local-test is ready.
        if _STAGE_RANK.get(stage, 0) >= _STAGE_RANK["LOCAL_TEST_READY"]:
            stage = "PACK_GENERATION"
            stamps["pack_generation_at"] = stamps["pack_generation_at"] or now
            support_class = support_class or "AUTO_POSSIBLE"

    if (
        stage in {"SUBMIT_READY", "LOCAL_TEST_READY", "ARENA_READY", "PACK_GENERATION"}
        and skill is not None
        and int((similar["c"] if similar is not None else 0) or 0) >= 3
    ):
        if stage == "SUBMIT_READY" or stage == "PACK_GENERATION":
            # Fully indexed requires submit-ready OR explicit unsupported skip with arena.
            if stage == "SUBMIT_READY":
                stage = "FULLY_INDEXED"
                stamps["fully_indexed_at"] = stamps["fully_indexed_at"] or now

    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO problem_lifecycle (
                problem_id, contest_id, stage, support_class,
                discovered_at, catalog_imported_at, statement_imported_at,
                arena_ready_at, local_test_ready_at, pack_generation_at,
                submit_ready_at, fully_indexed_at, unsupported_reason, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(problem_id) DO UPDATE SET
                contest_id = excluded.contest_id,
                stage = excluded.stage,
                support_class = excluded.support_class,
                discovered_at = COALESCE(problem_lifecycle.discovered_at, excluded.discovered_at),
                catalog_imported_at = COALESCE(problem_lifecycle.catalog_imported_at, excluded.catalog_imported_at),
                statement_imported_at = COALESCE(problem_lifecycle.statement_imported_at, excluded.statement_imported_at),
                arena_ready_at = COALESCE(problem_lifecycle.arena_ready_at, excluded.arena_ready_at),
                local_test_ready_at = COALESCE(problem_lifecycle.local_test_ready_at, excluded.local_test_ready_at),
                pack_generation_at = COALESCE(problem_lifecycle.pack_generation_at, excluded.pack_generation_at),
                submit_ready_at = COALESCE(problem_lifecycle.submit_ready_at, excluded.submit_ready_at),
                fully_indexed_at = COALESCE(problem_lifecycle.fully_indexed_at, excluded.fully_indexed_at),
                unsupported_reason = excluded.unsupported_reason,
                updated_at = excluded.updated_at
            """,
            (
                problem_id,
                contest_id,
                stage,
                support_class,
                stamps["discovered_at"],
                stamps["catalog_imported_at"],
                stamps["statement_imported_at"],
                stamps["arena_ready_at"],
                stamps["local_test_ready_at"],
                stamps["pack_generation_at"],
                stamps["submit_ready_at"],
                stamps["fully_indexed_at"],
                unsupported_reason,
                now,
            ),
        )

    return {
        "problem_id": problem_id,
        "contest_id": contest_id,
        "stage": stage,
        "support_class": support_class,
        "unsupported_reason": unsupported_reason,
        "timestamps": stamps,
        "submit_capable": submit_ready,
        "arena_capable": stage
        in {
            "ARENA_READY",
            "LOCAL_TEST_READY",
            "PACK_GENERATION",
            "SUBMIT_READY",
            "FULLY_INDEXED",
        },
    }


def refresh_contest_lifecycles(contest_id: int) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT problem_key FROM problems WHERE contest_id = ? ORDER BY problem_index",
            (contest_id,),
        ).fetchall()
    return [refresh_problem_lifecycle(r["problem_key"]) for r in rows]


def readiness_payload(lifecycle: dict[str, Any]) -> dict[str, Any]:
    stage = lifecycle.get("stage") or "DISCOVERED"
    unsupported = stage == "UNSUPPORTED"
    arena = bool(lifecycle.get("arena_capable"))
    submit = bool(lifecycle.get("submit_capable"))
    statement = stage not in {"DISCOVERED", "CATALOG_IMPORTED"} or arena
    pack_generating = stage == "PACK_GENERATION"
    return {
        "stage": stage,
        "statement": "unsupported"
        if unsupported and lifecycle.get("unsupported_reason") in {"asset_required"}
        else ("ready" if statement and stage != "DISCOVERED" else "pending"),
        "arena": "unsupported" if unsupported else ("ready" if arena else "pending"),
        "local_test": "ready"
        if stage in {"LOCAL_TEST_READY", "PACK_GENERATION", "SUBMIT_READY", "FULLY_INDEXED"}
        else ("unsupported" if unsupported else "pending"),
        "submit": (
            "unsupported"
            if unsupported
            else ("ready" if submit else ("generating" if pack_generating else "pending"))
        ),
        "ai_analysis": "ready"
        if stage in {"FULLY_INDEXED", "SUBMIT_READY", "PACK_GENERATION", "LOCAL_TEST_READY"}
        else "pending",
        "related_practice": "ready" if stage == "FULLY_INDEXED" or submit else "pending",
        "unsupported_reason": lifecycle.get("unsupported_reason"),
        "eta_hint": (
            None
            if submit or unsupported
            else ("5–15 minutes" if pack_generating or arena else "3–10 minutes")
        ),
    }
