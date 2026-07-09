"""Phase G4.1 live duel room tests: ready flow, state polling, hints, winner v2."""

from __future__ import annotations

import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels, gamification, product_events
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "duels-live-admin-key"
HANDLE_A = "Live-Creator"
HANDLE_B = "Live-Challenger"
HANDLE_C = "Live-Stranger"

SUBJECT_A = f"handle:{HANDLE_A.lower()}"
SUBJECT_B = f"handle:{HANDLE_B.lower()}"

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
    return problems


def _create(client, mode="rapid_10"):
    return client.post(
        f"/api/v1/duels?handle={HANDLE_A}",
        json={"mode": mode, "display_name": "Creator"},
    ).json()


def _join(client, created):
    return client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger", "handle": HANDLE_B},
    )


def _ready(client, duel_id, handle):
    return client.post(f"/api/v1/duels/{duel_id}/ready?handle={handle}")


def _state(client, duel_id, handle):
    return client.get(f"/api/v1/duels/{duel_id}/state?handle={handle}")


def _skip_countdown(duel_id):
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET starts_at = ? WHERE duel_id = ?", (past, duel_id))


def _seed_active(client):
    created = _create(client)
    _join(client, created)
    _ready(client, created["duel_id"], HANDLE_A)
    _ready(client, created["duel_id"], HANDLE_B)
    _skip_countdown(created["duel_id"])
    return created


def _submit(client, duel_id, handle, result, source="print(1)"):
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            return client.post(
                f"/api/v1/duels/{duel_id}/submit?handle={handle}",
                json={"language": "python3", "source_code": source, "stdin": "", "expected_output": "1"},
            )


def _events(handle, event_type):
    return [e for e in product_events.events_for(f"handle:{handle.lower()}") if e["event_type"] == event_type]


# ─── Ready flow ───────────────────────────────────────────────────────────────


def test_ready_marks_participant_ready(client, catalog):
    created = _create(client)
    _join(client, created)
    response = _ready(client, created["duel_id"], HANDLE_A)
    assert response.status_code == 200
    state = response.json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert me["ready"] is True
    assert opponent["ready"] is False
    assert state["status"] == "waiting"
    assert len(_events(HANDLE_A, "duel_ready")) == 1


def test_ready_is_idempotent_single_event(client, catalog):
    created = _create(client)
    _join(client, created)
    _ready(client, created["duel_id"], HANDLE_A)
    _ready(client, created["duel_id"], HANDLE_A)
    assert len(_events(HANDLE_A, "duel_ready")) == 1


def test_both_ready_auto_starts_with_countdown(client, catalog):
    created = _create(client)
    _join(client, created)
    _ready(client, created["duel_id"], HANDLE_A)
    state = _ready(client, created["duel_id"], HANDLE_B).json()
    assert state["status"] == "active"
    assert state["countdown_started_at"]
    assert state["starts_at"]
    assert state["arena_path"] == f"/arena?duel={created['duel_id']}"
    # Active window = countdown end + mode duration.
    starts = dt.datetime.fromisoformat(state["starts_at"])
    expires = dt.datetime.fromisoformat(state["expires_at"])
    assert (expires - starts) == dt.timedelta(minutes=10)
    assert len(_events(HANDLE_A, "duel_started")) == 1
    assert len(_events(HANDLE_B, "duel_started")) == 1


def test_start_requires_two_participants(client, catalog):
    created = _create(client)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    assert response.status_code == 409
    assert response.json()["error_code"] == "WAITING_FOR_OPPONENT"


def test_start_requires_both_ready(client, catalog):
    created = _create(client)
    _join(client, created)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    assert response.status_code == 409
    assert response.json()["error_code"] == "PLAYERS_NOT_READY"


def test_start_returns_arena_redirect_path(client, catalog):
    created = _create(client)
    _join(client, created)
    _ready(client, created["duel_id"], HANDLE_A)
    _ready(client, created["duel_id"], HANDLE_B)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/start?handle={HANDLE_A}")
    assert response.status_code == 200
    assert response.json()["arena_path"] == f"/arena?duel={created['duel_id']}"


