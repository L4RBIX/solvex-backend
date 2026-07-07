"""Sync service tests — fully mocked, never touch live Codeforces."""

import importlib
import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import store
from contestiq_api.cfdata import sync as cf_sync
from contestiq_api.cfdata.client import CircuitBreaker, CodeforcesClient, GlobalRateLimiter, TransportResponse


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    cf_sync._handle_locks.clear()


def ok(result):
    return TransportResponse(200, {"status": "OK", "result": result})


def make_submission(sid, contest_id, index, name, rating, tags, verdict, handle="Sync-User"):
    return {
        "id": sid,
        "contestId": contest_id,
        "creationTimeSeconds": 1700000000 + sid,
        "relativeTimeSeconds": 2147483647,
        "problem": {
            "contestId": contest_id,
            "index": index,
            "name": name,
            "type": "PROGRAMMING",
            **({"rating": rating} if rating is not None else {}),
            "tags": tags,
        },
        "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"},
        "programmingLanguage": "GNU C++17",
        "verdict": verdict,
        "testset": "TESTS",
        "passedTestCount": 12,
        "timeConsumedMillis": 154,
        "memoryConsumedBytes": 4096000,
    }


class FakeCodeforces:
    """Scripted Codeforces API with user.status paging semantics (newest-first)."""

    def __init__(self):
        self.user = {"handle": "Sync-User", "rating": 1500, "maxRating": 1600, "rank": "specialist", "maxRank": "expert"}
        self.rating_history = [
            {"contestId": 900, "contestName": "Round 900", "rank": 42, "oldRating": 1400, "newRating": 1500,
             "ratingUpdateTimeSeconds": 1700000000},
        ]
        self.submissions = []  # newest-first
        self.problemset = {"problems": [], "problemStatistics": []}
        self.calls = []

    def transport(self, url, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, dict(params)))
        if endpoint == "user.info":
            return ok([self.user])
        if endpoint == "user.rating":
            return ok(self.rating_history)
        if endpoint == "user.status":
            start = int(params.get("from", 1)) - 1
            count = int(params.get("count", len(self.submissions) or 1))
            return ok(self.submissions[start : start + count])
        if endpoint == "problemset.problems":
            return ok(self.problemset)
        raise AssertionError(f"unexpected endpoint {endpoint}")

    def status_calls(self):
        return [c for c in self.calls if c[0] == "user.status"]


def make_client(world):
    return CodeforcesClient(
        transport=world.transport,
        rate_limiter=GlobalRateLimiter(0.0, clock=lambda: 0.0, sleep=lambda s: None),
        breaker=CircuitBreaker(failure_threshold=100),
        sleep=lambda s: None,
        rng=lambda: 0.0,
    )


@pytest.fixture
def world():
    w = FakeCodeforces()
    w.submissions = [
        make_submission(3, 200, "B", "Rated DP", 1400, ["dp", "math"], "WRONG_ANSWER"),
        make_submission(2, 200, "B", "Rated DP", 1400, ["dp", "math"], "OK"),
        make_submission(1, 100, "A", "Unrated Gym Task", None, ["implementation"], "OK"),
    ]
    w.problemset = {
        "problems": [
            {"contestId": 200, "index": "B", "name": "Rated DP", "rating": 1400, "tags": ["dp", "math"]},
            {"contestId": 300, "index": "C", "name": "No Rating Yet", "tags": ["greedy"]},
        ],
        "problemStatistics": [
            {"contestId": 200, "index": "B", "solvedCount": 5000},
            {"contestId": 300, "index": "C", "solvedCount": 123},
        ],
    }
    return w


# ─── Full sync ───────────────────────────────────────────────────────────────


def test_full_sync_persists_raw_and_normalized(world):
    job = cf_sync.sync_handle("Sync-User", client=make_client(world))
    assert job["status"] == "success"
    assert job["sync_type"] == "full"
    assert job["stats"]["submissions_fetched"] == 3
    assert job["stats"]["submissions_new"] == 3

    user = store.get_user("sync-user")
    assert user["display_handle"] == "Sync-User"
    assert user["rating"] == 1500
    assert user["max_submission_id"] == 3
    assert user["submission_count"] == 3

    counts = store.submission_counts("sync-user")
    assert counts == {"raw": 3, "normalized": 3}

    with store.connect() as conn:
        history = conn.execute("SELECT COUNT(*) FROM cf_user_rating_history WHERE handle='sync-user'").fetchone()[0]
    assert history == 1


