"""Importer for the SolveX problem-statement database export.

The source archive is a flat zip with no directories: manifest.json,
problem_catalog.json(.gz), problem_content.json(.gz), problem_assets_queue.json,
problem_fallback_queue.json. It is PUBLIC DISPLAY content — plain text and
LaTeX, no HTML — meant to populate the `problem_statements` table so the
public problem API (contestiq_api/routes/problems.py) can show real
statements instead of only authored duel-pack summaries.

SECURITY — read this before touching this file:

1. `editorial` and `reference_code` are present in the source content records
   and contain full solutions. This module NEVER reads those two keys off a
   content entry, anywhere. `_parse_content_entry` only ever pulls the
   specific fields listed in its body — do not change it to pass the raw
   content dict through, and do not add "editorial" or "reference_code" to
   any payload, report, or log line below.
2. This module never imports into or reads from `duel_problem_packs`, and the
   `problem_statements` table it writes to has no judge-test column at all.
   Judging content and display content are different trust boundaries.
3. Archive extraction re-validates path/size safety at runtime (zip slip,
   absolute paths, symlinks, zip-bomb entry/size limits) even though the
   known-good archive has already been audited — defense in depth against a
   corrupted or swapped file.
4. Every file's sha256 is checked against manifest.json before any row is
   imported; a mismatch aborts the whole batch.

CATALOG BACKFILL: routes/problems.py resolves a problem through the
`problems` table first (populated by the live CF problemset sync), and only
then looks up `problem_statements`. A fresh database with no CF sync ever
run would otherwise 404 every problem even after a successful statement
import. So this importer ALSO backfills `problems`/`problem_statistics` from
problem_catalog.json, keyed with the exact same `stable_problem_key` helper
the live sync uses. PRECEDENCE RULE: this archive is a point-in-time
snapshot; the live sync is the fresher, authoritative source, so this only
INSERTs rows that don't already exist (see `_upsert_catalog_row_if_missing`)
and never overwrites what a live sync already populated.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import stat
import sqlite3
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from contestiq_api.cfdata import store
from contestiq_core.codeforces.normalizer import stable_problem_key

# ─── Safety limits (defense in depth; the audited archive is ~23MB / 7 files) ─

MAX_UNCOMPRESSED_TOTAL_BYTES = 200 * 1024 * 1024  # 200MB zip-bomb guard
MAX_ARCHIVE_ENTRIES = 50
DEFAULT_CHUNK_SIZE = 500

REQUIRED_FILES = (
    "manifest.json",
    "problem_catalog.json",
    "problem_content.json",
    "problem_assets_queue.json",
    "problem_fallback_queue.json",
)

VALID_AVAILABILITY_STATUSES = (
    "missing",
    "asset_required",
    "complete_interactive",
    "partial",
    "complete_standard",
)


class ArchiveSecurityError(ValueError):
    """Raised when the archive fails path/size/entry-count safety checks."""


class ChecksumMismatchError(ValueError):
    """Raised when a file's sha256 doesn't match manifest.json."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Archive extraction & validation ─────────────────────────────────────────


def _validate_entry_name(name: str) -> None:
    if not name or name.endswith("/"):
        raise ArchiveSecurityError(f"unsupported directory entry: {name!r}")
    if name.startswith("/") or name.startswith("\\"):
        raise ArchiveSecurityError(f"absolute path entry rejected: {name!r}")
    if len(name) > 1 and name[1] == ":":  # e.g. "C:\\..."
        raise ArchiveSecurityError(f"absolute path entry rejected: {name!r}")
    parts = PurePosixPath(name).parts
    if PurePosixPath(name).is_absolute() or ".." in parts:
        raise ArchiveSecurityError(f"path traversal entry rejected: {name!r}")


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return bool(mode) and stat.S_ISLNK(mode)


