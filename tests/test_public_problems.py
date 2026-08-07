from __future__ import annotations

import json
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from contestiq_api import duels
from contestiq_api.cfdata import store


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def catalog():
    problems = [
        {
            "contestId": 71,
            "index": "A",
            "name": "Way Too Long Words",
            "rating": 800,
            "tags": ["strings", "implementation"],
        },
        {
            "contestId": 1364,
            "index": "B",
            "name": "Most socially-distanced subsequence",
            "rating": 1300,
            "tags": ["greedy", "two pointers"],
        },
    ]
    store.save_problemset_snapshot({"problems": problems, "problemStatistics": []})
    assert duels.upsert_duel_problem_pack(
        {
            "pack_id": "test-71a-v1",
            "problem_id": "71A",
            "version": 1,
            "statement_summary": "Shorten every word longer than ten characters.",
            "input_format": "The first line contains n, followed by n words.",
            "output_format": "Print each original or shortened word.",
            "constraints_text": "1 <= n <= 100.",
            "sample_tests": [
                {
                    "input": "2\nword\nlocalization\n",
                    "output": "word\nl10n\n",
                    "note": "The first word stays unchanged.",
                }
            ],
            "judge_tests": [
                {
                    "input": "hidden server input\n",
                    "expected_output": "hidden server output\n",
                }
            ],
        }
    )
    return problems


def test_known_problem_returns_public_metadata_without_authentication(client, catalog):
    response = client.get("/api/v1/problems/71A")
    assert response.status_code == 200
    data = response.json()
    assert data["problem_id"] == "71A"
    assert data["contest_id"] == 71
    assert data["index"] == "A"
    assert data["name"] == "Way Too Long Words"
    assert data["rating"] == 800
    assert data["tags"] == ["strings", "implementation"]
    assert data["official_url"] == "https://codeforces.com/problemset/problem/71/A"


@pytest.mark.parametrize("problem_id", ["71a", "%2071a%20"])
def test_problem_id_normalizes_case_and_surrounding_whitespace(client, catalog, problem_id):
    response = client.get(f"/api/v1/problems/{problem_id}")
    assert response.status_code == 200
    assert response.json()["problem_id"] == "71A"


@pytest.mark.parametrize(
    "problem_id",
    [
        "A71",
        "71%2FA",
        "-71A",
        "0A",
        quote("https://codeforces.com/problemset/problem/71/A", safe=""),
        quote("../../etc/passwd", safe=""),
        quote("71A' OR 1=1 --", safe=""),
    ],
)
def test_malformed_and_path_like_problem_ids_are_rejected(client, catalog, problem_id):
    response = client.get(f"/api/v1/problems/{problem_id}")
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_PROBLEM_ID"


def test_empty_problem_id_is_rejected(client, catalog):
    response = client.get("/api/v1/problems")
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_PROBLEM_ID"


def test_unknown_valid_problem_returns_not_found(client, catalog):
    response = client.get("/api/v1/problems/9999Z")
    assert response.status_code == 404
    assert response.json()["error_code"] == "PROBLEM_NOT_FOUND"


def test_catalog_only_problem_has_no_invented_content(client, catalog):
    response = client.get("/api/v1/problems/1364B")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Most socially-distanced subsequence"
    assert data["content_available"] is False
    assert data["authored_content"] is None


def test_authored_problem_returns_only_public_authored_content(client, catalog):
    data = client.get("/api/v1/problems/71A").json()
    assert data["content_available"] is True
    assert data["authored_content"] == {
        "summary": "Shorten every word longer than ten characters.",
        "input_format": "The first line contains n, followed by n words.",
        "output_format": "Print each original or shortened word.",
        "constraints": "1 <= n <= 100.",
        "samples": [
            {
                "input": "2\nword\nlocalization\n",
                "output": "word\nl10n\n",
                "note": "The first word stays unchanged.",
            }
        ],
    }

    serialized = json.dumps(data).lower()
    for forbidden in (
        "judge_tests",
        "expected_output",
        "hidden server input",
        "hidden server output",
        "duel_id",
        "pack_id",
        "test_set_hash",
        "winner",
        "hint_count",
    ):
        assert forbidden not in serialized


# ─── statement_content (PR: problem-database import) ────────────────────────


