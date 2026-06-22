from __future__ import annotations

import time

from contestiq_api.errors import APIError

_ANALYZE_LAST_SEEN: dict[str, float] = {}


def check_analyze_rate_limit(key: str, window_seconds: int) -> None:
    if window_seconds <= 0:
        return
    now = time.monotonic()
    previous = _ANALYZE_LAST_SEEN.get(key)
    if previous is not None and now - previous < window_seconds:
        raise APIError("RATE_LIMITED", "Please wait before running another analysis.", 429)
    _ANALYZE_LAST_SEEN[key] = now


def reset_rate_limits() -> None:
    _ANALYZE_LAST_SEEN.clear()
