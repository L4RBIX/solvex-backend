"""GET /api/copilot/profile  ·  POST /api/copilot/profile/update  ·  POST /api/copilot/events"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from contestiq_api import auth
from contestiq_api.coach_service import (
    load_profile,
    save_solving_event,
    update_user_solving_profile,
)
from contestiq_api.settings import get_settings

router = APIRouter(prefix="/api/copilot")


# ─── Request models ───────────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    anonymous_user_key: str | None = None
    user_id: str | None = None


class SolvingEventRequest(BaseModel):
    anonymous_user_key: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    problem_id: str | None = None
    contest_id: int | None = None
    problem_index: str | None = None
    problem_title: str | None = None
    problem_rating: int | None = None
    problem_tags: list[str] = Field(default_factory=list)
    language: str | None = None
    # compile_error | runtime_error | wrong_answer | accepted | tle | copilot_question | run_attempt
    event_type: str
    # undeclared_variable | syntax | overflow | index_error | edge_case | complexity | unknown | ...
    error_type: str | None = None
    short_summary: str | None = None
    source_code_excerpt: str | None = None
    compiler_output_excerpt: str | None = None
    runtime_output_excerpt: str | None = None
    metadata: dict = Field(default_factory=dict)


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(
    anonymous_user_key: str | None = None,
    user_id: str | None = None,
    user: dict[str, Any] = Depends(auth.require_user),
):
    """Return only the bearer token owner's private solving profile."""
    settings = get_settings()
    profile = await load_profile(
        settings,
        user_id=user["user_id"],
        anonymous_user_key=None,
    )
    if not profile:
        return {"status": "not_found", "profile": None}
    return {"status": "ok", "profile": profile}


@router.post("/profile/update")
async def update_profile(req: ProfileUpdateRequest, user: dict[str, Any] = Depends(auth.require_user)):
    """Re-aggregate solving events and update the user profile. Returns updated profile."""
    settings = get_settings()
    profile = await update_user_solving_profile(
        settings,
        user_id=user["user_id"],
        anonymous_user_key=None,
    )
    if profile is None:
        return {"status": "no_data", "profile": None}
    return {"status": "ok", "profile": profile}


@router.post("/events")
async def create_event(req: SolvingEventRequest, user: dict[str, Any] = Depends(auth.require_user)):
    """Save a solving event from the frontend (run result, WA, accepted, etc.)."""
    settings = get_settings()
    event = req.model_dump()
    event["id"] = str(uuid.uuid4())
    event["user_id"] = user["user_id"]
    event["anonymous_user_key"] = None
    await save_solving_event(settings, event)
    return {"status": "ok"}
