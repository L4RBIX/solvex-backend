"""Backend-only Judge0 adapter for SkillTrace.

Rules enforced here:
- Judge0 is called ONLY from the backend; credentials never leave this module.
- Submissions use wait=false. Results arrive via callback first; a reconciler
  polls as fallback. wait=true is not a production path anywhere.
- All payloads are base64-encoded both ways (base64_encoded=true).
- Language allowlist; network disabled; CPU/memory/wall limits on every run.
- Each submission carries a per-submission callback secret in the callback URL
  so callbacks can be authenticated (Judge0 CE does not sign callbacks).
"""

from __future__ import annotations

import base64
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

LANGUAGE_IDS = {"cpp17": 54, "python3": 71}

CPU_TIME_LIMIT_S = 2.0
WALL_TIME_LIMIT_S = 8.0
MEMORY_LIMIT_KB = 256_000

TERMINAL_STATUS_MIN = 3  # Judge0: 1=queued, 2=processing, >=3 terminal
ACCEPTED_STATUS_ID = 3


def b64enc(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def b64dec(s: object) -> str:
    if not s:
        return ""
    try:
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except Exception:
        return str(s)


def _http_post(url: str, json_payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    import requests

    response = requests.post(url, json=json_payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def _http_get(url: str, headers: dict[str, str]) -> dict[str, Any]:
    import requests

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


@dataclass
class Judge0Adapter:
    post: Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]] = field(default=_http_post)
    get: Callable[[str, dict[str, str]], dict[str, Any]] = field(default=_http_get)

    def _config(self) -> tuple[str, dict[str, str]]:
        settings = get_settings()
        if not settings.judge0_base_url:
            raise APIError("JUDGE0_NOT_CONFIGURED", "Judge0 is not configured on this backend.", 503)
        headers = {"Content-Type": "application/json"}
        if settings.judge0_api_key:
            headers["X-RapidAPI-Key"] = settings.judge0_api_key
        if settings.judge0_api_host:
            headers["X-RapidAPI-Host"] = settings.judge0_api_host
        return settings.judge0_base_url, headers

    def submit(
        self,
        attempt_id: str,
        test_index: int,
        language: str,
        source_code: str,
        stdin: str,
        expected_output: str | None,
    ) -> dict[str, Any]:
        """Create one async Judge0 submission and persist its tracking row."""
        if language not in LANGUAGE_IDS:
            raise APIError("UNSUPPORTED_LANGUAGE", "Supported languages: cpp17, python3.", 422)
        base_url, headers = self._config()
        settings = get_settings()

        submission_id = str(uuid.uuid4())
        callback_secret = secrets.token_hex(16)
        payload: dict[str, Any] = {
            "language_id": LANGUAGE_IDS[language],
            "source_code": b64enc(source_code),
            "stdin": b64enc(stdin),
            "cpu_time_limit": CPU_TIME_LIMIT_S,
            "wall_time_limit": WALL_TIME_LIMIT_S,
            "memory_limit": MEMORY_LIMIT_KB,
            "enable_network": False,
        }
        if expected_output is not None:
            payload["expected_output"] = b64enc(expected_output)
        if settings.judge0_callback_base:
            payload["callback_url"] = (
                f"{settings.judge0_callback_base}/api/v1/judge0/callback?secret={callback_secret}"
            )

        result = self.post(f"{base_url}/submissions?base64_encoded=true&wait=false", payload, headers)
        token = result.get("token")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO judge0_submissions (submission_id, attempt_id, test_index, judge0_token,"
                " callback_secret, submission_status, created_at) VALUES (?, ?, ?, ?, ?, 'submitted', ?)",
                (submission_id, attempt_id, test_index, token, callback_secret, store._now()),
            )
        return {"submission_id": submission_id, "judge0_token": token}

    def poll(self, judge0_token: str) -> dict[str, Any]:
        base_url, headers = self._config()
        return self.get(f"{base_url}/submissions/{judge0_token}?base64_encoded=true", headers)


_adapter: Judge0Adapter | None = None


def get_adapter() -> Judge0Adapter:
    global _adapter
    if _adapter is None:
        _adapter = Judge0Adapter()
    return _adapter


def set_adapter(adapter: Judge0Adapter | None) -> None:
    """Test hook: inject a fake-transport adapter."""
    global _adapter
    _adapter = adapter


def record_result(submission: dict[str, Any], judge0_payload: dict[str, Any], source: str) -> bool:
    """Persist a terminal Judge0 result. Returns False if already recorded (idempotent)."""
    if submission["submission_status"] == "done":
        return False
    status_id = int((judge0_payload.get("status") or {}).get("id") or 0)
    if status_id < TERMINAL_STATUS_MIN:
        return False

    from datetime import datetime, timezone

    from contestiq_api import metrics

    try:
        created = datetime.fromisoformat(submission["created_at"])
        lag_ms = (datetime.now(timezone.utc) - created).total_seconds() * 1000
        metrics.observe("judge0_callback_lag_ms", max(lag_ms, 0.0))
    except (ValueError, TypeError):
        pass
    if status_id == 13:  # Judge0 internal error
        metrics.inc("judge0_errors_total")
    metrics.inc("judge0_results_total")

    time_ms = None
    raw_time = judge0_payload.get("time")
    if raw_time is not None:
        try:
            time_ms = int(float(raw_time) * 1000)
        except (TypeError, ValueError):
            pass
    # Hidden-test outputs are redacted to length only: stdout of a hidden test
    # could leak expected outputs to anyone who later reads the row.
    stdout_len = len(b64dec(judge0_payload.get("stdout")))
    stderr_len = len(b64dec(judge0_payload.get("stderr")))
    field_name = "callback_received_at" if source == "judge0_callback" else "polled_at"
    with store.connect() as conn:
        conn.execute(
            f"UPDATE judge0_submissions SET submission_status = 'done', status_id = ?, passed = ?,"
            f" time_ms = ?, memory_kb = ?, stdout_redacted = ?, stderr_redacted = ?, {field_name} = ?"
            f" WHERE submission_id = ?",
            (
                status_id,
                1 if status_id == ACCEPTED_STATUS_ID else 0,
                time_ms,
                judge0_payload.get("memory"),
                f"<redacted:{stdout_len} bytes>",
                f"<redacted:{stderr_len} bytes>",
                store._now(),
                submission["submission_id"],
            ),
        )
    return True


def get_submission_by_secret(secret: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM judge0_submissions WHERE callback_secret = ?", (secret,)).fetchone()
    return dict(row) if row else None


def pending_submissions(older_than_seconds: float = 20.0) -> list[dict[str, Any]]:
    from datetime import datetime, timedelta, timezone

    threshold = (datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)).isoformat()
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM judge0_submissions WHERE submission_status = 'submitted' AND created_at <= ?",
            (threshold,),
        ).fetchall()
    return [dict(row) for row in rows]
