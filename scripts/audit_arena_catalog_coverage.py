#!/usr/bin/env python3.11
"""Audit Arena catalog vs imported statement coverage.

Usage:
  python3.11 scripts/audit_arena_catalog_coverage.py
  python3.11 scripts/audit_arena_catalog_coverage.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contestiq_api.cfdata import store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    stats = store.arena_catalog_coverage_stats()
    if args.json:
        print(json.dumps(stats, indent=2, sort_keys=True))
        return 0

    print("SolveX Arena catalog coverage")
    print(f"  total canonical problems : {stats['total_canonical_problems']}")
    print(f"  with statement row       : {stats['with_statement_row']}")
    print(f"  display_ready            : {stats['display_ready']}")
    print(f"  solve_ready              : {stats['solve_ready']}")
    print(f"  missing/not display-ready: {stats['missing_or_not_display_ready']}")
    print("  availability_status counts:")
    for key, value in sorted((stats.get("availability_status_counts") or {}).items()):
        print(f"    {key}: {value}")
    print("  sample missing IDs:")
    for pid in stats.get("sample_missing_ids") or []:
        print(f"    {pid}")
    print("  probe 2228B:")
    print(f"    {stats.get('probe_2228B')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
