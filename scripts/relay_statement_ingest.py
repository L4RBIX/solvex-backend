#!/usr/bin/env python3.11
"""Relay: fetch official CF HTML locally and upsert into SolveX production.

Railway cannot fetch Codeforces pages (Cloudflare 403). This relay runs on a
network that can, then POSTs HTML to /api/v1/admin/statements/ingest-html.

Usage:
  ADMIN_API_KEY=... python3.11 scripts/relay_statement_ingest.py --limit 40 --min-contest-id 2248
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from curl_cffi import requests as cf_requests  # noqa: E402


def api(base: str, key: str, method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "X-Admin-Key": key},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SOLVEX_API_BASE", "https://web-production-3ea15.up.railway.app"))
    parser.add_argument("--admin-key", default=os.getenv("ADMIN_API_KEY", ""))
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--min-contest-id", type=int, default=2248)
    parser.add_argument("--problem-id", action="append", default=[])
    parser.add_argument("--sleep", type=float, default=2.5)
    args = parser.parse_args()
    if not args.admin_key:
        print("ADMIN_API_KEY required", file=sys.stderr)
        return 2

    if args.problem_id:
        chosen = []
        for pid in args.problem_id:
            m = re.match(r"^(\d+)([A-Za-z][A-Za-z0-9]*)$", pid)
            if not m:
                print("skip invalid", pid)
                continue
            chosen.append((pid, int(m.group(1)), m.group(2).upper()))
    else:
        stats = api(args.base_url, args.admin_key, "GET", "/api/v1/admin/statements/ingest/stats")
        ids = stats.get("missing_newest") or []
        chosen = []
        for pid in ids:
            m = re.match(r"^(\d+)([A-Za-z][A-Za-z0-9]*)$", pid)
            if not m:
                continue
            if int(m.group(1)) < args.min_contest_id:
                continue
            chosen.append((pid, int(m.group(1)), m.group(2).upper()))
            if len(chosen) >= args.limit:
                break

    print("selected", [c[0] for c in chosen])
    items = []
    for pid, contest_id, index in chosen:
        url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        r = cf_requests.get(url, impersonate="chrome131", timeout=30)
        ok = r.status_code == 200 and "problem-statement" in (r.text or "")
        print("fetch", pid, r.status_code, "ok" if ok else "fail", len(r.text or ""))
        if ok:
            items.append({"problem_id": pid, "html": r.text})
        time.sleep(args.sleep)

    if not items:
        print("no HTML fetched", file=sys.stderr)
        return 1

    totals = {"succeeded": 0, "failed": 0, "partial": 0, "asset_required": 0}
    coverage = None
    for i in range(0, len(items), 5):
        chunk = items[i : i + 5]
        out = api(args.base_url, args.admin_key, "POST", "/api/v1/admin/statements/ingest-html", {"items": chunk})
        for k in totals:
            totals[k] += int(out.get(k) or 0)
        coverage = out.get("coverage")
        print("upsert_chunk", [c["problem_id"] for c in chunk], {k: out.get(k) for k in totals})

    print(json.dumps({"totals": totals, "coverage": coverage}, indent=2))
    return 0 if totals["succeeded"] + totals["partial"] + totals["asset_required"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
