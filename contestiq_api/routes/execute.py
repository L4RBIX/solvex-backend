"""POST /api/execute — run user code through Judge0 (C++17 and Python 3 only)."""

from __future__ import annotations

import hashlib
import logging
import uuid

import httpx
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field, field_validator

from contestiq_api.errors import APIError
from contestiq_api.judge0_client import Judge0ResultError, run_submission
from contestiq_api.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

_LANGUAGE_IDS: dict[str, int] = {
    "cpp17":   54,
    "python3": 71,
}

_UNSUPPORTED_MSG = (
    "Unsupported language. This MVP supports only C++17 and Python 3."
)

_MAX_SOURCE_BYTES = 100 * 1024
_MAX_STDIN_BYTES  =  64 * 1024
_INVALID_RESULT_MSG = (
    "Execution service returned an invalid result. Please run again."
)


class ExecuteRequest(BaseModel):
    language: str
    source_code: str
    stdin: str = ""
    expected_output: str | None = None
    problem_key: str | None = None
    client_run_id: str | None = Field(default=None, max_length=128)

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

    @field_validator("client_run_id")
    @classmethod
    def _check_client_run_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned or None


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
    client_run_id: str | None = None
    execution_id: str


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(
    req: ExecuteRequest,
    response: Response,
    request: Request,
) -> ExecuteResponse:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    from contestiq_api.throttle import throttle

    throttle(request, "execute")
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
    execution_id = str(uuid.uuid4())
    client_run_id = req.client_run_id
    source_sha = _sha256_hex(req.source_code)
    stdin_sha = _sha256_hex(req.stdin)
    logger.info(
        "execute_start execution_id=%s client_run_id=%s problem_key=%s lang=%s "
        "lang_id=%d source_sha256=%s stdin_sha256=%s code_bytes=%d stdin_bytes=%d",
        execution_id,
        client_run_id,
        req.problem_key,
        req.language,
        language_id,
        source_sha,
        stdin_sha,
        len(req.source_code.encode()),
        len(req.stdin.encode()),
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
            execution_id=execution_id,
            source_sha256=source_sha,
            stdin_sha256=stdin_sha,
        )
    except Judge0ResultError as exc:
        logger.warning(
            "execute_invalid_result execution_id=%s client_run_id=%s reason=%s",
            execution_id,
            client_run_id,
            str(exc),
        )
        raise APIError(
            "judge0_invalid_result",
            _INVALID_RESULT_MSG,
            status_code=502,
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "judge0 http error execution_id=%s status=%d",
            execution_id,
            exc.response.status_code,
        )
        raise APIError(
            "judge0_error",
            f"Judge0 returned HTTP {exc.response.status_code}",
            status_code=502,
        ) from exc
    except httpx.RequestError as exc:
        logger.warning(
            "judge0 connection error execution_id=%s err=%s",
            execution_id,
            type(exc).__name__,
        )
        raise APIError(
            "judge0_unreachable",
            "Cannot reach Judge0. Check JUDGE0_BASE_URL and network.",
            status_code=503,
        ) from exc

    token_hash = result.get("provider_token_sha256")
    logger.info(
        "execute_done execution_id=%s client_run_id=%s status=%s "
        "provider_token_sha256=%s duration_hint_ms=%s",
        execution_id,
        client_run_id,
        result["status"],
        token_hash,
        result.get("time_ms"),
    )

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
        client_run_id=client_run_id,
        execution_id=execution_id,
    )
