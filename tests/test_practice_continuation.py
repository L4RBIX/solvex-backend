"""Deterministic practice continuation, exclusion, ownership, and exhaustion tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "practice-continuation-admin"

PROBLEMS = (
    {"contestId": 4200, "index": "A", "name": "Current Math", "rating": 1000, "tags": ["math"]},
    {"contestId": 4201, "index": "A", "name": "Near Math", "rating": 1100, "tags": ["math"]},
    {"contestId": 4202, "index": "A", "name": "Far Math", "rating": 1400, "tags": ["math"]},
    {"contestId": 4203, "index": "A", "name": "Greedy Fallback", "rating": 1050, "tags": ["greedy"]},
    {"contestId": 4204, "index": "A", "name": "Unbacked Nearest", "rating": 1025, "tags": ["math"]},
)

ACCEPTED = {
    "status": "accepted",
    "status_id": 3,
    "passed": True,
    "stdout": "",
    "stderr": "",
    "compile_output": "",
    "time_ms": 4,
    "memory_kb": 64,
    "message": "accepted",
}


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "practice-continuation.db"))
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://fake-judge0")
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def world():
    store.save_problemset_snapshot({"problems": list(PROBLEMS), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    for problem in PROBLEMS[:-1]:
        problem_id = f"{problem['contestId']}{problem['index']}"
        assert duels.upsert_duel_problem_pack(
            {
                "pack_id": f"continuation-{problem_id}-v1",
                "problem_id": problem_id,
                "version": 1,
                "statement_summary": f"Reviewed {problem_id}.",
                "input_format": "One value.",
                "output_format": "One answer.",
                "constraints_text": "Finite reviewed constraints.",
                "sample_tests": [{"input": "1\n", "output": "1\n"}],
                "judge_tests": [{"input": "private\n", "expected_output": "answer\n"}],
            }
        )
    return PROBLEMS


def admin() -> dict[str, str]:
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client: TestClient, handle: str | None = None) -> dict:
    user = client.post("/api/v1/admin/users", json={}, headers=admin()).json()
    if handle:
        response = client.post(
            "/api/v1/admin/handles/bind",
            json={"user_id": user["user_id"], "handle": handle},
            headers=admin(),
        )
        assert response.status_code == 200
    return user


def bearer(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['api_token']}"}


def submit_payload(
    problem_id: str,
    request_id: str,
    *,
    source: str = "direct_arena",
    queue_item_id: str | None = None,
    visible: list[str] | None = None,
    completed: list[str] | None = None,
) -> dict:
    return {
        "problem_id": problem_id,
        "language": "python3",
        "source_code": "print('answer')",
        "request_id": request_id,
        "source": source,
        "queue_item_id": queue_item_id,
        "visible_problem_ids": visible or [],
        "completed_problem_ids": completed or [],
    }


def accepted_mock(count: int = 1) -> AsyncMock:
    return AsyncMock(side_effect=[dict(ACCEPTED) for _ in range(count)])


def _primary_skill(problem_id: str) -> str:
    with store.connect() as conn:
        return conn.execute(
            """
            SELECT skill_id FROM problem_skill_map
            WHERE problem_id = ?
            ORDER BY is_primary DESC, weight DESC
            LIMIT 1
            """,
            (problem_id,),
        ).fetchone()[0]


def test_authenticated_selector_uses_full_cf_capable_catalog_and_server_visible_inventory(
    client, world
):
    user = make_user(client)
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "near"),
            headers=bearer(user),
        )
    body = response.json()
    # Authenticated continuous training can recommend an ordinary Codeforces
    # task even when it has no SolveX private pack.
    assert body["next_problem"]["problem_id"] == "4204A"
    assert body["next_problem"]["target_skill"] == _primary_skill("4200A")
    assert body["next_problem"]["rating"] == 1025

    other = make_user(client)
    for problem_id in ("4204A", "4201A"):
        opened = client.post(
            "/api/v1/practice/open",
            json={"problem_id": problem_id, "source": "direct_arena"},
            headers=bearer(other),
        )
        assert opened.status_code == 200
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        relaxed = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "relaxed"),
            headers=bearer(other),
        ).json()
    assert relaxed["next_problem"]["problem_id"] == "4202A"
    assert relaxed["next_problem"]["rating"] == 1400
    assert relaxed["next_problem"]["target_skill"] == _primary_skill("4200A")


def test_guest_private_pack_selector_rejects_latest_incomplete_pack(client, world):
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO duel_problem_packs (
                pack_id, problem_id, version, statement_summary, input_format,
                output_format, constraints_text, sample_tests, judge_tests,
                active, created_at
            ) VALUES (
                'continuation-4201A-v2-incomplete', '4201A', 2, '',
                'One value.', 'One answer.', 'Finite reviewed constraints.',
                '[]', '[{"input":"private\\n","expected_output":"answer\\n"}]',
                1, ?
            )
            """,
            (store._now(),),
        )

    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "latest-incomplete"),
        )

    assert response.status_code == 200
    assert response.json()["next_problem"]["problem_id"] == "4202A"


