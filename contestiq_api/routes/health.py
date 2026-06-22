from __future__ import annotations

import time

import httpx
from fastapi import APIRouter

from contestiq_api import MODEL_VERSION
from contestiq_api.settings import get_settings

router = APIRouter()

_judge0_cache: dict[str, object] = {}
_JUDGE0_CACHE_TTL = 30.0  # seconds


@router.get("/api/health")
async def health():
    settings = get_settings()
    judge0_configured = bool(settings.judge0_base_url)

    # Check Judge0 reachability at most once per 30 s
    judge0_reachable = False
    if judge0_configured:
        now = time.monotonic()
        cached_at = _judge0_cache.get("at", 0.0)
        if now - float(cached_at) < _JUDGE0_CACHE_TTL:
            judge0_reachable = bool(_judge0_cache.get("reachable", False))
        else:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    r = await client.get(f"{settings.judge0_base_url}/languages")
                    judge0_reachable = r.status_code == 200
            except Exception:
                judge0_reachable = False
            _judge0_cache["reachable"] = judge0_reachable
            _judge0_cache["at"] = now

    return {
        "status": "ok",
        "service": "contestiq-api",
        "model_version": MODEL_VERSION,
        "judge0_configured": judge0_configured,
        "judge0_reachable": judge0_reachable,
    }
