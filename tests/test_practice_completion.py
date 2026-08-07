"""Authoritative Solo-practice completion, security, and idempotency tests."""

from __future__ import annotations

import concurrent.futures
import json
import threading
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "practice-admin-key"

PROBLEMS = (
    {"contestId": 4100, "index": "A", "name": "Current", "rating": 1000, "tags": ["math"]},
    {"contestId": 4101, "index": "A", "name": "Near Math", "rating": 1100, "tags": ["math"]},
    {"contestId": 4102, "index": "A", "name": "Far Math", "rating": 1400, "tags": ["math"]},
    {"contestId": 4103, "index": "A", "name": "Greedy", "rating": 1050, "tags": ["greedy"]},
    {"contestId": 4104, "index": "A", "name": "No Pack", "rating": 1150, "tags": ["math"]},
)


def verdict(status: str, status_id: int | None, *, passed: bool = False) -> dict:
    return {
        "status": status,
        "status_id": status_id,
        "passed": passed,
        "stdout": "safe output",
        "stderr": "safe stderr" if status == "runtime_error" else "",
        "compile_output": "safe compiler output" if status == "compilation_error" else "",
        "time_ms": 7,
        "memory_kb": 128,
        "message": status,
    }


ACCEPTED = verdict("accepted", 3, passed=True)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "practice.db"))
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://fake-judge0")
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def practice_world():
    store.save_problemset_snapshot({"problems": list(PROBLEMS), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    for problem in PROBLEMS[:-1]:
        problem_id = f"{problem['contestId']}{problem['index']}"
        assert duels.upsert_duel_problem_pack(
            {
                "pack_id": f"practice-{problem_id}-v1",
                "problem_id": problem_id,
                "version": 1,
                "statement_summary": f"Reviewed task {problem_id}.",
                "input_format": "A server-owned private input.",
                "output_format": "Print the required answer.",
                "constraints_text": "Reviewed finite constraints.",
                "sample_tests": [{"input": "sample\n", "output": "sample answer\n"}],
                "judge_tests": [
                    {
                        "input": f"PRIVATE_INPUT_{problem_id}_ONE\n",
                        "expected_output": f"PRIVATE_EXPECTED_{problem_id}_ONE\n",
                    },
                    {
                        "input": f"PRIVATE_INPUT_{problem_id}_TWO\n",
                        "expected_output": f"PRIVATE_EXPECTED_{problem_id}_TWO\n",
                    },
                ],
            }
        )
    return PROBLEMS


def admin() -> dict[str, str]:
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client: TestClient) -> dict:
    return client.post("/api/v1/admin/users", json={}, headers=admin()).json()


def bearer(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['api_token']}"}


def payload(
    *,
    problem_id: str = "4100A",
    request_id: str = "request-1",
    **updates,
) -> dict:
    data = {
        "problem_id": problem_id,
        "language": "python3",
        "source_code": "print(1)",
        "request_id": request_id,
        "source": "direct_arena",
        "visible_problem_ids": [],
        "completed_problem_ids": [],
    }
    data.update(updates)
    return data


def table_count(table: str) -> int:
    with store.connect() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def accepted_mock(test_count: int = 2) -> AsyncMock:
    return AsyncMock(side_effect=[dict(ACCEPTED) for _ in range(test_count)])


def test_guest_accepted_is_authoritative_but_nonpersistent(client, practice_world):
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post("/api/v1/practice/submit", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["status_id"] == 3
    assert body["judging_mode"] == "solvex_practice"
    assert body["judged"] is True
    assert body["passed"] is True
    assert body["completion"] == {
        "completion_id": None,
        "persistent": False,
        "recorded": False,
        "already_completed": False,
        "completed_at": body["completion"]["completed_at"],
        "xp_awarded": 0,
        "attempt_count": 1,
        "source": "direct_arena",
    }
    assert body["progress"] is None
    assert table_count("practice_submissions") == 0
    assert table_count("practice_completions") == 0
    assert table_count("practice_continuations") == 0
    assert table_count("product_events") == 0


def test_accepted_records_completion_event_progress_and_safe_attempt(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )

    assert response.status_code == 200
    body = response.json()
    completion = body["completion"]
    assert completion["persistent"] is True
    assert completion["recorded"] is True
    assert completion["already_completed"] is False
    assert completion["xp_awarded"] == 25
    assert completion["attempt_count"] == 1
    assert body["progress"]["xp_total"] == 25
    assert body["progress"]["streak"] == 1
    assert body["progress"]["daily_goal"]["completed_count"] == 1
    assert body["next_problem"]["problem_id"] != "4100A"
    assert body["next_problem"]["queue_item_id"] == body["next_problem"]["recommendation_id"]

    with store.connect() as conn:
        attempt = dict(conn.execute("SELECT * FROM practice_submissions").fetchone())
        stored_completion = dict(conn.execute("SELECT * FROM practice_completions").fetchone())
        event = dict(conn.execute("SELECT * FROM product_events").fetchone())
    assert attempt["user_id"] == user["user_id"]
    assert attempt["problem_id"] == "4100A"
    assert attempt["pack_id"] == "practice-4100A-v1"
    assert attempt["pack_version"] == 1
    assert len(attempt["test_set_hash"]) == 64
    assert attempt["source_hash"] != "print(1)"
    assert "print(1)" not in json.dumps(attempt)
    assert stored_completion["completion_id"] == completion["completion_id"]
    assert event["event_id"] == completion["completion_id"]
    assert event["event_type"] == "practice_problem_completed"

    with store.connect() as conn:
        canonical = dict(
            conn.execute(
                "SELECT * FROM problem_completions WHERE completion_id = ?",
                (completion["completion_id"],),
            ).fetchone()
        )
    assert canonical["completion_source"] == "solvex_practice_judge"
    assert canonical["is_historical"] == 0
    assert canonical["xp_awarded"] == 25
    assert canonical["assigned_at"]


def test_submit_uses_all_locked_pack_tests_and_no_caller_oracle(client, practice_world):
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json={**payload(), "stdin": "FORGED", "expected_output": "FORGED"},
        )
    # Unknown oracle fields are rejected rather than forwarded.
    assert response.status_code == 422
    assert judge.await_count == 0

    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post("/api/v1/practice/submit", json=payload())
    assert response.status_code == 200
    assert judge.await_count == 2
    calls = judge.await_args_list
    assert [call.kwargs["stdin"] for call in calls] == [
        "PRIVATE_INPUT_4100A_ONE\n",
        "PRIVATE_INPUT_4100A_TWO\n",
    ]
    assert [call.kwargs["expected_output"] for call in calls] == [
        "PRIVATE_EXPECTED_4100A_ONE\n",
        "PRIVATE_EXPECTED_4100A_TWO\n",
    ]


@pytest.mark.parametrize(
    ("result", "expected_status", "judged"),
    [
        (verdict("wrong_answer", 4), "wrong_answer", True),
        (verdict("compilation_error", 6), "compilation_error", True),
        (verdict("runtime_error", 11), "runtime_error", True),
        (verdict("time_limit", 5), "time_limit", True),
        (verdict("memory_limit", 12), "memory_limit", True),
        (verdict("error", 13), "service_error", False),
    ],
)
def test_nonaccepted_and_service_verdicts_never_complete(
    client, practice_world, result, expected_status, judged
):
    user = make_user(client)
    judge = AsyncMock(return_value=result)
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == expected_status
    assert body["judged"] is judged
    assert body["passed"] is False
    assert body["completion"] is None
    assert body["next_problem"] is None
    assert body["progress"]["xp_total"] == 0
    assert body["progress"]["streak"] == 0
    assert body["progress"]["daily_goal"]["completed_count"] == 0
    assert table_count("practice_submissions") == 1
    assert table_count("practice_completions") == 0
    assert table_count("practice_continuations") == 0
    assert table_count("product_events") == 0


def test_compiler_diagnostics_and_source_echo_are_never_persisted(
    client, practice_world
):
    user = make_user(client)
    source_token = "SOURCE_ECHO_MUST_NOT_PERSIST"
    diagnostic_token = "COMPILER_DIAGNOSTIC_MUST_NOT_PERSIST"
    compilation_error = verdict("compilation_error", 6)
    compilation_error["compile_output"] = (
        f"main.cpp:1: error: {diagnostic_token}\n"
        f"1 | {source_token}\n"
    )
    with patch(
        "contestiq_api.judge0_client.run_submission",
        AsyncMock(return_value=compilation_error),
    ):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(source_code=source_token),
            headers=bearer(user),
        )

    assert response.status_code == 200
    assert response.json()["status"] == "compilation_error"
    assert response.json()["compile_output"] == ""
    with store.connect() as conn:
        attempt = dict(conn.execute("SELECT * FROM practice_submissions").fetchone())
    assert "compile_output_excerpt" not in attempt
    assert "stderr_excerpt" not in attempt
    persisted = json.dumps(attempt)
    assert source_token not in persisted
    assert diagnostic_token not in persisted


