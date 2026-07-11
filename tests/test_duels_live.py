"""Phase G4.1 live duel room tests: ready flow, state polling, hints, winner v2.

Security hotfix: identity is resolved exclusively from bearer tokens (never a
caller-supplied handle) — see tests/test_identity_security.py for the
dedicated spoofing/authorization regression suite.
"""

from __future__ import annotations

import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels, gamification, product_events
from contestiq_api.cfdata import store, taxonomy
from contestiq_api.identity import account_display_name

ADMIN_KEY = "duels-live-admin-key"

ACCEPTED = {
    "status": "accepted", "passed": True, "stdout": "1", "stderr": "",
    "compile_output": "", "time_ms": 5, "memory_kb": 100, "message": "ok",
}
WRONG = {
    "status": "wrong_answer", "passed": False, "stdout": "2", "stderr": "",
    "compile_output": "", "time_ms": 5, "memory_kb": 100, "message": "wa",
}


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
    problems = []
    for i, rating in enumerate([1000, 1100, 1200, 1300, 1400]):
        problems.append({
            "contestId": 2000 + i,
            "index": "A",
            "name": f"Live Prob {i}",
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


def make_user(client):
    return client.post("/api/v1/admin/users", json={}, headers=admin()).json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def subject(user):
    return f"user:{user['user_id']}"


@pytest.fixture
def user_a(client):
    return make_user(client)


@pytest.fixture
def user_b(client):
    return make_user(client)


@pytest.fixture
def user_c(client):
    return make_user(client)


def _create(client, user, mode="rapid_10"):
    return client.post(
        "/api/v1/duels", json={"mode": mode, "display_name": "Creator"}, headers=bearer(user)
    ).json()


def _join(client, user, created):
    return client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger"},
        headers=bearer(user),
    )


def _ready(client, duel_id, user):
    return client.post(f"/api/v1/duels/{duel_id}/ready", headers=bearer(user))


def _state(client, duel_id, user):
    return client.get(f"/api/v1/duels/{duel_id}/state", headers=bearer(user))


def _skip_countdown(duel_id):
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET starts_at = ? WHERE duel_id = ?", (past, duel_id))


def _seed_active(client, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    _ready(client, created["duel_id"], user_a)
    _ready(client, created["duel_id"], user_b)
    _skip_countdown(created["duel_id"])
    return created


def _submit(client, duel_id, user, result, source="print(1)"):
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            return client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={"language": "python3", "source_code": source, "stdin": "", "expected_output": "1"},
                headers=bearer(user),
            )


def _events(user, event_type):
    return [e for e in product_events.events_for(subject(user)) if e["event_type"] == event_type]


# ─── Ready flow ───────────────────────────────────────────────────────────────


def test_ready_marks_participant_ready(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    response = _ready(client, created["duel_id"], user_a)
    assert response.status_code == 200
    state = response.json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert me["ready"] is True
    assert opponent["ready"] is False
    assert state["status"] == "waiting"
    assert len(_events(user_a, "duel_ready")) == 1


def test_ready_is_idempotent_single_event(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    _ready(client, created["duel_id"], user_a)
    _ready(client, created["duel_id"], user_a)
    assert len(_events(user_a, "duel_ready")) == 1


def test_both_ready_auto_starts_with_countdown(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    _ready(client, created["duel_id"], user_a)
    state = _ready(client, created["duel_id"], user_b).json()
    assert state["status"] == "active"
    assert state["countdown_started_at"]
    assert state["starts_at"]
    assert state["arena_path"] == f"/arena?duel={created['duel_id']}"
    # Active window = countdown end + mode duration.
    starts = dt.datetime.fromisoformat(state["starts_at"])
    expires = dt.datetime.fromisoformat(state["expires_at"])
    assert (expires - starts) == dt.timedelta(minutes=10)
    assert len(_events(user_a, "duel_started")) == 1
    assert len(_events(user_b, "duel_started")) == 1


def test_start_requires_two_participants(client, catalog, user_a):
    created = _create(client, user_a)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    assert response.status_code == 409
    assert response.json()["error_code"] == "WAITING_FOR_OPPONENT"


def test_start_requires_both_ready(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    assert response.status_code == 409
    assert response.json()["error_code"] == "PLAYERS_NOT_READY"


def test_start_returns_arena_redirect_path(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    _ready(client, created["duel_id"], user_a)
    _ready(client, created["duel_id"], user_b)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start", headers=bearer(user_a))
    assert response.status_code == 200
    assert response.json()["arena_path"] == f"/arena?duel={created['duel_id']}"


# ─── State polling ────────────────────────────────────────────────────────────


def test_state_returns_live_participant_statuses(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    _submit(client, created["duel_id"], user_b, WRONG)
    state = _state(client, created["duel_id"], user_a).json()
    assert state["status"] == "active"
    assert state["server_time"]
    assert state["judging_mode"] == "custom_tests"
    assert state["problem"]["problem_id"]
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert opponent["ready"] is True
    assert opponent["submission_count"] == 1
    assert opponent["wrong_attempts"] == 1
    assert opponent["accepted"] is False
    assert opponent["judging"] is False
    assert opponent["hint_count"] == 0


def test_non_participant_cannot_view_state(client, catalog, user_a, user_c):
    created = _create(client, user_a)
    response = _state(client, created["duel_id"], user_c)
    assert response.status_code == 403


def test_state_requires_auth(client, catalog, user_a):
    created = _create(client, user_a)
    response = client.get(f"/api/v1/duels/{created['duel_id']}/state")
    assert response.status_code == 401


def test_state_has_no_secrets_or_source(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    _submit(client, created["duel_id"], user_a, WRONG, source="SECRET_DUEL_SOURCE_ABC")
    raw = json.dumps(_state(client, created["duel_id"], user_b).json()).lower()
    assert "secret_duel_source_abc" not in raw
    assert "source_code" not in raw
    assert "invite_code" not in raw
    assert "judge0" not in raw
    assert "api_key" not in raw
    assert "admin" not in raw
    assert user_a["api_token"].lower() not in raw
    assert user_b["api_token"].lower() not in raw


def test_open_arena_telemetry(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    r1 = client.post(f"/api/v1/duels/{created['duel_id']}/open-arena", headers=bearer(user_a))
    r2 = client.post(f"/api/v1/duels/{created['duel_id']}/open-arena", headers=bearer(user_a))
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["arena_opened_at"]
    assert r2.json()["arena_opened_at"] == r1.json()["arena_opened_at"]
    assert len(_events(user_a, "duel_arena_opened")) == 1
    state = _state(client, created["duel_id"], user_b).json()
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert opponent["arena_opened"] is True


# ─── Hints ────────────────────────────────────────────────────────────────────


def test_hint_increments_hint_count(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/hint", headers=bearer(user_a))
    assert response.status_code == 200
    body = response.json()
    assert body["hint_number"] == 1
    assert body["hints_used"] == 1
    assert body["hints_remaining"] == 2
    assert body["hint_text"]
    state = _state(client, created["duel_id"], user_a).json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    assert me["hint_count"] == 1
    assert len(_events(user_a, "duel_hint_used")) == 1


def test_hint_only_while_active(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/hint", headers=bearer(user_a))
    assert response.status_code == 409
    assert response.json()["error_code"] == "DUEL_NOT_ACTIVE"


def test_hint_capped_and_no_solution_leak(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    for _ in range(3):
        client.post(f"/api/v1/duels/{created['duel_id']}/hint", headers=bearer(user_a))
    fourth = client.post(f"/api/v1/duels/{created['duel_id']}/hint", headers=bearer(user_a)).json()
    assert fourth["hints_used"] == 3
    assert fourth["hints_remaining"] == 0
    assert len(_events(user_a, "duel_hint_used")) == 3
    # Generic nudges only — never editorial/solution content or code.
    for hint in (fourth["hint_text"],):
        lowered = hint.lower()
        assert "def " not in lowered and "#include" not in lowered
        assert "answer is" not in lowered and "editorial" not in lowered


def test_hints_award_no_xp(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    before = gamification.compute_xp_total(product_events.events_for(subject(user_a)), daily_cap=1000)
    client.post(f"/api/v1/duels/{created['duel_id']}/hint", headers=bearer(user_a))
    after = gamification.compute_xp_total(product_events.events_for(subject(user_a)), daily_cap=1000)
    assert after == before
    assert "duel_hint_used" not in gamification.XP_RULES


# ─── Winner v2 ────────────────────────────────────────────────────────────────


def test_fewer_hints_beats_earlier_accept(client, catalog, user_a, user_b):
    """A accepts first but used a hint; B still has fewer hints, so the duel
    stays open — B's later accept with zero hints wins."""
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint", headers=bearer(user_a))
    response = _submit(client, duel_id, user_a, ACCEPTED)
    assert response.json()["passed"] is True
    assert response.json()["duel"]["status"] == "active"  # not decided yet
    response = _submit(client, duel_id, user_b, ACCEPTED)
    duel = response.json()["duel"]
    assert duel["status"] == "completed"
    assert duel["result_reason"] == "fewer_hints"
    winner = next(p for p in duel["participants"] if p["is_winner"])
    assert winner["display_name"] == account_display_name({"user_id": user_b["user_id"]})


def test_first_accept_wins_when_hints_not_worse(client, catalog, user_a, user_b):
    """A accepts with hints equal to B's (both 0) — decided immediately."""
    created = _seed_active(client, user_a, user_b)
    response = _submit(client, created["duel_id"], user_a, ACCEPTED)
    duel = response.json()["duel"]
    assert duel["status"] == "completed"
    assert duel["result_reason"] == "first_custom_test_pass"
    winner = next(p for p in duel["participants"] if p["is_winner"])
    assert winner["display_name"] == account_display_name({"user_id": user_a["user_id"]})


def test_equal_hints_earlier_accept_wins(client, catalog, user_a, user_b):
    """Both accepted with equal hint counts — earlier accepted_at breaks the tie."""
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    earlier = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=30)).isoformat()
    later = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)).isoformat()
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, hint_count = 2, final_status = 'accepted'"
            " WHERE duel_id = ? AND user_id = ?",
            (later, duel_id, user_a["user_id"]),
        )
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, hint_count = 2, final_status = 'accepted'"
            " WHERE duel_id = ? AND user_id = ?",
            (earlier, duel_id, user_b["user_id"]),
        )
    duels._finalize_duel(duel_id, at_timeout=False)
    duel = duels.get_duel(duel_id)
    assert duel["status"] == "completed"
    assert duel["winner_subject"] == subject(user_b)
    assert duel["result_reason"] == "first_custom_test_pass"


def test_hint_use_can_settle_pending_decision(client, catalog, user_a, user_b):
    """A accepted with 1 hint while B held 0 — when B burns a hint and matches
    A's count, B can no longer win the tie-break, so A wins immediately."""
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint", headers=bearer(user_a))
    _submit(client, duel_id, user_a, ACCEPTED)
    assert _state(client, duel_id, user_b).json()["status"] == "active"
    client.post(f"/api/v1/duels/{duel_id}/hint", headers=bearer(user_b))
    state = _state(client, duel_id, user_b).json()
    assert state["status"] == "completed"
    winner = next(p for p in state["participants"] if p["is_winner"])
    assert winner["display_name"] == account_display_name({"user_id": user_a["user_id"]})
    assert state["result"]["viewer_won"] is False


def test_wrong_attempts_counted(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    _submit(client, created["duel_id"], user_a, WRONG)
    _submit(client, created["duel_id"], user_a, WRONG)
    state = _state(client, created["duel_id"], user_a).json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    assert me["wrong_attempts"] == 2
    assert me["submission_count"] == 2
    assert me["final_status"] == "failed"


def test_lone_accept_wins_at_timeout_despite_more_hints(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint", headers=bearer(user_a))
    _submit(client, duel_id, user_a, ACCEPTED)
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, duel_id))
    state = _state(client, duel_id, user_a).json()
    assert state["status"] == "completed"
    assert state["result"]["viewer_won"] is True
    winner = next(p for p in state["participants"] if p["is_winner"])
    assert winner["display_name"] == account_display_name({"user_id": user_a["user_id"]})


def test_no_accept_expires_draw_and_no_xp_events(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, duel_id))
    state = _state(client, duel_id, user_a).json()
    assert state["status"] == "expired"
    assert state["result"]["is_draw"] is True
    assert state["result"]["xp_awarded"] == 0
    assert not _events(user_a, "duel_completed")
    assert not _events(user_b, "duel_completed")
    assert not _events(user_a, "duel_won")


def test_completion_events_emitted_exactly_once(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    _submit(client, duel_id, user_a, ACCEPTED)
    # Repeated polls / result reads must not re-emit completion events.
    for _ in range(3):
        _state(client, duel_id, user_a)
        _state(client, duel_id, user_b)
        client.get(f"/api/v1/duels/{duel_id}/result", headers=bearer(user_a))
    duels._finalize_duel(duel_id, at_timeout=True)  # direct re-entry is also a no-op
    assert len(_events(user_a, "duel_completed")) == 1
    assert len(_events(user_b, "duel_completed")) == 1
    assert len(_events(user_a, "duel_won")) == 1
    assert len(_events(user_b, "duel_won")) == 0


def test_submit_uses_server_tests_without_player_expected_output(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=ACCEPTED) as run:
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            response = client.post(
                f"/api/v1/duels/{created['duel_id']}/submit",
                json={"language": "python3", "source_code": "print(1)"},
                headers=bearer(user_a),
            )
    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert run.call_args.kwargs["expected_output"] == "1\n"


def test_submit_requires_auth(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    response = client.post(
        f"/api/v1/duels/{created['duel_id']}/submit",
        json={"language": "python3", "source_code": "print(1)", "stdin": "", "expected_output": "1"},
    )
    assert response.status_code == 401


def test_submit_blocked_during_countdown(client, catalog, user_a, user_b):
    created = _create(client, user_a)
    _join(client, user_b, created)
    _ready(client, created["duel_id"], user_a)
    _ready(client, created["duel_id"], user_b)  # auto-start, countdown running
    response = _submit(client, created["duel_id"], user_a, ACCEPTED)
    assert response.status_code == 409
    assert response.json()["error_code"] == "DUEL_COUNTDOWN"


def test_result_includes_hints_time_and_xp(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint", headers=bearer(user_b))
    _submit(client, duel_id, user_a, ACCEPTED)
    state = _state(client, duel_id, user_a).json()
    assert state["status"] == "completed"
    result = state["result"]
    assert result["viewer_won"] is True
    assert result["winner_display_name"] == account_display_name({"user_id": user_a["user_id"]})
    assert result["xp_awarded"] == 25  # 10 completed + 15 won
    me = next(p for p in state["participants"] if p["is_viewer"])
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert me["seconds_to_accept"] is not None
    assert opponent["hint_count"] == 1
    loser_state = _state(client, duel_id, user_b).json()
    assert loser_state["result"]["viewer_won"] is False
    assert loser_state["result"]["xp_awarded"] == 10
