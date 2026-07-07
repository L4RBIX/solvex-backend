"""Codeforces client tests — fully mocked, never touch live Codeforces."""

import pytest

from contestiq_api.cfdata.client import (
    CircuitBreaker,
    CodeforcesClient,
    CodeforcesClientError,
    CodeforcesNotFoundError,
    CodeforcesRateLimitedError,
    CodeforcesUnavailableError,
    GlobalRateLimiter,
    TransportResponse,
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)


def ok(result):
    return TransportResponse(200, {"status": "OK", "result": result})


def failed(comment):
    return TransportResponse(200, {"status": "FAILED", "comment": comment})


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.handlers = {}

    def set(self, endpoint, handler):
        self.handlers[endpoint] = handler

    def __call__(self, url, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, dict(params)))
        result = self.handlers[endpoint](params)
        if isinstance(result, Exception):
            raise result
        return result


def make_client(transport, **overrides):
    sleeps = []
    defaults = dict(
        transport=transport,
        rate_limiter=GlobalRateLimiter(0.0, clock=lambda: 0.0, sleep=lambda s: None),
        breaker=CircuitBreaker(failure_threshold=100),
        max_retries=3,
        backoff_base_seconds=1.5,
        jitter_seconds=1.0,
        sleep=sleeps.append,
        rng=lambda: 0.0,
    )
    defaults.update(overrides)
    client = CodeforcesClient(**defaults)
    return client, sleeps


def test_ok_response_returns_data_and_records_raw():
    transport = FakeTransport()
    transport.set("user.info", lambda p: ok([{"handle": "tourist", "rating": 3800}]))
    client, _ = make_client(transport)

    result = client.get_user_info("tourist")
    assert result.data["handle"] == "tourist"
    assert result.stale is False

    from contestiq_api.cfdata.store import latest_ok_raw_response

    cached = latest_ok_raw_response("user.info", {"handles": "tourist"})
    assert cached is not None
    assert cached["data"][0]["rating"] == 3800


def test_failed_not_found_raises_without_retry():
    transport = FakeTransport()
    transport.set("user.info", lambda p: failed("handles: User with handle ghost not found"))
    client, sleeps = make_client(transport)

    with pytest.raises(CodeforcesNotFoundError):
        client.get_user_info("ghost")
    assert len(transport.calls) == 1
    assert sleeps == []


def test_empty_user_info_result_raises_not_found():
    transport = FakeTransport()
    transport.set("user.info", lambda p: ok([]))
    client, _ = make_client(transport)
    with pytest.raises(CodeforcesNotFoundError):
        client.get_user_info("ghost")


def test_call_limit_exceeded_retries_with_backoff_then_raises():
    transport = FakeTransport()
    transport.set("user.rating", lambda p: failed("Call limit exceeded"))
    client, sleeps = make_client(transport)

    with pytest.raises(CodeforcesRateLimitedError):
        client.get_user_rating("someone")
    assert len(transport.calls) == 3
    # Exponential backoff with rng=0: base * 2^0, base * 2^1
    assert sleeps == [1.5, 3.0]


def test_backoff_includes_jitter():
    transport = FakeTransport()
    transport.set("user.rating", lambda p: TransportResponse(429, None))
    client, sleeps = make_client(transport, rng=lambda: 1.0, jitter_seconds=0.25)

    with pytest.raises(CodeforcesRateLimitedError):
        client.get_user_rating("someone")
    assert sleeps == [1.75, 3.25]


def test_timeout_retries_then_unavailable():
    transport = FakeTransport()
    transport.set("user.status", lambda p: TimeoutError("connect timeout"))
    client, _ = make_client(transport)

    with pytest.raises(CodeforcesUnavailableError):
        client.get_user_status("someone")
    assert len(transport.calls) == 3


def test_unknown_failed_comment_raises_generic_error_without_retry():
    transport = FakeTransport()
    transport.set("user.status", lambda p: failed("contestId: Contest is not started"))
    client, _ = make_client(transport)

    with pytest.raises(CodeforcesClientError) as excinfo:
        client.get_user_status("someone")
    assert not isinstance(excinfo.value, (CodeforcesNotFoundError, CodeforcesRateLimitedError))
    assert len(transport.calls) == 1


