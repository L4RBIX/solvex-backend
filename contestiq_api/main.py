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
    auth_routes,
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
    problems,
    practice,
    recommendations,
    relay,
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


async def _periodic_codeforces_catalog_sync() -> None:
    """Keep CF_CURRENT ⊆ SOLVEX_CATALOG without a separate cron service.

    Interval is CODEFORCES_CATALOG_SYNC_INTERVAL_HOURS (default 6). Set to 0 to
    disable. Uses force=True so TTL cannot leave the catalog stale for weeks.
    """
    interval_hours = float(settings.codeforces_catalog_sync_interval_hours or 0.0)
    if interval_hours <= 0:
        logger.info("periodic_codeforces_catalog_sync disabled (interval_hours<=0)")
        return

    from contestiq_api.cfdata import sync as cf_sync

    # Stagger first run so deploy health checks are not competing with CF I/O.
    await asyncio.sleep(min(90.0, interval_hours * 3600 * 0.01))
    while True:
        try:
            result = await asyncio.to_thread(cf_sync.sync_problemset, True)
            catalog = (result or {}).get("catalog_sync") or {}
            logger.info(
                json.dumps(
                    {
                        "event": "periodic_codeforces_catalog_sync",
                        "refetched": (result or {}).get("refetched"),
                        "status": (result or {}).get("status"),
                        **catalog,
                    },
                    default=str,
                )
            )
            if catalog.get("missing_from_solvex_after"):
                logger.error(
                    "catalog parity gap after sync: missing_from_solvex_after=%s sample=%s",
                    catalog.get("missing_from_solvex_after"),
                    catalog.get("cf_only_ids_sample"),
                )
        except Exception:
            logger.exception("periodic_codeforces_catalog_sync failed")
        await asyncio.sleep(max(60.0, interval_hours * 3600))


async def _periodic_statement_ingest() -> None:
    """Prime the statement ingest queue on a slow cadence."""
    interval_hours = float(settings.statement_ingest_interval_hours or 0.0)
    if interval_hours <= 0:
        logger.info("periodic_statement_ingest disabled (interval_hours<=0)")
        return

    from contestiq_api.cfdata import statement_ingest
    from contestiq_api.cfdata import store as cf_store

    await asyncio.sleep(min(180.0, max(30.0, interval_hours * 3600 * 0.05)))
    while True:
        try:
            queued = await asyncio.to_thread(
                statement_ingest.enqueue_statement_ingestion,
                None,
                reason="periodic_enqueue",
                only_missing=True,
            )
            logger.info(
                json.dumps(
                    {
                        "event": "statement_ingest_enqueue",
                        **queued,
                        "relay_observability": cf_store.statement_relay_observability(),
                    },
                    default=str,
                )
            )
        except Exception:
            logger.exception("periodic_statement_ingest failed")
        await asyncio.sleep(max(60.0, interval_hours * 3600))


