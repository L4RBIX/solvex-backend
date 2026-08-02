#!/usr/bin/env python3
"""Import the SolveX problem-statement database export into problem_statements.

This is display content only (statements, samples, limits, difficulty). It
never imports `editorial` or `reference_code` (full solutions), and it never
touches duel_problem_packs or judge_tests — see
contestiq_api/cfdata/problem_import.py for the full security rationale.

Usage:
    python3 scripts/import_problem_database.py \\
        --archive /path/to/solvex_problem_database_v1.zip \\
        --database /tmp/solvex_import_check.db \\
        --report /tmp/import_report.json

    # Preview without writing anything:
    python3 scripts/import_problem_database.py --archive ... --dry-run

    # Resume a batch that was interrupted mid-run:
    python3 scripts/import_problem_database.py --archive ... --batch-id <same-id>

Exit codes: 0 = completed, 1 = batch finished but with status != completed,
2 = archive failed safety validation, 3 = checksum mismatch against manifest.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archive", required=True, help="Path to the problem database zip export")
    parser.add_argument(
        "--database",
        default=None,
        help="SQLite database path to write to (defaults to DATABASE_PATH env, then api_cache/backend_jobs.db)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and classify without writing to the database")
    parser.add_argument("--batch-id", default=None, help="Reuse a specific batch id (to resume an interrupted run)")
    parser.add_argument("--report", default=None, help="Write the JSON import report to this path")
    parser.add_argument("--chunk-size", type=int, default=500, help="Rows processed per commit chunk (default 500)")
    args = parser.parse_args()

    if args.database:
        os.environ["DATABASE_PATH"] = str(Path(args.database))

    from contestiq_api.cfdata import problem_import

    try:
        report = problem_import.import_problem_database(
            archive_path=Path(args.archive),
            batch_id=args.batch_id,
            dry_run=args.dry_run,
            chunk_size=args.chunk_size,
        )
    except problem_import.ArchiveSecurityError as exc:
        print(f"Archive failed safety validation: {exc}", file=sys.stderr)
        return 2
    except problem_import.ChecksumMismatchError as exc:
        print(f"Checksum mismatch against manifest.json, aborting: {exc}", file=sys.stderr)
        return 3

    report_dict = report.to_dict()
    print(json.dumps(report_dict, indent=2))
    if args.report:
        Path(args.report).write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        print(f"Report written to {args.report}", file=sys.stderr)

    return 0 if report.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