def _read_archive_members(archive_path: Path) -> dict[str, bytes]:
    """Extract every entry into memory after re-validating archive safety.

    Rejects absolute paths, `..` traversal, symlink entries, too many
    entries, and a total uncompressed size over MAX_UNCOMPRESSED_TOTAL_BYTES
    (zip-bomb guard). Never writes anything to disk.
    """
    with zipfile.ZipFile(archive_path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise ArchiveSecurityError(
                f"archive has {len(infos)} entries, exceeds max {MAX_ARCHIVE_ENTRIES}"
            )
        members: dict[str, bytes] = {}
        total_uncompressed = 0
        for info in infos:
            _validate_entry_name(info.filename)
            if _is_symlink(info):
                raise ArchiveSecurityError(f"symlink entries are not allowed: {info.filename!r}")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_UNCOMPRESSED_TOTAL_BYTES:
                raise ArchiveSecurityError(
                    "archive exceeds max total uncompressed size (zip-bomb guard)"
                )
            members[info.filename] = zf.read(info)
    missing = [name for name in REQUIRED_FILES if name not in members]
    if missing:
        raise ArchiveSecurityError(f"archive is missing required files: {missing}")
    return members


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_checksums(members: dict[str, bytes], manifest: dict[str, Any]) -> None:
    files_meta = manifest.get("files")
    if not isinstance(files_meta, dict):
        raise ChecksumMismatchError("manifest.json has no 'files' checksum table")
    for name, meta in files_meta.items():
        if name not in members:
            continue  # e.g. the .gz twin we don't need to read
        expected = meta.get("sha256") if isinstance(meta, dict) else None
        if not isinstance(expected, str):
            raise ChecksumMismatchError(f"manifest.json has no sha256 for {name!r}")
        actual = hashlib.sha256(members[name]).hexdigest()
        if actual != expected:
            raise ChecksumMismatchError(
                f"checksum mismatch for {name!r}: expected {expected}, got {actual}"
            )


def _load_json_member(members: dict[str, bytes], name: str) -> Any:
    """Read a plain .json member (the .json/.json.gz pairs are byte-identical
    per the dataset audit; we always read the plain .json, never the gzip)."""
    return json.loads(members[name].decode("utf-8"))


# ─── Stable hashing ───────────────────────────────────────────────────────────


def _stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json_dumps(payload).encode("utf-8")).hexdigest()


# ─── Catalog / content validation (quarantine boundary) ──────────────────────


def _validate_catalog_row(row: Any) -> str | None:
    """Return a quarantine reason, or None if the catalog row is well-formed
    enough to look up content for. Does not require content to exist."""
    if not isinstance(row, dict):
        return "catalog row is not a JSON object"
    problem_id = row.get("problem_id")
    if not isinstance(problem_id, str) or not problem_id.strip():
        return "missing or blank problem_id"
    contest_id = row.get("contest_id")
    if not isinstance(contest_id, int) or isinstance(contest_id, bool):
        return "contest_id is not an integer"
    return None


def _validate_content_entry(content: Any) -> str | None:
    """Return a quarantine reason, or None if the content entry is safe to
    classify. `content` may be None (no content record for this problem)."""
    if content is None:
        return None
    if not isinstance(content, dict):
        return "content entry is not a JSON object"
    examples = content.get("examples")
    if examples is not None and not isinstance(examples, list):
        return "examples is not a list"
    if isinstance(examples, list):
        for example in examples:
            if not isinstance(example, dict):
                return "sample entry is not a {input, output} object"
            if not isinstance(example.get("input"), str) or not isinstance(example.get("output"), str):
                return "sample entry is not a {input, output} string pair"
    return None


def _extract_samples(examples: Any) -> list[dict[str, str]]:
    if not isinstance(examples, list):
        return []
    samples: list[dict[str, str]] = []
    for example in examples:
        if isinstance(example, dict) and isinstance(example.get("input"), str) and isinstance(
            example.get("output"), str
        ):
            # Stored verbatim: some problems (e.g. 125B, 172E) legitimately
            # contain literal "<a>"/"<p>" as problem content (XML-parsing
            # problems) — never strip or HTML-sanitize this text.
            samples.append({"input": example["input"], "output": example["output"]})
    return samples


# ─── Classification (deterministic, see PR spec for the exact rules) ─────────