async def _embedded_statement_relay() -> None:
    """24/7 in-process statement fetch relay (Railway-hosted).

    Uses curl_cffi chrome116 which currently reaches Codeforces from Railway.
    Communicates through the same lease/result store path as the HTTP relay API.
    """
    if not settings.statement_relay_embedded:
        logger.info("embedded statement relay disabled")
        return
    if not (settings.statement_relay_token or "").strip():
        logger.info("embedded statement relay idle (STATEMENT_RELAY_TOKEN unset)")
        return

    from contestiq_api.cfdata import statement_fetch
    from contestiq_api.cfdata import statement_html
    from contestiq_api.cfdata import statement_ingest
    from contestiq_api.cfdata import store as cf_store

    relay_id = "railway-embedded"
    version = "embedded-1.0.0"
    await asyncio.sleep(20)
    logger.info(json.dumps({"event": "embedded_statement_relay_start", "relay_id": relay_id}))
    while True:
        try:
            cf_store.upsert_relay_heartbeat(relay_id, version=version, note="embedded")
            cf_store.enqueue_statement_ingest(
                cf_store.list_non_display_ready_problem_ids()[:200],
                reason="embedded_prime",
            )
            jobs = cf_store.lease_next_statement_jobs(
                limit=1,
                relay_id=relay_id,
                lease_seconds=int(settings.statement_relay_lease_seconds or 600),
            )
            if not jobs:
                await asyncio.sleep(20)
                continue
            job = jobs[0]
            problem_id = job["problem_id"]
            try:
                fetched = await asyncio.to_thread(
                    statement_fetch.fetch_problem_html,
                    int(job["contest_id"]),
                    str(job["index"]),
                )
            except Exception as exc:
                cf_store.record_statement_job_result(
                    problem_id,
                    relay_id=relay_id,
                    ok=False,
                    error=str(exc)[:400],
                    failure_class="retryable",
                )
                cf_store.bump_statement_ingest_failure(
                    problem_id,
                    error=str(exc)[:400],
                    next_attempt_at=_relay_backoff_iso(job.get("attempt") or 1),
                )
                cf_store.upsert_relay_heartbeat(relay_id, failed=True)
                await asyncio.sleep(float(settings.statement_ingest_rate_limit_seconds or 3))
                continue

            html = fetched.text
            usable = fetched.status_code == 200 and "problem-statement" in html
            if not usable:
                failure_class = "blocked" if (
                    fetched.status_code in {401, 403}
                    or statement_html.is_cloudflare_or_challenge_page(html)
                ) else ("permanent" if fetched.status_code == 404 else "retryable")
                cf_store.record_statement_job_result(
                    problem_id,
                    relay_id=relay_id,
                    ok=False,
                    http_status=fetched.status_code,
                    final_url=fetched.url,
                    error=f"unusable_fetch:{fetched.status_code}",
                    failure_class=failure_class,
                )
                if failure_class == "permanent":
                    cf_store.finish_statement_ingest(
                        problem_id, status="failed", detail="permanent fetch failure"
                    )
                else:
                    cf_store.bump_statement_ingest_failure(
                        problem_id,
                        error=f"unusable_fetch:{fetched.status_code}",
                        next_attempt_at=_relay_backoff_iso(
                            job.get("attempt") or 1, blocked=(failure_class == "blocked")
                        ),
                    )
                cf_store.upsert_relay_heartbeat(
                    relay_id,
                    blocked=(failure_class == "blocked"),
                    failed=(failure_class != "blocked"),
                )
                await asyncio.sleep(float(settings.statement_ingest_rate_limit_seconds or 3))
                continue

            cf_store.record_statement_job_result(
                problem_id,
                relay_id=relay_id,
                ok=True,
                html=html,
                http_status=fetched.status_code,
                final_url=fetched.url,
            )
            outcome = await asyncio.to_thread(
                lambda pid=problem_id, body=html: statement_ingest.ingest_one(pid, html=body)
            )
            status = outcome.get("status") or "failed"
            cf_store.finish_statement_ingest(
                problem_id,
                status=status if status != "skipped" else "succeeded",
            )
            cf_store.upsert_relay_heartbeat(
                relay_id,
                successful_fetch=status in {"succeeded", "partial", "asset_required"},
                failed=status == "failed",
            )
            logger.info(
                json.dumps(
                    {
                        "event": "embedded_statement_relay_ingest",
                        "problem_id": problem_id,
                        "status": status,
                        "display_ready": outcome.get("display_ready"),
                    },
                    default=str,
                )
            )
            await asyncio.sleep(float(settings.statement_ingest_rate_limit_seconds or 3))
        except Exception:
            logger.exception("embedded statement relay loop error")
            await asyncio.sleep(30)


def _relay_backoff_iso(attempts: int, *, blocked: bool = False) -> str:
    from datetime import datetime, timedelta, timezone

    table = {1: 300, 2: 900, 3: 3600, 4: 21600}
    seconds = float(table.get(int(attempts), 86400))
    if blocked:
        seconds = max(seconds, 3600.0)
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


@asynccontextmanager
async def lifespan(app: FastAPI):
    diag = _log_storage_diagnostics()
    asyncio.create_task(_maybe_auto_seed_catalog(diag))
    asyncio.create_task(_periodic_codeforces_catalog_sync())
    asyncio.create_task(_periodic_statement_ingest())
    asyncio.create_task(_embedded_statement_relay())
    yield


app = FastAPI(title="SolveX API", version=MODEL_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
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
app.include_router(auth_routes.router)
app.include_router(v1.router)
app.include_router(sync.router)
app.include_router(episodes.router)
app.include_router(weakness.router)
app.include_router(recommendations.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(relay.router)
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
app.include_router(problems.router)
app.include_router(practice.router)
