#!/usr/bin/env python3.11
"""24/7 Codeforces statement-fetch relay worker.

Pulls leased jobs from SolveX, fetches official problem HTML at low rate,
and posts results back. Designed to run as a Railway service (or any host
where curl_cffi chrome116 can reach Codeforces).

Env:
  SOLVEX_API_BASE          default https://web-production-3ea15.up.railway.app
  STATEMENT_RELAY_TOKEN    required bearer token
  STATEMENT_RELAY_ID       default railway-relay
  STATEMENT_RELAY_VERSION  default 1.0.0
  RELAY_POLL_SECONDS       default 20
  RELAY_FETCH_SLEEP        default 3
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

VERSION = os.getenv("STATEMENT_RELAY_VERSION", "1.0.0")
RELAY_ID = os.getenv("STATEMENT_RELAY_ID", "railway-relay")
BASE = (os.getenv("SOLVEX_API_BASE") or "https://web-production-3ea15.up.railway.app").rstrip("/")
TOKEN = (os.getenv("STATEMENT_RELAY_TOKEN") or "").strip()
POLL_SECONDS = float(os.getenv("RELAY_POLL_SECONDS") or "20")
FETCH_SLEEP = float(os.getenv("RELAY_FETCH_SLEEP") or "3")


def _api(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
            "X-Relay-Id": RELAY_ID,
            "User-Agent": f"SolveXStatementRelay/{VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {path}: {body[:300]}") from exc


def _fetch_html(url: str) -> tuple[int, str, str]:
    from curl_cffi import requests as cf_requests

    last_status = 0
    last_text = ""
    last_url = url
    for impersonate in ("chrome116", "chrome110", "chrome99"):
        response = cf_requests.get(
            url,
            impersonate=impersonate,
            timeout=30,
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        last_status = int(response.status_code)
        last_text = response.text or ""
        last_url = str(getattr(response, "url", url) or url)
        if last_status == 200 and "problem-statement" in last_text:
            return last_status, last_text, last_url
    return last_status, last_text, last_url


def _heartbeat() -> None:
    _api("POST", "/api/v1/relay/statements/heartbeat", {"version": VERSION, "note": "ok"})


def process_one() -> bool:
    payload = _api("GET", "/api/v1/relay/statements/jobs/next?limit=1")
    job = payload.get("job")
    if not job:
        return False
    problem_id = job["problem_id"]
    url = job["official_url"]
    print(json.dumps({"event": "relay_fetch_start", "problem_id": problem_id, "url": url}), flush=True)
    try:
        status, html, final_url = _fetch_html(url)
    except Exception as exc:
        _api(
            "POST",
            f"/api/v1/relay/statements/jobs/{problem_id}/result",
            {
                "http_status": None,
                "error": str(exc)[:400],
                "failure_class": "retryable",
            },
        )
        print(json.dumps({"event": "relay_fetch_error", "problem_id": problem_id, "error": str(exc)[:200]}), flush=True)
        return True

    result_body: dict[str, Any] = {
        "http_status": status,
        "final_url": final_url,
    }
    if status == 200 and "problem-statement" in html:
        result_body["html"] = html
    else:
        result_body["error"] = f"fetch_not_usable status={status}"
        if status in {401, 403} or "just a moment" in html.lower():
            result_body["failure_class"] = "blocked"
        elif status == 404:
            result_body["failure_class"] = "permanent"
        else:
            result_body["failure_class"] = "retryable"
        # Do not ship challenge pages as HTML.
        result_body["html"] = None

    out = _api("POST", f"/api/v1/relay/statements/jobs/{problem_id}/result", result_body)
    print(
        json.dumps(
            {
                "event": "relay_fetch_done",
                "problem_id": problem_id,
                "http_status": status,
                "ingest": (out.get("ingest") or {}).get("status"),
            }
        ),
        flush=True,
    )
    time.sleep(FETCH_SLEEP)
    return True


def main() -> int:
    if not TOKEN or len(TOKEN) < 24:
        print("STATEMENT_RELAY_TOKEN required (>=24 chars)", file=sys.stderr)
        return 2
    print(json.dumps({"event": "relay_start", "base": BASE, "relay_id": RELAY_ID, "version": VERSION}), flush=True)
    while True:
        try:
            _heartbeat()
            worked = process_one()
            if not worked:
                time.sleep(POLL_SECONDS)
        except Exception as exc:
            print(json.dumps({"event": "relay_loop_error", "error": str(exc)[:300]}), flush=True)
            time.sleep(max(15.0, POLL_SECONDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
