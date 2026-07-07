#!/usr/bin/env python3
"""In-process load test scenarios (Phase 09).

Drives the FastAPI app through TestClient with thread pools — measures the
application + SQLite layer without network overhead (label results as
in-process). Scenarios follow the Phase 09 spec, scaled by --scale.

Usage: python3.11 scripts/loadtest.py [--scale 1.0] [--out report.md]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import statistics
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

ADMIN_KEY = "loadtest-admin-key-0123456789"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(pct / 100.0 * (len(ordered) - 1))))]


def run_scenario(name: str, func, requests: int, concurrency: int) -> dict:
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    started = time.monotonic()

    def one(i: int):
        t0 = time.monotonic()
        status = func(i)
        latencies.append((time.monotonic() - t0) * 1000)
        statuses[status] = statuses.get(status, 0) + 1

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(one, range(requests)))
    wall = time.monotonic() - started
    errors = sum(count for status, count in statuses.items() if status >= 500)
    return {
        "scenario": name,
        "requests": requests,
        "concurrency": concurrency,
        "wall_s": round(wall, 2),
        "rps": round(requests / wall, 1) if wall > 0 else 0,
        "p50_ms": round(percentile(latencies, 50), 1),
        "p95_ms": round(percentile(latencies, 95), 1),
        "p99_ms": round(percentile(latencies, 99), 1),
        "statuses": dict(sorted(statuses.items())),
        "error_rate": round(errors / requests, 4) if requests else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    scale = args.scale

    workdir = tempfile.mkdtemp(prefix="solvex-loadtest-")
    os.chdir(workdir)
    os.environ["ADMIN_API_KEY"] = ADMIN_KEY
    os.environ["CONTESTIQ_API_OFFLINE_SAMPLE"] = "1"
    os.environ["JUDGE0_BASE_URL"] = "http://fake-judge0"
    os.environ["LOG_LEVEL"] = "WARNING"

    from fastapi.testclient import TestClient

    from contestiq_api.main import app
    from contestiq_api.skilltrace import judge0 as j0
    from contestiq_api import throttle

    throttle.DAILY_LIMITS = {k: 10_000_000 for k in throttle.DAILY_LIMITS}  # measure capacity, not caps

    class FakeJudge0:
        def __init__(self):
            self.count = 0

        def post(self, url, payload, headers):
            self.count += 1
            return {"token": f"tok-{self.count}"}

        def get(self, url, headers):
            return {"status": {"id": 3}, "stdout": base64.b64encode(b"1").decode(), "time": "0.01", "memory": 100}

    j0.set_adapter(j0.Judge0Adapter(post=FakeJudge0().post, get=FakeJudge0().get))
    client = TestClient(app)
    admin = {"X-Admin-Key": ADMIN_KEY}

    results = []

    # 1) 100 concurrent analysis requests (offline sample; distinct handles).
    n = max(1, int(100 * scale))
    results.append(run_scenario(
        "100 concurrent analysis requests",
        lambda i: client.post(f"/api/v1/weakness/load-user-{i}/analyze", headers=admin).status_code,
        n, min(n, 20),
    ))

    # 2) 1000 cached dashboard views (weakness latest for one prepared handle).
    client.post("/api/v1/weakness/cached-user/analyze", headers=admin)
    n = max(1, int(1000 * scale))
    results.append(run_scenario(
        "1000 cached dashboard views",
        lambda i: client.get("/api/v1/weakness/cached-user/latest", headers=admin).status_code,
        n, min(n, 50),
    ))

    # 3) 50 concurrent Judge0 runs (fake adapter, real session bookkeeping).
    user = client.post("/api/v1/admin/users", json={"handle": "load-verify"}, headers=admin).json()
    client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                json={"plan": "premium_student"}, headers=admin)
    token = {"Authorization": f"Bearer {user['api_token']}"}
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                          headers=token).json()
    sid = session["session_id"]
    n = max(1, int(50 * scale))
    results.append(run_scenario(
        "50 concurrent Judge0 runs",
        lambda i: client.post(f"/api/v1/verification/sessions/{sid}/run",
                              json={"language": "python3", "source_code": f"print({i})", "stdin": ""},
                              headers=token).status_code,
        n, min(n, 25),
    ))

    # 4) 500-applicant event dashboard.
    organizer = client.post("/api/v1/admin/users", json={"handle": "load-org"}, headers=admin).json()
    client.post(f"/api/v1/admin/users/{organizer['user_id']}/grant-entitlement",
                json={"plan": "event"}, headers=admin)
    org_token = {"Authorization": f"Bearer {organizer['api_token']}"}
    org = client.post("/api/v1/orgs", json={"name": "LoadOrg"}, headers=org_token).json()
    event = client.post(f"/api/v1/orgs/{org['org_id']}/events",
                        json={"name": "LoadEvent", "requirements": [{"skill_id": "implementation"}]},
                        headers=org_token).json()
    applicants = max(1, int(500 * scale))
    for i in range(applicants):
        client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                    json={"display_name": f"A{i}"}, headers=org_token)
    n = max(1, int(50 * scale))
    results.append(run_scenario(
        f"event dashboard with {applicants} applicants",
        lambda i: client.get(f"/api/v1/events/{event['event_id']}/dashboard", headers=org_token).status_code,
        n, min(n, 10),
    ))

    # 5) Codeforces outage: failing transport → sync must fail fast with 502.
    from contestiq_api.cfdata import sync as cf_sync
    from contestiq_api.cfdata.client import CircuitBreaker, CodeforcesClient, GlobalRateLimiter

    def outage_transport(url, params, timeout):
        raise TimeoutError("cf outage")

    outage_client = CodeforcesClient(
        transport=outage_transport,
        rate_limiter=GlobalRateLimiter(0.0, clock=lambda: 0.0, sleep=lambda s: None),
        breaker=CircuitBreaker(failure_threshold=3, cooldown_seconds=60),
        sleep=lambda s: None, rng=lambda: 0.0, max_retries=1,
    )

    def outage_call(i: int) -> int:
        try:
            cf_sync.sync_handle(f"outage-user-{i}", client=outage_client)
            return 200
        except Exception:
            return 502

    n = max(1, int(20 * scale))
    results.append(run_scenario("Codeforces outage (circuit breaker)", outage_call, n, min(n, 10)))

    # 6) Judge0 callback storm: valid + replayed callbacks.
    with __import__("sqlite3").connect("api_cache/backend_jobs.db") as conn:
        conn.row_factory = __import__("sqlite3").Row
        subs = [dict(r) for r in conn.execute(
            "SELECT * FROM judge0_submissions WHERE submission_status = 'submitted' LIMIT 200").fetchall()]
    payloads = []
    for sub in subs:
        payloads.append((sub["callback_secret"], {"token": sub["judge0_token"], "status": {"id": 3},
                                                  "stdout": base64.b64encode(b"1").decode()}))
    storm = max(1, int(500 * scale))

    def callback_call(i: int) -> int:
        secret, payload = payloads[i % len(payloads)]
        return client.put(f"/api/v1/judge0/callback?secret={secret}", json=payload).status_code

    if payloads:
        results.append(run_scenario("Judge0 callback storm (with replays)", callback_call, storm, min(storm, 25)))

    lines = [
        "# SolveX Load Test Report",
        "",
        f"- Mode: in-process (TestClient + SQLite), scale={scale}",
        f"- Date: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "- Note: numbers measure application + storage layer; network/TLS overhead excluded.",
        "",
        "| Scenario | Requests | Conc. | Wall (s) | RPS | p50 ms | p95 ms | p99 ms | Statuses | Err rate |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['scenario']} | {r['requests']} | {r['concurrency']} | {r['wall_s']} | {r['rps']} "
            f"| {r['p50_ms']} | {r['p95_ms']} | {r['p99_ms']} | {json.dumps(r['statuses'])} | {r['error_rate']} |"
        )
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
