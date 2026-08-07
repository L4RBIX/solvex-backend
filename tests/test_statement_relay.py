"""24/7 statement relay: auth, leases, retries, heartbeat."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from contestiq_api.arena_eligibility import is_arena_solvable
from contestiq_api.cfdata import store
from contestiq_api.cfdata import statement_ingest
from contestiq_api.main import app

FIXTURES = Path(__file__).parent / "fixtures" / "cf_html"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("STATEMENT_RELAY_TOKEN", "relay-test-token-123456789012")
    monkeypatch.setenv("STATEMENT_RELAY_EMBEDDED", "0")
    monkeypatch.setenv("ADMIN_API_KEY", "admin-test-key-1234567890")
    from contestiq_api import settings as settings_mod

    settings_mod.get_settings = lambda: settings_mod.Settings(
        app_env="development",
        statement_relay_token="relay-test-token-123456789012",
        statement_relay_embedded=False,
        statement_relay_lease_seconds=600,
        statement_ingest_max_attempts=8,
        admin_api_key="admin-test-key-1234567890",
    )
    return TestClient(app)


def _seed(problem_id: str):
    contest_id, index = statement_ingest.split_problem_id(problem_id)
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO problems
                (problem_key, contest_id, problem_index, name, rating, tags, problemset_name, updated_at)
            VALUES (?, ?, ?, ?, 800, '[]', 'test', ?)
            """,
            (problem_id, contest_id, index, problem_id, store._now()),
        )
    store.ensure_statement_pending_stubs([problem_id])
    store.enqueue_statement_ingest([problem_id], reason="test")


def test_relay_unauthorized(client):
    resp = client.get("/api/v1/relay/statements/jobs/next")
    assert resp.status_code == 401


def test_lease_and_result_success(client):
    _seed("2254A")
    headers = {"Authorization": "Bearer relay-test-token-123456789012", "X-Relay-Id": "t1"}
    hb = client.post("/api/v1/relay/statements/heartbeat", headers=headers, json={"version": "test"})
    assert hb.status_code == 200
    assert hb.json()["observability"]["relay_status"] in {"healthy", "degraded", "offline"}

    nxt = client.get("/api/v1/relay/statements/jobs/next", headers=headers)
    assert nxt.status_code == 200
    job = nxt.json()["job"]
    assert job["problem_id"] == "2254A"
    assert job["official_url"].endswith("/2254/A")

    # Second lease should not return the same active lease.
    nxt2 = client.get("/api/v1/relay/statements/jobs/next", headers={**headers, "X-Relay-Id": "t2"})
    assert nxt2.json()["job"] is None or nxt2.json()["job"]["problem_id"] != "2254A"

    html = (FIXTURES / "2254A.html").read_text()
    result = client.post(
        "/api/v1/relay/statements/jobs/2254A/result",
        headers=headers,
        json={"http_status": 200, "final_url": job["official_url"], "html": html},
    )
    assert result.status_code == 200
    body = result.json()
    assert body["accepted"] is True
    assert body["ingest"]["status"] in {"succeeded", "partial", "asset_required"}
    assert is_arena_solvable("2254A") is True


def test_blocked_403_classified(client):
    _seed("2227G")
    headers = {"Authorization": "Bearer relay-test-token-123456789012", "X-Relay-Id": "t1"}
    client.get("/api/v1/relay/statements/jobs/next", headers=headers)
    result = client.post(
        "/api/v1/relay/statements/jobs/2227G/result",
        headers=headers,
        json={
            "http_status": 403,
            "html": "<html><title>Just a moment...</title><div>cf-chl</div></html>",
            "error": "forbidden",
        },
    )
    assert result.status_code == 200
    assert result.json()["ingest"]["failure_class"] == "blocked"
    row = store.connect().execute(
        "SELECT status, failure_class FROM statement_ingest_queue WHERE problem_id='2227G'"
    ).fetchone()
    assert row["status"] == "retrying"
    assert row["failure_class"] == "blocked"


def test_expired_lease_can_be_reclaimed(client, monkeypatch):
    _seed("1A")
    headers = {"Authorization": "Bearer relay-test-token-123456789012", "X-Relay-Id": "t1"}
    job = client.get("/api/v1/relay/statements/jobs/next", headers=headers).json()["job"]
    assert job is not None
    # Force-expire lease.
    with store.connect() as conn:
        conn.execute(
            "UPDATE statement_ingest_queue SET leased_until='2000-01-01T00:00:00+00:00' WHERE problem_id='1A'"
        )
    job2 = client.get(
        "/api/v1/relay/statements/jobs/next",
        headers={**headers, "X-Relay-Id": "t2"},
    ).json()["job"]
    assert job2 is not None
    assert job2["problem_id"] == "1A"
    assert job2["leased_by"] == "t2"


def test_admin_relay_health(client):
    headers = {"Authorization": "Bearer relay-test-token-123456789012", "X-Relay-Id": "t1"}
    client.post("/api/v1/relay/statements/heartbeat", headers=headers, json={"version": "x"})
    admin = client.get("/api/v1/admin/statements/relay/health", headers={"X-Admin-Key": "admin-test-key-1234567890"})
    assert admin.status_code == 200
    assert "relay_status" in admin.json()
