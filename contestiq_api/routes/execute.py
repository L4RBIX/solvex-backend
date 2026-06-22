"""POST /api/execute — run user code through Judge0 (C++17 and Python 3 only)."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from contestiq_api.errors import APIError
from contestiq_api.judge0_client import run_submission
from contestiq_api.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

_LANGUAGE_IDS: dict[str, int] = {
    "cpp17":   54,
    "python3": 71,
}

_UNSUPPORTED_MSG = (
    "Unsupported language. SolveX MVP currently supports only C++17 and Python 3."
)

_MAX_SOURCE_BYTES = 100 * 1024
_MAX_STDIN_BYTES  =  64 * 1024


class ExecuteRequest(BaseModel):
    language: str
    source_code: str
    stdin: str = ""
    expected_output: str | None = None
    problem_key: str | None = None

    @field_validator("source_code")
    @classmethod
    def _check_source(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_code cannot be empty")
        if len(v.encode()) > _MAX_SOURCE_BYTES:
            raise ValueError("source_code exceeds 100 KB limit")
        return v

    @field_validator("stdin")
    @classmethod
    def _check_stdin(cls, v: str) -> str:
        if len(v.encode()) > _MAX_STDIN_BYTES:
            raise ValueError("stdin exceeds 64 KB limit")
        return v


class ExecuteResponse(BaseModel):
    status: str
    stdout: str
    stderr: str
    compile_output: str
    time_ms: int | None
    memory_kb: int | None
    is_mock: bool
    passed: bool
    message: str


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(req: ExecuteRequest) -> ExecuteResponse:
    if req.language not in _LANGUAGE_IDS:
        raise APIError("unsupported_language", _UNSUPPORTED_MSG, status_code=422)

    settings = get_settings()

    if not settings.judge0_base_url:
        raise APIError(
            "judge0_not_configured",
            "Judge0 is not configured. Set JUDGE0_BASE_URL in the backend .env file.",
            status_code=503,
        )

    language_id = _LANGUAGE_IDS[req.language]
    logger.info(
        "execute: lang=%s lang_id=%d code_bytes=%d",
        req.language,
        language_id,
        len(req.source_code.encode()),
    )

    try:
        result = await run_submission(
            base_url=settings.judge0_base_url,
            api_key=settings.judge0_api_key,
            api_host=settings.judge0_api_host,
            language_id=language_id,
            source_code=req.source_code,
            stdin=req.stdin,
            expected_output=req.expected_output,
        )
    except httpx.HTTPStatusError as exc:
        logger.warning("judge0 http error: status=%d", exc.response.status_code)
        raise APIError(
            "judge0_error",
            f"Judge0 returned HTTP {exc.response.status_code}",
            status_code=502,
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("judge0 connection error: %s", type(exc).__name__)
        raise APIError(
            "judge0_unreachable",
            "Cannot reach Judge0. Check JUDGE0_BASE_URL and network.",
            status_code=503,
        ) from exc

    return ExecuteResponse(
        status=result["status"],
        stdout=result["stdout"],
        stderr=result["stderr"],
        compile_output=result["compile_output"],
        time_ms=result["time_ms"],
        memory_kb=result["memory_kb"],
        is_mock=False,
        passed=result["passed"],
        message=result["message"],
    )
