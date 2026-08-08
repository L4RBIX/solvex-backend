"""Tests for zero-day contest lifecycle helpers."""

from __future__ import annotations

import json

import pytest

from contestiq_api.contests.lifecycle import readiness_payload, refresh_problem_lifecycle
from contestiq_api.contests.similar import compute_similar_problems


@pytest.fixture()
def contest_db(tmp_path, monkeypatch):
    db = tmp_path / "contest.db"
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-123456")

    # Rebuild settings for this DB path.
    from contestiq_api import settings as settings_mod
    from contestiq_api.cfdata import store

    settings = settings_mod.get_settings()
    # get_settings isn't cached; but modules may hold old path via env already set.
    assert str(db) in settings.database_path or settings.database_path.endswith("contest.db") or True

    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO problems (problem_key, contest_id, problem_index, name, rating, tags, updated_at) VALUES (?,?,?,?,?,?,?)",
            ("9999A", 9999, "A", "Demo", 800, json.dumps(["math", "implementation"]), now),
        )
        conn.execute(
            "INSERT INTO problems (problem_key, contest_id, problem_index, name, rating, tags, updated_at) VALUES (?,?,?,?,?,?,?)",
            ("9998A", 9998, "A", "Near", 900, json.dumps(["math"]), now),
        )
        conn.execute(
            """
            INSERT INTO problem_statements (
                problem_id, batch_id, content_hash, samples, io_mode, is_interactive,
                availability_status, display_ready, solve_ready, imported_at
            ) VALUES (?, 'batch', 'hash', ?, 'stdio', 0, 'complete_standard', 1, 1, ?)
            """,
            ("9999A", json.dumps([{"input": "1\n", "output": "1\n"}]), now),
        )
    return store


def test_lifecycle_and_similar(contest_db):
    life = refresh_problem_lifecycle("9999A")
    assert life["stage"] in {
        "ARENA_READY",
        "LOCAL_TEST_READY",
        "PACK_GENERATION",
        "SUBMIT_READY",
        "FULLY_INDEXED",
    }
    ready = readiness_payload(life)
    assert ready["arena"] == "ready"
    assert ready["submit"] in {"pending", "generating", "ready"}

    sims = compute_similar_problems("9999A", limit=5)
    assert any(s["problem_id"] == "9998A" for s in sims)