def test_current_visible_completed_and_persisted_continuations_never_repeat(client, world):
    user = make_user(client)
    judge = accepted_mock(count=2)
    with patch("contestiq_api.judge0_client.run_submission", judge):
        first = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "first"),
            headers=bearer(user),
        ).json()
        first_next = first["next_problem"]
        opened = client.post(
            "/api/v1/practice/open",
            json={"problem_id": "4202A", "source": "direct_arena"},
            headers=bearer(user),
        )
        assert opened.status_code == 200
        second = client.post(
            "/api/v1/practice/submit",
            json=submit_payload(
                "4201A",
                "second",
            ),
            headers=bearer(user),
        ).json()

    assert first_next["problem_id"] == "4204A"
    assert second["next_problem"]["problem_id"] == "4203A"
    assert second["next_problem"]["problem_id"] not in {
        "4200A",
        "4201A",
        "4202A",
        "4204A",
    }
    progress = client.get("/api/v1/practice/progress", headers=bearer(user)).json()
    assert progress["total_completed"] == 2
    assert set(progress["completed_problem_ids"]) == {"4200A", "4201A"}
    assert progress["continuation_items"] == [first_next, second["next_problem"]]
    assert progress["queue"] == {
        "exhausted": False,
        "message": "A continuation problem is ready.",
    }
    with store.connect() as conn:
        statuses = conn.execute(
            "SELECT problem_id, status FROM practice_continuations ORDER BY created_at"
        ).fetchall()
    assert [(row["problem_id"], row["status"]) for row in statuses] == [
        ("4204A", "active"),
        ("4203A", "active"),
    ]


def test_guest_completed_exclusions_are_honored_but_not_persisted(client, world):
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload(
                "4200A",
                "guest",
                completed=["4201A"],
                visible=["4202A"],
            ),
        )
    assert response.json()["next_problem"]["problem_id"] == "4203A"
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM practice_completions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM practice_continuations").fetchone()[0] == 0


def test_guest_accepts_500_completed_exclusions_but_keeps_other_list_caps(client, world):
    completed = ["4201A", *(f"{5000 + offset}A" for offset in range(499))]
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "guest-500", completed=completed),
        )

    assert response.status_code == 200
    assert response.json()["next_problem"]["problem_id"] == "4202A"

    too_many_completed = client.post(
        "/api/v1/practice/submit",
        json=submit_payload(
            "4200A",
            "guest-501",
            completed=[*completed, "9999B"],
        ),
    )
    assert too_many_completed.status_code == 422

    too_many_visible = client.post(
        "/api/v1/practice/submit",
        json=submit_payload(
            "4200A",
            "visible-101",
            visible=[f"{6000 + offset}A" for offset in range(101)],
        ),
    )
    assert too_many_visible.status_code == 422


