"""Catalog parity: CF problemset.problems must upsert into SolveX without deletes."""

from __future__ import annotations

import json

import pytest

from contestiq_api.arena_eligibility import is_arena_solvable
from contestiq_api.cfdata import store
from contestiq_api.cfdata import sync as cf_sync
from contestiq_api.cfdata.client import TransportResponse


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    cf_sync._handle_locks.clear()
    yield


def ok(result):
    return TransportResponse(200, {"status": "OK", "result": result})


class ProblemsetClient:
    def __init__(self, problems, statistics=None):
        self.problems = problems
        self.statistics = statistics or []
        self.stale = False
        self.calls = 0

    def get_problemset(self):
        self.calls += 1

        class Result:
            def __init__(self, data, stale):
                self.data = data
                self.stale = stale

        return Result({"problems": self.problems, "problemStatistics": self.statistics}, self.stale)


def test_new_codeforces_identity_inserts_and_is_not_arena_capable():
    client = ProblemsetClient(
        [
            {
                "contestId": 2255,
                "index": "A",
                "name": "Fresh Contest A",
                "rating": 800,
                "tags": ["implementation"],
                "type": "PROGRAMMING",
            }
        ]
    )
    result = cf_sync.sync_problemset(force=True, client=client)
    assert result["refetched"] is True
    assert store.get_problem("2255A") is not None
    assert store.get_problem("2255A")["name"] == "Fresh Contest A"
    stub = store.get_problem_statement("2255A")
    assert stub is not None
    assert stub["availability_status"] == "missing"
    assert bool(stub["display_ready"]) is False
    assert is_arena_solvable("2255A") is False
    assert result["catalog_sync"]["missing_from_solvex_after"] == 0
    assert result["catalog_sync"]["new_problems"] == 1
    assert result["catalog_sync"]["statement_stubs_created"] == 1


def test_rerunning_sync_is_idempotent_no_duplicates():
    problems = [
        {"contestId": 1, "index": "A", "name": "Theatre Square", "rating": 1000, "tags": ["math"]},
        {"contestId": 2255, "index": "B", "name": "Fresh B", "rating": 900, "tags": ["greedy"]},
    ]
    client = ProblemsetClient(problems)
    first = cf_sync.sync_problemset(force=True, client=client)
    second = cf_sync.sync_problemset(force=True, client=client)
    assert first["catalog_sync"]["new_problems"] == 2
    assert second["catalog_sync"]["new_problems"] == 0
    assert second["catalog_sync"]["unchanged"] == 2
    assert store.problem_counts()["problems"] == 2
    assert store.catalog_parity_report({"1A", "2255B"})["missing_from_solvex"] == 0


def test_changed_rating_and_tags_update_without_delete():
    client = ProblemsetClient(
        [{"contestId": 42, "index": "C", "name": "Old Name", "rating": 1200, "tags": ["dp"]}]
    )
    cf_sync.sync_problemset(force=True, client=client)
    client.problems = [
        {"contestId": 42, "index": "C", "name": "New Name", "rating": 1400, "tags": ["dp", "greedy"]}
    ]
    # Keep a historical ID that CF no longer returns — must survive.
    store.save_problemset_snapshot(
        {
            "problems": [
                {"contestId": 999999, "index": "Z", "name": "Historical", "rating": 800, "tags": []}
            ],
            "problemStatistics": [],
        }
    )
    result = cf_sync.sync_problemset(force=True, client=client)
    row = store.get_problem("42C")
    assert row["name"] == "New Name"
    assert row["rating"] == 1400
    assert json.loads(row["tags"]) == ["dp", "greedy"]
    assert result["catalog_sync"]["updated_problems"] == 1
    assert store.get_problem("999999Z") is not None
    assert result["catalog_sync"]["extra_historical_solvex"] >= 1


def test_missing_statement_does_not_block_catalog_or_api(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import contestiq_api.main as main

    client = ProblemsetClient(
        [{"contestId": 2255, "index": "C", "name": "Pending Statement", "rating": 1100, "tags": ["math"]}]
    )
    cf_sync.sync_problemset(force=True, client=client)
    api = TestClient(main.app)
    response = api.get("/api/v1/problems/2255C")
    assert response.status_code == 200
    body = response.json()
    assert body["problem_id"] == "2255C"
    assert body["name"] == "Pending Statement"
    assert body["arena_capable"] is False
    assert body["statement_content"]["availability"]["display_ready"] is False
    assert body["statement_content"]["availability"]["status"] == "missing"
    assert body["official_url"].endswith("/problemset/problem/2255/C")


def test_malformed_upstream_entries_are_skipped():
    client = ProblemsetClient(
        [
            None,
            "bad",
            {"contestId": 7, "index": "A", "name": "Good", "rating": 800, "tags": []},
            {"name": "No identity"},
        ]
    )
    result = cf_sync.sync_problemset(force=True, client=client)
    assert store.get_problem("7A") is not None
    assert result["catalog_sync"]["new_problems"] == 1
    assert result["catalog_sync"]["skipped_malformed"] >= 1


def test_recommendation_guard_still_requires_display_ready():
    from contestiq_api.arena_eligibility import select_arena_recommendations

    client = ProblemsetClient(
        [
            {"contestId": 2255, "index": "D", "name": "Catalog Only", "rating": 1000, "tags": ["math"]},
            {"contestId": 1, "index": "A", "name": "Theatre Square", "rating": 1000, "tags": ["math"]},
        ]
    )
    cf_sync.sync_problemset(force=True, client=client)
    # Seed display-ready only for 1A.
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO problem_import_batches (batch_id, source_name, source_sha256, status, started_at)"
            " VALUES ('ready','t','h','completed',?)",
            (now,),
        )
        conn.execute(
            """
            UPDATE problem_statements
            SET statement='Body', display_ready=1, solve_ready=1, availability_status='complete_standard',
                unavailable_reason=NULL
            WHERE problem_id='1A'
            """
        )
        # If stub missing for 1A, insert ready row
        if conn.execute("SELECT 1 FROM problem_statements WHERE problem_id='1A'").fetchone() is None:
            conn.execute(
                """
                INSERT INTO problem_statements (
                    problem_id, batch_id, content_hash, title, statement, samples,
                    availability_status, display_ready, solve_ready, source_urls, imported_at
                ) VALUES ('1A','ready','h','Theatre Square','Body','[]','complete_standard',1,1,'[]',?)
                """,
                (now,),
            )
    selected = select_arena_recommendations(
        [
            {"name": "Catalog Only", "contestId": 2255, "index": "D", "rating": 1000, "tags": ["math"]},
            {"name": "Theatre Square", "contestId": 1, "index": "A", "rating": 1000, "tags": ["math"]},
        ],
        limit=8,
    )
    ids = {f"{p['contestId']}{p['index']}" for p in selected}
    assert "2255D" not in ids
    assert "1A" in ids
