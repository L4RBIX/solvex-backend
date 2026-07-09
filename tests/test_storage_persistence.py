"""Persistence tests for Railway's ephemeral filesystem problem.

Context: SQLite lives at DATABASE_PATH (settings.py). On Railway, unless that
path is inside a mounted persistent volume, every redeploy wipes the file —
including the shared problem catalog (`problems`) and `problem_skill_map` —
which silently empties the daily queue/plans even though episodes exist.
These tests cover: (1) DATABASE_PATH is honored end-to-end including nested
directories that don't exist yet, (2) data written under a custom path
survives a fresh `connect()` (simulating a process restart against the same
volume), (3) the storage diagnostics used by the admin health check and
startup log, and (4) the opt-in (flag-gated) auto-seed startup hook.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest
from fastapi.testclient import TestClient

ADMIN_KEY = "test-admin-key-storage"


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("FEATURE_FLAGS", raising=False)


def _reload_settings():
    import contestiq_api.settings as settings

    importlib.reload(settings)
    return settings


def seed_problems(*problems):
    from contestiq_api.cfdata import store

    store.save_problemset_snapshot({"problems": list(problems), "problemStatistics": []})


# ─── DATABASE_PATH is honored ────────────────────────────────────────────────


def test_database_path_defaults_to_api_cache(monkeypatch):
    settings = _reload_settings()
    assert settings.get_settings().database_path == "api_cache/backend_jobs.db"


def test_custom_database_path_is_used_and_nested_dirs_are_created(tmp_path, monkeypatch):
    custom_path = tmp_path / "data" / "nested" / "backend_jobs.db"
    assert not custom_path.parent.exists()
    monkeypatch.setenv("DATABASE_PATH", str(custom_path))

    _reload_settings()
    from contestiq_api.cfdata import store

    importlib.reload(store)
    with store.connect() as conn:
        conn.execute("SELECT 1")

    assert custom_path.exists()


def test_data_survives_reconnect_at_same_custom_path(tmp_path, monkeypatch):
    """Simulates a Railway redeploy: process restarts, but DATABASE_PATH points
    at the same (persistent-volume-backed) file, so previously written rows
    must still be readable through a brand-new connection."""
    custom_path = tmp_path / "volume" / "backend_jobs.db"
    monkeypatch.setenv("DATABASE_PATH", str(custom_path))
    _reload_settings()
    from contestiq_api.cfdata import store

    importlib.reload(store)
    seed_problems({"contestId": 1, "index": "A", "name": "Watermelon", "rating": 800, "tags": ["math"]})

    # Fresh connection object, same underlying file — nothing in-process is reused.
    with store.connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM problems").fetchone()
    assert row[0] == 1

    with store.connect() as conn:
        name = conn.execute("SELECT name FROM problems WHERE problem_key = ?", ("1A",)).fetchone()["name"]
    assert name == "Watermelon"


def test_database_path_looks_persistent_heuristic():
    from contestiq_api.settings import database_path_looks_persistent

    assert database_path_looks_persistent("/data/backend_jobs.db") is True
    assert database_path_looks_persistent("api_cache/backend_jobs.db") is False
    assert database_path_looks_persistent("./api_cache/backend_jobs.db") is False


# ─── storage_diagnostics() ───────────────────────────────────────────────────


def test_storage_diagnostics_reports_zero_on_empty_catalog():
    from contestiq_api.cfdata import store

    diag = store.storage_diagnostics()
    assert diag == {
        "problemset_count": 0,
        "problem_skill_map_count": 0,
        "latest_problemset_sync_at": None,
    }


def test_storage_diagnostics_reports_real_counts_after_seed():
    from contestiq_api.cfdata import store, taxonomy

    seed_problems(
        {"contestId": 4, "index": "A", "name": "Watermelon", "rating": 800, "tags": ["math"]},
        {"contestId": 4, "index": "B", "name": "Before an Exam", "rating": 1400, "tags": ["greedy"]},
    )
    taxonomy.build_problem_skill_map()

    diag = store.storage_diagnostics()
    assert diag["problemset_count"] == 2
    assert diag["problem_skill_map_count"] > 0
    assert diag["latest_problemset_sync_at"] is not None


# ─── Admin storage-health endpoint ───────────────────────────────────────────


def _client(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    import contestiq_api.main as main

    importlib.reload(main)
    return TestClient(main.app), main


def test_storage_health_requires_admin_key(monkeypatch):
    client, _ = _client(monkeypatch)
    resp = client.get("/api/v1/admin/storage-health")
    assert resp.status_code in (401, 403)


def test_storage_health_reports_catalog_not_ready_when_empty(monkeypatch):
    client, _ = _client(monkeypatch)
    resp = client.get("/api/v1/admin/storage-health", headers={"X-Admin-Key": ADMIN_KEY})
    assert resp.status_code == 200
    body = resp.json()
    assert body["catalog_ready"] is False
    assert body["problemset_count"] == 0
    assert body["problem_skill_map_count"] == 0
    assert body["database_path_looks_persistent"] is False


def test_storage_health_reports_catalog_ready_after_seed(monkeypatch):
    client, _ = _client(monkeypatch)
    seed_problems({"contestId": 4, "index": "A", "name": "Watermelon", "rating": 800, "tags": ["math"]})
    from contestiq_api.cfdata import taxonomy

    taxonomy.build_problem_skill_map()

    resp = client.get("/api/v1/admin/storage-health", headers={"X-Admin-Key": ADMIN_KEY})
    body = resp.json()
    assert body["catalog_ready"] is True
    assert body["problemset_count"] == 1
    assert body["problem_skill_map_count"] > 0


def test_storage_health_flags_absolute_path_as_persistent(tmp_path, monkeypatch):
    custom_path = tmp_path / "data" / "backend_jobs.db"
    monkeypatch.setenv("DATABASE_PATH", str(custom_path))
    client, _ = _client(monkeypatch)
    resp = client.get("/api/v1/admin/storage-health", headers={"X-Admin-Key": ADMIN_KEY})
    assert resp.json()["database_path_looks_persistent"] is True


# ─── Opt-in auto-seed startup hook ───────────────────────────────────────────


def _run_auto_seed(main, diag, monkeypatch, sync_calls, rebuild_calls):
    def fake_sync(*args, **kwargs):
        sync_calls.append(True)
        return {"status": "success"}

    def fake_rebuild(*args, **kwargs):
        rebuild_calls.append(True)
        return {"problems_mapped": 1}

    monkeypatch.setattr("contestiq_api.cfdata.sync.sync_problemset", fake_sync)
    monkeypatch.setattr("contestiq_api.cfdata.taxonomy.build_problem_skill_map", fake_rebuild)
    asyncio.run(main._maybe_auto_seed_catalog(diag))


def test_auto_seed_does_nothing_when_flag_disabled(monkeypatch):
    _, main = _client(monkeypatch)
    sync_calls: list[bool] = []
    rebuild_calls: list[bool] = []
    empty_diag = {"problemset_count": 0, "problem_skill_map_count": 0}
    _run_auto_seed(main, empty_diag, monkeypatch, sync_calls, rebuild_calls)
    assert sync_calls == []
    assert rebuild_calls == []


def test_auto_seed_does_nothing_when_catalog_already_populated(monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS", "auto_seed_catalog_on_startup")
    _, main = _client(monkeypatch)
    sync_calls: list[bool] = []
    rebuild_calls: list[bool] = []
    healthy_diag = {"problemset_count": 100, "problem_skill_map_count": 200}
    _run_auto_seed(main, healthy_diag, monkeypatch, sync_calls, rebuild_calls)
    assert sync_calls == []
    assert rebuild_calls == []


def test_auto_seed_runs_when_flag_enabled_and_catalog_empty(monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS", "auto_seed_catalog_on_startup")
    _, main = _client(monkeypatch)
    sync_calls: list[bool] = []
    rebuild_calls: list[bool] = []
    empty_diag = {"problemset_count": 0, "problem_skill_map_count": 0}
    _run_auto_seed(main, empty_diag, monkeypatch, sync_calls, rebuild_calls)
    assert sync_calls == [True]
    assert rebuild_calls == [True]


def test_log_storage_diagnostics_never_raises_on_store_failure(monkeypatch):
    """A broken/unreachable store must never take the whole process down at boot."""
    _, main = _client(monkeypatch)

    def boom():
        raise RuntimeError("disk unavailable")

    monkeypatch.setattr("contestiq_api.cfdata.store.storage_diagnostics", boom)
    diag = main._log_storage_diagnostics()
    assert "problemset_count" not in diag