def _classify(catalog_row: dict[str, Any], content: dict[str, Any] | None) -> dict[str, Any]:
    catalog_status = catalog_row.get("content_status")

    if content is None:
        return {
            "title": None,
            "statement": None,
            "input_format": None,
            "output_format": None,
            "interaction_format": None,
            "notes": None,
            "samples": [],
            "time_limit_seconds": None,
            "memory_limit_megabytes": None,
            "difficulty": None,
            "io_mode": None,
            "is_interactive": False,
            "picture_count": None,
            "has_missing_diagrams": bool(catalog_row.get("missing_assets")),
            "availability_status": "missing",
            "display_ready": False,
            "solve_ready": False,
            "unavailable_reason": "Statement not available in SolveX yet.",
            "source_dataset": None,
            "source_urls": [],
            "statement_relation": None,
            "shared_statement_from": None,
        }

    # NOTE: this function only ever reads the specific keys below. It must
    # NEVER read content.get("editorial") or content.get("reference_code").
    statement = content.get("description") or ""
    raw_statement = content.get("raw_statement") or ""
    interaction_format = content.get("interaction_format") or None
    io_mode = content.get("input_mode")
    if io_mode not in ("stdio", "file"):
        io_mode = None

    is_interactive = bool(interaction_format) or catalog_status == "complete_interactive"

    picture_count = content.get("picture_count")
    picture_count_num = picture_count if isinstance(picture_count, int) else 0
    asset_required = bool(content.get("asset_required"))
    has_missing_diagrams = (
        bool(catalog_row.get("missing_assets"))
        or asset_required
        or (picture_count_num > 0 and catalog_row.get("asset_status") == "missing")
    )

    if asset_required or catalog_status == "special_asset_required":
        availability_status = "asset_required"
    elif is_interactive:
        availability_status = "complete_interactive"
    elif catalog_status in ("partial", "raw_only") or not statement.strip():
        availability_status = "partial"
    else:
        availability_status = "complete_standard"

    if catalog_status == "raw_only":
        display_ready = bool(statement.strip()) or bool(raw_statement.strip())
    else:
        display_ready = bool(statement.strip())

    samples = _extract_samples(content.get("examples"))
    solve_ready = display_ready and len(samples) >= 1 and not is_interactive and io_mode != "file"

    sources = content.get("sources")
    source_urls = [s for s in sources if isinstance(s, str)] if isinstance(sources, list) else []
    source_url = content.get("source_url")
    if isinstance(source_url, str) and source_url not in source_urls:
        source_urls = [source_url, *source_urls]

    return {
        "title": content.get("title"),
        "statement": statement or None,
        "input_format": content.get("input_format"),
        "output_format": content.get("output_format"),
        "interaction_format": interaction_format,
        "notes": content.get("note"),
        "samples": samples,
        "time_limit_seconds": content.get("time_limit_seconds"),
        "memory_limit_megabytes": content.get("memory_limit_megabytes"),
        "difficulty": content.get("difficulty"),
        "io_mode": io_mode,
        "is_interactive": is_interactive,
        "picture_count": picture_count if isinstance(picture_count, int) else None,
        "has_missing_diagrams": has_missing_diagrams,
        "availability_status": availability_status,
        "display_ready": display_ready,
        "solve_ready": solve_ready,
        "unavailable_reason": content.get("content_unavailable_reason"),
        "source_dataset": content.get("source"),
        "source_urls": source_urls,
        "statement_relation": content.get("statement_relation"),
        "shared_statement_from": content.get("shared_statement_from"),
    }


# ─── Report ───────────────────────────────────────────────────────────────────


@dataclass
class ImportReport:
    batch_id: str
    status: str
    dry_run: bool
    source_name: str
    source_sha256: str
    manifest_version: str | None
    started_at: str
    completed_at: str
    duration_seconds: float
    total_catalog: int
    imported: int
    updated: int
    skipped: int
    quarantined: int
    catalog_rows_created: int
    catalog_rows_existing_skipped: int
    availability_status_counts: dict[str, int]
    display_ready_count: int
    solve_ready_count: int
    fallback_queue_count: int
    asset_queue_count: int
    error: str | None = None
    quarantine_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "status": self.status,
            "dry_run": self.dry_run,
            "source_name": self.source_name,
            "source_sha256": self.source_sha256,
            "manifest_version": self.manifest_version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "total_catalog": self.total_catalog,
            "imported": self.imported,
            "updated": self.updated,
            "skipped": self.skipped,
            "quarantined": self.quarantined,
            "catalog_rows_created": self.catalog_rows_created,
            "catalog_rows_existing_skipped": self.catalog_rows_existing_skipped,
            "availability_status_counts": self.availability_status_counts,
            "display_ready_count": self.display_ready_count,
            "solve_ready_count": self.solve_ready_count,
            "fallback_queue_count": self.fallback_queue_count,
            "asset_queue_count": self.asset_queue_count,
            "error": self.error,
            "quarantine_reasons": self.quarantine_reasons,
        }


