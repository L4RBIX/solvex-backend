#!/usr/bin/env python3.11
"""Synchronize the SolveX canonical catalog from Codeforces problemset.problems.

Usage:
  python3.11 scripts/sync_codeforces_catalog.py
  python3.11 scripts/sync_codeforces_catalog.py --force
  python3.11 scripts/sync_codeforces_catalog.py --dry-run

Exit code 0 only when missing_from_solvex_after == 0 (after a real sync),
or when --dry-run reports the current gap without writing.
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
from contestiq_api.cfdata import sync as cf_sync  # noqa: E402
from contestiq_api.cfdata.client import CodeforcesClient  # noqa: E402
from contestiq_core.codeforces.normalizer import stable_problem_key  # noqa: E402


def _cf_ids(client: CodeforcesClient | None = None) -> set[str]:
    client = client or CodeforcesClient()
    result = client.get_problemset()
    problems = (result.data or {}).get("problems") or []
    ids: set[str] = set()
    for problem in problems:
        if not isinstance(problem, dict):
            continue
        key = stable_problem_key(problem)
        if key:
            ids.add(key)
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Bypass TTL and refetch")
    parser.add_argument("--dry-run", action="store_true", help="Report parity only; no writes")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    if args.dry_run:
        cf_ids = _cf_ids()
        report = store.catalog_parity_report(cf_ids)
        payload = {"mode": "dry_run", **report}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("Codeforces catalog parity (dry-run)")
            print(f"  cf_total                 : {report['cf_total']}")
            print(f"  solvex_total             : {report['solvex_total']}")
            print(f"  matched                  : {report['matched']}")
            print(f"  missing_from_solvex      : {report['missing_from_solvex']}")
            print(f"  extra_historical_solvex  : {report['extra_historical_solvex']}")
            if report["cf_only_ids"]:
                print("  CF_ONLY sample:")
                for pid in report["cf_only_ids"][:40]:
                    print(f"    {pid}")
        return 0 if report["missing_from_solvex"] == 0 else 1

    result = cf_sync.sync_problemset(force=args.force)
    catalog = (result or {}).get("catalog_sync") or {}
    if args.json:
        print(json.dumps({"mode": "sync", "result": result}, indent=2, sort_keys=True, default=str))
    else:
        print("Codeforces catalog sync")
        print(f"  status                   : {result.get('status')}")
        print(f"  refetched                : {result.get('refetched')}")
        for key in (
            "cf_total",
            "solvex_before",
            "new_problems",
            "updated_problems",
            "unchanged",
            "statement_stubs_created",
            "solvex_after",
            "missing_from_solvex_after",
            "extra_historical_solvex",
            "sync_duration_ms",
        ):
            if key in catalog:
                print(f"  {key:26}: {catalog[key]}")
        sample = catalog.get("cf_only_ids_sample") or []
        if sample:
            print("  remaining CF_ONLY sample:")
            for pid in sample:
                print(f"    {pid}")
    missing = int(catalog.get("missing_from_solvex_after") or 0)
    # Fresh TTL skip is OK if we already have parity.
    if result.get("refetched") is False and result.get("status") == "fresh":
        cf_ids = _cf_ids()
        missing = store.catalog_parity_report(cf_ids)["missing_from_solvex"]
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