def test_normalized_row_field_correctness(world):
    cf_sync.sync_handle("Sync-User", client=make_client(world))
    row = store.get_normalized_submission(2)
    assert row == {
        "submission_id": 2,
        "handle": "sync-user",
        "contest_id": 200,
        "problem_index": "B",
        "problem_key": "200B",
        "participant_type": "PRACTICE",
        "programming_language": "GNU C++17",
        "verdict": "OK",
        "passed_test_count": 12,
        "time_consumed_ms": 154,
        "memory_consumed_bytes": 4096000,
        "creation_time": 1700000002,
        "relative_time_seconds": 2147483647,
        "problem_rating": 1400,
        "problem_tags_snapshot": json.dumps(["dp", "math"]),
    }


def test_ratingless_problem_normalizes_with_null_rating(world):
    cf_sync.sync_handle("Sync-User", client=make_client(world))
    row = store.get_normalized_submission(1)
    assert row["problem_rating"] is None
    assert row["problem_key"] == "100A"


# ─── Idempotent / incremental resync ─────────────────────────────────────────


def test_resync_does_not_duplicate_rows(world):
    cf_sync.sync_handle("Sync-User", client=make_client(world))
    second = cf_sync.sync_handle("Sync-User", client=make_client(world))
    assert second["sync_type"] == "incremental"
    assert second["stats"]["submissions_new"] == 0
    assert store.submission_counts("sync-user") == {"raw": 3, "normalized": 3}
    with store.connect() as conn:
        history = conn.execute("SELECT COUNT(*) FROM cf_user_rating_history WHERE handle='sync-user'").fetchone()[0]
    assert history == 1


def test_incremental_sync_fetches_only_new_submissions(world, monkeypatch):
    monkeypatch.setattr(cf_sync, "PAGE_SIZE", 2)
    cf_sync.sync_handle("Sync-User", client=make_client(world))

    world.submissions = [
        make_submission(5, 400, "D", "Fresh Problem", 1600, ["graphs"], "OK"),
        make_submission(4, 400, "D", "Fresh Problem", 1600, ["graphs"], "WRONG_ANSWER"),
    ] + world.submissions
    world.calls.clear()

    job = cf_sync.sync_handle("Sync-User", client=make_client(world))
    assert job["sync_type"] == "incremental"
    assert job["stats"]["submissions_new"] == 2
    assert store.submission_counts("sync-user") == {"raw": 5, "normalized": 5}
    assert store.get_user("sync-user")["max_submission_id"] == 5
    # With page size 2 the first page [5, 4] has no overlap, the second page
    # [3, 2] hits already-synced ids and paging stops — never reaches page 3.
    assert len(world.status_calls()) == 2


def test_full_sync_pages_through_everything(world, monkeypatch):
    monkeypatch.setattr(cf_sync, "PAGE_SIZE", 2)
    job = cf_sync.sync_handle("Sync-User", client=make_client(world))
    assert job["stats"]["pages_fetched"] == 2
    assert job["stats"]["submissions_fetched"] == 3


def test_force_full_resync_stays_idempotent(world):
    cf_sync.sync_handle("Sync-User", client=make_client(world))
    job = cf_sync.sync_handle("Sync-User", force_full=True, client=make_client(world))
    assert job["sync_type"] == "full"
    assert job["stats"]["submissions_new"] == 0
    assert store.submission_counts("sync-user") == {"raw": 3, "normalized": 3}


