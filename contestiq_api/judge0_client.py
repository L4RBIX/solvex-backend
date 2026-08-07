"""
Async client for Judge0 CE.
Submits code, polls until final status, returns normalised result dict.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_IN_PROGRESS_IDS = {1, 2}   # In Queue, Processing

# Judge0 status ID → SolveX status string
_STATUS_MAP: dict[int, str] = {
    3:  "accepted",
    4:  "wrong_answer",
    5:  "time_limit",
    6:  "compilation_error",
    7:  "runtime_error",   # SIGSEGV
    8:  "runtime_error",   # SIGXFSZ
    9:  "runtime_error",   # SIGFPE
    10: "runtime_error",   # SIGABRT
    11: "runtime_error",   # NZEC
    12: "runtime_error",   # Other
    13: "error",
    14: "runtime_error",
}


class Judge0ResultError(RuntimeError):
    """Provider returned a malformed or inconsistent execution payload."""


def _normalized_status(status_id: int, description: str = "") -> str:
    if "memory limit" in description.casefold():
        return "memory_limit"
    return _STATUS_MAP.get(status_id, "error")


_POLL_INTERVAL_S = 1.0
_MAX_POLLS = 15         # 15 s total timeout


def _norm(s: object) -> str:
    return s if isinstance(s, str) else ""


def _b64enc(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def _b64dec(s: object) -> str:
    if s is None or s is False:
        return ""
    if not isinstance(s, str):
        raise Judge0ResultError("stdout/stderr/compile_output must be base64 strings")
    if s == "":
        return ""
    try:
        return base64.b64decode(s, validate=False).decode("utf-8", errors="replace")
    except Exception as exc:
        raise Judge0ResultError("failed to decode base64 execution field") from exc


def _outputs_match(actual: str, expected: str) -> bool:
    def lines(s: str) -> list[str]:
        return [ln.rstrip() for ln in s.replace("\r\n", "\n").rstrip("\n").split("\n")]
    return lines(actual) == lines(expected)


def _token_sha(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def run_submission(
    *,
    base_url: str,
    api_key: str,
    api_host: str,
    language_id: int,
    source_code: str,
    stdin: str,
    expected_output: str | None = None,
    execution_id: str | None = None,
    source_sha256: str | None = None,
    stdin_sha256: str | None = None,
) -> dict[str, Any]:
    """Submit code to Judge0, poll until final, return normalised result."""
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
    }
    if api_key:
        headers["X-RapidAPI-Key"] = api_key
    if api_host:
        headers["X-RapidAPI-Host"] = api_host

    payload = {
        "language_id": language_id,
        "source_code": _b64enc(source_code),
        "stdin": _b64enc(stdin),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base_url}/submissions?base64_encoded=true&wait=false",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        try:
            created = r.json()
        except Exception as exc:
            raise Judge0ResultError("create submission returned non-JSON") from exc
        token = created.get("token")
        if not isinstance(token, str) or not token.strip():
            raise Judge0ResultError("create submission missing token")
        token = token.strip()
        token_hash = _token_sha(token)
        logger.info(
            "judge0_submit execution_id=%s token_sha256=%s lang_id=%d "
            "source_sha256=%s stdin_sha256=%s",
            execution_id,
            token_hash,
            language_id,
            source_sha256,
            stdin_sha256,
        )

        final: dict[str, Any] | None = None
        for _ in range(_MAX_POLLS):
            await asyncio.sleep(_POLL_INTERVAL_S)
            r = await client.get(
                f"{base_url}/submissions/{token}?base64_encoded=true",
                headers=headers,
            )
            r.raise_for_status()
            try:
                data: dict[str, Any] = r.json()
            except Exception as exc:
                raise Judge0ResultError("poll returned non-JSON") from exc
            raw_status = data.get("status")
            if not isinstance(raw_status, dict):
                raise Judge0ResultError("poll missing status object")
            status_id = raw_status.get("id")
            if not isinstance(status_id, int):
                raise Judge0ResultError("poll status.id is not an int")
            # Guard against token mix-ups if the provider echoes a token field.
            echoed = data.get("token")
            if isinstance(echoed, str) and echoed.strip() and echoed.strip() != token:
                raise Judge0ResultError("poll token mismatch")
            if status_id not in _IN_PROGRESS_IDS:
                final = data
                break

    if final is None:
        return {
            "status": "error",
            "status_id": None,
            "stdout": "",
            "stderr": "",
            "compile_output": "",
            "time_ms": None,
            "memory_kb": None,
            "passed": False,
            "message": "Execution timed out waiting for Judge0.",
            "provider_token_sha256": token_hash,
        }

    stdout = _b64dec(final.get("stdout"))
    stderr = _b64dec(final.get("stderr"))
    compile_output = _b64dec(final.get("compile_output"))
    message = _norm(final.get("message"))
    raw_status = final.get("status") or {}
    if not isinstance(raw_status, dict):
        raise Judge0ResultError("final status object missing")
    status_id = raw_status.get("id", 13)
    if not isinstance(status_id, int):
        raise Judge0ResultError("final status.id is not an int")
    solvex_status = _normalized_status(
        status_id,
        _norm(raw_status.get("description")),
    )

    if solvex_status == "accepted" and expected_output is not None:
        if not _outputs_match(stdout, expected_output):
            solvex_status = "wrong_answer"
            # The normalized status must remain internally consistent even
            # though Judge0 itself reported process success (3).
            status_id = 4

    raw_time = final.get("time")
    time_ms: int | None = None
    if raw_time is not None:
        try:
            time_ms = int(float(raw_time) * 1000)
        except (ValueError, TypeError):
            pass

    memory_kb = final.get("memory")
    if memory_kb is not None and not isinstance(memory_kb, int):
        try:
            memory_kb = int(memory_kb)
        except (TypeError, ValueError) as exc:
            raise Judge0ResultError("memory field is not an int") from exc

    return {
        "status": solvex_status,
        "status_id": status_id,
        "stdout": stdout,
        "stderr": stderr,
        "compile_output": compile_output,
        "time_ms": time_ms,
        "memory_kb": memory_kb,
        "passed": solvex_status == "accepted",
        "message": message,
        "provider_token_sha256": token_hash,
    }
