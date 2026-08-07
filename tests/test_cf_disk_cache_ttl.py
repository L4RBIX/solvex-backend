"""Disk-cache TTL behavior for the core Codeforces HTTP client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contestiq_core.codeforces import client as cf_client


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(cf_client, "CACHE_DIR", tmp_path / "cf-cache")
    monkeypatch.setattr(cf_client, "RATE_LIMIT_SECONDS", 0.0)
    cf_client._last_request_at = 0.0
    monkeypatch.chdir(tmp_path)


def test_stale_user_status_cache_is_refetched(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        calls["n"] += 1
        handle = (params or {}).get("handle")
        return _Resp({"status": "OK", "result": [{"id": calls["n"], "handle": handle, "verdict": "OK"}]})

    monkeypatch.setattr(cf_client.requests, "get", fake_get)

    first = cf_client.fetch_user_status("Dan1c", max_age_seconds=60)
    assert first[0]["id"] == 1
    assert calls["n"] == 1

    # Fresh within TTL — no network.
    second = cf_client.fetch_user_status("Dan1c", max_age_seconds=60)
    assert second[0]["id"] == 1
    assert calls["n"] == 1

    # Expire by mtime.
    path = cf_client._cache_path("user.status", {"handle": "Dan1c"})
    assert path.exists()
    older = path.stat().st_mtime - 120
    Path(path).touch()
    import os

    os.utime(path, (older, older))

    third = cf_client.fetch_user_status("Dan1c", max_age_seconds=60)
    assert third[0]["id"] == 2
    assert calls["n"] == 2


def test_use_cache_false_does_not_read_or_write_disk(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _Resp({"status": "OK", "result": [{"handle": "live", "rating": 1}]})

    monkeypatch.setattr(cf_client.requests, "get", fake_get)
    path = cf_client._cache_path("user.info", {"handles": "secret"})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"handle": "stale", "rating": 999}]), encoding="utf-8")

    profile = cf_client.fetch_user_info("secret", use_cache=False)
    assert profile["handle"] == "live"
    # Must not overwrite the on-disk public cache with verification material.
    assert json.loads(path.read_text(encoding="utf-8"))[0]["handle"] == "stale"


def test_rate_limit_falls_back_to_stale_cache(monkeypatch):
    path = cf_client._cache_path("user.status", {"handle": "Dan1c"})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"id": 42, "verdict": "OK"}]), encoding="utf-8")
    # Make it stale so we attempt network.
    import os

    older = path.stat().st_mtime - 10_000
    os.utime(path, (older, older))

    def always_429(url, params=None, timeout=None):
        return _Resp({"status": "FAILED", "comment": "Call limit exceeded"}, status_code=429)

    monkeypatch.setattr(cf_client.requests, "get", always_429)
    monkeypatch.setattr(cf_client, "MAX_RETRIES", 1)
    monkeypatch.setattr(cf_client, "_RATE_LIMIT_BACKOFF_S", (0,))

    result = cf_client.fetch_user_status("Dan1c", max_age_seconds=60)
    assert result[0]["id"] == 42