# ─── DB helpers (this module owns problem_import_* writes, mirroring how
# contestiq_api/duels.py owns duel_problem_packs writes via store.connect()) ──


def _get_batch(conn: sqlite3.Connection, batch_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM problem_import_batches WHERE batch_id = ?", (batch_id,)
    ).fetchone()
    return dict(row) if row else None


def _create_or_resume_batch(
    conn: sqlite3.Connection,
    batch_id: str,
    source_name: str,
    source_sha256: str,
    manifest_version: str | None,
) -> None:
    existing = _get_batch(conn, batch_id)
    if existing is None:
        conn.execute(
            """
            INSERT INTO problem_import_batches
                (batch_id, source_name, source_sha256, manifest_version, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (batch_id, source_name, source_sha256, manifest_version, _now()),
        )
    else:
        # Resuming a previously running/failed batch under the same id.
        conn.execute(
            """
            UPDATE problem_import_batches
            SET status = 'running', source_sha256 = ?, manifest_version = ?, completed_at = NULL
            WHERE batch_id = ?
            """,
            (source_sha256, manifest_version, batch_id),
        )
    conn.commit()


def _update_batch_progress(conn: sqlite3.Connection, batch_id: str, totals: dict[str, int]) -> None:
    conn.execute(
        """
        UPDATE problem_import_batches
        SET total_catalog = ?, imported = ?, updated = ?, skipped = ?, quarantined = ?,
            catalog_rows_created = ?, catalog_rows_existing_skipped = ?
        WHERE batch_id = ?
        """,
        (
            totals["total_catalog"],
            totals["imported"],
            totals["updated"],
            totals["skipped"],
            totals["quarantined"],
            totals["catalog_rows_created"],
            totals["catalog_rows_existing_skipped"],
            batch_id,
        ),
    )
    conn.commit()


def _finish_batch(conn: sqlite3.Connection, batch_id: str, status: str, totals: dict[str, int]) -> None:
    conn.execute(
        """
        UPDATE problem_import_batches
        SET status = ?, completed_at = ?, total_catalog = ?, imported = ?, updated = ?,
            skipped = ?, quarantined = ?, catalog_rows_created = ?, catalog_rows_existing_skipped = ?
        WHERE batch_id = ?
        """,
        (
            status,
            _now(),
            totals["total_catalog"],
            totals["imported"],
            totals["updated"],
            totals["skipped"],
            totals["quarantined"],
            totals["catalog_rows_created"],
            totals["catalog_rows_existing_skipped"],
            batch_id,
        ),
    )
    conn.commit()


def _existing_content_hash(conn: sqlite3.Connection, problem_id: str) -> str | None:
    row = conn.execute(
        "SELECT content_hash FROM problem_statements WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    return row["content_hash"] if row else None


def _upsert_statement(
    conn: sqlite3.Connection,
    problem_id: str,
    batch_id: str,
    content_hash: str,
    payload: dict[str, Any],
) -> None:
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
        ON CONFLICT(problem_id) DO UPDATE SET
            batch_id=excluded.batch_id,
            content_hash=excluded.content_hash,
            title=excluded.title,
            statement=excluded.statement,
            input_format=excluded.input_format,
            output_format=excluded.output_format,
            interaction_format=excluded.interaction_format,
            notes=excluded.notes,
            samples=excluded.samples,
            time_limit_seconds=excluded.time_limit_seconds,
            memory_limit_megabytes=excluded.memory_limit_megabytes,
            difficulty=excluded.difficulty,
            io_mode=excluded.io_mode,
            is_interactive=excluded.is_interactive,
            picture_count=excluded.picture_count,
            has_missing_diagrams=excluded.has_missing_diagrams,
            availability_status=excluded.availability_status,
            display_ready=excluded.display_ready,
            solve_ready=excluded.solve_ready,
            unavailable_reason=excluded.unavailable_reason,
            source_dataset=excluded.source_dataset,
            source_urls=excluded.source_urls,
            statement_relation=excluded.statement_relation,
            shared_statement_from=excluded.shared_statement_from,
            imported_at=excluded.imported_at
        """,
        {
            "problem_id": problem_id,
            "batch_id": batch_id,
            "content_hash": content_hash,
            "title": payload["title"],
            "statement": payload["statement"],
            "input_format": payload["input_format"],
            "output_format": payload["output_format"],
            "interaction_format": payload["interaction_format"],
            "notes": payload["notes"],
            "samples": _stable_json_dumps(payload["samples"]),
            "time_limit_seconds": payload["time_limit_seconds"],
            "memory_limit_megabytes": payload["memory_limit_megabytes"],
            "difficulty": payload["difficulty"],
            "io_mode": payload["io_mode"],
            "is_interactive": int(bool(payload["is_interactive"])),
            "picture_count": payload["picture_count"],
            "has_missing_diagrams": int(bool(payload["has_missing_diagrams"])),
            "availability_status": payload["availability_status"],
            "display_ready": int(bool(payload["display_ready"])),
            "solve_ready": int(bool(payload["solve_ready"])),
            "unavailable_reason": payload["unavailable_reason"],
            "source_dataset": payload["source_dataset"],
            "source_urls": _stable_json_dumps(payload["source_urls"]),
            "statement_relation": payload["statement_relation"],
            "shared_statement_from": payload["shared_statement_from"],
            "imported_at": _now(),
        },
    )


