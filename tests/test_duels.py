"""Friend 1v1 duels (Phase G4) tests.

Security hotfix: duel identity is resolved EXCLUSIVELY from a bearer token
(never a caller-supplied handle) — see tests/test_identity_security.py for
the dedicated spoofing/authorization regression suite. These tests use real
admin-issued accounts throughout.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels, gamification, product_events
from contestiq_api.cfdata import store, taxonomy
from contestiq_api.identity import account_display_name

ADMIN_KEY = "duels-admin-key"


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
    for problem in problems:
        key = f"{problem['contestId']}{problem['index']}"
        assert duels.upsert_duel_problem_pack({
            "pack_id": f"test-{key}-v1", "problem_id": key, "version": 1,
            "statement_summary": "Print one for the shared test.", "input_format": "No input.",
            "output_format": "Print 1.", "constraints_text": "No input values.",
            "sample_tests": [{"input": "", "output": "1\n"}],
            "judge_tests": [{"input": "", "expected_output": "1\n"}],
        })
    return problems


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client, handle=None):
    return client.post("/api/v1/admin/users", json={"handle": handle}, headers=admin()).json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def _create(client, user, mode="rapid_10", display="Creator"):
    return client.post("/api/v1/duels", json={"mode": mode, "display_name": display}, headers=bearer(user))


def _join(client, user, invite_code, display="Challenger"):
    return client.post(
        "/api/v1/duels/join",
        json={"invite_code": invite_code, "display_name": display},
        headers=bearer(user),
    )


# ─── Create / invite ──────────────────────────────────────────────────────────


def test_create_duel_returns_invite_code_once(client, catalog):
    user_a = make_user(client)
    response = _create(client, user_a)
    assert response.status_code == 200
    data = response.json()
    assert "invite_code" in data
    assert len(data["invite_code"]) >= 8
    assert data["status"] == "waiting"
    assert data["problem"]["problem_id"]
    assert data["mode"] == "rapid_10"


def test_create_duel_requires_auth(client, catalog):
    response = client.post("/api/v1/duels", json={"mode": "rapid_10", "display_name": "Nobody"})
    assert response.status_code == 401


def test_invite_code_stored_hashed(client, catalog):
    user_a = make_user(client)
    data = _create(client, user_a).json()
    with store.connect() as conn:
        row = conn.execute("SELECT invite_code_hash FROM duel_matches").fetchone()
    assert row["invite_code_hash"] != data["invite_code"]
    assert row["invite_code_hash"] == hashlib.sha256(data["invite_code"].encode()).hexdigest()


def test_invite_preview_safe(client, catalog):
    user_a = make_user(client)
    created = _create(client, user_a).json()
    preview = client.get(f"/api/v1/duels/invite/{created['invite_code']}").json()
    assert preview["mode"] == "rapid_10"
    assert "creator_display_name" in preview
    assert "problem" in preview
    raw = json.dumps(preview).lower()
    assert "invite_code_hash" not in raw
    assert "source" not in raw
    assert "token" not in raw


def test_join_with_valid_invite(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _create(client, user_a).json()
    response = _join(client, user_b, created["invite_code"])
    assert response.status_code == 200
    assert response.json()["already_member"] is False
    assert response.json()["role"] == "challenger"


def test_join_requires_auth(client, catalog):
    user_a = make_user(client)
    created = _create(client, user_a).json()
    response = client.post(
        "/api/v1/duels/join", json={"invite_code": created["invite_code"], "display_name": "Ghost"}
    )
    assert response.status_code == 401


def test_invalid_invite_rejected(client, catalog):
    user_b = make_user(client)
    response = _join(client, user_b, "not-a-real-invite")
    assert response.status_code == 404
    assert response.json()["error_code"] == "INVITE_INVALID"


# ─── Authorization ────────────────────────────────────────────────────────────


def test_non_participant_cannot_view_duel(client, catalog):
    user_a = make_user(client)
    user_stranger = make_user(client)
    created = _create(client, user_a).json()
    response = client.get(f"/api/v1/duels/{created['duel_id']}", headers=bearer(user_stranger))
    assert response.status_code == 403


def test_participant_can_view_duel(client, catalog):
    user_a = make_user(client)
    created = _create(client, user_a).json()
    response = client.get(f"/api/v1/duels/{created['duel_id']}", headers=bearer(user_a))
    assert response.status_code == 200
    assert response.json()["duel_id"] == created["duel_id"]
    assert len(response.json()["participants"]) == 1


def test_duel_starts_with_two_participants(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _create(client, user_a).json()
    _join(client, user_b, created["invite_code"])
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_b))
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["starts_at"]
    assert len(data["participants"]) == 2


def test_problem_assigned_from_catalog(client, catalog):
    user_a = make_user(client)
    created = _create(client, user_a).json()
    problem_id = created["problem"]["problem_id"]
    assert store.get_problem(problem_id) is not None
    assert created["problem"]["rating"] is not None


# ─── Winner rules ─────────────────────────────────────────────────────────────


def _skip_countdown(duel_id):
    """Rewind starts_at so tests can submit without waiting the 3-2-1 countdown."""
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET starts_at = ? WHERE duel_id = ?", (past, duel_id))


def _seed_active_duel(client, user_a, user_b):
    created = _create(client, user_a).json()
    _join(client, user_b, created["invite_code"])
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_b))
    client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    _skip_countdown(created["duel_id"])
    return created


def test_accepted_submission_wins(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _seed_active_duel(client, user_a, user_b)
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
                f"/api/v1/duels/{created['duel_id']}/submit",
                json={"language": "python3", "source_code": "print(1)", "stdin": "", "expected_output": "1"},
                headers=bearer(user_a),
            )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["duel"]["status"] == "completed"
    assert body["duel"]["result_reason"] == "first_custom_test_pass"
    winners = [p for p in body["duel"]["participants"] if p["is_winner"]]
    assert len(winners) == 1
    assert winners[0]["display_name"] == account_display_name({"user_id": user_a["user_id"]})


def test_earlier_accepted_submission_wins_tie(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _seed_active_duel(client, user_a, user_b)
    duel_id = created["duel_id"]
    now = store._now()
    earlier = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)).isoformat()
    later = now
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, final_status = 'accepted' WHERE duel_id = ? AND user_id = ?",
            (earlier, duel_id, user_b["user_id"]),
        )
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, final_status = 'accepted' WHERE duel_id = ? AND user_id = ?",
            (later, duel_id, user_a["user_id"]),
        )
    duels._finalize_duel(duel_id, at_timeout=False)
    duel = duels.get_duel(duel_id)
    assert duel["status"] == "completed"
    assert duel["winner_subject"] == f"user:{user_b['user_id']}"


def test_no_accepted_submissions_expires_draws(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _seed_active_duel(client, user_a, user_b)
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, created["duel_id"]))
    detail = client.get(f"/api/v1/duels/{created['duel_id']}", headers=bearer(user_a)).json()
    assert detail["status"] == "expired"
    assert "winner_subject" not in detail
    assert detail["result_reason"] == "expired_draw"


def test_source_code_secrets_not_exposed(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    created = _seed_active_duel(client, user_a, user_b)
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
                f"/api/v1/duels/{created['duel_id']}/submit",
                json={"language": "python3", "source_code": "SECRET_SOURCE_CODE_XYZ", "stdin": "", "expected_output": "1"},
                headers=bearer(user_a),
            )
    detail = client.get(f"/api/v1/duels/{created['duel_id']}", headers=bearer(user_a)).json()
    raw = json.dumps(detail)
    assert "SECRET_SOURCE_CODE_XYZ" not in raw
    assert "secret-key" not in raw
    assert "source_code" not in raw.lower()
    assert user_a["api_token"] not in raw
    preview = client.get(f"/api/v1/duels/invite/{created['invite_code']}")
    # invite may be closed after start — either 410 or safe preview
    if preview.status_code == 200:
        assert "SECRET" not in preview.text


# ─── Gamification / XP farming ────────────────────────────────────────────────


def test_product_events_emitted_for_completed_duel_only(client, catalog):
    user_a = make_user(client)
    user_b = make_user(client)
    subject_a = f"user:{user_a['user_id']}"
    subject_b = f"user:{user_b['user_id']}"
    created = _create(client, user_a).json()
    events = product_events.events_for(subject_a)
    assert any(e["event_type"] == "duel_created" for e in events)
    # Creating alone must not emit duel_completed / duel_won.
    assert not any(e["event_type"] == "duel_completed" for e in events)
    assert not any(e["event_type"] == "duel_won" for e in events)

    _join(client, user_b, created["invite_code"])
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_b))
    client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    _skip_countdown(created["duel_id"])
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
                f"/api/v1/duels/{created['duel_id']}/submit",
                json={"language": "python3", "source_code": "print(1)", "expected_output": "1"},
                headers=bearer(user_a),
            )

    creator_events = {e["event_type"] for e in product_events.events_for(subject_a)}
    challenger_events = {e["event_type"] for e in product_events.events_for(subject_b)}
    assert "duel_completed" in creator_events
    assert "duel_won" in creator_events
    assert "duel_completed" in challenger_events
    assert "duel_won" not in challenger_events


def test_xp_not_farmable_from_abandoned_duels(client, catalog):
    user_a = make_user(client)
    subject_a = f"user:{user_a['user_id']}"
    before = gamification.compute_xp_total(product_events.events_for(subject_a), daily_cap=1000)
    for _ in range(3):
        _create(client, user_a)
    after_events = product_events.events_for(subject_a)
    after = gamification.compute_xp_total(after_events, daily_cap=1000)
    # duel_created is tracked but awards 0 XP (not in XP_RULES meaningful awards beyond completed/won).
    assert after == before
    assert "duel_created" not in gamification.XP_RULES
    assert gamification.XP_RULES["duel_completed"] == 10
    assert gamification.XP_RULES["duel_won"] == 15
