"""v1 friend 1v1 duel endpoints (Phase G4). Invite-link only — no matchmaking.

Security: every endpoint except the invite preview requires a bearer token.
The participant is resolved EXCLUSIVELY from the authenticated user
(auth.require_user_subject) — any caller-supplied handle/subject/user_id is
ignored for authorization. A Codeforces handle is public data and must never
be trusted as identity.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, duels, metrics

router = APIRouter(prefix="/api/v1/duels")


def _timed(name: str):
    started = time.monotonic()

    def finish(ok: bool) -> None:
        metrics.observe(f"duels_{name}_latency_ms", (time.monotonic() - started) * 1000)
        if not ok:
            metrics.inc("duels_errors_total")
            metrics.inc(f"duels_{name}_errors_total")

    return finish


class CreateDuelRequest(BaseModel):
    mode: str = Field(pattern="^(rapid_10|classic_30)$")
    # Backward-compatible input only. The server derives the authoritative
    # presentation label from the authenticated account and never trusts this.
    display_name: str | None = Field(default=None, min_length=1, max_length=40)


class JoinDuelRequest(BaseModel):
    invite_code: str = Field(min_length=8, max_length=64)
    display_name: str | None = Field(default=None, min_length=1, max_length=40)


class SubmitDuelRequest(BaseModel):
    language: str = Field(pattern="^(cpp17|python3)$")
    source_code: str = Field(min_length=1, max_length=100_000)


@router.post("")
def create_duel(payload: CreateDuelRequest, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("create")
    try:
        result = duels.create_duel(caller, mode=payload.mode, display_name=payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("")
def list_duels(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("list")
    try:
        items = duels.list_duels_for_caller(caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"duels": items}


@router.get("/invite/{invite_code}")
def preview_invite(invite_code: str):
    """Public, unauthenticated: safe preview only (mode, creator display
    name, problem rating/tags) — no participant/session data."""
    finish = _timed("preview")
    try:
        result = duels.invite_preview(invite_code)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/join")
def join_duel(payload: JoinDuelRequest, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("join")
    try:
        result = duels.join_duel(caller, payload.invite_code, payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}")
def get_duel(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("get")
    try:
        result = duels.public_detail(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}/state")
def duel_state(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    """Lightweight participant-only state for 1–2s polling (room + Arena)."""
    finish = _timed("state")
    try:
        result = duels.duel_state(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/ready")
def ready_duel(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("ready")
    try:
        result = duels.mark_ready(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/open-arena")
def open_arena(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("open_arena")
    try:
        result = duels.open_arena(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/hint")
def duel_hint(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("hint")
    try:
        result = duels.use_hint(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/start")
def start_duel(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("start")
    try:
        result = duels.start_duel(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{duel_id}/submit")
async def submit_duel(
    duel_id: str,
    payload: SubmitDuelRequest,
    caller: dict[str, Any] = Depends(auth.require_user_subject),
):
    finish = _timed("submit")
    try:
        result = await duels.submit_solution(
            duel_id,
            caller["user_id"],
            language=payload.language,
            source_code=payload.source_code,
        )
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{duel_id}/result")
def duel_result(duel_id: str, caller: dict[str, Any] = Depends(auth.require_user_subject)):
    finish = _timed("result")
    try:
        result = duels.result_view(duel_id, caller["user_id"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result