def test_verified_handle_official_solve_is_excluded(client, world):
    user = make_user(client, "HistoryOwner")
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO problem_episodes (
                episode_id, handle, problem_id, last_submission_at,
                total_submissions, failed_before_ac, final_status, eventual_ac,
                rating_band, verdict_sequence, passed_test_progression, episode_hash
            ) VALUES (?, ?, '4201A', 1000, 1, 0, 'solved', 1,
                      'at_level', '["OK"]', '[]', 'history-hash')
            """,
            (str(uuid.uuid4()), "historyowner"),
        )
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        body = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "history"),
            headers=bearer(user),
        ).json()
    assert body["next_problem"]["problem_id"] == "4204A"
    assert body["next_problem"]["problem_id"] != "4201A"


def test_exhaustion_is_structured_and_persisted_per_completion(client, world):
    user = make_user(client)
    for problem_id in ("4201A", "4202A", "4203A", "4204A"):
        opened = client.post(
            "/api/v1/practice/open",
            json={"problem_id": problem_id, "source": "direct_arena"},
            headers=bearer(user),
        )
        assert opened.status_code == 200
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload(
                "4200A",
                "exhausted",
            ),
            headers=bearer(user),
        )
    body = response.json()
    assert body["next_problem"] is None
    assert body["queue"]["exhausted"] is True
    assert "No unseen" in body["queue"]["message"]
    assert body["completion"]["recorded"] is True
    with store.connect() as conn:
        row = dict(conn.execute("SELECT * FROM practice_continuations").fetchone())
    assert row["completion_id"] == body["completion"]["completion_id"]
    assert row["status"] == "exhausted"
    assert row["exhausted"] == 1
    assert row["problem_id"] is None
    progress = client.get(
        "/api/v1/practice/progress",
        headers=bearer(user),
    ).json()
    assert progress["continuation_items"] == []
    assert progress["queue"] == body["queue"]


def test_transient_selector_failure_keeps_completion_and_is_not_false_exhaustion(
    client, world
):
    user = make_user(client)
    with (
        patch("contestiq_api.judge0_client.run_submission", accepted_mock()),
        patch("contestiq_api.practice._select_next", side_effect=RuntimeError("temporary")),
    ):
        first = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "selector-failed"),
            headers=bearer(user),
        ).json()
    assert first["completion"]["recorded"] is True
    assert first["completion"]["xp_awarded"] == 25
    assert first["next_problem"] is None
    assert first["queue"]["exhausted"] is False
    assert "temporarily unavailable" in first["queue"]["message"]
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM practice_completions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM practice_continuations").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM product_events").fetchone()[0] == 1
    progress = client.get(
        "/api/v1/practice/progress",
        headers=bearer(user),
    ).json()
    assert progress["queue"] == first["queue"]

    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        retried = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "selector-retry"),
            headers=bearer(user),
        ).json()
    assert retried["completion"]["already_completed"] is True
    assert retried["completion"]["xp_awarded"] == 0
    assert retried["next_problem"] is not None
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM practice_continuations").fetchone()[0] == 1


def test_personalized_world_load_failure_never_falls_back_to_unrestricted_candidates(
    client, world
):
    user = make_user(client, "FailClosedWorld")
    with (
        patch("contestiq_api.judge0_client.run_submission", accepted_mock()),
        patch(
            "contestiq_api.practice.planner._load_world",
            side_effect=RuntimeError("temporary profile failure"),
        ),
    ):
        response = client.post(
            "/api/v1/practice/submit",
            json=submit_payload("4200A", "world-failed"),
            headers=bearer(user),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["completion"]["recorded"] is True
    assert body["next_problem"] is None
    assert body["queue"] == {
        "exhausted": False,
        "message": (
            "Completion was saved, but continuation selection is temporarily unavailable."
        ),
    }
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM practice_completions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM product_events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM practice_continuations").fetchone()[0] == 0
    progress = client.get(
        "/api/v1/practice/progress",
        headers=bearer(user),
    ).json()
    assert progress["queue"] == body["queue"]


def _seed_daily_items(handle: str, *, owner_user_id: str) -> tuple[str, str]:
    current_item = str(uuid.uuid4())
    sibling_item = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    skill = _primary_skill("4200A")
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO recommendation_runs (
                run_id, handle, owner_user_id, analysis_run_id, queue_date, recent_struggle,
                warnings, created_at
            ) VALUES (?, ?, ?, NULL, '2026-07-29', 0, '[]', ?)
            """,
            (run_id, store.canonical_handle(handle), owner_user_id, now),
        )
        for slot, item_id, problem_id in (
            (1, current_item, "4200A"),
            (2, sibling_item, "4201A"),
        ):
            conn.execute(
                """
                INSERT INTO recommendation_items (
                    item_id, run_id, slot, mode, problem_id, skill_id,
                    target_rating, problem_rating, quality_score, final_score,
                    why_selected, item_status
                ) VALUES (?, ?, ?, 'core_repair', ?, ?, 1000, 1000, 0.5, 0.5, 'test', 'proposed')
                """,
                (item_id, run_id, slot, problem_id, skill),
            )
    return current_item, sibling_item


def test_owned_queue_context_marks_only_verified_handle_items_and_excludes_siblings(
    client, world
):
    owner = make_user(client, "QueueOwner")
    current_item, sibling_item = _seed_daily_items(
        "QueueOwner",
        owner_user_id=owner["user_id"],
    )
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        body = client.post(
            "/api/v1/practice/submit",
            json=submit_payload(
                "4200A",
                "owned-context",
                source="direct_arena",
                queue_item_id=current_item,
            ),
            headers=bearer(owner),
        ).json()
    assert body["completion"]["source"] == "daily_queue"
    assert body["next_problem"]["problem_id"] != "4201A"
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT item_id, item_status FROM recommendation_items ORDER BY slot"
        ).fetchall()
    by_id = {row["item_id"]: row["item_status"] for row in rows}
    assert by_id[current_item] == "completed"
    assert by_id[sibling_item] == "proposed"


def test_unverified_or_wrong_owner_cannot_borrow_or_mutate_queue_context(client, world):
    owner = make_user(client, "RealOwner")
    current_item, _sibling = _seed_daily_items(
        "RealOwner",
        owner_user_id=owner["user_id"],
    )
    attacker = make_user(client)  # no verified handle
    with patch("contestiq_api.judge0_client.run_submission", accepted_mock()):
        body = client.post(
            "/api/v1/practice/submit",
            json=submit_payload(
                "4200A",
                "forged-context",
                source="direct_arena",
                queue_item_id=current_item,
            ),
            headers=bearer(attacker),
        ).json()
    assert body["completion"]["source"] == "direct_arena"
    with store.connect() as conn:
        assert conn.execute(
            "SELECT item_status FROM recommendation_items WHERE item_id = ?",
            (current_item,),
        ).fetchone()[0] == "proposed"
