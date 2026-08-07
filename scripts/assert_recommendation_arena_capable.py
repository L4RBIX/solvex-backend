#!/usr/bin/env python3.11
"""Assert recommendation/queue Arena CTAs resolve to arena-capable problems.

Usage:
  python3.11 scripts/assert_recommendation_arena_capable.py
  SOLVEX_API_BASE=https://web-production-3ea15.up.railway.app \\
    python3.11 scripts/assert_recommendation_arena_capable.py

Checks handles: Dan1c, tourist, jiangly, Benq
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HANDLES = ("Dan1c", "tourist", "jiangly", "Benq")
MIN_ITEMS = 50


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def _collect_arena_ids(payload: dict) -> list[str]:
    ids: list[str] = []
    for item in payload.get("recommendedProblems") or []:
        if item.get("arenaAvailable") is True and item.get("contestId") is not None and item.get("index"):
            ids.append(f"{item['contestId']}{item['index']}")
    for item in payload.get("sevenDayQueue") or []:
        if item.get("arenaAvailable") is True and item.get("contestId") is not None and item.get("index"):
            ids.append(f"{item['contestId']}{item['index']}")
    for area in payload.get("frictionAreas") or []:
        for item in area.get("recommendedProblems") or []:
            if item.get("arenaAvailable") is True and item.get("contestId") is not None and item.get("index"):
                ids.append(f"{item['contestId']}{item['index']}")
    return ids


def main() -> int:
    base = os.environ.get("SOLVEX_API_BASE", "https://web-production-3ea15.up.railway.app").rstrip("/")
    checked: list[str] = []
    failures: list[str] = []

    for handle in HANDLES:
        analyze = _get(f"{base}/api/v1/compat/analyze/{handle}")
        for problem_id in _collect_arena_ids(analyze):
            checked.append(f"{handle}:{problem_id}")
            try:
                problem = _get(f"{base}/api/v1/problems/{problem_id}")
            except urllib.error.HTTPError as exc:
                failures.append(f"{handle}:{problem_id} HTTP {exc.code}")
                continue
            capable = problem.get("arena_capable")
            display_ready = (
                ((problem.get("statement_content") or {}).get("availability") or {}).get("display_ready")
            )
            if capable is not True or display_ready is not True:
                failures.append(
                    f"{handle}:{problem_id} arena_capable={capable} display_ready={display_ready}"
                )

    print(f"checked={len(checked)} unique_targets={len(set(p.split(':', 1)[1] for p in checked))}")
    if len(checked) < MIN_ITEMS and len(checked) > 0:
        # Fewer than 50 is acceptable when emitters return fewer; still require zero failures.
        print(f"note: fewer than {MIN_ITEMS} Arena targets available ({len(checked)})")
    if failures:
        print("FAILURES:")
        for row in failures:
            print(f"  {row}")
        return 1
    if not checked:
        print("FAILURE: no Arena targets found to validate")
        return 1
    print("OK: all SolveX-generated Arena targets are arena_capable + display_ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
