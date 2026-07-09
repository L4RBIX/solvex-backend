from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

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
    gamification,
    health,
    leaderboards,
    duels,
    recommendations,
    share,
    sync,
    v1,
    verification,
    weakness,
    workspace,
)
from contestiq_api.settings import database_path_looks_persistent, get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger("solvex.api")


def _log_storage_diagnostics() -> dict[str, object]:
    """Surface, on every boot, the exact signal for the "empty daily queue
    despite many episodes" bug: an ephemeral DATABASE_PATH wiping the shared
    problem catalog / skill map on redeploy. Cheap (two COUNT queries) and
    never raises — a diagnostics failure must never block startup.
    """
    from contestiq_api.cfdata import store

    diag = {"database_path": settings.database_path,
            "database_path_looks_persistent": database_path_looks_persistent(settings.database_path)}
    try:
        diag.update(store.storage_diagnostics())
    except Exception:
        logger.exception("storage_diagnostics check failed at startup")
        return diag
    logger.info(json.dumps({"event": "storage_diagnostics", **diag}))
    if diag.get("problemset_count") == 0 or diag.get("problem_skill_map_count") == 0:
        logger.warning(
            "Problem catalog or skill map is empty at startup — the daily queue and "
            "training plans will return no candidates until POST /api/v1/sync/problemset "
            "and POST /api/v1/skill-map/rebuild are run (see scripts/seed_production_catalog.py). "
            "If this happens after every deploy, DATABASE_PATH is not pointed at a persistent "
            "volume — see docs/deployment.md 'Persistent Storage on Railway'."
        )
    return diag


async def _maybe_auto_seed_catalog(diag: dict[str, object]) -> None:
    """Opt-in recovery only: enabled via FEATURE_FLAGS=auto_seed_catalog_on_startup.
    Disabled by default, per design — this hits the live Codeforces API and can
    take several seconds, so it must never run on every boring restart. Runs in
    the background (never blocks startup/health checks) and only seeds when the
    catalog is actually empty; a healthy persistent volume makes this a no-op.
    """
    if not settings.flag_enabled("auto_seed_catalog_on_startup"):
        return
    if diag.get("problemset_count") and diag.get("problem_skill_map_count"):
        return
    from contestiq_api.cfdata import sync as cf_sync
    from contestiq_api.cfdata import taxonomy

    logger.info("auto_seed_catalog_on_startup: catalog empty, seeding in the background...")
    try:
        await asyncio.to_thread(cf_sync.sync_problemset)
        result = await asyncio.to_thread(taxonomy.build_problem_skill_map)
        logger.info(json.dumps({"event": "auto_seed_catalog_complete", **result}))
    except Exception:
        logger.exception("auto_seed_catalog_on_startup failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    diag = _log_storage_diagnostics()
    asyncio.create_task(_maybe_auto_seed_catalog(diag))
    yield


app = FastAPI(title="SolveX API", version=MODEL_VERSION, lifespan=lifespan)

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
app.include_router(gamification.router)
app.include_router(leaderboards.router)
app.include_router(duels.router)
