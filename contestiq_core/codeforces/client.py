from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from contestiq_core.config import CACHE_DIR, CODEFORCES_API_BASE, DEFAULT_TIMEOUT_SECONDS, MAX_RETRIES, RATE_LIMIT_SECONDS

_last_request_at = 0.0

# Backoff delays (seconds) before each retry when Codeforces returns HTTP 429.
_RATE_LIMIT_BACKOFF_S: tuple[int, ...] = (3, 7, 15)


class CodeforcesAPIError(RuntimeError):
    pass


def _cache_path(endpoint: str, params: dict[str, Any] | None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "_".join(f"{k}-{str(v).replace('/', '_')}" for k, v in sorted((params or {}).items()))
    safe_endpoint = endpoint.replace(".", "_")
    return CACHE_DIR / f"{safe_endpoint}{'_' + suffix if suffix else ''}.json"


def _request(endpoint: str, params: dict[str, Any] | None = None, use_cache: bool = True) -> Any:
    global _last_request_at
    # Ownership verification must be a genuinely live read.  In particular,
    # disabling the cache means *neither* consulting nor refreshing the public
    # disk cache: writing the one-time profile value here could let a later,
    # ordinary cached read observe verification material after the user has
    # removed it from Codeforces.
    path = _cache_path(endpoint, params) if use_cache else None
    if path is not None and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    url = f"{CODEFORCES_API_BASE}/{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        elapsed = time.monotonic() - _last_request_at
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        _last_request_at = time.monotonic()

        try:
            response = requests.get(url, params=params or {}, timeout=DEFAULT_TIMEOUT_SECONDS)
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise CodeforcesAPIError(f"Codeforces request failed for {endpoint}: {exc}") from exc
            time.sleep(0.75 * attempt)
            continue

        if response.status_code == 429:
            if attempt >= MAX_RETRIES:
                raise CodeforcesAPIError(
                    f"Codeforces returned HTTP 429 after {MAX_RETRIES} retries (rate limited)"
                )
            backoff = _RATE_LIMIT_BACKOFF_S[min(attempt - 1, len(_RATE_LIMIT_BACKOFF_S) - 1)]
            time.sleep(backoff)
            continue

        # Codeforces answers HTTP 400 with a FAILED payload for bad input
        # (e.g. unknown handle). Surface the comment immediately — retrying
        # a bad request cannot succeed, and the comment text ("… not found")
        # is what callers use to map the error correctly.
        if response.status_code == 400:
            try:
                comment = response.json().get("comment", "")
            except Exception:
                comment = ""
            raise CodeforcesAPIError(
                f"Codeforces API error for {endpoint}: {comment or 'HTTP 400 (bad request)'}"
            )

        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise CodeforcesAPIError(f"Codeforces request failed for {endpoint}: {exc}") from exc
            time.sleep(0.75 * attempt)
            continue

        if payload.get("status") != "OK":
            comment = payload.get("comment", "unknown Codeforces API error")
            if attempt == MAX_RETRIES:
                raise CodeforcesAPIError(f"Codeforces API error for {endpoint}: {comment}")
            time.sleep(0.75 * attempt)
            continue

        result = payload["result"]
        if path is not None:
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    raise CodeforcesAPIError(f"Codeforces request failed for {endpoint}")


def fetch_user_status(handle: str, count: int | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"handle": handle}
    if count is not None:
        params["from"] = 1
        params["count"] = count
    return _request("user.status", params)


def fetch_user_rating(handle: str) -> list[dict[str, Any]]:
    return _request("user.rating", {"handle": handle})


def fetch_user_info(handle: str, use_cache: bool = True) -> dict[str, Any]:
    """`use_cache=False` forces a live fetch — required for handle-ownership
    verification, where a stale cached profile would let a claim pass on a
    since-changed field, or fail on a just-edited one."""
    result = _request("user.info", {"handles": handle}, use_cache=use_cache)
    if not result:
        raise CodeforcesAPIError(f"Codeforces handle not found: {handle}")
    return result[0]


def fetch_problemset_problems() -> dict[str, Any]:
    return _request("problemset.problems")
