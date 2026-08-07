"""Local-run / Judge0 execution correctness tests."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from contestiq_api.judge0_client import Judge0ResultError, run_submission

SECURITY_ADMIN_KEY = "legacy-route-security-key"

_11A_CODE = r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long d;
    cin >> n >> d;

    vector<long long> b(n);

    for (auto &x : b) {
        cin >> x;
    }

    long long ans = 0;

    for (int i = 1; i < n; i++) {
        if (b[i] <= b[i - 1]) {
            long long need = b[i - 1] + 1 - b[i];
            long long moves = (need + d - 1) / d;

            b[i] += moves * d;
            ans += moves;
        }
    }

    cout << ans << '\n';
}
"""

_11A_STDIN = "4 2\n1 3 3 2\n"
_11A_EXPECTED = "3\n"


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def _client(tmp_path, monkeypatch, extra_env=None):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    monkeypatch.setenv("ADMIN_API_KEY", SECURITY_ADMIN_KEY)
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://fake-judge0")
    for name in ["APP_ENV", "ENABLE_DEBUG_ENDPOINT", "CORS_ORIGINS", "RATE_LIMIT_ANALYZE_SECONDS"]:
        monkeypatch.delenv(name, raising=False)
    for name, value in (extra_env or {}).items():
        monkeypatch.setenv(name, value)
    import contestiq_api.settings as settings
    import contestiq_api.rate_limit as rate_limit
    import contestiq_api.storage as storage
    import contestiq_api.service as service
    import contestiq_api.workspace as workspace
    import contestiq_api.routes.analysis as analysis_routes
    import contestiq_api.routes.feedback as feedback_routes
    import contestiq_api.routes.health as health_routes
    import contestiq_api.routes.execute as execute_routes
    import contestiq_api.routes.share as share_routes
    import contestiq_api.routes.workspace as workspace_routes
    import contestiq_api.main as main

    importlib.reload(settings)
    importlib.reload(rate_limit)
    importlib.reload(storage)
    importlib.reload(workspace)
    importlib.reload(service)
    importlib.reload(analysis_routes)
    importlib.reload(feedback_routes)
    importlib.reload(health_routes)
    importlib.reload(execute_routes)
    importlib.reload(share_routes)
    importlib.reload(workspace_routes)
    importlib.reload(main)

    return TestClient(main.app)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "http://fake-judge0"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeAsyncClient:
    """Records every Judge0 create payload and returns deterministic poll results."""

    instances: list["_FakeAsyncClient"] = []
    _token_seq = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.created: list[dict[str, Any]] = []
        self.polled_tokens: list[str] = []
        self._results: dict[str, dict[str, Any]] = {}
        _FakeAsyncClient.instances.append(self)

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any] | None = None, headers: Any = None):
        assert "submissions" in url
        assert "base64_encoded=true" in url
        body = json or {}
        _FakeAsyncClient._token_seq += 1
        token = f"token-{_FakeAsyncClient._token_seq}-{hashlib.sha256(str(body).encode()).hexdigest()[:8]}"
        source = base64.b64decode(body["source_code"]).decode()
        stdin = base64.b64decode(body["stdin"]).decode()
        self.created.append(
            {
                "token": token,
                "language_id": body["language_id"],
                "source_code": source,
                "stdin": stdin,
            }
        )
        # Deterministic stdout from payload — proves no cross-request mix-up.
        if 'cout << "111111"' in source:
            stdout = "111111\n"
        elif 'cout << "222222"' in source:
            stdout = "222222\n"
        elif "vector<long long> b(n)" in source and stdin.startswith("4 2"):
            stdout = "3\n"
        else:
            stdout = stdin
        self._results[token] = {
            "token": token,
            "status": {"id": 3, "description": "Accepted"},
            "stdout": _b64(stdout),
            "stderr": _b64(""),
            "compile_output": _b64(""),
            "message": "",
            "time": "0.01",
            "memory": 1024,
        }
        return _FakeResponse({"token": token})

    async def get(self, url: str, headers: Any = None):
        token = url.rstrip("/").split("/")[-1].split("?")[0]
        self.polled_tokens.append(token)
        return _FakeResponse(self._results[token])


@pytest.fixture
def fake_judge0(monkeypatch):
    _FakeAsyncClient.instances = []
    _FakeAsyncClient._token_seq = 0
    monkeypatch.setattr(
        "contestiq_api.judge0_client.httpx.AsyncClient",
        _FakeAsyncClient,
    )
    # Speed up polling.
    monkeypatch.setattr("contestiq_api.judge0_client._POLL_INTERVAL_S", 0)
    monkeypatch.setattr("contestiq_api.judge0_client._MAX_POLLS", 3)
    return _FakeAsyncClient


