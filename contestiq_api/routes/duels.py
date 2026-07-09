"""v1 friend 1v1 duel endpoints (Phase G4). Invite-link only — no matchmaking."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, duels, metrics
from contestiq_api.errors import APIError
from contestiq_api.leaderboards import resolve_caller

router = APIRouter(prefix="/api/v1/duels")


def _timed(name: str):
    started = time.monotonic()

    def finish(ok: bool) -> None:
        metrics.observe(f"duels_{name}_latency_ms", (time.monotonic() - started) * 1000)
        if not ok:
            metrics.inc("duels_errors_total")
            metrics.inc(f"duels_{name}_errors_total")

    return finish


def _caller(request: Request, handle: str | None) -> dict[str, Any]:
    user = auth.current_user(request)
    return resolve_caller(user, handle)


class CreateDuelRequest(BaseModel):
    mode: str = Field(pattern="^(rapid_10|classic_30)$")
    display_name: str = Field(min_length=1, max_length=40)


class JoinDuelRequest(BaseModel):
    invite_code: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=1, max_length=40)
    handle: str | None = Field(default=None, min_length=3, max_length=24)


class SubmitDuelRequest(BaseModel):
    language: str = Field(pattern="^(cpp17|python3)$")
    source_code: str = Field(min_length=1, max_length=100_000)
    stdin: str = Field(default="", max_length=64_000)
    expected_output: str | None = Field(default=None, max_length=64_000)


@router.post("")
def create_duel(
    payload: CreateDuelRequest,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("create")
    try:
        caller = _caller(request, handle)
        result = duels.create_duel(caller, mode=payload.mode, display_name=payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("")
def list_duels(
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("list")
    try:
        caller = _caller(request, handle)
        items = duels.list_duels_for_caller(caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"duels": items}


@router.get("/invite/{invite_code}")
def preview_invite(invite_code: str):
    finish = _timed("preview")
    try:
        result = duels.invite_preview(invite_code)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/join")
def join_duel(payload: JoinDuelRequest, request: Request):
    finish = _timed("join")
    try:
        user = auth.current_user(request)
        caller = resolve_caller(user, payload.handle)
        result = duels.join_duel(caller, payload.invite_code, payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}")
def get_duel(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("get")
    try:
        caller = _caller(request, handle)
        result = duels.public_detail(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}/state")
def duel_state(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    """Lightweight participant-only state for 1–2s polling (room + Arena)."""
    finish = _timed("state")
    try:
        caller = _caller(request, handle)
        result = duels.duel_state(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/ready")
def ready_duel(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("ready")
    try:
        caller = _caller(request, handle)
        result = duels.mark_ready(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/open-arena")
def open_arena(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("open_arena")
    try:
        caller = _caller(request, handle)
        result = duels.open_arena(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/hint")
def duel_hint(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("hint")
    try:
        caller = _caller(request, handle)
        result = duels.use_hint(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/start")
def start_duel(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("start")
    try:
        caller = _caller(request, handle)
        result = duels.start_duel(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/submit")
async def submit_duel(
    duel_id: str,
    payload: SubmitDuelRequest,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("submit")
    try:
        caller = _caller(request, handle)
        result = await duels.submit_solution(
            duel_id,
            caller["aliases"],
            language=payload.language,
            source_code=payload.source_code,
            stdin=payload.stdin,
            expected_output=payload.expected_output,
        )
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}/result")
def duel_result(
    duel_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("result")
    try:
        caller = _caller(request, handle)
        result = duels.result_view(duel_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result
