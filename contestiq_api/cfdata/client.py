"""Production Codeforces API client.

Codeforces is a slow external dependency, so every call goes through:
- a process-global rate limiter (1 request / CODEFORCES_RATE_LIMIT_SECONDS);
- retry with exponential backoff + jitter;
- a circuit breaker that stops hammering Codeforces when it is down;
- raw response recording (cf_raw_api_responses) for audit;
- stale-cache fallback from the most recent OK raw response.

Transport, clock, sleep, and RNG are injectable so tests never touch the
network or real time.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from contestiq_api.cfdata import store
from contestiq_api.settings import get_settings

CODEFORCES_API_BASE = "https://codeforces.com/api"
DEFAULT_TIMEOUT_SECONDS = 20.0


class CodeforcesClientError(RuntimeError):
    error_code = "CODEFORCES_API_ERROR"


class CodeforcesNotFoundError(CodeforcesClientError):
    error_code = "CODEFORCES_HANDLE_NOT_FOUND"


class CodeforcesRateLimitedError(CodeforcesClientError):
    error_code = "CODEFORCES_RATE_LIMITED"


class CodeforcesUnavailableError(CodeforcesClientError):
    error_code = "CODEFORCES_UNAVAILABLE"


@dataclass
class CFResult:
    data: Any
    stale: bool = False
    fetched_at: str | None = None


@dataclass
class TransportResponse:
    status_code: int
    payload: dict[str, Any] | None


class Transport(Protocol):
    def __call__(self, url: str, params: dict[str, Any], timeout: float) -> TransportResponse: ...


def _requests_transport(url: str, params: dict[str, Any], timeout: float) -> TransportResponse:
    import requests

    response = requests.get(url, params=params, timeout=timeout)
    try:
        payload = response.json()
    except ValueError:
        payload = None
    return TransportResponse(status_code=response.status_code, payload=payload)


class GlobalRateLimiter:
    """At most one Codeforces request every min_interval seconds, process-wide."""

    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last_request_at: float | None = None

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last_request_at is not None:
                remaining = self.min_interval - (now - self._last_request_at)
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._clock()
            self._last_request_at = now


class CircuitBreaker:
    """Opens after `failure_threshold` consecutive failed calls; half-opens after cooldown."""

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def allow(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if self._clock() - self._opened_at >= self.cooldown_seconds:
                # Half-open: allow one probe call through.
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._opened_at = self._clock()

    @property
    def is_open(self) -> bool:
        return not self.allow()


_shared_limiter_lock = threading.Lock()
_shared_limiter: GlobalRateLimiter | None = None


def shared_rate_limiter() -> GlobalRateLimiter:
    global _shared_limiter
    with _shared_limiter_lock:
        if _shared_limiter is None:
            _shared_limiter = GlobalRateLimiter(get_settings().codeforces_rate_limit_seconds)
        return _shared_limiter


@dataclass
class CodeforcesClient:
    base_url: str = CODEFORCES_API_BASE
    transport: Transport = field(default_factory=lambda: _requests_transport)
    rate_limiter: GlobalRateLimiter | None = None
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    max_retries: int = 3
    backoff_base_seconds: float = 1.5
    jitter_seconds: float = 1.0
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    sleep: Callable[[float], None] = time.sleep
    rng: Callable[[], float] = random.random
    recorder: Callable[..., None] = store.record_raw_response
    stale_reader: Callable[[str, dict[str, Any] | None], dict[str, Any] | None] = store.latest_ok_raw_response

    def __post_init__(self) -> None:
        if self.rate_limiter is None:
            self.rate_limiter = shared_rate_limiter()

    # ── Public API ───────────────────────────────────────────────────────────

    def get_user_info(self, handle: str) -> CFResult:
        result = self._call("user.info", {"handles": handle})
        rows = result.data
        if not rows:
            raise CodeforcesNotFoundError(f"Codeforces handle not found: {handle}")
        return CFResult(data=rows[0], stale=result.stale, fetched_at=result.fetched_at)

    def get_user_rating(self, handle: str) -> CFResult:
        return self._call("user.rating", {"handle": handle})

    def get_user_status(self, handle: str, from_index: int | None = None, count: int | None = None) -> CFResult:
        params: dict[str, Any] = {"handle": handle}
        if from_index is not None:
            params["from"] = from_index
        if count is not None:
            params["count"] = count
        return self._call("user.status", params)

    def get_problemset(self) -> CFResult:
        return self._call("problemset.problems", {})

    # ── Internals ────────────────────────────────────────────────────────────

    def _stale_fallback(self, endpoint: str, params: dict[str, Any]) -> CFResult | None:
        cached = self.stale_reader(endpoint, params)
        if cached is None:
            return None
        return CFResult(data=cached["data"], stale=True, fetched_at=cached["fetched_at"])

    def _backoff(self, attempt: int) -> None:
        delay = self.backoff_base_seconds * (2 ** (attempt - 1)) + self.rng() * self.jitter_seconds
        self.sleep(delay)

    def _call(self, endpoint: str, params: dict[str, Any]) -> CFResult:
        if not self.breaker.allow():
            stale = self._stale_fallback(endpoint, params)
            if stale is not None:
                return stale
            raise CodeforcesUnavailableError(
                "Codeforces circuit breaker is open (repeated failures); no cached data available."
            )

        url = f"{self.base_url}/{endpoint}"
        last_error: str = "unknown error"
        rate_limited = False

        for attempt in range(1, self.max_retries + 1):
            assert self.rate_limiter is not None
            self.rate_limiter.wait()
            try:
                response = self.transport(url, params, self.timeout_seconds)
            except Exception as exc:
                last_error = f"transport error: {exc}"
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue

            if response.status_code == 429:
                rate_limited = True
                last_error = "HTTP 429 (rate limited)"
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue

            if response.status_code >= 500 or response.payload is None:
                last_error = f"HTTP {response.status_code}"
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue

            payload = response.payload
            if payload.get("status") == "OK":
                self.recorder(endpoint, params, "ok", raw_json=payload.get("result"), http_status=response.status_code)
                self.breaker.record_success()
                return CFResult(data=payload.get("result"))

            comment = str(payload.get("comment") or "Codeforces API returned FAILED")
            lowered = comment.lower()
            if "not found" in lowered:
                # The API itself is healthy — a bad handle is not an availability failure.
                self.recorder(endpoint, params, "failed", http_status=response.status_code, error_message=comment)
                self.breaker.record_success()
                raise CodeforcesNotFoundError(comment)
            if "call limit" in lowered or "rate limit" in lowered or "too many requests" in lowered:
                rate_limited = True
                last_error = comment
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue

            # Unknown FAILED comment: record and surface without retrying.
            self.recorder(endpoint, params, "failed", http_status=response.status_code, error_message=comment)
            self.breaker.record_success()
            raise CodeforcesClientError(comment)

        self.breaker.record_failure()
        self.recorder(endpoint, params, "error", error_message=last_error)
        stale = self._stale_fallback(endpoint, params)
        if stale is not None:
            return stale
        if rate_limited:
            raise CodeforcesRateLimitedError(f"Codeforces rate limited after {self.max_retries} attempts: {last_error}")
        raise CodeforcesUnavailableError(f"Codeforces unavailable after {self.max_retries} attempts: {last_error}")