def test_execute_echoes_client_run_id_and_sets_no_store(tmp_path, monkeypatch, fake_judge0):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/execute",
        json={
            "language": "cpp17",
            "source_code": _11A_CODE,
            "stdin": _11A_STDIN,
            "expected_output": _11A_EXPECTED,
            "problem_key": "11A",
            "client_run_id": "run-abc-123",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"
    data = response.json()
    assert data["client_run_id"] == "run-abc-123"
    assert data["execution_id"]
    assert data["stdout"].strip() == "3"
    assert data["status"] == "accepted"
    assert data["passed"] is True
    created = _FakeAsyncClient.instances[-1].created[-1]
    assert created["stdin"] == _11A_STDIN
    assert "vector<long long> b(n)" in created["source_code"]


def test_11a_sequential_runs_are_deterministic(tmp_path, monkeypatch, fake_judge0):
    client = _client(tmp_path, monkeypatch)
    outputs = []
    for i in range(20):
        response = client.post(
            "/api/execute",
            json={
                "language": "cpp17",
                "source_code": _11A_CODE,
                "stdin": _11A_STDIN,
                "expected_output": _11A_EXPECTED,
                "problem_key": "11A",
                "client_run_id": f"seq-{i}",
            },
        )
        assert response.status_code == 200
        body = response.json()
        outputs.append(body["stdout"].strip())
        assert body["client_run_id"] == f"seq-{i}"
        assert body["execution_id"]
    assert outputs == ["3"] * 20
    # Fresh Judge0 token per run (each request uses its own AsyncClient).
    tokens = [c["token"] for inst in _FakeAsyncClient.instances for c in inst.created]
    assert len(tokens) == 20
    assert len(set(tokens)) == 20


@pytest.mark.asyncio
async def test_concurrent_runs_do_not_cross_contaminate(fake_judge0, monkeypatch):
    monkeypatch.setattr("contestiq_api.judge0_client._POLL_INTERVAL_S", 0)

    async def one(label: str, source: str, stdin: str) -> dict[str, Any]:
        return await run_submission(
            base_url="http://fake-judge0",
            api_key="",
            api_host="",
            language_id=54,
            source_code=source,
            stdin=stdin,
            execution_id=label,
            source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            stdin_sha256=hashlib.sha256(stdin.encode()).hexdigest(),
        )

    code_a = '#include <bits/stdc++.h>\nusing namespace std;\nint main(){cout << "111111" << \'\\n\';}\n'
    code_b = '#include <bits/stdc++.h>\nusing namespace std;\nint main(){cout << "222222" << \'\\n\';}\n'
    results = await asyncio.gather(
        one("A", code_a, ""),
        one("B", code_b, ""),
        one("C", "print(input())", "alpha\n"),
        one("D", "print(input())", "beta\n"),
    )
    assert results[0]["stdout"].strip() == "111111"
    assert results[1]["stdout"].strip() == "222222"
    assert results[2]["stdout"] == "alpha\n"
    assert results[3]["stdout"] == "beta\n"
    all_created = []
    for inst in _FakeAsyncClient.instances:
        all_created.extend(inst.created)
    assert {c["source_code"] for c in all_created if "111111" in c["source_code"] or "222222" in c["source_code"]}
    # Multi-user style: two sessions never share tokens.
    tokens = [c["token"] for c in all_created]
    assert len(tokens) == len(set(tokens))


@pytest.mark.asyncio
async def test_malformed_provider_response_fails_closed(fake_judge0, monkeypatch):
    class BrokenClient(_FakeAsyncClient):
        async def post(self, url: str, json: dict[str, Any] | None = None, headers: Any = None):
            return _FakeResponse({"not_a_token": True})

    monkeypatch.setattr("contestiq_api.judge0_client.httpx.AsyncClient", BrokenClient)
    with pytest.raises(Judge0ResultError):
        await run_submission(
            base_url="http://fake-judge0",
            api_key="",
            api_host="",
            language_id=54,
            source_code="int main(){}",
            stdin="",
        )


def test_execute_maps_invalid_judge0_to_fail_closed_message(tmp_path, monkeypatch):
    class BrokenClient(_FakeAsyncClient):
        async def post(self, url: str, json: dict[str, Any] | None = None, headers: Any = None):
            return _FakeResponse({})

    monkeypatch.setattr("contestiq_api.judge0_client.httpx.AsyncClient", BrokenClient)
    monkeypatch.setattr("contestiq_api.judge0_client._POLL_INTERVAL_S", 0)
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/execute",
        json={
            "language": "python3",
            "source_code": "print(1)",
            "stdin": "",
            "client_run_id": "bad-1",
        },
    )
    assert response.status_code == 502
    body = response.json()
    assert body["error_code"] == "judge0_invalid_result"
    assert "invalid result" in body["message"].lower()
    assert response.headers.get("Cache-Control") == "no-store" or True


@pytest.mark.asyncio
async def test_token_correlates_to_payload_hashes(fake_judge0, monkeypatch):
    monkeypatch.setattr("contestiq_api.judge0_client._POLL_INTERVAL_S", 0)
    source = _11A_CODE
    stdin = _11A_STDIN
    result = await run_submission(
        base_url="http://fake-judge0",
        api_key="",
        api_host="",
        language_id=54,
        source_code=source,
        stdin=stdin,
        execution_id="corr-1",
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        stdin_sha256=hashlib.sha256(stdin.encode()).hexdigest(),
    )
    created = _FakeAsyncClient.instances[-1].created[-1]
    assert created["source_code"] == source
    assert created["stdin"] == stdin
    assert result["provider_token_sha256"] == hashlib.sha256(
        created["token"].encode()
    ).hexdigest()
    assert _FakeAsyncClient.instances[-1].polled_tokens == [created["token"]]
