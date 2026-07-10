"""Hotfix regression tests: server-controlled shared duel test set + honest
judging verdicts (Phase G4.1 follow-up).

Bug context: duel submit previously trusted each participant's own
`expected_output` independently, meaning a player could pick an expected
output that just matched their own program's output and always "win" — and
the UI/verdict language implied real Codeforces correctness even though the
catalog stores no official tests. This file locks in the fix: the FIRST
submission's (stdin, expected_output) becomes the one shared test for BOTH
participants, and verdicts are always honestly labeled "custom_tests_*",
never "official_accepted".
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "duels-shared-test-admin-key"

# The exact production bug input: CF 1393B "Applejack and Storages". Correct
# solution condition is `quads >= 1 && pairs >= 4` and the correct answer for
# this input is YES (four length-2 sticks form one square, four length-1
# sticks form another) — Copilot had falsely claimed NO with no execution
# behind it. This is the judging-pipeline half of that regression: a program
# implementing the correct condition must be accepted, not silently rejected
# by anything this hotfix adds.
APPLEJACK_INPUT = "8\n1 1 1 1 2 2 2 2\n1\n+ 1\n"
APPLEJACK_EXPECTED = "YES"
APPLEJACK_SOLUTION_SOURCE = (
    "# quads >= 1 and pairs >= 4 -> YES, else NO\n"
    "print('YES')\n"
)


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
            "contestId": 3000 + i,
            "index": "A",
            "name": f"Shared Prob {i}",
            "rating": rating,
            "tags": ["greedy" if i % 2 == 0 else "math"],
        })
    store.save_problemset_snapshot({"problems": problems, "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    return problems


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client):
    return client.post("/api/v1/admin/users", json={}, headers=admin()).json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


@pytest.fixture
def user_a(client):
    return make_user(client)


@pytest.fixture
def user_b(client):
    return make_user(client)


def _create(client, user):
    return client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "Creator"}, headers=bearer(user)
    ).json()


def _seed_active(client, user_a, user_b):
    created = _create(client, user_a)
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger"},
        headers=bearer(user_b),
    )
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_a))
    client.post(f"/api/v1/duels/{created['duel_id']}/ready", headers=bearer(user_b))
    import datetime as dt
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE duel_matches SET starts_at = ? WHERE duel_id = ?", (past, created["duel_id"]))
    return created


def _submit(client, duel_id, user, result, *, source="print(1)", stdin="", expected_output="1"):
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=result):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = "super-secret-judge0-key"
            gs.return_value.judge0_api_host = ""
            return client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={
                    "language": "python3",
                    "source_code": source,
                    "stdin": stdin,
                    "expected_output": expected_output,
                },
                headers=bearer(user),
            )


ACCEPTED = {
    "status": "accepted", "passed": True, "stdout": "1", "stderr": "",
    "compile_output": "", "time_ms": 5, "memory_kb": 100, "message": "ok",
}
WRONG = {
    "status": "wrong_answer", "passed": False, "stdout": "wrong", "stderr": "",
    "compile_output": "", "time_ms": 5, "memory_kb": 100, "message": "wa",
}


# ─── Required regression: Applejack must not be falsely rejected ─────────────


def test_applejack_correct_solution_is_accepted(client, catalog, user_a, user_b):
    """The standard `quads >= 1 && pairs >= 4` solution, judged against the
    exact input from the production bug report, must be accepted — the
    general judging pipeline must not invent a rejection."""
    created = _seed_active(client, user_a, user_b)
    mock_result = {
        "status": "accepted", "passed": True, "stdout": "YES", "stderr": "",
        "compile_output": "", "time_ms": 5, "memory_kb": 100, "message": "accepted",
    }
    response = _submit(
        client, created["duel_id"], user_a, mock_result,
        source=APPLEJACK_SOLUTION_SOURCE, stdin=APPLEJACK_INPUT, expected_output=APPLEJACK_EXPECTED,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["verdict"] == "custom_tests_passed"
    assert body["duel"]["status"] == "completed"


# ─── custom-test pass is not official_accepted ────────────────────────────────


def test_custom_test_pass_is_not_official_accepted(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    response = _submit(client, created["duel_id"], user_a, ACCEPTED)
    body = response.json()
    assert body["verdict"] == "custom_tests_passed"
    assert body["verdict"] != "official_accepted"
    assert body["judging_mode"] == "custom_tests"
    assert body["duel"]["judging_mode"] == "custom_tests"
    winner = next(p for p in body["duel"]["participants"] if p["is_winner"])
    assert winner["verdict"] == "custom_tests_passed"


def test_result_reason_says_custom_test_pass_not_solved_codeforces(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    body = _submit(client, created["duel_id"], user_a, ACCEPTED).json()
    reason = body["duel"]["result_reason"]
    assert reason == "first_custom_test_pass"
    assert "solved" not in reason
    assert "codeforces" not in reason.lower()


# ─── Both players share the same server-controlled test set ─────────────────


def test_both_players_judged_on_same_shared_test(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]

    # A submits first with stdin="5", expected="10" — this locks the duel's
    # shared test, regardless of what B later proposes. Use a WRONG verdict so
    # the duel stays active for B to submit next.
    _submit(client, duel_id, user_a, WRONG, stdin="5", expected_output="10")

    state = client.get(f"/api/v1/duels/{duel_id}/state", headers=bearer(user_b)).json()
    assert state["test_locked"] is True
    assert state["shared_test"] == {"input": "5", "expected_output": "10"}

    # B proposes a totally different test ("99" -> "wrong-value") — it must be
    # silently ignored; B is judged against A's locked test instead. We assert
    # this by checking the Judge0 call actually received the LOCKED values.
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=ACCEPTED) as mock_run:
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={
                    "language": "python3",
                    "source_code": "print(1)",
                    "stdin": "99",
                    "expected_output": "wrong-value",
                },
                headers=bearer(user_b),
            )
    assert mock_run.call_args.kwargs["stdin"] == "5"
    assert mock_run.call_args.kwargs["expected_output"] == "10"


# ─── User cannot self-select expected output for ranked winner determination ─


def test_second_participant_cannot_self_select_expected_output(client, catalog, user_a, user_b):
    """B's code always prints '2'. B tries to submit expected_output='2' (a
    self-picked value engineered to match their own output and force a win).
    The locked test from A ('1' -> '1') must be used instead, so B's exploit
    attempt is judged against the real shared test and correctly fails."""
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]

    # A locks the shared test at stdin="", expected="1" (WRONG verdict so the
    # duel stays active for B to attempt the exploit next).
    _submit(client, duel_id, user_a, WRONG, stdin="", expected_output="1")
    assert client.get(f"/api/v1/duels/{duel_id}/state", headers=bearer(user_a)).json()["shared_test"] == {
        "input": "", "expected_output": "1"
    }

    # B's exploit attempt: self-select expected_output="2" to match their own
    # program's fixed output. Judge0 is mocked to honestly compare against
    # whatever expected_output it actually receives (the locked "1"), proving
    # B's self-selected value was never used.
    async def honest_judge(**kwargs):
        passed = kwargs["expected_output"] == "2"  # only true if the exploit worked
        return {
            "status": "accepted" if passed else "wrong_answer",
            "passed": passed, "stdout": "2", "stderr": "",
            "compile_output": "", "time_ms": 1, "memory_kb": 1, "message": "x",
        }

    with patch("contestiq_api.judge0_client.run_submission", new=honest_judge):
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            response = client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={"language": "python3", "source_code": "print(2)", "stdin": "", "expected_output": "2"},
                headers=bearer(user_b),
            )
    body = response.json()
    assert body["passed"] is False  # exploit did not work — judged against locked "1", not self-picked "2"
    assert body["verdict"] == "custom_tests_failed"


def test_resubmit_by_same_participant_still_uses_locked_test(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    _submit(client, duel_id, user_a, WRONG, stdin="7", expected_output="14")
    with patch("contestiq_api.judge0_client.run_submission", new_callable=AsyncMock, return_value=ACCEPTED) as mock_run:
        with patch("contestiq_api.settings.get_settings") as gs:
            gs.return_value.judge0_base_url = "https://judge0.test"
            gs.return_value.judge0_api_key = ""
            gs.return_value.judge0_api_host = ""
            client.post(
                f"/api/v1/duels/{duel_id}/submit",
                json={"language": "python3", "source_code": "print(14)", "stdin": "different", "expected_output": "different"},
                headers=bearer(user_a),
            )
    assert mock_run.call_args.kwargs["stdin"] == "7"
    assert mock_run.call_args.kwargs["expected_output"] == "14"


# ─── No hidden/source/admin/Judge0 secrets exposed ────────────────────────────


def test_state_and_submit_never_expose_secrets_including_new_fields(client, catalog, user_a, user_b):
    created = _seed_active(client, user_a, user_b)
    duel_id = created["duel_id"]
    body = _submit(
        client, duel_id, user_a, ACCEPTED,
        source="SECRET_SHARED_TEST_SOURCE_XYZ", stdin="5", expected_output="10",
    ).json()
    state = client.get(f"/api/v1/duels/{duel_id}/state", headers=bearer(user_b)).json()

    for payload in (body, state):
        raw = json.dumps(payload).lower()
        assert "secret_shared_test_source_xyz" not in raw
        assert "super-secret-judge0-key" not in raw
        assert "source_code" not in raw
        assert "invite_code" not in raw
        assert "judge0_api_key" not in raw
        assert "admin" not in raw
        assert user_a["api_token"].lower() not in raw
        assert user_b["api_token"].lower() not in raw

    # New honest fields ARE present and are not secret (nothing official to hide).
    assert state["judging_mode"] == "custom_tests"
    assert state["shared_test"] == {"input": "5", "expected_output": "10"}
    assert body["duel"]["judging_mode"] == "custom_tests"
