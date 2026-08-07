"""Invariant: recommendation emitters never advertise Arena for non-display-ready IDs."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api.arena_eligibility import is_arena_solvable, select_arena_recommendations
from contestiq_api.cfdata import store


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def _seed_catalog(*problems: dict) -> None:
    store.save_problemset_snapshot({"problems": list(problems), "problemStatistics": []})


def _seed_statement(problem_id: str, **overrides) -> None:
    now = "2026-08-02T00:00:00+00:00"
    payload = {
        "problem_id": problem_id,
        "batch_id": "test-batch",
        "content_hash": f"hash-{problem_id}",
        "title": problem_id,
        "statement": "A verified statement body.",
        "input_format": "Input",
        "output_format": "Output",
        "interaction_format": None,
        "notes": None,
        "samples": json.dumps([{"input": "1\n", "output": "1\n"}]),
        "time_limit_seconds": 1.0,
        "memory_limit_megabytes": 256.0,
        "difficulty": None,
        "io_mode": "stdio",
        "is_interactive": 0,
        "picture_count": 0,
        "has_missing_diagrams": 0,
        "availability_status": "complete_standard",
        "display_ready": 1,
        "solve_ready": 1,
        "unavailable_reason": None,
        "source_dataset": "test",
        "source_urls": "[]",
        "statement_relation": None,
        "shared_statement_from": None,
        "imported_at": now,
    }
    payload.update(overrides)
    with store.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO problem_import_batches (batch_id, source_name, source_sha256, status, started_at)"
            " VALUES (?, 'test-archive.zip', 'deadbeef', 'completed', ?)",
            (payload["batch_id"], now),
        )
        conn.execute(
            """
            INSERT INTO problem_statements (
                problem_id, batch_id, content_hash, title, statement, input_format, output_format,
                interaction_format, notes, samples, time_limit_seconds, memory_limit_megabytes,
                difficulty, io_mode, is_interactive, picture_count, has_missing_diagrams,
                availability_status, display_ready, solve_ready, unavailable_reason,
                source_dataset, source_urls, statement_relation, shared_statement_from, imported_at
            ) VALUES (
                :problem_id, :batch_id, :content_hash, :title, :statement, :input_format, :output_format,
                :interaction_format, :notes, :samples, :time_limit_seconds, :memory_limit_megabytes,
                :difficulty, :io_mode, :is_interactive, :picture_count, :has_missing_diagrams,
                :availability_status, :display_ready, :solve_ready, :unavailable_reason,
                :source_dataset, :source_urls, :statement_relation, :shared_statement_from, :imported_at
            )
            """,
            payload,
        )


def test_is_arena_solvable_requires_display_ready_statement():
    _seed_catalog(
        {
            "contestId": 2228,
            "index": "B",
            "name": "Remilia Plays Soku",
            "rating": 1100,
            "tags": ["games"],
        }
    )
    assert store.get_problem("2228B") is not None
    assert store.get_problem_statement("2228B") is None
    assert is_arena_solvable("2228B") is False


def test_select_skips_catalog_only_2228B():
    _seed_catalog(
        {
            "contestId": 2228,
            "index": "B",
            "name": "Remilia Plays Soku",
            "rating": 1100,
            "tags": ["games"],
        },
        {
            "contestId": 1,
            "index": "A",
            "name": "Theatre Square",
            "rating": 1000,
            "tags": ["math"],
        },
    )
    _seed_statement("1A", title="Theatre Square")
    selected = select_arena_recommendations(
        [
            {"name": "Remilia Plays Soku", "contestId": 2228, "index": "B", "rating": 1100, "tags": ["games"]},
            {"name": "Theatre Square", "contestId": 1, "index": "A", "rating": 1000, "tags": ["math"]},
        ],
        limit=8,
    )
    ids = {f"{p['contestId']}{p['index']}" for p in selected}
    assert "2228B" not in ids
    assert "1A" in ids


def test_public_problem_2228B_is_not_arena_capable(client):
    _seed_catalog(
        {
            "contestId": 2228,
            "index": "B",
            "name": "Remilia Plays Soku",
            "rating": 1100,
            "tags": ["games"],
        }
    )
    response = client.get("/api/v1/problems/2228B")
    assert response.status_code == 200
    body = response.json()
    assert body["arena_capable"] is False
    assert body["statement_content"]["availability"]["display_ready"] is False
    reason = body["statement_content"]["availability"]["unavailable_reason"] or ""
    assert "no content record" not in reason
    assert reason == "Statement not available in SolveX yet."


def test_persisted_recommendation_item_without_statement_is_not_arena_solvable():
    _seed_catalog(
        {
            "contestId": 2228,
            "index": "B",
            "name": "Remilia Plays Soku",
            "rating": 1100,
            "tags": ["games"],
        }
    )
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO recommendation_runs (
                run_id, handle, queue_date, created_at
            ) VALUES ('run-bad', 'fixture', '2026-08-03', ?)
            """,
            (now,),
        )
        conn.execute(
            """
            INSERT INTO recommendation_items (
                item_id, run_id, slot, mode, problem_id, skill_id, why_selected
            ) VALUES ('item-bad', 'run-bad', 1, 'core_repair', '2228B', 'games', 'stale')
            """
        )
        rows = conn.execute(
            "SELECT problem_id FROM recommendation_items WHERE problem_id IS NOT NULL"
        ).fetchall()
    assert is_arena_solvable("2228B") is False
    assert any(row["problem_id"] == "2228B" and not is_arena_solvable(row["problem_id"]) for row in rows)
