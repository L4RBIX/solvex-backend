"""Shared helpers for seeding display-ready problem_statements in tests."""

from __future__ import annotations

import json

from contestiq_api.cfdata import store


def seed_display_ready_statements(problem_ids: list[str] | None = None) -> int:
    """Insert minimal display-ready statement rows for catalog problems.

    Arena eligibility requires ``problem_statements.display_ready``. Most
    recommendation/practice fixtures only seed ``problems`` / packs; this
    helper makes those IDs Arena-capable without importing a full archive.
    """
    now = store._now()
    batch_id = "test-display-ready-batch"
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_import_batches
                (batch_id, source_name, source_sha256, status, started_at)
            VALUES (?, 'test-archive.zip', 'testhash', 'completed', ?)
            """,
            (batch_id, now),
        )
        if problem_ids is None:
            rows = conn.execute("SELECT problem_key, name FROM problems").fetchall()
        else:
            rows = []
            for pid in problem_ids:
                row = conn.execute(
                    "SELECT problem_key, name FROM problems WHERE problem_key = ?",
                    (pid,),
                ).fetchone()
                if row:
                    rows.append(row)
                else:
                    rows.append({"problem_key": pid, "name": pid})
        inserted = 0
        for row in rows:
            pid = row["problem_key"]
            existing = conn.execute(
                "SELECT 1 FROM problem_statements WHERE problem_id = ?",
                (pid,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE problem_statements
                    SET display_ready = 1,
                        solve_ready = 1,
                        availability_status = 'complete_standard',
                        statement = COALESCE(NULLIF(TRIM(statement), ''), 'Test statement.'),
                        unavailable_reason = NULL
                    WHERE problem_id = ?
                    """,
                    (pid,),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO problem_statements (
                        problem_id, batch_id, content_hash, title, statement,
                        input_format, output_format, interaction_format, notes, samples,
                        time_limit_seconds, memory_limit_megabytes, difficulty, io_mode,
                        is_interactive, picture_count, has_missing_diagrams,
                        availability_status, display_ready, solve_ready, unavailable_reason,
                        source_dataset, source_urls, statement_relation, shared_statement_from,
                        imported_at
                    ) VALUES (
                        ?, ?, ?, ?, 'Test statement.',
                        'Input', 'Output', NULL, NULL, ?,
                        1.0, 256.0, NULL, 'stdio',
                        0, 0, 0,
                        'complete_standard', 1, 1, NULL,
                        'test', '[]', NULL, NULL, ?
                    )
                    """,
                    (
                        pid,
                        batch_id,
                        f"hash-{pid}",
                        row["name"] or pid,
                        json.dumps([{"input": "1\n", "output": "1\n"}]),
                        now,
                    ),
                )
            inserted += 1
        return inserted
