#!/usr/bin/env python3.11
"""Audit CF problemset.problems vs SolveX canonical catalog parity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contestiq_api.cfdata import store  # noqa: E402
from contestiq_api.cfdata.client import CodeforcesClient  # noqa: E402
from contestiq_core.codeforces.normalizer import stable_problem_key  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = CodeforcesClient().get_problemset()
    problems = (result.data or {}).get("problems") or []
    cf_ids = {
        stable_problem_key(p)
        for p in problems
        if isinstance(p, dict) and stable_problem_key(p)
    }
    report = store.catalog_parity_report(cf_ids)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("SolveX ↔ Codeforces catalog parity")
        print(f"  Codeforces : {report['cf_total']}")
        print(f"  SolveX     : {report['solvex_total']}")
        print(f"  matched    : {report['matched']}")
        print(f"  CF_ONLY    : {report['missing_from_solvex']}")
        print(f"  SOLVEX_ONLY: {report['extra_historical_solvex']}")
        if report["cf_only_ids"]:
            print("  missing IDs:")
            for pid in report["cf_only_ids"]:
                print(f"    {pid}")
    return 0 if report["missing_from_solvex"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
