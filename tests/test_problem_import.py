"""Tests for the SolveX problem-statement database importer.

Uses a small SYNTHETIC archive fixture built in-process (never the real
23MB dataset export) so these tests are fast and self-contained. Every
synthetic content entry includes `editorial`/`reference_code` with an
obvious marker string so the "never persisted" test can prove those never
reach the database, in addition to the parser never reading those keys.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from contestiq_api.cfdata import problem_import as pi
from contestiq_api.cfdata import store


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test_import.db"))
    yield


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _base_catalog_row(problem_id="1A", contest_id=1, index="A", content_status="complete_standard", **overrides):
    row = {
        "problem_id": problem_id,
        "contest_id": contest_id,
        "index": index,
        "name": f"Problem {problem_id}",
        "type": "PROGRAMMING",
        "points": None,
        "rating": 800,
        "tags": ["implementation"],
        "solved_count": 100,
        "problemset_name": None,
        "url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
        "content_status": content_status,
        "asset_status": "unknown",
        "missing_assets": False,
    }
    row.update(overrides)
    return row


def _base_content_entry(**overrides):
    entry = {
        "source": "open-r1/codeforces",
        "dataset_problem_id": "1/A",
        "title": "Sample Problem",
        "time_limit_seconds": 1.0,
        "memory_limit_megabytes": 256.0,
        "description": "Solve the problem.",
        "input_format": "One integer n.",
        "output_format": "Print n.",
        "interaction_format": None,
        "examples": [{"input": "1", "output": "1"}],
        "note": None,
        # Deliberately included with obvious marker strings — the importer
        # must never read or persist these two fields anywhere.
        "editorial": "TOP SECRET EDITORIAL MARKER 12345",
        "reference_code": "TOP SECRET REFERENCE CODE 67890",
        "difficulty": "EASY",
        "source_url": "https://codeforces.com/problemset/problem/1/A",
        "sources": ["open-r1/codeforces"],
        "input_mode": "stdio",
        "picture_count": 0,
        "asset_required": False,
        "content_unavailable_reason": None,
        "statement_intentionally_absent": False,
        "raw_statement": None,
        "raw_statement_format": None,
        "special_statement_format": None,
        "content_quality_note": None,
        "training_dataset_number": None,
        "raw_tags": [],
        "algorithm_tags": [],
        "tags": ["implementation"],
        "rating": 800,
        "shared_statement_from": None,
        "statement_relation": None,
    }
    entry.update(overrides)
    return entry


def _write_archive(
    path: Path,
    catalog: list,
    content: dict,
    fallback_queue: list | None = None,
    asset_queue: list | None = None,
    manifest_version: str = "1.0.0",
    tamper_file: str | None = None,
    extra_zip_entries: list[tuple[str, bytes, int]] | None = None,
) -> Path:
    payloads = {
        "problem_catalog.json": json.dumps(catalog, ensure_ascii=False).encode("utf-8"),
        "problem_content.json": json.dumps(content, ensure_ascii=False).encode("utf-8"),
        "problem_assets_queue.json": json.dumps(asset_queue or [], ensure_ascii=False).encode("utf-8"),
        "problem_fallback_queue.json": json.dumps(fallback_queue or [], ensure_ascii=False).encode("utf-8"),
    }
    files_meta = {name: {"size_bytes": len(data), "sha256": _sha256(data)} for name, data in payloads.items()}
    manifest = {
        "database_name": "Test Problem Database",
        "version": manifest_version,
        "files": files_meta,
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False).encode("utf-8")

    if tamper_file:
        # Corrupt the on-disk bytes AFTER the (now-stale) manifest checksum
        # was computed, simulating a corrupted/tampered file in the archive.
        payloads[tamper_file] = payloads[tamper_file] + b"tampered"

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_bytes)
        for name, data in payloads.items():
            zf.writestr(name, data)
        for name, data, external_attr in extra_zip_entries or []:
            info = zipfile.ZipInfo(name)
            info.external_attr = external_attr
            zf.writestr(info, data)

    return path


# ─── Idempotency / resumability / versioning ─────────────────────────────────


def test_import_is_idempotent_second_run_all_skipped(tmp_path):
    archive = _write_archive(
        tmp_path / "db.zip",
        catalog=[_base_catalog_row("1A"), _base_catalog_row("1B", index="B")],
        content={"1A": _base_content_entry(), "1B": _base_content_entry(title="Problem B")},
    )

    report1 = pi.import_problem_database(archive, batch_id="batch-1")
    assert report1.status == "completed"
    assert (report1.imported, report1.updated, report1.skipped) == (2, 0, 0)

    report2 = pi.import_problem_database(archive, batch_id="batch-2")
    assert report2.status == "completed"
    assert (report2.imported, report2.updated, report2.skipped) == (0, 0, 2)

    with store.connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
    assert count == 2


def test_resumable_interrupted_batch_continues_and_converges(tmp_path, monkeypatch):
    archive = _write_archive(
        tmp_path / "db.zip",
        catalog=[_base_catalog_row(f"{i}A", contest_id=i) for i in range(1, 6)],
        content={f"{i}A": _base_content_entry(title=f"Problem {i}") for i in range(1, 6)},
    )

    real_upsert = pi._upsert_statement
    call_count = {"n": 0}

    def flaky_upsert(conn, problem_id, batch_id, content_hash, payload):
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise RuntimeError("simulated crash mid-batch")
        return real_upsert(conn, problem_id, batch_id, content_hash, payload)

    monkeypatch.setattr(pi, "_upsert_statement", flaky_upsert)
    with pytest.raises(RuntimeError):
        pi.import_problem_database(archive, batch_id="resume-batch")

    with store.connect() as conn:
        batch = conn.execute(
            "SELECT status FROM problem_import_batches WHERE batch_id = ?", ("resume-batch",)
        ).fetchone()
        partial_count = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
    assert batch["status"] == "failed"
    assert partial_count < 5  # the crash happened before all 5 rows were written

    monkeypatch.setattr(pi, "_upsert_statement", real_upsert)
    report = pi.import_problem_database(archive, batch_id="resume-batch")
    assert report.status == "completed"
    assert report.imported + report.updated + report.skipped == 5

    with store.connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
        batch = conn.execute(
            "SELECT status FROM problem_import_batches WHERE batch_id = ?", ("resume-batch",)
        ).fetchone()
    assert count == 5
    assert batch["status"] == "completed"


def test_new_batch_records_source_sha256_and_updates_changed_content(tmp_path):
    archive_v1 = _write_archive(
        tmp_path / "v1.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry(description="Original statement.")},
    )
    report1 = pi.import_problem_database(archive_v1, batch_id="batch-v1")
    assert report1.status == "completed"
    assert report1.imported == 1

    archive_v2 = _write_archive(
        tmp_path / "v2.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry(description="Updated statement text.")},
    )
    report2 = pi.import_problem_database(archive_v2, batch_id="batch-v2")
    assert report2.status == "completed"
    assert (report2.imported, report2.updated) == (0, 1)

    with store.connect() as conn:
        batches = {row["batch_id"]: dict(row) for row in conn.execute("SELECT * FROM problem_import_batches")}
        row = conn.execute(
            "SELECT batch_id, statement FROM problem_statements WHERE problem_id = '1A'"
        ).fetchone()
    assert batches["batch-v1"]["source_sha256"] != batches["batch-v2"]["source_sha256"]
    assert row["batch_id"] == "batch-v2"
    assert row["statement"] == "Updated statement text."


def test_dry_run_never_writes_to_the_database(tmp_path):
    archive = _write_archive(
        tmp_path / "dry.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
    )
    report = pi.import_problem_database(archive, batch_id="dry-batch", dry_run=True)
    assert report.status == "completed"
    assert report.dry_run is True

    with store.connect() as conn:
        statements = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
        batches = conn.execute("SELECT COUNT(*) FROM problem_import_batches").fetchone()[0]
    assert statements == 0
    assert batches == 0


# ─── Archive safety ───────────────────────────────────────────────────────────


def test_checksum_mismatch_aborts_the_batch(tmp_path):
    archive = _write_archive(
        tmp_path / "bad.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
        tamper_file="problem_content.json",
    )
    with pytest.raises(pi.ChecksumMismatchError):
        pi.import_problem_database(archive, batch_id="bad-batch")

    with store.connect() as conn:
        statements = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
        batches = conn.execute(
            "SELECT COUNT(*) FROM problem_import_batches WHERE batch_id = 'bad-batch'"
        ).fetchone()[0]
    assert statements == 0
    assert batches == 0


@pytest.mark.parametrize(
    "entry_name,external_attr",
    [
        ("../evil.txt", 0),
        ("/etc/passwd", 0),
        ("subdir/../../escape.txt", 0),
        ("innocuous_symlink.txt", 0xA1FF << 16),  # S_IFLNK | 0o777
    ],
    ids=["parent-traversal", "absolute-path", "nested-traversal", "symlink-entry"],
)
def test_malicious_archive_entries_are_rejected(tmp_path, entry_name, external_attr):
    archive = _write_archive(
        tmp_path / "evil.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
        extra_zip_entries=[(entry_name, b"payload", external_attr)],
    )
    with pytest.raises(pi.ArchiveSecurityError):
        pi.import_problem_database(archive, batch_id="evil-batch")


def test_oversized_archive_triggers_zip_bomb_guard(tmp_path):
    huge_padding = b"\x00" * (pi.MAX_UNCOMPRESSED_TOTAL_BYTES + 1024 * 1024)
    archive = _write_archive(
        tmp_path / "bomb.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
        extra_zip_entries=[("huge_padding.bin", huge_padding, 0)],
    )
    with pytest.raises(pi.ArchiveSecurityError):
        pi.import_problem_database(archive, batch_id="bomb-batch")


# ─── Quarantine ───────────────────────────────────────────────────────────────


def test_malformed_records_are_quarantined_not_written_and_batch_completes(tmp_path):
    catalog = [
        _base_catalog_row("1A"),
        "not-a-dict-row",
        {"problem_id": "", "contest_id": 2},
        _base_catalog_row("3A", contest_id="not-an-int"),
        _base_catalog_row("4A", contest_id=4, index="A"),
        _base_catalog_row("5A", contest_id=5, index="A"),
    ]
    content = {
        "1A": _base_content_entry(),
        "4A": _base_content_entry(examples="not-a-list"),
        "5A": _base_content_entry(examples=[{"input": 5, "output": "5"}]),
    }
    archive = _write_archive(tmp_path / "malformed.zip", catalog=catalog, content=content)

    report = pi.import_problem_database(archive, batch_id="malformed-batch")

    assert report.status == "completed"
    assert report.total_catalog == 6
    assert report.imported == 1
    assert report.quarantined == 5

    with store.connect() as conn:
        ids = {row["problem_id"] for row in conn.execute("SELECT problem_id FROM problem_statements")}
        quarantine_count = conn.execute(
            "SELECT COUNT(*) FROM problem_import_quarantine WHERE batch_id = 'malformed-batch'"
        ).fetchone()[0]
    assert ids == {"1A"}
    assert quarantine_count == 5


# ─── Security: editorial / reference_code must never persist ────────────────


def test_editorial_and_reference_code_are_never_persisted_anywhere(tmp_path):
    archive = _write_archive(
        tmp_path / "secret.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
    )
    report = pi.import_problem_database(archive, batch_id="secret-batch")
    assert report.status == "completed"
    assert report.imported == 1

    with store.connect() as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        full_dump_parts = []
        for table in tables:
            columns = [col[1] for col in conn.execute(f"PRAGMA table_info({table})")]
            assert "editorial" not in columns
            assert "reference_code" not in columns
            for row in conn.execute(f"SELECT * FROM {table}"):
                full_dump_parts.append(str(tuple(row)))
        full_dump = "\n".join(full_dump_parts)

    assert "TOP SECRET EDITORIAL MARKER" not in full_dump
    assert "TOP SECRET REFERENCE CODE" not in full_dump


# ─── Classification rules ─────────────────────────────────────────────────────


def test_interaction_format_fixes_catalog_mislabeled_interactive_problem(tmp_path):
    archive = _write_archive(
        tmp_path / "interactive.zip",
        catalog=[_base_catalog_row("1A", content_status="complete_standard")],
        content={"1A": _base_content_entry(interaction_format="Read a query, print a response.")},
    )
    pi.import_problem_database(archive, batch_id="interactive-batch")

    with store.connect() as conn:
        row = conn.execute(
            "SELECT availability_status, is_interactive, solve_ready FROM problem_statements WHERE problem_id = '1A'"
        ).fetchone()
    assert row["is_interactive"] == 1
    assert row["availability_status"] == "complete_interactive"
    assert row["solve_ready"] == 0


def test_file_io_mode_forces_solve_ready_false(tmp_path):
    archive = _write_archive(
        tmp_path / "file_io.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry(input_mode="file")},
    )
    pi.import_problem_database(archive, batch_id="file-io-batch")

    with store.connect() as conn:
        row = conn.execute(
            "SELECT io_mode, display_ready, solve_ready FROM problem_statements WHERE problem_id = '1A'"
        ).fetchone()
    assert row["io_mode"] == "file"
    assert row["display_ready"] == 1
    assert row["solve_ready"] == 0


def test_missing_content_record_is_classified_missing(tmp_path):
    archive = _write_archive(
        tmp_path / "missing.zip",
        catalog=[_base_catalog_row("1A", content_status="missing")],
        content={},
    )
    report = pi.import_problem_database(archive, batch_id="missing-batch")
    assert report.imported == 1
    assert report.availability_status_counts["missing"] == 1

    with store.connect() as conn:
        row = conn.execute(
            "SELECT availability_status, display_ready, solve_ready FROM problem_statements WHERE problem_id = '1A'"
        ).fetchone()
    assert row["availability_status"] == "missing"
    assert row["display_ready"] == 0
    assert row["solve_ready"] == 0


def test_latex_and_angle_bracket_content_round_trips_verbatim(tmp_path):
    tricky_statement = (
        "Parse the opening tag <a> and verify $x < y$ holds.\n"
        "The matching closing tag </a> must appear later.\n"
        "Note: 5 < 10 and $\\alpha \\le \\beta$ must both hold."
    )
    archive = _write_archive(
        tmp_path / "xml.zip",
        catalog=[_base_catalog_row("125B", contest_id=125, index="B")],
        content={"125B": _base_content_entry(description=tricky_statement, title="XML Parsing")},
    )
    pi.import_problem_database(archive, batch_id="xml-batch")

    with store.connect() as conn:
        row = conn.execute("SELECT statement FROM problem_statements WHERE problem_id = '125B'").fetchone()
    assert row["statement"] == tricky_statement


def test_report_includes_queue_counts_and_source_sha256(tmp_path):
    archive = _write_archive(
        tmp_path / "queues.zip",
        catalog=[_base_catalog_row("1A")],
        content={"1A": _base_content_entry()},
        fallback_queue=[{"problem_id": "9A", "content_status": "missing"}],
        asset_queue=[{"problem_id": "8A", "asset_status": "missing"}],
    )
    report = pi.import_problem_database(archive, batch_id="queues-batch")
    assert report.fallback_queue_count == 1
    assert report.asset_queue_count == 1
    assert report.source_sha256 == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert report.batch_id == "queues-batch"
