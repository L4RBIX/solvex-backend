"""v1 team and event-screening endpoints (Phase 08).

Entitlements: creating teams requires the team plan (coach_dashboard feature);
creating orgs/events requires the event plan (event_dashboard feature); admin
passes both. All object access is scope-checked server-side.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, entitlements, events_screening as ev, teams as teams_mod
from contestiq_api.errors import APIError

router = APIRouter(prefix="/api/v1")


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class InviteRequest(BaseModel):
    member_role: str = Field(pattern="^(coach|student)$")
    expires_in_days: int = Field(default=14, ge=1, le=90)


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=8, max_length=64)


class AssignmentRequest(BaseModel):
    student_user_id: str
    kind: str = Field(pattern="^(skill_focus|problems|verification)$")
    skill_id: str | None = None
    problem_ids: list[str] = Field(default_factory=list, max_length=20)
    challenge_skill_id: str | None = None
    due_date: str | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CreateOrgRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class EventRequirement(BaseModel):
    skill_id: str
    level: int | None = Field(default=None, ge=1, le=3)
    min_evidence_label: str = "sufficient_process_evidence"


class CreateEventRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    requirements: list[EventRequirement] = Field(min_length=1, max_length=5)
    expires_in_days: int = Field(default=30, ge=1, le=180)


class ApplicantLinkRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    expires_in_days: int = Field(default=7, ge=1, le=60)


def _require_user(request: Request) -> dict[str, Any]:
    user = auth.current_user(request)
    if user is None:
        raise APIError("AUTH_REQUIRED", "This endpoint requires an API token.", 401)
    return user


# ─── Teams ───────────────────────────────────────────────────────────────────


@router.post("/teams")
def create_team(payload: CreateTeamRequest, request: Request,
                ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    user = _require_user(request)
    entitlements.require_feature(ctx, "coach_dashboard")
    return teams_mod.create_team(user, payload.name)


@router.post("/teams/{team_id}/invites")
def create_invite(team_id: str, payload: InviteRequest, request: Request):
    user = _require_user(request)
    teams_mod.require_member(team_id, user)  # owner/coach
    return teams_mod.create_invite(team_id, user["user_id"], payload.member_role, payload.expires_in_days)


@router.post("/teams/invites/accept")
def accept_invite(payload: AcceptInviteRequest, request: Request):
    user = _require_user(request)
    return teams_mod.accept_invite(user, payload.token)


@router.get("/teams/{team_id}/students")
def team_students(team_id: str, request: Request):
    user = _require_user(request)
    teams_mod.require_member(team_id, user)
    return {"team_id": team_id, "members": teams_mod.list_students(team_id)}


@router.get("/teams/{team_id}/dashboard")
def team_dashboard(team_id: str, request: Request):
    user = _require_user(request)
    teams_mod.require_member(team_id, user)
    return teams_mod.team_dashboard(team_id)


@router.post("/teams/{team_id}/assignments")
def create_assignment(team_id: str, payload: AssignmentRequest, request: Request):
    user = _require_user(request)
    teams_mod.require_member(team_id, user)
    return teams_mod.create_assignment(team_id, user["user_id"], payload.model_dump())


@router.get("/teams/{team_id}/assignments")
def list_assignments(team_id: str, request: Request, student_user_id: str | None = Query(default=None)):
    user = _require_user(request)
    member = teams_mod.get_member(team_id, user["user_id"])
    if user.get("role") == "admin" or (member and member["member_role"] in teams_mod.MANAGER_ROLES):
        return {"assignments": teams_mod.list_assignments(team_id, student_user_id)}
    if member and member["member_role"] == "student":
        return {"assignments": teams_mod.list_assignments(team_id, user["user_id"])}  # own only
    raise APIError("FORBIDDEN", "You do not have access to this team.", 403)


# ─── Organizations + events ──────────────────────────────────────────────────


@router.post("/orgs")
def create_org(payload: CreateOrgRequest, request: Request,
               ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    user = _require_user(request)
    entitlements.require_feature(ctx, "event_dashboard")
    return ev.create_org(user, payload.name)


@router.post("/orgs/{org_id}/events")
def create_event(org_id: str, payload: CreateEventRequest, request: Request):
    user = _require_user(request)
    ev.require_org_member(org_id, user)
    return ev.create_event(
        org_id, user["user_id"], payload.name,
        [req.model_dump() for req in payload.requirements], payload.expires_in_days,
    )


@router.post("/events/{event_id}/applicant-links")
def create_applicant_link(event_id: str, payload: ApplicantLinkRequest, request: Request):
    user = _require_user(request)
    event = ev.require_event_access(event_id, user)
    return ev.create_applicant_link(event, payload.display_name, payload.email, payload.expires_in_days)


@router.post("/events/links/{token}/start")
def start_applicant_session(token: str, request: Request):
    # Public by design: the expiring, single-use link token IS the credential.
    return ev.start_applicant_session(token, getattr(request.state, "request_id", None))


@router.get("/events/{event_id}/dashboard")
def event_dashboard(event_id: str, request: Request):
    user = _require_user(request)
    event = ev.require_event_access(event_id, user)
    return ev.event_dashboard(event)


@router.get("/events/{event_id}/applicants/{applicant_id}/report")
def applicant_report(event_id: str, applicant_id: str, request: Request):
    user = _require_user(request)
    event = ev.require_event_access(event_id, user)
    return ev.applicant_report(event, applicant_id, f"user:{user['user_id']}")