def _upsert_catalog_row_if_missing(conn: sqlite3.Connection, catalog_row: dict[str, Any]) -> bool:
    """Backfill `problems`/`problem_statistics` from one catalog row.

    Uses the same `stable_problem_key` the live CF problemset sync
    (store.save_problemset_snapshot) uses, so keys match exactly and
    duel/practice lookups keep working against either source.

    PRECEDENCE RULE: this archive is a 2026-07-26 point-in-time snapshot;
    the live CF sync is the authoritative, fresher source for catalog
    metadata. INSERT OR IGNORE means an existing row (from a prior or later
    live sync) is never overwritten by stale archive data — only missing
    rows are created. Returns True iff a new `problems` row was created.
    """
    problem_key = stable_problem_key(catalog_row)
    now = _now()
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO problems
            (problem_key, contest_id, problem_index, name, rating, tags, problemset_name, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            problem_key,
            catalog_row.get("contest_id"),
            catalog_row.get("index"),
            catalog_row.get("name") or problem_key,
            catalog_row.get("rating"),
            json.dumps(catalog_row.get("tags") or [], ensure_ascii=False),
            catalog_row.get("problemset_name"),
            now,
        ),
    )
    created = cursor.rowcount > 0
    if created:
        # solved_count from the archive only accompanies a newly created
        # catalog row — an existing problem_statistics row is left to the
        # live sync for the same precedence reason as `problems` above.
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_statistics (problem_key, solved_count, updated_at)
            VALUES (?, ?, ?)
            """,
            (problem_key, catalog_row.get("solved_count"), now),
        )
    return created


def _insert_quarantine(
    conn: sqlite3.Connection,
    batch_id: str,
    problem_id: str | None,
    reason: str,
    detail: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO problem_import_quarantine (id, batch_id, problem_id, reason, detail, quarantined_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), batch_id, problem_id, reason, detail, _now()),
    )


# ─── Main entry point ─────────────────────────────────────────────────────────


def import_problem_database(
    archive_path: Path | str,
    batch_id: str | None = None,
    dry_run: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ImportReport:
    """Import the problem-statement database export into `problem_statements`.

    Deterministic: iterates the catalog sorted by problem_id.
    Idempotent: a row whose computed content_hash matches what's already
        stored is left untouched and counted as 'skipped'.
    Resumable: re-running with the same batch_id continues a batch that
        never reached 'completed' — already-current rows are skipped fast,
        the rest are (re)written, and the batch is finalized.
    Never crashes on bad data: malformed catalog/content records are
        quarantined (batch continues); only archive-level failures (safety
        violation, checksum mismatch) abort the whole batch.
    """
    archive_path = Path(archive_path)
    started = time.monotonic()
    started_at = _now()
    batch_id = batch_id or str(uuid.uuid4())
    source_name = archive_path.name

    members = _read_archive_members(archive_path)  # raises ArchiveSecurityError
    manifest = _load_json_member(members, "manifest.json")
    if not isinstance(manifest, dict):
        raise ChecksumMismatchError("manifest.json did not parse to a JSON object")
    _verify_checksums(members, manifest)  # raises ChecksumMismatchError
    source_sha256 = _sha256_file(archive_path)
    manifest_version = manifest.get("version") if isinstance(manifest.get("version"), str) else None

    catalog = _load_json_member(members, "problem_catalog.json")
    content_map = _load_json_member(members, "problem_content.json")
    fallback_queue = _load_json_member(members, "problem_fallback_queue.json")
    asset_queue = _load_json_member(members, "problem_assets_queue.json")

    if not isinstance(catalog, list):
        raise ArchiveSecurityError("problem_catalog.json did not parse to a JSON list")
    if not isinstance(content_map, dict):
        raise ArchiveSecurityError("problem_content.json did not parse to a JSON object")

    fallback_queue_count = len(fallback_queue) if isinstance(fallback_queue, list) else 0
    asset_queue_count = len(asset_queue) if isinstance(asset_queue, list) else 0

    totals = {
        "total_catalog": len(catalog),
        "imported": 0,
        "updated": 0,
        "skipped": 0,
        "quarantined": 0,
        "catalog_rows_created": 0,
        "catalog_rows_existing_skipped": 0,
    }
    availability_counts: dict[str, int] = {status: 0 for status in VALID_AVAILABILITY_STATUSES}
    quarantine_reasons: dict[str, int] = {}
    display_ready_count = 0
    solve_ready_count = 0
    seen_problem_ids: set[str] = set()

    conn = None if dry_run else store.connect()
    status = "running"
    error_message: str | None = None
    try:
        if conn is not None:
            _create_or_resume_batch(conn, batch_id, source_name, source_sha256, manifest_version)

        def quarantine(problem_id: str | None, reason: str, detail: str | None = None) -> None:
            totals["quarantined"] += 1
            quarantine_reasons[reason] = quarantine_reasons.get(reason, 0) + 1
            if conn is not None:
                _insert_quarantine(conn, batch_id, problem_id, reason, detail)

        # Separate malformed rows (no usable problem_id / not a dict / bad
        # contest_id) before sorting — those can't be ordered by problem_id.
        valid_rows: list[tuple[str, dict[str, Any]]] = []
        for row in catalog:
            reason = _validate_catalog_row(row)
            if reason is not None:
                problem_id = row.get("problem_id") if isinstance(row, dict) else None
                quarantine(problem_id if isinstance(problem_id, str) else None, reason, repr(row)[:500])
                continue
            problem_id = row["problem_id"]
            if problem_id in seen_problem_ids:
                quarantine(problem_id, "duplicate problem_id in catalog", None)
                continue
            seen_problem_ids.add(problem_id)
            valid_rows.append((problem_id, row))

        valid_rows.sort(key=lambda item: item[0])

        processed_since_commit = 0
        for problem_id, catalog_row in valid_rows:
            if conn is not None:
                # Backfill problems/problem_statistics regardless of whether
                # this row's *content* later turns out to be quarantined —
                # the catalog metadata (name/rating/tags) is independent of
                # problem_content.json and is still valid on its own.
                if _upsert_catalog_row_if_missing(conn, catalog_row):
                    totals["catalog_rows_created"] += 1
                else:
                    totals["catalog_rows_existing_skipped"] += 1

            content = content_map.get(problem_id)
            reason = _validate_content_entry(content)
            if reason is not None:
                quarantine(problem_id, reason, None)
                continue

            payload = _classify(catalog_row, content)
            content_hash = _content_hash(payload)

            availability_counts[payload["availability_status"]] = (
                availability_counts.get(payload["availability_status"], 0) + 1
            )
            if payload["display_ready"]:
                display_ready_count += 1
            if payload["solve_ready"]:
                solve_ready_count += 1

            if conn is None:
                # dry-run: classify and count only, never write or query state.
                totals["imported"] += 1
                continue

            existing_hash = _existing_content_hash(conn, problem_id)
            if existing_hash == content_hash:
                totals["skipped"] += 1
                continue
            _upsert_statement(conn, problem_id, batch_id, content_hash, payload)
            if existing_hash is None:
                totals["imported"] += 1
            else:
                totals["updated"] += 1

            processed_since_commit += 1
            if processed_since_commit >= chunk_size:
                _update_batch_progress(conn, batch_id, totals)
                processed_since_commit = 0

        status = "completed"
        if conn is not None:
            _finish_batch(conn, batch_id, status, totals)
    except Exception as exc:  # noqa: BLE001 - convert to a failed batch record, then re-raise
        status = "failed"
        error_message = str(exc)
        if conn is not None:
            try:
                _finish_batch(conn, batch_id, status, totals)
            except Exception:  # noqa: BLE001 - don't mask the original error
                pass
        raise
    finally:
        if conn is not None:
            conn.close()

    completed_at = _now()
    duration = time.monotonic() - started
    return ImportReport(
        batch_id=batch_id,
        status=status,
        dry_run=dry_run,
        source_name=source_name,
        source_sha256=source_sha256,
        manifest_version=manifest_version,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration,
        total_catalog=totals["total_catalog"],
        imported=totals["imported"],
        updated=totals["updated"],
        skipped=totals["skipped"],
        quarantined=totals["quarantined"],
        catalog_rows_created=totals["catalog_rows_created"],
        catalog_rows_existing_skipped=totals["catalog_rows_existing_skipped"],
        availability_status_counts=availability_counts,
        display_ready_count=display_ready_count,
        solve_ready_count=solve_ready_count,
        fallback_queue_count=fallback_queue_count,
        asset_queue_count=asset_queue_count,
        error=error_message,
        quarantine_reasons=quarantine_reasons,
    )


def apply_statement_content(
    problem_id: str,
    catalog_row: dict[str, Any],
    content: dict[str, Any] | None,
    *,
    batch_id: str,
    source_name: str = "codeforces-official-page",
    force: bool = False,
) -> dict[str, Any]:
    """Classify + upsert one statement through the same trusted import path.

    Used by automatic HTML ingestion so live fetches reuse `_classify` /
    `_upsert_statement` instead of inventing a second statement store.

    Overwrite policy (unless ``force``):
    - always allow replacing ``missing`` / pending-* stubs / empty statements
    - allow replacing ``partial`` rows
    - skip already display-ready rows from other trusted sources
    """
    reason = _validate_content_entry(content)
    if reason is not None:
        raise ValueError(f"invalid content for {problem_id}: {reason}")

    payload = _classify(catalog_row, content)
    # Prefer an explicit ingest source tag when the content omitted it.
    if content and not payload.get("source_dataset"):
        payload["source_dataset"] = content.get("source") or source_name
    content_hash = _content_hash(payload)

    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_import_batches
                (batch_id, source_name, source_sha256, status, started_at)
            VALUES (?, ?, 'n/a', 'completed', ?)
            """,
            (batch_id, source_name, _now()),
        )
        existing = conn.execute(
            """
            SELECT content_hash, availability_status, display_ready, source_dataset, statement
            FROM problem_statements WHERE problem_id = ?
            """,
            (problem_id,),
        ).fetchone()
        if existing is not None and not force:
            existing_hash = existing["content_hash"]
            if existing_hash == content_hash:
                return {
                    "action": "skipped",
                    "reason": "unchanged",
                    "payload": payload,
                    "content_hash": content_hash,
                }
            is_pending = str(existing_hash or "").startswith("pending-")
            is_missing = existing["availability_status"] == "missing" or not (
                existing["statement"] or ""
            ).strip()
            is_partial = existing["availability_status"] == "partial"
            already_ready = bool(existing["display_ready"])
            if already_ready and not is_pending and not is_missing and not is_partial:
                other_source = existing["source_dataset"]
                if other_source and other_source != (payload.get("source_dataset") or source_name):
                    return {
                        "action": "skipped",
                        "reason": "display_ready_other_source",
                        "payload": {
                            "availability_status": existing["availability_status"],
                            "display_ready": True,
                            "solve_ready": False,
                        },
                        "content_hash": existing_hash,
                    }

        action = "imported" if existing is None else "updated"
        _upsert_statement(conn, problem_id, batch_id, content_hash, payload)
        conn.commit()

    return {
        "action": action,
        "reason": None,
        "payload": payload,
        "content_hash": content_hash,
    }
