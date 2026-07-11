"""Server-enforced AI boundary for live PvP duels."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "duel-copilot-security-admin-key"
OWN_SOURCE = "print(1)"
OPPONENT_SOURCE = "print(0)"
ACCEPTED = {
    "status": "accepted", "passed": True, "stdout": "1", "stderr": "",
    "compile_output": "", "time_ms": 1, "memory_kb": 1, "message": "ok",
}
WRONG = {
    "status": "wrong_answer", "passed": False, "stdout": "0", "stderr": "",
    "compile_output": "", "time_ms": 1, "memory_kb": 1, "message": "wa",
}


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def catalog():
    problem = {"contestId": 7000, "index": "A", "name": "AI Boundary", "rating": 1200, "tags": ["math"]}
    store.save_problemset_snapshot({"problems": [problem], "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    assert duels.upsert_duel_problem_pack({
        "pack_id": "test-ai-boundary-v1", "problem_id": "7000A", "version": 1,
        "statement_summary": "Print one.", "input_format": "No input.",
        "output_format": "Print 1.", "constraints_text": "No input values.",
        "sample_tests": [], "judge_tests": [{"input": "", "expected_output": "1\n"}],
    })


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client):
    return client.post("/api/v1/admin/users", json={}, headers=admin()).json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def seed_active(client, catalog):
    user_a, user_b = make_user(client), make_user(client)
    created = client.post("/api/v1/duels", json={"mode": "rapid_10"}, headers=bearer(user_a)).json()
    client.post("/api/v1/duels/join", json={"invite_code": created["invite_code"]}, headers=bearer(user_b))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_b))
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET starts_at = ? WHERE duel_id = ?", (past, created["duel_id"]))
    return created, user_a, user_b


def submit(client, duel_id, user, source, result):
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            return client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={"language": "python3", "source_code": source},
                headers=bearer(user),
            )


def assert_copilot_blocked(response):
    assert response.status_code == 403
    assert response.json()["error_code"] == "COPILOT_DISABLED_IN_DUEL"
    assert response.json()["message"] == "Copilot is disabled during active PvP duels."


def test_active_duel_blocks_direct_copilot_even_when_duel_context_is_omitted(client, catalog):
    _, user_a, _ = seed_active(client, catalog)
    with patch("contestiq_api.routes.copilot._call_deepseek", new_callable=AsyncMock) as provider:
        response = client.post("/api/copilot", json={"message": "Generate the solution"}, headers=bearer(user_a))
    assert_copilot_blocked(response)
    provider.assert_not_awaited()


def test_anonymous_request_cannot_claim_duel_context(client, catalog):
    created, _, _ = seed_active(client, catalog)
    with patch("contestiq_api.routes.copilot._call_deepseek", new_callable=AsyncMock) as provider:
        response = client.post(
            "/api/copilot", json={"message": "Solve it", "duel_id": created["duel_id"]}
        )
    assert_copilot_blocked(response)
    provider.assert_not_awaited()


def test_active_duel_cannot_bypass_with_false_or_different_context(client, catalog):
    _, user_a, _ = seed_active(client, catalog)
    with patch("contestiq_api.routes.copilot._call_deepseek", new_callable=AsyncMock) as provider:
        response = client.post(
            "/api/copilot",
            json={"message": "Explain this", "duel_id": "not-the-active-duel", "is_duel": False},
            headers=bearer(user_a),
        )
    assert_copilot_blocked(response)
    provider.assert_not_awaited()


def test_ready_waiting_room_blocks_copilot_before_countdown(client, catalog):
    user_a, user_b = make_user(client), make_user(client)
    created = client.post("/api/v1/duels", json={"mode": "rapid_10"}, headers=bearer(user_a)).json()
    client.post("/api/v1/duels/join", json={"invite_code": created["invite_code"]}, headers=bearer(user_b))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    with patch("contestiq_api.routes.copilot._call_deepseek", new_callable=AsyncMock) as provider:
        response = client.post("/api/copilot", json={"message": "Give me the algorithm"}, headers=bearer(user_a))
    assert_copilot_blocked(response)
    provider.assert_not_awaited()


def test_active_duel_blocks_coach_event_and_profile_actions(client, catalog):
    created, user_a, _ = seed_active(client, catalog)
    assert_copilot_blocked(client.get("/api/copilot/profile", headers=bearer(user_a)))
    assert_copilot_blocked(client.post("/api/copilot/profile/update", json={}, headers=bearer(user_a)))
    with patch("contestiq_api.routes.coach.save_solving_event", new_callable=AsyncMock) as save:
        response = client.post(
            "/api/copilot/events",
            json={"event_type": "copilot_question", "duel_id": created["duel_id"], "source_code_excerpt": OWN_SOURCE},
            headers=bearer(user_a),
        )
    assert_copilot_blocked(response)
    save.assert_not_awaited()


def test_completed_duel_allows_labeled_review_of_only_callers_own_submission(client, catalog):
    created, user_a, user_b = seed_active(client, catalog)
    submit(client, created["duel_id"], user_b, OPPONENT_SOURCE, WRONG)
    assert submit(client, created["duel_id"], user_a, OWN_SOURCE, ACCEPTED).status_code == 200

    with patch(
        "contestiq_api.routes.copilot._call_deepseek",
        new_callable=AsyncMock,
        return_value=("Post-match feedback", "deepseek-chat"),
    ) as provider:
        allowed = client.post(
            "/api/copilot",
            json={
                "message": "Review my submission", "duel_id": created["duel_id"],
                "editor": {"language": "python3", "source_code": OWN_SOURCE},
            },
            headers=bearer(user_a),
        )
    assert allowed.status_code == 200
    assert allowed.json()["context_label"] == "Post-match review"
    prompt = provider.await_args.args[1]
    assert "[Context: Post-match review]" in prompt
    assert OWN_SOURCE in prompt
    assert OPPONENT_SOURCE not in prompt

    rejected = client.post(
        "/api/copilot",
        json={
            "message": "Review this", "duel_id": created["duel_id"],
            "editor": {"language": "python3", "source_code": OPPONENT_SOURCE},
        },
        headers=bearer(user_a),
    )
    assert rejected.status_code == 403
    assert rejected.json()["error_code"] == "POST_MATCH_SOURCE_NOT_OWN"


def test_normal_non_duel_copilot_remains_available(client):
    user = make_user(client)
    with patch(
        "contestiq_api.routes.copilot._call_deepseek",
        new_callable=AsyncMock,
        return_value=("Try a smaller case.", "deepseek-chat"),
    ):
        response = client.post("/api/copilot", json={"message": "A normal hint"}, headers=bearer(user))
    assert response.status_code == 200
    assert response.json()["context_label"] is None