def test_stale_cache_fallback_on_failure():
    transport = FakeTransport()
    transport.set("user.rating", lambda p: ok([{"contestId": 1, "newRating": 1500}]))
    client, _ = make_client(transport)
    fresh = client.get_user_rating("someone")
    assert fresh.stale is False

    transport.set("user.rating", lambda p: TransportResponse(503, None))
    stale = client.get_user_rating("someone")
    assert stale.stale is True
    assert stale.data == [{"contestId": 1, "newRating": 1500}]
    assert stale.fetched_at is not None


def test_not_found_never_falls_back_to_stale():
    transport = FakeTransport()
    transport.set("user.info", lambda p: ok([{"handle": "gone"}]))
    client, _ = make_client(transport)
    client.get_user_info("gone")

    transport.set("user.info", lambda p: failed("handles: User with handle gone not found"))
    with pytest.raises(CodeforcesNotFoundError):
        client.get_user_info("gone")


def test_circuit_breaker_opens_and_blocks_transport():
    clock = {"now": 0.0}
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=1000.0, clock=lambda: clock["now"])
    transport = FakeTransport()
    transport.set("user.rating", lambda p: TransportResponse(500, None))
    client, _ = make_client(transport, breaker=breaker, max_retries=1)

    for _ in range(2):
        with pytest.raises(CodeforcesUnavailableError):
            client.get_user_rating("someone")
    assert len(transport.calls) == 2
    assert breaker.is_open

    # Circuit open, no stale data: fail fast without calling transport.
    with pytest.raises(CodeforcesUnavailableError):
        client.get_user_rating("someone")
    assert len(transport.calls) == 2


def test_circuit_breaker_open_serves_stale_cache():
    clock = {"now": 0.0}
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=1000.0, clock=lambda: clock["now"])
    transport = FakeTransport()
    transport.set("problemset.problems", lambda p: ok({"problems": [{"contestId": 1, "index": "A", "name": "P"}]}))
    client, _ = make_client(transport, breaker=breaker, max_retries=1)
    client.get_problemset()

    transport.set("problemset.problems", lambda p: TransportResponse(500, None))
    stale = client.get_problemset()  # failure trips the breaker but stale data saves the call
    assert stale.stale is True

    calls_before = len(transport.calls)
    again = client.get_problemset()  # circuit open: served from stale cache, no transport call
    assert again.stale is True
    assert len(transport.calls) == calls_before


def test_circuit_breaker_half_opens_after_cooldown():
    clock = {"now": 0.0}
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=60.0, clock=lambda: clock["now"])
    transport = FakeTransport()
    transport.set("user.rating", lambda p: TransportResponse(500, None))
    client, _ = make_client(transport, breaker=breaker, max_retries=1)

    with pytest.raises(CodeforcesUnavailableError):
        client.get_user_rating("someone")
    assert breaker.is_open

    clock["now"] = 61.0
    transport.set("user.rating", lambda p: ok([]))
    result = client.get_user_rating("someone")
    assert result.data == []
    assert not breaker.is_open


def test_global_rate_limiter_enforces_spacing():
    sleeps = []
    clock = {"now": 100.0}
    limiter = GlobalRateLimiter(2.0, clock=lambda: clock["now"], sleep=sleeps.append)

    limiter.wait()
    assert sleeps == []
    clock["now"] = 100.5  # only 0.5 s elapsed since last request
    limiter.wait()
    assert sleeps == [1.5]


def test_client_waits_on_limiter_before_every_request():
    waits = []

    class SpyLimiter:
        def wait(self):
            waits.append(1)

    transport = FakeTransport()
    transport.set("user.rating", lambda p: TransportResponse(429, None))
    client, _ = make_client(transport, rate_limiter=SpyLimiter())

    with pytest.raises(CodeforcesRateLimitedError):
        client.get_user_rating("someone")
    assert len(waits) == len(transport.calls) == 3