def _seed_statement(problem_id: str, **overrides) -> None:
    """Insert a problem_statements row directly (bypassing the importer,
    which has its own dedicated tests in tests/test_problem_import.py)."""
    now = "2026-08-02T00:00:00+00:00"
    payload = {
        "problem_id": problem_id,
        "batch_id": "test-batch",
        "content_hash": "test-hash",
        "title": "Way Too Long Words",
        "statement": "Parse the opening tag <a> and verify $x < y$ holds.",
        "input_format": "The first line contains n.",
        "output_format": "Print the answer.",
        "interaction_format": None,
        "notes": None,
        "samples": json.dumps([{"input": "2\nword\nlocalization\n", "output": "word\nl10n\n"}]),
        "time_limit_seconds": 1.0,
        "memory_limit_megabytes": 256.0,
        "difficulty": "EASY",
        "io_mode": "stdio",
        "is_interactive": 0,
        "picture_count": 0,
        "has_missing_diagrams": 0,
        "availability_status": "complete_standard",
        "display_ready": 1,
        "solve_ready": 1,
        "unavailable_reason": None,
        "source_dataset": "open-r1/codeforces",
        "source_urls": json.dumps(["https://codeforces.com/problemset/problem/71/A"]),
        "statement_relation": None,
        "shared_statement_from": None,
        "imported_at": now,
    }
    payload.update(overrides)
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO problem_import_batches (batch_id, source_name, source_sha256, status, started_at)"
            " VALUES (?, 'test-archive.zip', 'deadbeef', 'completed', ?)",
            (payload["batch_id"], now),
        )
        conn.execute(
            """
            INSERT INTO problem_statements (
                problem_id, batch_id, content_hash, title, statement, input_format, output_format,
                interaction_format, notes, samples, time_limit_seconds, memory_limit_megabytes,
                difficulty, io_mode, is_interactive, picture_count, has_missing_diagrams,
                availability_status, display_ready, solve_ready, unavailable_reason,
                source_dataset, source_urls, statement_relation, shared_statement_from, imported_at
            ) VALUES (
                :problem_id, :batch_id, :content_hash, :title, :statement, :input_format, :output_format,
                :interaction_format, :notes, :samples, :time_limit_seconds, :memory_limit_megabytes,
                :difficulty, :io_mode, :is_interactive, :picture_count, :has_missing_diagrams,
                :availability_status, :display_ready, :solve_ready, :unavailable_reason,
                :source_dataset, :source_urls, :statement_relation, :shared_statement_from, :imported_at
            )
            """,
            payload,
        )


def test_statement_content_is_served_when_imported(client, catalog):
    _seed_statement("71A")

    response = client.get("/api/v1/problems/71A")
    assert response.status_code == 200
    data = response.json()

    assert data["statement_content"] is not None
    statement = data["statement_content"]
    assert statement["title"] == "Way Too Long Words"
    assert statement["statement"] == "Parse the opening tag <a> and verify $x < y$ holds."
    assert statement["examples"] == [{"input": "2\nword\nlocalization\n", "output": "word\nl10n\n"}]
    assert statement["io_mode"] == "stdio"
    assert statement["is_interactive"] is False
    assert statement["has_missing_diagrams"] is False
    assert statement["availability"] == {
        "status": "complete_standard",
        "display_ready": True,
        "solve_ready": True,
        "unavailable_reason": None,
    }
    assert statement["source"] == {
        "dataset": "open-r1/codeforces",
        "urls": ["https://codeforces.com/problemset/problem/71/A"],
    }

    # The public API response must never leak judging/private internals,
    # even now that statement_content is populated from imported data.
    serialized = json.dumps(data).lower()
    for forbidden in ("editorial", "reference_code", "judge_tests", "expected_output"):
        assert forbidden not in serialized


def test_problem_without_imported_statement_has_missing_statement_content(client, catalog):
    response = client.get("/api/v1/problems/1364B")
    assert response.status_code == 200
    body = response.json()
    assert body["arena_capable"] is False
    content = body["statement_content"]
    assert content is not None
    assert content["availability"]["status"] == "missing"
    assert content["availability"]["display_ready"] is False
    assert content["availability"]["unavailable_reason"] == "Statement not available in SolveX yet."
    assert "no content record" not in json.dumps(body)


def test_newest_active_authored_content_is_selected(client, catalog):
    assert duels.upsert_duel_problem_pack(
        {
            "pack_id": "test-71a-v2",
            "problem_id": "71A",
            "version": 2,
            "statement_summary": "Version two public summary.",
            "input_format": "Version two input.",
            "output_format": "Version two output.",
            "constraints_text": "Version two constraints.",
            "sample_tests": [{"input": "1\nword\n", "output": "word\n"}],
            "judge_tests": [{"input": "private\n", "expected_output": "private\n"}],
        }
    )

    data = client.get("/api/v1/problems/71A").json()
    assert data["authored_content"]["summary"] == "Version two public summary."
    with store.connect() as conn:
        states = conn.execute(
            "SELECT version, active FROM duel_problem_packs WHERE problem_id = '71A' ORDER BY version"
        ).fetchall()
    assert [(row["version"], row["active"]) for row in states] == [(1, 0), (2, 1)]
