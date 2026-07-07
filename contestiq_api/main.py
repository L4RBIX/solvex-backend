from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from contestiq_api import metrics

from contestiq_api import MODEL_VERSION
from contestiq_api.errors import APIError
from contestiq_api.routes import (
    admin,
    analysis,
    b2b,
    billing,
    coach,
    copilot,
    episodes,
    execute,
    feedback,
    health,
    recommendations,
    share,
    sync,
    v1,
    verification,
    weakness,
    workspace,
)
from contestiq_api.settings import get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger("solvex.api")

app = FastAPI(title="SolveX API", version=MODEL_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Request/trace IDs, structured JSON access logs, and golden-signal metrics.

    Never log headers, bodies, tokens, or query strings — only the path.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-Id") or request_id
    request.state.request_id = request_id
    request.state.trace_id = trace_id
    started = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-Id"] = trace_id

    group = metrics.path_group(request.url.path)
    metrics.inc(f"http_requests_total_{group}_{response.status_code // 100}xx")
    metrics.observe(f"http_request_duration_ms_{group}", duration_ms)
    if response.status_code in (401, 403, 429):
        metrics.inc(f"auth_denials_total_{response.status_code}")

    logger.info(json.dumps({
        "event": "http_request",
        "request_id": request_id,
        "trace_id": trace_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round(duration_ms, 1),
    }))
    return response


@app.get("/api/v1/metrics", response_class=PlainTextResponse)
async def metrics_endpoint(request: Request):
    from contestiq_api.auth import require_admin

    require_admin(request)
    return metrics.render_text()


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    # Error body is a stable contract; the request id travels in the X-Request-ID header.
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failed",
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


app.include_router(health.router)
app.include_router(v1.router)
app.include_router(sync.router)
app.include_router(episodes.router)
app.include_router(weakness.router)
app.include_router(recommendations.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(verification.router)
app.include_router(b2b.router)
app.include_router(analysis.router)
app.include_router(execute.router)
app.include_router(share.router)
app.include_router(workspace.router)
app.include_router(feedback.router)
app.include_router(copilot.router)
app.include_router(coach.router)
