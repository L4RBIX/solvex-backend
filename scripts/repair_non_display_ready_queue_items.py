#!/usr/bin/env python3.11
"""Repair persisted recommendation/plan items that are not Arena display-ready.

Marks recommendation_items / training_plan_items whose problem_id fails
``is_arena_solvable`` by rewriting them to a focus-only placeholder is unsafe.
Instead this script deletes non-display-ready concrete items from the newest
active containers so the next analyze/plan rebuild fills with eligible IDs.

Usage:
  python3.11 scripts/repair_non_display_ready_queue_items.py --dry-run
  python3.11 scripts/repair_non_display_ready_queue_items.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contestiq_api.arena_eligibility import is_arena_solvable  # noqa: E402
from contestiq_api.cfdata import store  # noqa: E402


def _collect_bad_ids(conn) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for table, id_col in (
        ("recommendation_items", "item_id"),
        ("training_plan_items", "item_id"),
        ("practice_continuations", "continuation_id"),
    ):
        try:
            found = conn.execute(
                f"SELECT {id_col} AS row_id, problem_id FROM {table} WHERE problem_id IS NOT NULL"
            ).fetchall()
        except Exception:
            continue
        for row in found:
            pid = row["problem_id"]
            if pid and not is_arena_solvable(pid):
                rows.append((table, row["row_id"], pid))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    apply = bool(args.apply)

    with store.connect() as conn:
        bad = _collect_bad_ids(conn)
        print(f"non_display_ready_persisted_items={len(bad)}")
        for table, row_id, pid in bad[:40]:
            print(f"  {table} {row_id} -> {pid}")
        if len(bad) > 40:
            print(f"  … {len(bad) - 40} more")
        if not apply:
            print("dry-run only; pass --apply to delete these rows")
            return 0
        deleted = 0
        for table, row_id, _pid in bad:
            id_col = {
                "recommendation_items": "item_id",
                "training_plan_items": "item_id",
                "practice_continuations": "continuation_id",
            }[table]
            conn.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (row_id,))
            deleted += 1
        print(f"deleted={deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
