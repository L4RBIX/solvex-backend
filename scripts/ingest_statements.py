#!/usr/bin/env python3.11
"""Enqueue/process automatic Codeforces statement ingestion.

Usage:
  python3.11 scripts/ingest_statements.py --enqueue-only
  python3.11 scripts/ingest_statements.py --limit 40 --min-contest-id 2248
  python3.11 scripts/ingest_statements.py --problem-id 2254A --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contestiq_api.cfdata import statement_ingest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enqueue-only", action="store_true")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--min-contest-id", type=int, default=None)
    parser.add_argument("--problem-id", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    problem_ids = args.problem_id or None
    if args.enqueue_only:
        report = statement_ingest.enqueue_statement_ingestion(
            problem_ids, reason="cli", only_missing=problem_ids is None
        )
    elif problem_ids:
        statement_ingest.enqueue_statement_ingestion(problem_ids, reason="cli")
        report = statement_ingest.process_statement_ingest_batch(
            limit=args.limit or len(problem_ids),
            problem_ids=problem_ids,
            force=args.force,
        )
    else:
        report = statement_ingest.backfill_missing_statements(
            limit=args.limit,
            min_contest_id=args.min_contest_id,
            force=args.force,
        )

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
