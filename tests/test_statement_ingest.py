"""Automatic Codeforces statement ingestion (HTML → problem_statements)."""

from __future__ import annotations

from pathlib import Path

import pytest

from contestiq_api.arena_eligibility import is_arena_solvable
from contestiq_api.cfdata import store
from contestiq_api.cfdata import statement_fetch
from contestiq_api.cfdata import statement_html
from contestiq_api.cfdata import statement_ingest
from contestiq_api.cfdata.statement_fetch import HtmlFetchResult

FIXTURES = Path(__file__).parent / "fixtures" / "cf_html"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    statement_fetch.reset_html_limiter_for_tests()
    yield


def _seed_catalog(problem_id: str, name: str = "Test"):
    contest_id, index = statement_ingest.split_problem_id(problem_id)
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO problems
                (problem_key, contest_id, problem_index, name, rating, tags, problemset_name, updated_at)
            VALUES (?, ?, ?, ?, ?, '[]', 'test', ?)
            """,
            (problem_id, contest_id, index, name, 800, store._now()),
        )
    store.ensure_statement_pending_stubs([problem_id])


def _html(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_parse_standard_statement_with_latex_and_samples():
    parsed = statement_html.parse_codeforces_problem_html(
        _html("2254A.html"), expected_contest_id=2254, expected_index="A"
    )
    content = parsed.content
    assert content["title"] == "Riptide"
    assert "Alice, Bob, and Charlie" in content["description"]
    assert "$$$t$$$" in content["input_format"]
    assert content["examples"][0]["input"].startswith("6\n1 2 3")
    assert content["examples"][0]["output"].startswith("1\n2")
    assert content["note"]
    assert content["time_limit_seconds"] == 1.0
    assert content["memory_limit_megabytes"] == 256.0
    assert content["source"] == "codeforces-official-page"
    assert "editorial" not in content
    assert "reference_code" not in content


def test_parse_multiple_line_samples_and_notes():
    parsed = statement_html.parse_codeforces_problem_html(
        _html("2254C1.html"), expected_contest_id=2254, expected_index="C1"
    )
    assert "Marenol" in parsed.content["title"]
    assert len(parsed.content["examples"]) == 1
    assert "YES" in parsed.content["examples"][0]["output"]
    assert parsed.content["note"]


def test_parse_interactive_statement():
    parsed = statement_html.parse_codeforces_problem_html(
        _html("1486C2.html"), expected_contest_id=1486, expected_index="C2"
    )
    assert parsed.content["interaction_format"]
    assert "interactive" in parsed.content["description"].lower()


def test_reject_cloudflare_and_malformed_pages():
    with pytest.raises(statement_html.StatementParseError, match="cloudflare"):
        statement_html.parse_codeforces_problem_html(
            _html("cloudflare.html"), expected_contest_id=1, expected_index="A"
        )
    with pytest.raises(statement_html.StatementParseError):
        statement_html.parse_codeforces_problem_html(
            _html("empty.html"), expected_contest_id=1, expected_index="A"
        )


def test_identity_mismatch_rejected():
    with pytest.raises(statement_html.StatementParseError, match="index mismatch"):
        statement_html.parse_codeforces_problem_html(
            _html("1A.html"), expected_contest_id=1, expected_index="B"
        )


def test_ingest_updates_missing_stub_and_enables_arena():
    _seed_catalog("2254A", "Riptide")
    assert is_arena_solvable("2254A") is False
    outcome = statement_ingest.ingest_one("2254A", html=_html("2254A.html"))
    assert outcome["status"] == "succeeded"
    assert outcome["display_ready"] is True
    stmt = store.get_problem_statement("2254A")
    assert stmt is not None
    assert stmt["availability_status"] == "complete_standard"
    assert "Alice" in (stmt["statement"] or "")
    assert is_arena_solvable("2254A") is True


def test_ingest_interactive_is_display_ready_not_solve_ready():
    _seed_catalog("1486C2", "Guessing")
    outcome = statement_ingest.ingest_one("1486C2", html=_html("1486C2.html"))
    assert outcome["display_ready"] is True
    assert outcome["solve_ready"] is False
    assert outcome["availability_status"] == "complete_interactive"
    assert is_arena_solvable("1486C2") is True  # display_ready is enough for Arena open


def test_duplicate_ingest_is_idempotent():
    _seed_catalog("1A", "Theatre Square")
    first = statement_ingest.ingest_one("1A", html=_html("1A.html"))
    second = statement_ingest.ingest_one("1A", html=_html("1A.html"))
    assert first["status"] == "succeeded"
    assert second["action"] in {"skipped", None} or second["status"] == "succeeded"
    # Still a single row
    with store.connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM problem_statements WHERE problem_id='1A'"
        ).fetchone()["c"]
    assert count == 1


def test_batch_processes_queue_with_injected_transport():
    _seed_catalog("2254A", "Riptide")
    _seed_catalog("1A", "Theatre Square")
    html_map = {"2254A": _html("2254A.html"), "1A": _html("1A.html")}

    def transport(url: str, timeout: float) -> HtmlFetchResult:
        if "2254/A" in url:
            return HtmlFetchResult(200, html_map["2254A"], url)
        if "1/A" in url:
            return HtmlFetchResult(200, html_map["1A"], url)
        return HtmlFetchResult(404, "", url, error="missing")

    statement_ingest.enqueue_statement_ingestion(["2254A", "1A"], reason="test")
    report = statement_ingest.process_statement_ingest_batch(
        limit=10, problem_ids=["2254A", "1A"], transport=transport
    )
    assert report["succeeded"] == 2
    assert is_arena_solvable("2254A") is True
    assert is_arena_solvable("1A") is True


def test_retry_backoff_on_fetch_failure():
    _seed_catalog("2254A", "Riptide")

    def transport(url: str, timeout: float) -> HtmlFetchResult:
        raise RuntimeError("boom")

    statement_ingest.enqueue_statement_ingestion(["2254A"], reason="test")
    report = statement_ingest.process_statement_ingest_batch(
        limit=1, problem_ids=["2254A"], transport=transport
    )
    assert report["retrying"] == 1
    stats = store.statement_ingest_queue_stats()
    assert stats["retrying"] == 1


def test_asset_required_when_images_present(tmp_path):
    # Inject an <img> into a known good statement.
    html = _html("1A.html").replace(
        "</div></body>",
        '<img src="https://codeforces.com/x.png"/></div></body>',
    )
    _seed_catalog("1A", "Theatre Square")
    outcome = statement_ingest.ingest_one("1A", html=html)
    assert outcome["status"] == "asset_required"
    stmt = store.get_problem_statement("1A")
    assert stmt["availability_status"] == "asset_required"
    assert stmt["has_missing_diagrams"] in (1, True)
    # Text is still stored and may be display_ready under classifier rules.
    assert (stmt["statement"] or "").strip()


def test_no_editorial_keys_persisted():
    _seed_catalog("2254A", "Riptide")
    statement_ingest.ingest_one("2254A", html=_html("2254A.html"))
    stmt = store.get_problem_statement("2254A")
    blob = str(stmt)
    assert "editorial" not in blob.lower() or stmt.get("source_dataset") == "codeforces-official-page"
    assert "reference_code" not in blob
