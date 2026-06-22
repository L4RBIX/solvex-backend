"""
Async client for Judge0 CE.
Submits code, polls until final status, returns normalised result dict.
"""

from __future__ import annotations

import asyncio
import base64
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

_POLL_INTERVAL_S = 1.0
_MAX_POLLS = 15         # 15 s total timeout


def _norm(s: object) -> str:
    return s if isinstance(s, str) else ""


def _b64enc(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def _b64dec(s: object) -> str:
    if not s:
        return ""
    try:
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except Exception:
        return str(s)


def _outputs_match(actual: str, expected: str) -> bool:
    def lines(s: str) -> list[str]:
        return [ln.rstrip() for ln in s.replace("\r\n", "\n").rstrip("\n").split("\n")]
    return lines(actual) == lines(expected)


async def run_submission(
    *,
    base_url: str,
    api_key: str,
    api_host: str,
    language_id: int,
    source_code: str,
    stdin: str,
    expected_output: str | None = None,
) -> dict[str, Any]:
    """Submit code to Judge0, poll until final, return normalised result."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
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
        token: str = r.json()["token"]
        logger.info("judge0 token=%s lang_id=%d", token, language_id)

        final: dict[str, Any] | None = None
        for _ in range(_MAX_POLLS):
            await asyncio.sleep(_POLL_INTERVAL_S)
            r = await client.get(
                f"{base_url}/submissions/{token}?base64_encoded=true",
                headers=headers,
            )
            r.raise_for_status()
            data: dict[str, Any] = r.json()
            status_id: int = (data.get("status") or {}).get("id", 0)
            if status_id not in _IN_PROGRESS_IDS:
                final = data
                break

    if final is None:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "",
            "compile_output": "",
            "time_ms": None,
            "memory_kb": None,
            "passed": False,
            "message": "Execution timed out waiting for Judge0.",
        }

    stdout = _b64dec(final.get("stdout"))
    stderr = _b64dec(final.get("stderr"))
    compile_output = _b64dec(final.get("compile_output"))
    message = _norm(final.get("message"))
    status_id = (final.get("status") or {}).get("id", 13)
    solvex_status = _STATUS_MAP.get(status_id, "error")

    if solvex_status == "accepted" and expected_output is not None:
        if not _outputs_match(stdout, expected_output):
            solvex_status = "wrong_answer"

    raw_time = final.get("time")
    time_ms: int | None = None
    if raw_time is not None:
        try:
            time_ms = int(float(raw_time) * 1000)
        except (ValueError, TypeError):
            pass

    return {
        "status": solvex_status,
        "stdout": stdout,
        "stderr": stderr,
        "compile_output": compile_output,
        "time_ms": time_ms,
        "memory_kb": final.get("memory"),
        "passed": solvex_status == "accepted",
        "message": message,
    }
