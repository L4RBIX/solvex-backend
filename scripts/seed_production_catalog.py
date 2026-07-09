#!/usr/bin/env python3
"""Seed the shared problem catalog and skill map after a deploy.

The problem catalog (`problems`) and the derived `problem_skill_map` are not
part of db/migrations — they are seeded data, fetched from the Codeforces
public API and then rebuilt deterministically. On Railway, if DATABASE_PATH
is not pointed at a persistent volume, both are wiped by every redeploy,
which is what causes "empty daily queue despite many episodes" bugs even
though the code itself is fine.

Run this once after any deploy that starts from an empty/fresh database
(check first with GET /api/v1/admin/storage-health — if `catalog_ready` is
false, run this script). It is safe to re-run any time: the problemset sync
skips refetching within CODEFORCES_PROBLEMSET_TTL_HOURS unless --force is
passed, and the skill-map rebuild is a deterministic, idempotent upsert.

Usage:
    python3.11 scripts/seed_production_catalog.py \\
        --base-url https://web-production-3ea15.up.railway.app \\
        --admin-key "$ADMIN_API_KEY"

    # Force a full problemset refetch even if the TTL hasn't expired yet:
    python3.11 scripts/seed_production_catalog.py --base-url ... --admin-key ... --force
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

# POST /api/v1/sync/problemset and POST /api/v1/skill-map/rebuild are
# unauthenticated (Codeforces problemset data isn't sensitive), so --admin-key
# is only required for the optional --check-only storage-health probe.
SYNC_TIMEOUT_SECONDS = 120


def _post(url: str, payload: dict, admin_key: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if admin_key:
        headers["X-Admin-Key"] = admin_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=SYNC_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str, admin_key: str | None = None) -> dict:
    headers = {"X-Admin-Key": admin_key} if admin_key else {}
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="Backend base URL, e.g. https://web-production-3ea15.up.railway.app")
    parser.add_argument("--admin-key", default=None, help="ADMIN_API_KEY, only needed for --check-only")
    parser.add_argument("--force", action="store_true", help="Force a full problemset refetch even if the TTL hasn't expired")
    parser.add_argument("--check-only", action="store_true", help="Only print GET /api/v1/admin/storage-health and exit (requires --admin-key)")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    if args.check_only:
        if not args.admin_key:
            print("--check-only requires --admin-key", file=sys.stderr)
            return 2
        health = _get(f"{base}/api/v1/admin/storage-health", args.admin_key)
        print(json.dumps(health, indent=2))
        return 0 if health.get("catalog_ready") else 1

    try:
        print(f"Syncing problemset from {base} ...")
        problemset = _post(f"{base}/api/v1/sync/problemset", {"force": args.force})
        print(json.dumps(problemset, indent=2))

        print("Rebuilding problem_skill_map ...")
        skill_map = _post(f"{base}/api/v1/skill-map/rebuild", {})
        print(json.dumps(skill_map, indent=2))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {exc.url}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    mapped = skill_map.get("problems_mapped", 0)
    if not mapped:
        print("WARNING: 0 problems mapped — the catalog may still be empty.", file=sys.stderr)
        return 1
    print(f"Done: {mapped} problems mapped to skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