def test_failed_sync_records_failed_job(world):
    def broken_transport(url, params, timeout):
        raise TimeoutError("cf is down")

    client = CodeforcesClient(
        transport=broken_transport,
        rate_limiter=GlobalRateLimiter(0.0, clock=lambda: 0.0, sleep=lambda s: None),
        breaker=CircuitBreaker(failure_threshold=100),
        sleep=lambda s: None,
        rng=lambda: 0.0,
        max_retries=1,
    )
    with pytest.raises(Exception):
        cf_sync.sync_handle("Sync-User", client=client)
    jobs = store.list_sync_jobs("sync-user")
    assert jobs[0]["status"] == "failed"
    assert "cf is down" in jobs[0]["error_message"]


def test_active_job_is_reused_not_duplicated(world):
    job = store.create_sync_job("full", "sync-user")
    store.mark_sync_running(job["id"])
    result = cf_sync.sync_handle("Sync-User", client=make_client(world))
    assert result["id"] == job["id"]
    assert world.calls == []  # no Codeforces traffic while a sync is active


# ─── Problemset ──────────────────────────────────────────────────────────────


def test_problemset_sync_persists_problems_and_statistics(world):
    result = cf_sync.sync_problemset(client=make_client(world))
    assert result["status"] == "success"
    assert result["refetched"] is True
    assert store.problem_counts() == {"problems": 2, "statistics": 2}

    rated = store.get_problem("200B")
    assert rated["rating"] == 1400
    assert json.loads(rated["tags"]) == ["dp", "math"]
    unrated = store.get_problem("300C")
    assert unrated["rating"] is None


def test_problemset_is_globally_cached_within_ttl(world):
    cf_sync.sync_problemset(client=make_client(world))
    calls_before = len(world.calls)
    second = cf_sync.sync_problemset(client=make_client(world))
    assert second["status"] == "fresh"
    assert second["refetched"] is False
    assert len(world.calls) == calls_before


def test_problemset_force_refetch_does_not_duplicate(world):
    cf_sync.sync_problemset(client=make_client(world))
    result = cf_sync.sync_problemset(force=True, client=make_client(world))
    assert result["refetched"] is True
    assert store.problem_counts() == {"problems": 2, "statistics": 2}


# ─── Sync status + endpoints ─────────────────────────────────────────────────


def test_sync_status_visibility(world):
    cf_sync.sync_handle("Sync-User", client=make_client(world))
    status = cf_sync.sync_status("Sync-User")
    assert status["synced"] is True
    assert status["user"]["submission_count"] == 3
    assert status["submissions"] == {"raw": 3, "normalized": 3}
    assert status["recent_jobs"][0]["status"] == "success"


def _api_client(monkeypatch, world):
    import contestiq_api.rate_limit as rate_limit

    rate_limit.reset_rate_limits()
    monkeypatch.setattr(cf_sync, "CodeforcesClient", lambda: make_client(world))
    import contestiq_api.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_sync_endpoint_runs_sync_and_returns_job(tmp_path, monkeypatch, world):
    client = _api_client(monkeypatch, world)
    response = client.post("/api/v1/sync/codeforces/Sync-User", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["job"]["status"] == "success"
    assert data["job"]["sync_type"] == "full"

    status = client.get("/api/v1/sync/codeforces/Sync-User")
    assert status.status_code == 200
    assert status.json()["submissions"]["normalized"] == 3


def test_sync_endpoint_maps_handle_not_found(tmp_path, monkeypatch, world):
    def not_found_transport(url, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        if endpoint == "user.info":
            return TransportResponse(200, {"status": "FAILED", "comment": "handles: User with handle ghost not found"})
        raise AssertionError("should stop at user.info")

    ghost = FakeCodeforces()
    ghost.transport = not_found_transport
    client = _api_client(monkeypatch, ghost)
    response = client.post("/api/v1/sync/codeforces/ghost-handle", json={})
    assert response.status_code == 404
    assert response.json()["error_code"] == "CODEFORCES_HANDLE_NOT_FOUND"
    jobs = store.list_sync_jobs("ghost-handle")
    assert jobs[0]["status"] == "failed"


def test_problemset_endpoint(tmp_path, monkeypatch, world):
    client = _api_client(monkeypatch, world)
    response = client.post("/api/v1/sync/problemset", json={})
    assert response.status_code == 200
    assert response.json()["refetched"] is True
    again = client.post("/api/v1/sync/problemset", json={})
    assert again.json()["refetched"] is False