def test_judge_transport_failure_is_neutral_and_safe(client, practice_world):
    user = make_user(client)
    judge = AsyncMock(side_effect=RuntimeError("secret upstream detail"))
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    body = response.json()
    assert body["status"] == "service_error"
    assert body["status_id"] is None
    assert body["judged"] is False
    assert "secret upstream detail" not in json.dumps(body)
    assert table_count("practice_completions") == 0
    assert table_count("product_events") == 0


def test_disconnected_submission_is_canceled_without_judging_or_completion(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with (
        patch("contestiq_api.judge0_client.run_submission", judge),
        patch(
            "starlette.requests.Request.is_disconnected",
            AsyncMock(return_value=True),
        ),
    ):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    body = response.json()
    assert body["status"] == "canceled"
    assert body["judged"] is False
    assert body["completion"] is None
    assert judge.await_count == 0
    assert table_count("practice_submissions") == 1
    assert table_count("practice_completions") == 0
    assert table_count("product_events") == 0


def test_disconnect_after_last_test_still_prevents_completion(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    disconnected = AsyncMock(side_effect=[False, False, True])
    with (
        patch("contestiq_api.judge0_client.run_submission", judge),
        patch("starlette.requests.Request.is_disconnected", disconnected),
    ):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    assert response.json()["status"] == "canceled"
    assert judge.await_count == 2
    assert table_count("practice_completions") == 0
    assert table_count("practice_continuations") == 0
    assert table_count("product_events") == 0


def test_generic_execute_acceptance_never_completes(client, practice_world):
    generic = AsyncMock(return_value=dict(ACCEPTED))
    with patch("contestiq_api.routes.execute.run_submission", generic):
        response = client.post(
            "/api/execute",
            json={
                "language": "python3",
                "source_code": "print(1)",
                "stdin": "caller input",
                "expected_output": "caller output",
                "problem_key": "4100A",
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert table_count("practice_submissions") == 0
    assert table_count("practice_completions") == 0


def test_same_request_replay_is_fully_idempotent(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
        second = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert judge.await_count == 2
    assert table_count("practice_submissions") == 1
    assert table_count("practice_completions") == 1
    assert table_count("practice_continuations") == 1
    assert table_count("product_events") == 1


def test_finalized_replay_does_not_depend_on_current_pack_state(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_problem_packs SET active = 0 WHERE problem_id = '4100A'"
        )
    with patch("contestiq_api.judge0_client.run_submission", judge):
        replay = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert judge.await_count == 2


def test_new_accepted_attempt_preserves_history_without_duplicate_rewards(client, practice_world):
    user = make_user(client)
    judge = accepted_mock(test_count=4)
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
        second = client.post(
            "/api/v1/practice/submit",
            json=payload(request_id="request-2"),
            headers=bearer(user),
        )
    first_body, second_body = first.json(), second.json()
    assert first_body["completion"]["xp_awarded"] == 25
    assert second_body["completion"]["recorded"] is False
    assert second_body["completion"]["already_completed"] is True
    assert second_body["completion"]["xp_awarded"] == 0
    assert second_body["completion"]["attempt_count"] == 2
    assert second_body["next_problem"] == first_body["next_problem"]
    assert table_count("practice_submissions") == 2
    assert table_count("practice_completions") == 1
    assert table_count("practice_continuations") == 1
    assert table_count("product_events") == 1


def test_distinct_completions_each_award_25_until_daily_cap(client, practice_world):
    user = make_user(client)
    judge = accepted_mock(test_count=6)
    awards = []
    with patch("contestiq_api.judge0_client.run_submission", judge):
        for index, problem_id in enumerate(("4100A", "4101A", "4102A"), start=1):
            body = client.post(
                "/api/v1/practice/submit",
                json=payload(problem_id=problem_id, request_id=f"completion-{index}"),
                headers=bearer(user),
            ).json()
            awards.append(body["completion"]["xp_awarded"])
    assert awards == [25, 25, 0]  # free-plan UTC daily cap is 50
    progress = client.get("/api/v1/practice/progress", headers=bearer(user)).json()
    assert progress["total_completed"] == 3
    assert table_count("product_events") == 3
    from contestiq_api import gamification, product_events

    events = product_events.events_for_account(user["user_id"])
    assert gamification.compute_xp_total(events, daily_cap=50) == 50
    assert gamification.compute_xp_total(events, daily_cap=150) == 75


def test_concurrent_completions_near_cap_report_one_deterministic_award(
    client, practice_world
):
    user = make_user(client)
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        initial = client.post(
            "/api/v1/practice/submit",
            json=payload(problem_id="4100A", request_id="cap-initial"),
            headers=bearer(user),
        ).json()
    assert initial["completion"]["xp_awarded"] == 25

    barrier = threading.Barrier(2)

    async def synchronized_accepted(**_kwargs):
        barrier.wait(timeout=10)
        return dict(ACCEPTED)

    def complete(problem_id: str, request_id: str) -> dict:
        with TestClient(client.app) as worker:
            response = worker.post(
                "/api/v1/practice/submit",
                json=payload(problem_id=problem_id, request_id=request_id),
                headers=bearer(user),
            )
        assert response.status_code == 200
        return response.json()

    with patch("contestiq_api.judge0_client.run_submission", synchronized_accepted):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(complete, "4101A", "cap-concurrent-1"),
                executor.submit(complete, "4102A", "cap-concurrent-2"),
            ]
            bodies = [future.result(timeout=20) for future in futures]

    assert sorted(body["completion"]["xp_awarded"] for body in bodies) == [0, 25]
    assert all(body["completion"]["recorded"] for body in bodies)
    progress = client.get(
        "/api/v1/practice/progress",
        headers=bearer(user),
    ).json()
    assert progress["total_completed"] == 3
    from contestiq_api import gamification, product_events

    events = product_events.events_for_account(user["user_id"])
    assert gamification.compute_xp_total(events, daily_cap=50) == 50
    with store.connect() as conn:
        timestamps = [
            row["completed_at"]
            for row in conn.execute(
                """
                SELECT completed_at FROM practice_completions
                WHERE user_id = ?
                ORDER BY completed_at
                """,
                (user["user_id"],),
            ).fetchall()
        ]
    assert timestamps == sorted(timestamps)
    assert len(timestamps) == len(set(timestamps)) == 3


def test_failed_request_replay_returns_the_same_final_queue_contract(client, practice_world):
    user = make_user(client)
    judge = AsyncMock(return_value=verdict("wrong_answer", 4))
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
        replay = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    assert first.json() == replay.json()
    assert judge.await_count == 1
    assert first.json()["queue"]["message"] == "The problem remains available for another attempt."


def test_terminal_attempt_recovers_when_response_cache_was_not_written(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    with store.connect() as conn:
        conn.execute("UPDATE practice_submissions SET response_json = NULL")
    with patch("contestiq_api.judge0_client.run_submission", judge):
        recovered = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    assert recovered.status_code == 200
    assert recovered.json()["submission_id"] == first.json()["submission_id"]
    assert recovered.json()["completion"]["completion_id"] == first.json()["completion"]["completion_id"]
    assert recovered.json()["completion"]["xp_awarded"] == 25
    assert judge.await_count == 2
    with store.connect() as conn:
        assert conn.execute("SELECT response_json FROM practice_submissions").fetchone()[0]


def test_concurrent_terminal_replays_return_one_canonical_cached_response(
    client, practice_world
):
    user = make_user(client)
    judge = AsyncMock(return_value=verdict("wrong_answer", 4))
    with patch("contestiq_api.judge0_client.run_submission", judge):
        original = client.post(
            "/api/v1/practice/submit",
            json=payload(request_id="canonical-replay"),
            headers=bearer(user),
        )
    assert original.status_code == 200
    with store.connect() as conn:
        conn.execute(
            """
            UPDATE practice_submissions
            SET response_json = NULL
            WHERE request_id = 'canonical-replay'
            """
        )

    barrier = threading.Barrier(2)
    snapshot_lock = threading.Lock()
    snapshot_number = 0

    def divergent_snapshot(_caller):
        nonlocal snapshot_number
        with snapshot_lock:
            snapshot_number += 1
            value = snapshot_number
        barrier.wait(timeout=10)
        return {
            "xp_total": value,
            "streak": value,
            "daily_goal": {
                "date": "2026-08-03",
                "completed": False,
                "completed_count": 0,
                "required_count": 2,
                "items": [],
            },
        }

    def replay() -> dict:
        with TestClient(client.app) as worker:
            result = worker.post(
                "/api/v1/practice/submit",
                json=payload(request_id="canonical-replay"),
                headers=bearer(user),
            )
        assert result.status_code == 200
        return result.json()

    with patch("contestiq_api.practice._gamification_snapshot", divergent_snapshot):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            bodies = [
                future.result(timeout=20)
                for future in (executor.submit(replay), executor.submit(replay))
            ]

    assert bodies[0] == bodies[1]
    assert (bodies[0]["progress"]["xp_total"], bodies[0]["progress"]["streak"]) in (
        (1, 1),
        (2, 2),
    )
    with store.connect() as conn:
        cached = json.loads(
            conn.execute(
                """
                SELECT response_json FROM practice_submissions
                WHERE request_id = 'canonical-replay'
                """
            ).fetchone()[0]
        )
    assert cached == bodies[0]


def test_stale_judging_claim_recovers_to_neutral_terminal_response(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
    with store.connect() as conn:
        conn.execute("DELETE FROM practice_continuations")
        conn.execute("DELETE FROM practice_completions")
        conn.execute("DELETE FROM product_events")
        conn.execute(
            """
            UPDATE practice_submissions
            SET status = 'judging', status_id = NULL, judged = 0, passed = 0,
                completion_id = NULL, response_json = NULL,
                created_at = '2000-01-01T00:00:00+00:00'
            """
        )
    with patch("contestiq_api.judge0_client.run_submission", judge):
        recovered = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    assert recovered.status_code == 200
    assert recovered.json()["status"] == "service_error"
    assert recovered.json()["judged"] is False
    assert recovered.json()["completion"] is None
    assert judge.await_count == 2
    with store.connect() as conn:
        row = dict(conn.execute("SELECT * FROM practice_submissions").fetchone())
    assert row["status"] == "service_error"
    assert row["response_json"]


def test_revoked_stale_worker_cannot_later_complete_or_award(client, practice_world):
    user = make_user(client)
    started = threading.Event()
    release = threading.Event()

    async def delayed_accepted(**_kwargs):
        started.set()
        if not release.wait(timeout=10):
            raise RuntimeError("test judge release timed out")
        return dict(ACCEPTED)

    def original_submit():
        with TestClient(client.app) as worker:
            return worker.post(
                "/api/v1/practice/submit",
                json=payload(request_id="stale-worker"),
                headers=bearer(user),
            )

    with patch("contestiq_api.judge0_client.run_submission", delayed_accepted):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(original_submit)
            assert started.wait(timeout=5)
            with store.connect() as conn:
                conn.execute(
                    """
                    UPDATE practice_submissions
                    SET created_at = '2000-01-01T00:00:00+00:00'
                    WHERE request_id = 'stale-worker'
                    """
                )
            revoked = client.post(
                "/api/v1/practice/submit",
                json=payload(request_id="stale-worker"),
                headers=bearer(user),
            )
            release.set()
            original = future.result(timeout=10)

    assert revoked.status_code == original.status_code == 200
    assert revoked.json()["status"] == original.json()["status"] == "service_error"
    assert revoked.json()["completion"] is None
    with store.connect() as conn:
        attempt = dict(
            conn.execute(
                "SELECT * FROM practice_submissions WHERE request_id = 'stale-worker'"
            ).fetchone()
        )
    assert attempt["status"] == "service_error"
    assert attempt["claim_token"] is None
    assert table_count("practice_completions") == 0
    assert table_count("practice_continuations") == 0
    assert table_count("product_events") == 0


def test_request_id_reuse_for_different_payload_is_rejected(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
        conflict = client.post(
            "/api/v1/practice/submit",
            json=payload(problem_id="4101A", source_code="print(2)"),
            headers=bearer(user),
        )
    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["error_code"] == "IDEMPOTENCY_KEY_REUSED"
    assert judge.await_count == 2
    assert table_count("practice_submissions") == 1


def test_request_id_is_bound_to_context_and_visible_exclusions(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post("/api/v1/practice/submit", json=payload(), headers=bearer(user))
        changed = client.post(
            "/api/v1/practice/submit",
            json=payload(source="retry_queue", visible_problem_ids=["4101A"]),
            headers=bearer(user),
        )
    assert first.status_code == 200
    assert changed.status_code == 409
    assert changed.json()["error_code"] == "IDEMPOTENCY_KEY_REUSED"
    assert judge.await_count == 2


def test_caller_identity_fields_are_forbidden(client, practice_world):
    attacker = make_user(client)
    victim = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json={**payload(), "user_id": victim["user_id"]},
            headers=bearer(attacker),
        )
    assert response.status_code == 422
    assert judge.await_count == 0
    assert table_count("practice_submissions") == 0


def test_missing_pack_never_judges_or_persists(client, practice_world):
    user = make_user(client)
    judge = accepted_mock()
    with patch("contestiq_api.judge0_client.run_submission", judge):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(problem_id="4104A"),
            headers=bearer(user),
        )
    assert response.status_code == 409
    assert response.json()["error_code"] == "PRACTICE_TESTS_UNAVAILABLE"
    assert judge.await_count == 0
    assert table_count("practice_submissions") == 0


def test_progress_persists_and_is_account_scoped(client, practice_world):
    user = make_user(client)
    other = make_user(client)
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        submitted = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        ).json()

    with TestClient(client.app) as fresh:
        progress = fresh.get("/api/v1/practice/progress", headers=bearer(user))
        other_progress = fresh.get("/api/v1/practice/progress", headers=bearer(other))
        forged = fresh.get(
            f"/api/v1/practice/progress?user_id={user['user_id']}",
            headers=bearer(other),
        )
    assert progress.status_code == 200
    assert progress.json()["completed_problem_ids"] == ["4100A"]
    assert progress.json()["total_completed"] == 1
    assert progress.json()["completions"][0]["completion_id"] == submitted["completion"]["completion_id"]
    assert progress.json()["continuation_items"] == [submitted["next_problem"]]
    assert other_progress.json() == {
        "total_completed": 0,
        "completed_problem_ids": [],
        "completions": [],
        "continuation_items": [],
        "queue": {
            "exhausted": False,
            "message": "Complete this problem to continue training.",
        },
    }
    assert forged.json() == other_progress.json()
    assert client.get("/api/v1/practice/progress").status_code == 401


def test_responses_and_persisted_json_never_expose_hidden_material(client, practice_world):
    user = make_user(client)
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        submitted = client.post(
            "/api/v1/practice/submit",
            json=payload(source_code="TOP_SECRET_SOURCE"),
            headers=bearer(user),
        )
    progress = client.get("/api/v1/practice/progress", headers=bearer(user))
    with store.connect() as conn:
        stored = conn.execute("SELECT response_json FROM practice_submissions").fetchone()[0]
    combined = json.dumps([submitted.json(), progress.json(), json.loads(stored)])
    for secret in (
        "PRIVATE_INPUT",
        "PRIVATE_EXPECTED",
        "judge_tests",
        "expected_output",
        "TOP_SECRET_SOURCE",
        "fake-judge0",
    ):
        assert secret not in combined


def test_user_program_cannot_echo_hidden_input_through_stderr(client, practice_world):
    user = make_user(client)
    leaked = verdict("runtime_error", 11)
    leaked["stderr"] = "PRIVATE_INPUT_4100A_ONE"
    with patch(
        "contestiq_api.judge0_client.run_submission",
        AsyncMock(return_value=leaked),
    ):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    assert response.json()["status"] == "runtime_error"
    assert response.json()["stderr"] == ""
    with store.connect() as conn:
        row = dict(conn.execute("SELECT * FROM practice_submissions").fetchone())
    assert "stderr_excerpt" not in row
    assert "PRIVATE_INPUT" not in row["response_json"]


def test_practice_accept_does_not_mutate_pvp_state(client, practice_world):
    user = make_user(client)
    with store.connect() as conn:
        before = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("duel_matches", "duel_participants", "duel_submissions")
        }
        pack_before = dict(
            conn.execute(
                "SELECT * FROM duel_problem_packs WHERE pack_id = 'practice-4100A-v1'"
            ).fetchone()
        )
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=payload(),
            headers=bearer(user),
        )
    assert response.status_code == 200
    with store.connect() as conn:
        after = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("duel_matches", "duel_participants", "duel_submissions")
        }
        pack_after = dict(
            conn.execute(
                "SELECT * FROM duel_problem_packs WHERE pack_id = 'practice-4100A-v1'"
            ).fetchone()
        )
    assert after == before
    assert pack_after == pack_before