# ─── State polling ────────────────────────────────────────────────────────────


def test_state_returns_live_participant_statuses(client, catalog):
    created = _seed_active(client)
    _submit(client, created["duel_id"], HANDLE_B, WRONG)
    state = _state(client, created["duel_id"], HANDLE_A).json()
    assert state["status"] == "active"
    assert state["server_time"]
    assert state["judging_mode"] == "sample"
    assert state["problem"]["problem_id"]
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert opponent["ready"] is True
    assert opponent["submission_count"] == 1
    assert opponent["wrong_attempts"] == 1
    assert opponent["accepted"] is False
    assert opponent["judging"] is False
    assert opponent["hint_count"] == 0


def test_non_participant_cannot_view_state(client, catalog):
    created = _create(client)
    response = _state(client, created["duel_id"], HANDLE_C)
    assert response.status_code == 403


def test_state_has_no_secrets_or_source(client, catalog):
    created = _seed_active(client)
    _submit(client, created["duel_id"], HANDLE_A, WRONG, source="SECRET_DUEL_SOURCE_ABC")
    raw = json.dumps(_state(client, created["duel_id"], HANDLE_B).json()).lower()
    assert "secret_duel_source_abc" not in raw
    assert "source_code" not in raw
    assert "invite_code" not in raw
    assert "judge0" not in raw
    assert "api_key" not in raw
    assert "admin" not in raw


def test_open_arena_telemetry(client, catalog):
    created = _seed_active(client)
    r1 = client.post(f"/api/v1/duels/{created['duel_id']}/open-arena?handle={HANDLE_A}")
    r2 = client.post(f"/api/v1/duels/{created['duel_id']}/open-arena?handle={HANDLE_A}")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["arena_opened_at"]
    assert r2.json()["arena_opened_at"] == r1.json()["arena_opened_at"]
    assert len(_events(HANDLE_A, "duel_arena_opened")) == 1
    state = _state(client, created["duel_id"], HANDLE_B).json()
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert opponent["arena_opened"] is True


# ─── Hints ────────────────────────────────────────────────────────────────────


def test_hint_increments_hint_count(client, catalog):
    created = _seed_active(client)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/hint?handle={HANDLE_A}")
    assert response.status_code == 200
    body = response.json()
    assert body["hint_number"] == 1
    assert body["hints_used"] == 1
    assert body["hints_remaining"] == 2
    assert body["hint_text"]
    state = _state(client, created["duel_id"], HANDLE_A).json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    assert me["hint_count"] == 1
    assert len(_events(HANDLE_A, "duel_hint_used")) == 1


def test_hint_only_while_active(client, catalog):
    created = _create(client)
    _join(client, created)
    response = client.post(f"/api/v1/duels/{created['duel_id']}/hint?handle={HANDLE_A}")
    assert response.status_code == 409
    assert response.json()["error_code"] == "DUEL_NOT_ACTIVE"


def test_hint_capped_and_no_solution_leak(client, catalog):
    created = _seed_active(client)
    for _ in range(3):
        client.post(f"/api/v1/duels/{created['duel_id']}/hint?handle={HANDLE_A}")
    fourth = client.post(f"/api/v1/duels/{created['duel_id']}/hint?handle={HANDLE_A}").json()
    assert fourth["hints_used"] == 3
    assert fourth["hints_remaining"] == 0
    assert len(_events(HANDLE_A, "duel_hint_used")) == 3
    # Generic nudges only — never editorial/solution content or code.
    for hint in (fourth["hint_text"],):
        lowered = hint.lower()
        assert "def " not in lowered and "#include" not in lowered
        assert "answer is" not in lowered and "editorial" not in lowered


