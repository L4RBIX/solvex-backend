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
