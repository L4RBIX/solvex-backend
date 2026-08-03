"""Codeforces-verified completion: historical vs current reward and history rules."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "cf-completion-admin-key"

PROBLEMS = (
    {"contestId": 5100, "index": "A", "name": "Current Task", "rating": 1000, "tags": ["math"]},
    {"contestId": 5101, "index": "A", "name": "Near Math", "rating": 1050, "tags": ["math"]},
    {"contestId": 5102, "index": "A", "name": "Far Math", "rating": 1400, "tags": ["math"]},
    {"contestId": 5103, "index": "A", "name": "Greedy", "rating": 1100, "tags": ["greedy"]},
)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "cf-completion.db"))
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def world():
    store.save_problemset_snapshot({"problems": list(PROBLEMS), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
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


def open_problem(client: TestClient, user: dict, problem_id: str = "5100A") -> dict:
    response = client.post(
        "/api/v1/practice/open",
        json={"problem_id": problem_id, "source": "direct_arena"},
        headers=bearer(user),
    )
    assert response.status_code == 200
    return response.json()


def seed_submission(
    *,
    handle: str,
    contest_id: int = 5100,
    index: str = "A",
    submission_id: int = 900001,
    creation_time: int,
    verdict: str = "OK",
) -> None:
    store.upsert_submissions(
        handle,
        [
            {
                "id": submission_id,
                "contestId": contest_id,
                "creationTimeSeconds": creation_time,
                "relativeTimeSeconds": 0,
                "programmingLanguage": "GNU C++17",
                "verdict": verdict,
                "passedTestCount": 10,
                "timeConsumedMillis": 15,
                "memoryConsumedBytes": 1024,
                "problem": {
                    "contestId": contest_id,
                    "index": index,
                    "name": "Current Task",
                    "rating": 1000,
                    "tags": ["math"],
                },
                "author": {"participantType": "PRACTICE", "members": [{"handle": handle}]},
            }
        ],
    )


def check(client: TestClient, user: dict, problem_id: str = "5100A") -> dict:
    response = client.post(
        "/api/v1/practice/codeforces/check",
        json={"problem_id": problem_id, "source": "direct_arena", "visible_problem_ids": [problem_id]},
        headers=bearer(user),
    )
    assert response.status_code == 200
    return response.json()


def test_capability_reports_codeforces_only_without_private_pack(client, world):
    response = client.get("/api/v1/practice/capability/5100A")
    assert response.status_code == 200
    body = response.json()
    assert body["practice_judge_available"] is False
    assert body["primary_completion_source"] == "codeforces_verified"
    assert body["completion_sources"] == ["codeforces_verified"]


def test_check_requires_verified_handle(client, world):
    user = make_user(client)
    open_problem(client, user)
    body = check(client, user)
    assert body["status"] == "verification_required"
    assert body["completion"] is None
    assert body["effects"]["xp_updated"] is False
    assert body["progress"]["xp_total"] == 0


def test_historical_accepted_grants_no_xp_streak_or_replacement(client, world):
    user = make_user(client, "HistSolver")
    opened = open_problem(client, user)
    assigned_at = dt.datetime.fromisoformat(opened["assignment"]["assigned_at"])
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="HistSolver",
        creation_time=int((assigned_at - dt.timedelta(days=2)).timestamp()),
        submission_id=910001,
    )

    body = check(client, user)
    assert body["status"] == "completed"
    completion = body["completion"]
    assert completion["completion_source"] == "codeforces_verified"
    assert completion["historical"] is True
    assert completion["xp_awarded"] == 0
    assert body["effects"] == {
        "solution_verified": True,
        "problem_marked_completed": True,
        "solved_history_updated": True,
        "xp_updated": False,
        "daily_goal_updated": False,
        "training_queue_refreshed": False,
    }
    assert body["next_problem"] is None
    assert body["progress"]["xp_total"] == 0
    assert body["progress"]["streak"] == 0
    assert body["progress"]["daily_goal"]["completed_count"] == 0

    with store.connect() as conn:
        row = dict(conn.execute("SELECT * FROM problem_completions").fetchone())
        events = conn.execute("SELECT COUNT(*) FROM product_events").fetchone()[0]
        continuations = conn.execute("SELECT COUNT(*) FROM practice_continuations").fetchone()[0]
    assert row["is_historical"] == 1
    assert row["xp_awarded"] == 0
    assert row["queue_refreshed"] == 0
    assert events == 0
    assert continuations == 0


def test_current_accepted_awards_xp_replacement_and_history(client, world):
    user = make_user(client, "CurrSolver")
    opened = open_problem(client, user)
    assigned_at = dt.datetime.fromisoformat(opened["assignment"]["assigned_at"])
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="CurrSolver",
        creation_time=int((assigned_at + dt.timedelta(minutes=5)).timestamp()),
        submission_id=920001,
    )

    body = check(client, user)
    assert body["status"] == "completed"
    completion = body["completion"]
    assert completion["historical"] is False
    assert completion["xp_awarded"] == 25
    assert body["effects"]["xp_updated"] is True
    assert body["effects"]["daily_goal_updated"] is True
    assert body["effects"]["training_queue_refreshed"] is True
    assert body["effects"]["solved_history_updated"] is True
    assert body["next_problem"] is not None
    assert body["next_problem"]["problem_id"] != "5100A"
    assert body["progress"]["xp_total"] == 25
    assert body["progress"]["streak"] == 1
    assert body["progress"]["daily_goal"]["completed_count"] == 1

    history = client.get("/api/v1/practice/history", headers=bearer(user)).json()
    assert history["total"] == 1
    assert history["items"][0]["completion_source"] == "codeforces_verified"
    assert history["items"][0]["historical"] is False
    assert history["items"][0]["xp_awarded"] == 25
    assert history["items"][0]["assigned_at"] == opened["assignment"]["assigned_at"]
    assert history["items"][0]["verified_at"]


def test_current_accepted_never_recommends_completed_or_visible_siblings(client, world):
    user = make_user(client, "ExcludeSolver")
    # Active assignments are part of server-owned visible inventory.
    for problem_id in ("5100A", "5101A", "5103A"):
        assert open_problem(client, user, problem_id)["assignment"]["problem_id"] == problem_id
    with store.connect() as conn:
        assigned_raw = conn.execute(
            """
            SELECT assigned_at FROM solo_problem_assignments
            WHERE user_id = ? AND problem_id = '5100A' AND status = 'active'
            """,
            (user["user_id"],),
        ).fetchone()[0]
    assigned_at = dt.datetime.fromisoformat(assigned_raw)
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="ExcludeSolver",
        creation_time=int((assigned_at + dt.timedelta(minutes=1)).timestamp()),
        submission_id=930001,
    )
    body = check(client, user)
    assert body["status"] == "completed"
    assert body["next_problem"] is not None
    assert body["next_problem"]["problem_id"] == "5102A"
    assert body["next_problem"]["problem_id"] not in {"5100A", "5101A", "5103A"}


def test_already_completed_is_idempotent(client, world):
    user = make_user(client, "IdemSolver")
    opened = open_problem(client, user)
    assigned_at = dt.datetime.fromisoformat(opened["assignment"]["assigned_at"])
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="IdemSolver",
        creation_time=int((assigned_at + dt.timedelta(minutes=2)).timestamp()),
        submission_id=940001,
    )
    first = check(client, user)
    second = check(client, user)
    assert first["status"] == "completed"
    assert second["status"] == "already_completed"
    assert second["effects"]["xp_updated"] is False
    assert second["completion"]["completion_id"] == first["completion"]["completion_id"]
    assert second["progress"]["xp_total"] == 25
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM problem_completions").fetchone()[0] == 1


def test_pending_and_cooldown_do_not_invent_completion(client, world, monkeypatch):
    user = make_user(client, "PendingSolver")
    open_problem(client, user)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_user_status(self, handle, from_index=1, count=500):
            return SimpleNamespace(data=[], stale=False, fetched_at=store._now())

    monkeypatch.setattr("contestiq_api.completions.CodeforcesClient", FakeClient)
    first = check(client, user)
    assert first["status"] == "pending"
    assert first["completion"] is None
    assert first["cooldown_seconds"] > 0

    second = check(client, user)
    assert second["status"] == "cooldown"
    assert second["completion"] is None
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM problem_completions").fetchone()[0] == 0


def test_codeforces_outage_returns_unavailable(client, world, monkeypatch):
    from contestiq_api.cfdata.client import CodeforcesClientError

    user = make_user(client, "OutageSolver")
    open_problem(client, user)

    class BrokenClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_user_status(self, *args, **kwargs):
            raise CodeforcesClientError("down")

    monkeypatch.setattr("contestiq_api.completions.CodeforcesClient", BrokenClient)
    body = check(client, user)
    assert body["status"] == "unavailable"
    assert body["completion"] is None
    assert "temporarily unavailable" in body["message"].lower()


def test_history_filters_source_and_historical(client, world):
    user = make_user(client, "FilterSolver")
    opened = open_problem(client, user)
    assigned_at = dt.datetime.fromisoformat(opened["assignment"]["assigned_at"])
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="FilterSolver",
        creation_time=int((assigned_at - dt.timedelta(hours=3)).timestamp()),
        submission_id=950001,
    )
    assert check(client, user)["completion"]["historical"] is True

    # Second problem after assignment => current.
    opened2 = open_problem(client, user, "5101A")
    assigned2 = dt.datetime.fromisoformat(opened2["assignment"]["assigned_at"])
    if assigned2.tzinfo is None:
        assigned2 = assigned2.replace(tzinfo=dt.timezone.utc)
    seed_submission(
        handle="FilterSolver",
        contest_id=5101,
        index="A",
        creation_time=int((assigned2 + dt.timedelta(minutes=1)).timestamp()),
        submission_id=950002,
    )
    assert check(client, user, "5101A")["completion"]["historical"] is False

    all_items = client.get("/api/v1/practice/history", headers=bearer(user)).json()
    assert all_items["total"] == 2
    assert all_items["source"] == "all"
    assert all_items["historical"] == "all"

    hist_only = client.get(
        "/api/v1/practice/history?historical=historical",
        headers=bearer(user),
    ).json()
    assert hist_only["total"] == 1
    assert hist_only["items"][0]["problem_id"] == "5100A"
    assert hist_only["items"][0]["historical"] is True
    assert hist_only["items"][0]["xp_awarded"] == 0

    current_only = client.get(
        "/api/v1/practice/history?historical=current&source=codeforces_verified",
        headers=bearer(user),
    ).json()
    assert current_only["total"] == 1
    assert current_only["items"][0]["problem_id"] == "5101A"
    assert current_only["items"][0]["xp_awarded"] == 25

    practice_only = client.get(
        "/api/v1/practice/history?source=solvex_practice_judge",
        headers=bearer(user),
    ).json()
    assert practice_only["total"] == 0
    assert practice_only["items"] == []
