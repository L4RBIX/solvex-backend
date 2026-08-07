#!/usr/bin/env python3.11
"""Import only missing statement rows from a newer verified archive.

Baseline bulk dataset remains authoritative. This script reuses
``import_problem_database`` against a newer zip so catalog IDs that lack
display-ready content can be filled without scraping HTML.

Usage:
  python3.11 scripts/import_missing_statements.py --archive /path/to/solvex_problem_database_vN.zip
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contestiq_api.cfdata import store  # noqa: E402
from contestiq_api.cfdata.problem_import import import_problem_database  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, help="Verified SolveX problem database zip")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args()

    before = store.arena_catalog_coverage_stats()
    print("before:", {k: before[k] for k in (
        "total_canonical_problems", "display_ready", "missing_or_not_display_ready"
    )})
    report = import_problem_database(
        args.archive,
        batch_id=args.batch_id,
        dry_run=args.dry_run,
    )
    after = store.arena_catalog_coverage_stats()
    print("import_report:", report.to_dict() if hasattr(report, "to_dict") else report)
    print("after:", {k: after[k] for k in (
        "total_canonical_problems", "display_ready", "missing_or_not_display_ready"
    )})
    print("probe_2228B:", after.get("probe_2228B"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
