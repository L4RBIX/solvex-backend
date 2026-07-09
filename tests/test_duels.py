"""Friend 1v1 duels (Phase G4) tests."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels, gamification, product_events
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "duels-admin-key"
HANDLE_A = "Duel-Creator"
HANDLE_B = "Duel-Challenger"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def catalog():
    """Seed a small mapped problem catalog for duel assignment."""
    problems = []
    for i, rating in enumerate([1000, 1100, 1200, 1300, 1400]):
        problems.append({
            "contestId": 1000 + i,
            "index": "A",
            "name": f"Duel Prob {i}",
            "rating": rating,
            "tags": ["greedy" if i % 2 == 0 else "math"],
        })
    store.save_problemset_snapshot({"problems": problems, "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    return problems


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client, handle=None):
    return client.post("/api/v1/admin/users", json={"handle": handle}, headers=admin()).json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def _create(client, handle=HANDLE_A, mode="rapid_10", display="Creator"):
    return client.post(
        f"/api/v1/duels?handle={handle}",
        json={"mode": mode, "display_name": display},
    )


# ─── Create / invite ──────────────────────────────────────────────────────────


def test_create_duel_returns_invite_code_once(client, catalog):
    response = _create(client)
    assert response.status_code == 200
    data = response.json()
    assert "invite_code" in data
    assert len(data["invite_code"]) >= 8
    assert data["status"] == "waiting"
    assert data["problem"]["problem_id"]
    assert data["mode"] == "rapid_10"


def test_invite_code_stored_hashed(client, catalog):
    data = _create(client).json()
    with store.connect() as conn:
        row = conn.execute("SELECT invite_code_hash FROM duel_matches").fetchone()
    assert row["invite_code_hash"] != data["invite_code"]
    assert row["invite_code_hash"] == hashlib.sha256(data["invite_code"].encode()).hexdigest()


def test_invite_preview_safe(client, catalog):
    created = _create(client).json()
    preview = client.get(f"/api/v1/duels/invite/{created['invite_code']}").json()
    assert preview["mode"] == "rapid_10"
    assert "creator_display_name" in preview
    assert "problem" in preview
    raw = json.dumps(preview).lower()
    assert "invite_code_hash" not in raw
    assert "source" not in raw
    assert "token" not in raw


def test_join_with_valid_invite(client, catalog):
    created = _create(client).json()
    response = client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger", "handle": HANDLE_B},
    )
    assert response.status_code == 200
    assert response.json()["already_member"] is False
    assert response.json()["role"] == "challenger"


def test_invalid_invite_rejected(client, catalog):
    response = client.post(
        "/api/v1/duels/join",
        json={"invite_code": "not-a-real-invite", "display_name": "X", "handle": HANDLE_B},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "INVITE_INVALID"


# ─── Authorization ────────────────────────────────────────────────────────────


def test_non_participant_cannot_view_duel(client, catalog):
    created = _create(client).json()
    response = client.get(f"/api/v1/duels/{created['duel_id']}?handle={HANDLE_B}")
    assert response.status_code == 403


def test_participant_can_view_duel(client, catalog):
    created = _create(client).json()
    response = client.get(f"/api/v1/duels/{created['duel_id']}?handle={HANDLE_A}")
    assert response.status_code == 200
    assert response.json()["duel_id"] == created["duel_id"]
    assert len(response.json()["participants"]) == 1


def test_duel_starts_with_two_participants(client, catalog):
    created = _create(client).json()
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger", "handle": HANDLE_B},
    )
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["starts_at"]
    assert len(data["participants"]) == 2


def test_problem_assigned_from_catalog(client, catalog):
    created = _create(client).json()
    problem_id = created["problem"]["problem_id"]
    assert store.get_problem(problem_id) is not None
    assert created["problem"]["rating"] is not None


# ─── Winner rules ─────────────────────────────────────────────────────────────


def _seed_active_duel(client):
    created = _create(client).json()
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger", "handle": HANDLE_B},
    )
    client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    return created


def test_accepted_submission_wins(client, catalog):
    created = _seed_active_duel(client)
    mock_result = {
        "status": "accepted", "passed": True, "stdout": "ok", "stderr": "",
        "compile_output": "", "time_ms": 10, "memory_kb": 100, "message": "accepted",
    }
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=mock_result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            response = client.post(
                f"/api/v1/duels/{created['duel_id']}/submit?handle={HANDLE_A}",
                json={"language": "python3", "source_code": "print(1)", "stdin": "", "expected_output": "1"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["duel"]["status"] == "completed"
    assert body["duel"]["result_reason"] == "first_accepted"
    winners = [p for p in body["duel"]["participants"] if p["is_winner"]]
    assert len(winners) == 1
    assert winners[0]["handle"] == HANDLE_A.lower()


def test_earlier_accepted_submission_wins_tie(client, catalog):
    created = _seed_active_duel(client)
    duel_id = created["duel_id"]
    now = store._now()
    earlier = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)).isoformat()
    later = now
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, final_status = 'accepted' WHERE duel_id = ? AND handle = ?",
            (earlier, duel_id, HANDLE_B.lower()),
        )
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, final_status = 'accepted' WHERE duel_id = ? AND handle = ?",
            (later, duel_id, HANDLE_A.lower()),
        )
    duels._decide_winner_if_ready(duel_id)
    duel = duels.get_duel(duel_id)
    assert duel["status"] == "completed"
    assert duel["winner_subject"] == f"handle:{HANDLE_B.lower()}"


def test_no_accepted_submissions_expires_draws(client, catalog):
    created = _seed_active_duel(client)
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, created["duel_id"]))
    detail = client.get(f"/api/v1/duels/{created['duel_id']}?handle={HANDLE_A}").json()
    assert detail["status"] == "expired"
    assert detail["winner_subject"] is None
    assert detail["result_reason"] == "expired_draw"


def test_source_code_secrets_not_exposed(client, catalog):
    created = _seed_active_duel(client)
    mock_result = {
        "status": "wrong_answer", "passed": False, "stdout": "x", "stderr": "",
        "compile_output": "", "time_ms": 1, "memory_kb": 1, "message": "wa",
    }
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=mock_result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = "secret-key"
            gs.return_value.judge0_api_host = ""
            client.post(
                f"/api/v1/duels/{created['duel_id']}/submit?handle={HANDLE_A}",
                json={"language": "python3", "source_code": "SECRET_SOURCE_CODE_XYZ", "stdin": ""},
            )
    detail = client.get(f"/api/v1/duels/{created['duel_id']}?handle={HANDLE_A}").json()
    raw = json.dumps(detail)
    assert "SECRET_SOURCE_CODE_XYZ" not in raw
    assert "secret-key" not in raw
    assert "source_code" not in raw.lower()
    preview = client.get(f"/api/v1/duels/invite/{created['invite_code']}")
    # invite may be closed after start — either 410 or safe preview
    if preview.status_code == 200:
        assert "SECRET" not in preview.text


# ─── Gamification / XP farming ────────────────────────────────────────────────


def test_product_events_emitted_for_completed_duel_only(client, catalog):
    created = _create(client).json()
    events = product_events.events_for(f"handle:{HANDLE_A.lower()}")
    assert any(e["event_type"] == "duel_created" for e in events)
    # Creating alone must not emit duel_completed / duel_won.
    assert not any(e["event_type"] == "duel_completed" for e in events)
    assert not any(e["event_type"] == "duel_won" for e in events)

    client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger", "handle": HANDLE_B},
    )
    client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    mock_result = {
        "status": "accepted", "passed": True, "stdout": "1", "stderr": "",
        "compile_output": "", "time_ms": 1, "memory_kb": 1, "message": "ok",
    }
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=mock_result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            client.post(
                f"/api/v1/duels/{created['duel_id']}/submit?handle={HANDLE_A}",
                json={"language": "python3", "source_code": "print(1)", "expected_output": "1"},
            )

    creator_events = {e["event_type"] for e in product_events.events_for(f"handle:{HANDLE_A.lower()}")}
    challenger_events = {e["event_type"] for e in product_events.events_for(f"handle:{HANDLE_B.lower()}")}
    assert "duel_completed" in creator_events
    assert "duel_won" in creator_events
    assert "duel_completed" in challenger_events
    assert "duel_won" not in challenger_events


def test_xp_not_farmable_from_abandoned_duels(client, catalog):
    before = gamification.compute_xp_total(
        product_events.events_for(f"handle:{HANDLE_A.lower()}"), daily_cap=1000
    )
    for _ in range(3):
        _create(client)
    after_events = product_events.events_for(f"handle:{HANDLE_A.lower()}")
    after = gamification.compute_xp_total(after_events, daily_cap=1000)
    # duel_created is tracked but awards 0 XP (not in XP_RULES meaningful awards beyond completed/won).
    assert after == before
    assert "duel_created" not in gamification.XP_RULES
    assert gamification.XP_RULES["duel_completed"] == 10
    assert gamification.XP_RULES["duel_won"] == 15