def test_hints_award_no_xp(client, catalog):
    created = _seed_active(client)
    before = gamification.compute_xp_total(
        product_events.events_for(SUBJECT_A), daily_cap=1000
    )
    client.post(f"/api/v1/duels/{created['duel_id']}/hint?handle={HANDLE_A}")
    after = gamification.compute_xp_total(
        product_events.events_for(SUBJECT_A), daily_cap=1000
    )
    assert after == before
    assert "duel_hint_used" not in gamification.XP_RULES


# ─── Winner v2 ────────────────────────────────────────────────────────────────


def test_fewer_hints_beats_earlier_accept(client, catalog):
    """A accepts first but used a hint; B still has fewer hints, so the duel
    stays open — B's later accept with zero hints wins."""
    created = _seed_active(client)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint?handle={HANDLE_A}")
    response = _submit(client, duel_id, HANDLE_A, ACCEPTED)
    assert response.json()["passed"] is True
    assert response.json()["duel"]["status"] == "active"  # not decided yet
    response = _submit(client, duel_id, HANDLE_B, ACCEPTED)
    duel = response.json()["duel"]
    assert duel["status"] == "completed"
    assert duel["result_reason"] == "fewer_hints"
    winner = next(p for p in duel["participants"] if p["is_winner"])
    assert winner["handle"] == HANDLE_B.lower()


def test_first_accept_wins_when_hints_not_worse(client, catalog):
    """A accepts with hints equal to B's (both 0) — decided immediately."""
    created = _seed_active(client)
    response = _submit(client, created["duel_id"], HANDLE_A, ACCEPTED)
    duel = response.json()["duel"]
    assert duel["status"] == "completed"
    assert duel["result_reason"] == "first_accepted"
    winner = next(p for p in duel["participants"] if p["is_winner"])
    assert winner["handle"] == HANDLE_A.lower()


def test_equal_hints_earlier_accept_wins(client, catalog):
    """Both accepted with equal hint counts — earlier accepted_at breaks the tie."""
    created = _seed_active(client)
    duel_id = created["duel_id"]
    earlier = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=30)).isoformat()
    later = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)).isoformat()
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, hint_count = 2, final_status = 'accepted'"
            " WHERE duel_id = ? AND subject = ?",
            (later, duel_id, SUBJECT_A),
        )
        conn.execute(
            "UPDATE duel_participants SET accepted_at = ?, hint_count = 2, final_status = 'accepted'"
            " WHERE duel_id = ? AND subject = ?",
            (earlier, duel_id, SUBJECT_B),
        )
    duels._finalize_duel(duel_id, at_timeout=False)
    duel = duels.get_duel(duel_id)
    assert duel["status"] == "completed"
    assert duel["winner_subject"] == SUBJECT_B
    assert duel["result_reason"] == "first_accepted"


def test_hint_use_can_settle_pending_decision(client, catalog):
    """A accepted with 1 hint while B held 0 — when B burns a hint and matches
    A's count, B can no longer win the tie-break, so A wins immediately."""
    created = _seed_active(client)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint?handle={HANDLE_A}")
    _submit(client, duel_id, HANDLE_A, ACCEPTED)
    assert _state(client, duel_id, HANDLE_B).json()["status"] == "active"
    client.post(f"/api/v1/duels/{duel_id}/hint?handle={HANDLE_B}")
    state = _state(client, duel_id, HANDLE_B).json()
    assert state["status"] == "completed"
    winner = next(p for p in state["participants"] if p["is_winner"])
    assert winner["handle"] == HANDLE_A.lower()
    assert state["result"]["viewer_won"] is False


def test_wrong_attempts_counted(client, catalog):
    created = _seed_active(client)
    _submit(client, created["duel_id"], HANDLE_A, WRONG)
    _submit(client, created["duel_id"], HANDLE_A, WRONG)
    state = _state(client, created["duel_id"], HANDLE_A).json()
    me = next(p for p in state["participants"] if p["is_viewer"])
    assert me["wrong_attempts"] == 2
    assert me["submission_count"] == 2
    assert me["final_status"] == "failed"


