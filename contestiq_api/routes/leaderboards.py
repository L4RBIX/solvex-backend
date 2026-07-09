"""v1 private weekly leaderboard endpoints (Phase G3).

Invite-only groups scored from product_events/gamification XP. No global
leaderboard, no duels, no public profiles. Only members can view standings.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, leaderboards, metrics
from contestiq_api.errors import APIError

router = APIRouter(prefix="/api/v1/leaderboards")


def _timed(name: str):
    started = time.monotonic()

    def finish(ok: bool) -> None:
        metrics.observe(f"leaderboards_{name}_latency_ms", (time.monotonic() - started) * 1000)
        if not ok:
            metrics.inc("leaderboards_errors_total")
            metrics.inc(f"leaderboards_{name}_errors_total")

    return finish


def _caller(request: Request, handle: str | None) -> dict[str, Any]:
    user = None
    try:
        user = auth.current_user(request)
    except APIError:
        raise
    return leaderboards.resolve_caller(user, handle)


class CreateLeaderboardRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    display_name: str = Field(min_length=1, max_length=40)


class CreateInviteRequest(BaseModel):
    expires_in_days: int = Field(default=30, ge=1, le=90)


class JoinLeaderboardRequest(BaseModel):
    invite_code: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=1, max_length=40)
    handle: str | None = Field(default=None, min_length=3, max_length=24)


@router.post("")
def create_leaderboard(
    payload: CreateLeaderboardRequest,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("create")
    try:
        caller = _caller(request, handle)
        result = leaderboards.create_group(caller, payload.name, payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("")
def list_leaderboards(
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("list")
    try:
        caller = _caller(request, handle)
        groups = leaderboards.list_groups_for_caller(caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return {"leaderboards": groups}


@router.get("/{leaderboard_id}")
def get_leaderboard(
    leaderboard_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("get")
    try:
        caller = _caller(request, handle)
        leaderboards.require_member(leaderboard_id, caller["aliases"])
        group = leaderboards.get_group(leaderboard_id)
        if group is None or not group["active"]:
            raise APIError("LEADERBOARD_NOT_FOUND", "Leaderboard not found.", 404)
        result = leaderboards._public_group(group)
        member = leaderboards.is_member(leaderboard_id, caller["aliases"])
        if member is not None:
            result["member_role"] = member["member_role"]
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/{leaderboard_id}/invites")
def create_invite(
    leaderboard_id: str,
    payload: CreateInviteRequest,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("invite")
    try:
        caller = _caller(request, handle)
        member = leaderboards.require_member(leaderboard_id, caller["aliases"])
        if member["member_role"] != leaderboards.OWNER_ROLE:
            raise APIError("FORBIDDEN", "Only the leaderboard owner can create invites.", 403)
        result = leaderboards.create_invite(
            leaderboard_id, created_by=caller["subject"], expires_in_days=payload.expires_in_days
        )
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.post("/join")
def join_leaderboard(
    payload: JoinLeaderboardRequest,
    request: Request,
):
    finish = _timed("join")
    try:
        user = None
        try:
            user = auth.current_user(request)
        except APIError:
            raise
        caller = leaderboards.resolve_caller(user, payload.handle)
        result = leaderboards.join_group(caller, payload.invite_code, payload.display_name)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{leaderboard_id}/weekly")
def weekly_leaderboard(
    leaderboard_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("weekly")
    try:
        caller = _caller(request, handle)
        result = leaderboards.weekly_standings(leaderboard_id, caller["aliases"])
        result.pop("viewer_entry", None)
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result


@router.get("/{leaderboard_id}/me")
def my_weekly_rank(
    leaderboard_id: str,
    request: Request,
    handle: str | None = Query(default=None, min_length=3, max_length=24),
):
    finish = _timed("me")
    try:
        caller = _caller(request, handle)
        result = leaderboards.viewer_weekly_me(leaderboard_id, caller["aliases"])
    except Exception:
        finish(ok=False)
        raise
    finish(ok=True)
    return result
