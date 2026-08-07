"""Fetch official Codeforces problem pages for statement ingestion.

Uses Chrome TLS impersonation (curl_cffi) because bare HTTP clients hit
Cloudflare challenge pages from many datacenter IPs. Falls back to requests
only when an injectable transport is supplied by tests.

Reuses the process-global Codeforces rate limiter pacing so catalog API and
HTML ingestion do not stampede the origin.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from contestiq_api.cfdata.client import GlobalRateLimiter
from contestiq_api.cfdata.statement_html import official_problem_url
from contestiq_api.settings import get_settings

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_html_limiter_lock = threading.Lock()
_html_limiter: GlobalRateLimiter | None = None


class HtmlTransport(Protocol):
    def __call__(self, url: str, timeout: float) -> "HtmlFetchResult": ...


@dataclass
class HtmlFetchResult:
    status_code: int
    text: str
    url: str
    error: str | None = None


class StatementFetchError(RuntimeError):
    error_code = "STATEMENT_FETCH_ERROR"


def _get_html_limiter() -> GlobalRateLimiter:
    global _html_limiter
    with _html_limiter_lock:
        if _html_limiter is None:
            # HTML pages are heavier than API JSON — keep a polite floor.
            interval = max(2.0, float(get_settings().codeforces_rate_limit_seconds), 3.0)
            # Prefer dedicated setting when present.
            interval = max(
                interval,
                float(getattr(get_settings(), "statement_ingest_rate_limit_seconds", interval) or interval),
            )
            _html_limiter = GlobalRateLimiter(min_interval=interval)
        return _html_limiter


def reset_html_limiter_for_tests() -> None:
    global _html_limiter
    with _html_limiter_lock:
        _html_limiter = None


def _curl_cffi_transport(url: str, timeout: float) -> HtmlFetchResult:
    try:
        from curl_cffi import requests as cf_requests
    except ImportError as exc:  # pragma: no cover - exercised in degraded envs
        raise StatementFetchError(
            "curl_cffi is required to fetch Codeforces HTML (Cloudflare)."
        ) from exc

    # Prefer chrome116: Railway/datacenter egress is often 403 with newer
    # Chrome impersonation profiles, while chrome116 still returns real pages.
    impersonations = ("chrome116", "chrome110", "chrome99", "safari17_0", "chrome131")
    last: HtmlFetchResult | None = None
    for impersonate in impersonations:
        response = cf_requests.get(
            url,
            impersonate=impersonate,
            timeout=timeout,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        text = response.text or ""
        last = HtmlFetchResult(
            status_code=int(response.status_code),
            text=text,
            url=str(getattr(response, "url", url) or url),
        )
        if last.status_code == 200 and "problem-statement" in text:
            return last
        if last.status_code == 200 and text.strip() and "Just a moment" not in text:
            return last
    assert last is not None
    return last


def fetch_problem_html(
    contest_id: int,
    index: str,
    *,
    transport: HtmlTransport | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    rate_limiter: GlobalRateLimiter | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> HtmlFetchResult:
    """Fetch one public problem page. Raises StatementFetchError on hard failure."""
    url = official_problem_url(contest_id, index)
    limiter = rate_limiter or _get_html_limiter()
    limiter.wait()

    settings = get_settings()
    retries = max(1, int(settings.codeforces_max_retries))
    transport = transport or _curl_cffi_transport
    last_error: str | None = None

    for attempt in range(retries):
        try:
            result = transport(url, timeout)
        except Exception as exc:  # network / TLS
            last_error = str(exc)
            if attempt + 1 < retries:
                sleep(min(30.0, 2.0 ** attempt))
                continue
            raise StatementFetchError(f"fetch failed for {url}: {exc}") from exc

        if result.status_code == 200 and result.text.strip():
            return result
        if result.status_code in {403, 429, 503} and attempt + 1 < retries:
            last_error = f"HTTP {result.status_code}"
            sleep(min(30.0, 2.0 ** attempt))
            continue
        raise StatementFetchError(
            f"unexpected HTTP {result.status_code} for {url}"
            + (f" ({result.error})" if result.error else "")
        )

    raise StatementFetchError(f"fetch failed for {url}: {last_error or 'unknown'}")
