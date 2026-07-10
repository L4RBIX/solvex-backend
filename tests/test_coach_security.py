"""Bearer-only identity regressions for Coach profiles and Copilot memory."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


ADMIN_KEY = "coach-security-admin-key"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def make_user(client):
    response = client.post(
        "/api/v1/admin/users",
        json={},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    return response.json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def event_payload(**overrides):
    payload = {
        "event_type": "run_attempt",
        "short_summary": "Ran the sample",
        "user_id": "caller-supplied-user",
        "anonymous_user_key": "caller-supplied-anonymous-key",
    }
    payload.update(overrides)
    return payload


def test_private_coach_endpoints_require_bearer_auth(client):
    assert client.get(
        "/api/copilot/profile?user_id=victim&anonymous_user_key=victim-key"
    ).status_code == 401
    assert client.post(
        "/api/copilot/profile/update",
        json={"user_id": "victim", "anonymous_user_key": "victim-key"},
    ).status_code == 401
    assert client.post("/api/copilot/events", json=event_payload()).status_code == 401


def test_coach_profile_reads_and_updates_use_only_token_user_id(client):
    owner = make_user(client)
    victim = make_user(client)

    with patch(
        "contestiq_api.routes.coach.load_profile",
        new_callable=AsyncMock,
        return_value={"summary": "owner profile"},
    ) as load:
        response = client.get(
            f"/api/copilot/profile?user_id={victim['user_id']}&anonymous_user_key=victim-key",
            headers=bearer(owner),
        )
    assert response.status_code == 200
    assert response.json()["profile"]["summary"] == "owner profile"
    assert load.await_args.kwargs == {
        "user_id": owner["user_id"],
        "anonymous_user_key": None,
    }

    with patch(
        "contestiq_api.routes.coach.update_user_solving_profile",
        new_callable=AsyncMock,
        return_value={"summary": "updated owner profile"},
    ) as update:
        response = client.post(
            "/api/copilot/profile/update",
            json={"user_id": victim["user_id"], "anonymous_user_key": "victim-key"},
            headers=bearer(owner),
        )
    assert response.status_code == 200
    assert update.await_args.kwargs == {
        "user_id": owner["user_id"],
        "anonymous_user_key": None,
    }


def test_coach_event_overwrites_all_caller_supplied_identity(client):
    owner = make_user(client)
    victim = make_user(client)
    with patch(
        "contestiq_api.routes.coach.save_solving_event", new_callable=AsyncMock
    ) as save:
        response = client.post(
            "/api/copilot/events",
            json=event_payload(user_id=victim["user_id"]),
            headers=bearer(owner),
        )
    assert response.status_code == 200
    saved_event = save.await_args.args[1]
    assert saved_event["user_id"] == owner["user_id"]
    assert saved_event["user_id"] != victim["user_id"]
    assert saved_event["anonymous_user_key"] is None


def test_public_copilot_chat_ignores_anonymous_key_for_private_memory(client):
    with (
        patch(
            "contestiq_api.routes.copilot._call_deepseek",
            new_callable=AsyncMock,
            return_value=("Try a smaller example.", "deepseek-chat"),
        ),
        patch("contestiq_api.routes.copilot.load_profile", new_callable=AsyncMock) as load,
        patch("contestiq_api.routes.copilot.save_solving_event", new_callable=AsyncMock) as save,
        patch("contestiq_api.routes.copilot._persist", new_callable=AsyncMock) as persist,
    ):
        response = client.post(
            "/api/copilot",
            json={
                "message": "Can I have a hint?",
                "anonymous_user_key": "someone-elses-local-key",
                "user_id": "someone-elses-user-id",
            },
        )
    assert response.status_code == 200
    load.assert_not_awaited()
    save.assert_not_awaited()
    assert persist.await_args.kwargs["user_id"] is None


def test_authenticated_copilot_memory_uses_only_token_user_id(client):
    owner = make_user(client)
    with (
        patch(
            "contestiq_api.routes.copilot._call_deepseek",
            new_callable=AsyncMock,
            return_value=("Try a smaller example.", "deepseek-chat"),
        ),
        patch(
            "contestiq_api.routes.copilot.load_profile",
            new_callable=AsyncMock,
            return_value=None,
        ) as load,
        patch("contestiq_api.routes.copilot.save_solving_event", new_callable=AsyncMock) as save,
        patch("contestiq_api.routes.copilot._persist", new_callable=AsyncMock) as persist,
    ):
        response = client.post(
            "/api/copilot",
            json={
                "message": "Can I have a hint?",
                "anonymous_user_key": "attacker-controlled-key",
                "user_id": "attacker-controlled-user-id",
            },
            headers=bearer(owner),
        )
    assert response.status_code == 200
    assert load.await_args.kwargs == {
        "user_id": owner["user_id"],
        "anonymous_user_key": None,
    }
    assert persist.await_args.kwargs["user_id"] == owner["user_id"]
    saved_event = save.await_args.args[1]
    assert saved_event["user_id"] == owner["user_id"]
    assert saved_event["anonymous_user_key"] is None


def test_invalid_bearer_cannot_reach_public_copilot_as_anonymous(client):
    with patch(
        "contestiq_api.routes.copilot._call_deepseek", new_callable=AsyncMock
    ) as call_provider:
        response = client.post(
            "/api/copilot",
            json={"message": "hello", "anonymous_user_key": "fallback-key"},
            headers={"Authorization": "Bearer invalid-token"},
        )
    assert response.status_code == 401
    call_provider.assert_not_awaited()