def test_lone_accept_wins_at_timeout_despite_more_hints(client, catalog):
    created = _seed_active(client)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint?handle={HANDLE_A}")
    _submit(client, duel_id, HANDLE_A, ACCEPTED)
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, duel_id))
    state = _state(client, duel_id, HANDLE_A).json()
    assert state["status"] == "completed"
    assert state["result"]["viewer_won"] is True
    winner = next(p for p in state["participants"] if p["is_winner"])
    assert winner["handle"] == HANDLE_A.lower()


def test_no_accept_expires_draw_and_no_xp_events(client, catalog):
    created = _seed_active(client)
    duel_id = created["duel_id"]
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET expires_at = ? WHERE duel_id = ?", (past, duel_id))
    state = _state(client, duel_id, HANDLE_A).json()
    assert state["status"] == "expired"
    assert state["result"]["is_draw"] is True
    assert state["result"]["xp_awarded"] == 0
    assert not _events(HANDLE_A, "duel_completed")
    assert not _events(HANDLE_B, "duel_completed")
    assert not _events(HANDLE_A, "duel_won")


def test_completion_events_emitted_exactly_once(client, catalog):
    created = _seed_active(client)
    duel_id = created["duel_id"]
    _submit(client, duel_id, HANDLE_A, ACCEPTED)
    # Repeated polls / result reads must not re-emit completion events.
    for _ in range(3):
        _state(client, duel_id, HANDLE_A)
        _state(client, duel_id, HANDLE_B)
        client.get(f"/api/v1/duels/{duel_id}/result?handle={HANDLE_A}")
    duels._finalize_duel(duel_id, at_timeout=True)  # direct re-entry is also a no-op
    assert len(_events(HANDLE_A, "duel_completed")) == 1
    assert len(_events(HANDLE_B, "duel_completed")) == 1
    assert len(_events(HANDLE_A, "duel_won")) == 1
    assert len(_events(HANDLE_B, "duel_won")) == 0


def test_submit_requires_expected_output(client, catalog):
    """Without an expected output any running program would count as accepted —
    that is no basis for a duel verdict, so the API refuses it."""
    created = _seed_active(client)
    response = client.post(
        f"/api/v1/duels/{created['duel_id']}/submit?handle={HANDLE_A}",
        json={"language": "python3", "source_code": "print(1)", "stdin": ""},
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "EXPECTED_OUTPUT_REQUIRED"


def test_submit_blocked_during_countdown(client, catalog):
    created = _create(client)
    _join(client, created)
    _ready(client, created["duel_id"], HANDLE_A)
    _ready(client, created["duel_id"], HANDLE_B)  # auto-start, countdown running
    response = _submit(client, created["duel_id"], HANDLE_A, ACCEPTED)
    assert response.status_code == 409
    assert response.json()["error_code"] == "DUEL_COUNTDOWN"


def test_result_includes_hints_time_and_xp(client, catalog):
    created = _seed_active(client)
    duel_id = created["duel_id"]
    client.post(f"/api/v1/duels/{duel_id}/hint?handle={HANDLE_B}")
    _submit(client, duel_id, HANDLE_A, ACCEPTED)
    state = _state(client, duel_id, HANDLE_A).json()
    assert state["status"] == "completed"
    result = state["result"]
    assert result["viewer_won"] is True
    assert result["winner_display_name"] == "Creator"
    assert result["xp_awarded"] == 25  # 10 completed + 15 won
    me = next(p for p in state["participants"] if p["is_viewer"])
    opponent = next(p for p in state["participants"] if not p["is_viewer"])
    assert me["seconds_to_accept"] is not None
    assert opponent["hint_count"] == 1
    loser_state = _state(client, duel_id, HANDLE_B).json()
    assert loser_state["result"]["viewer_won"] is False
    assert loser_state["result"]["xp_awarded"] == 10
