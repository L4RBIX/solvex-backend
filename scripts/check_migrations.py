#!/usr/bin/env python3
"""Migration sanity check (Phase 09). Exit 1 on problems.

- db/migrations files are sequentially numbered with no gaps/duplicates;
- every migration contains at least one CREATE TABLE / ALTER statement;
- every backend-owned table enables row level security;
- the SQLite mirror schema (cfdata/store.py) parses and creates cleanly.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
IN_REPO_MIGRATIONS = BACKEND / "db" / "migrations"
LEGACY_MONOREPO_MIGRATIONS = BACKEND.parent.parent / "db" / "migrations"
MIGRATIONS = IN_REPO_MIGRATIONS if IN_REPO_MIGRATIONS.exists() else LEGACY_MONOREPO_MIGRATIONS


def main() -> int:
    errors: list[str] = []
    files = sorted(MIGRATIONS.glob("[0-9]*.sql"))
    if not files:
        print(f"No migrations found in {MIGRATIONS}")
        return 1

    numbers = []
    created_tables: dict[str, str] = {}
    rls_enabled: set[str] = set()
    for path in files:
        match = re.match(r"^(\d{3})_", path.name)
        if not match:
            errors.append(f"bad migration filename: {path.name}")
            continue
        numbers.append(int(match.group(1)))
        sql = path.read_text(encoding="utf-8").lower()
        if "create table" not in sql and "alter table" not in sql:
            errors.append(f"{path.name}: no create/alter statement found")
        for table in re.findall(r"create table if not exists (\w+)", sql):
            created_tables[table] = path.name
        rls_enabled.update(re.findall(r"alter table (\w+) enable row level security", sql))

    # RLS may be enabled in a later hardening migration — check across all files.
    for table, origin in sorted(created_tables.items()):
        if table not in rls_enabled:
            errors.append(f"table '{table}' (created in {origin}) never enables RLS")

    duplicates = {n for n in numbers if numbers.count(n) > 1}
    if duplicates:
        errors.append(f"duplicate migration numbers: {sorted(duplicates)}")
    expected = list(range(min(numbers), max(numbers) + 1))
    missing = sorted(set(expected) - set(numbers))
    if missing:
        errors.append(f"gaps in migration numbering: {missing}")

    # SQLite mirror must build a clean schema.
    sys.path.insert(0, str(BACKEND))
    try:
        from contestiq_api.cfdata.store import _SCHEMA

        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if len(tables) < 30:
            errors.append(f"SQLite mirror created only {len(tables)} tables — expected 30+")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"SQLite mirror schema failed: {exc}")

    if errors:
        print("MIGRATION CHECK FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Migration check passed: {len(files)} migrations, sequential, RLS enabled, SQLite mirror OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
