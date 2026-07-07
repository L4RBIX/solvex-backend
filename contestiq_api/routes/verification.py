"""v1 SkillTrace verification endpoints (Phase 07).

Security posture:
- All session operations require a bearer token and enforce ownership (BOLA).
- Judge0 is reached only through the backend adapter; credentials and hidden
  tests never appear in any response.
- The Judge0 callback authenticates with a per-submission secret and is
  idempotent; a reconciler endpoint covers missed callbacks.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field, field_validator

from contestiq_api import auth, entitlements
from contestiq_api.errors import APIError
from contestiq_api.skilltrace import sessions as st
from contestiq_api.skilltrace import events as st_events

router = APIRouter(prefix="/api/v1")

_MAX_SOURCE_BYTES = 100 * 1024
_MAX_STDIN_BYTES = 64 * 1024


class StartSessionRequest(BaseModel):
    skill_id: str = Field(min_length=2, max_length=64)
    level: int | None = Field(default=None, ge=1, le=3)


class SnapshotRequest(BaseModel):
    code: str = Field(min_length=0, max_length=_MAX_SOURCE_BYTES)


class RunRequest(BaseModel):
    language: str
    source_code: str
    stdin: str = ""

    @field_validator("source_code")
    @classmethod
    def _source_size(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_code cannot be empty")
        if len(v.encode()) > _MAX_SOURCE_BYTES:
            raise ValueError("source_code exceeds 100 KB limit")
        return v

    @field_validator("stdin")
    @classmethod
    def _stdin_size(cls, v: str) -> str:
        if len(v.encode()) > _MAX_STDIN_BYTES:
            raise ValueError("stdin exceeds 64 KB limit")
        return v


class SubmitRequest(BaseModel):
    language: str
    source_code: str

    @field_validator("source_code")
    @classmethod
    def _source_size(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_code cannot be empty")
        if len(v.encode()) > _MAX_SOURCE_BYTES:
            raise ValueError("source_code exceeds 100 KB limit")
        return v


def _require_user(request: Request) -> dict[str, Any]:
    user = auth.current_user(request)
    if user is None:
        raise APIError("AUTH_REQUIRED", "Verification requires an API token (Authorization: Bearer …).", 401)
    return user


def _owned_session(session_id: str, request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    user = _require_user(request)
    session = st.get_session(session_id)
    if session is None:
        raise APIError("SESSION_NOT_FOUND", f"No verification session found with id {session_id}.", 404)
    st.assert_owner(session, user)
    return session, user


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.post("/verification/sessions")
def start_session(payload: StartSessionRequest, request: Request,
                  ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    user = _require_user(request)
    entitlements.check_and_count_usage(ctx, "verification_attempts_per_week", window="week")
    from contestiq_api import product_events

    product_events.track("verification_attempted", f"user:{user['user_id']}", {"skill_id": payload.skill_id})
    return st.start_session(user, payload.skill_id, payload.level, _request_id(request))


@router.get("/verification/sessions/{session_id}")
def get_session(session_id: str, request: Request):
    session, _ = _owned_session(session_id, request)
    return st.session_view(session)


@router.post("/verification/sessions/{session_id}/snapshot")
def snapshot(session_id: str, payload: SnapshotRequest, request: Request):
    session, _ = _owned_session(session_id, request)
    return st.record_snapshot(session, payload.code, _request_id(request))


@router.post("/verification/sessions/{session_id}/run")
def run(session_id: str, payload: RunRequest, request: Request):
    session, _ = _owned_session(session_id, request)
    return st.create_run(session, payload.language, payload.source_code, payload.stdin, _request_id(request))


@router.post("/verification/sessions/{session_id}/submit")
def submit(session_id: str, payload: SubmitRequest, request: Request):
    session, _ = _owned_session(session_id, request)
    return st.submit_final(session, payload.language, payload.source_code, _request_id(request))


@router.get("/verification/sessions/{session_id}/events")
def session_events(session_id: str, request: Request):
    session, _ = _owned_session(session_id, request)
    return {
        "session_id": session_id,
        "chain_valid": st_events.verify_chain(session_id),
        "events": [
            {k: e[k] for k in ("seq", "event_type", "actor_type", "source_trust", "received_at",
                               "payload", "payload_redaction_level", "event_hash")}
            for e in st_events.list_events(session_id)
        ],
    }


# Judge0 sends PUT by default; POST accepted for flexibility. Authenticated by
# the per-submission secret — never by trusting the payload alone.
@router.put("/judge0/callback")
@router.post("/judge0/callback")
async def judge0_callback(request: Request, secret: str = Query(min_length=8)):
    from contestiq_api.throttle import throttle

    throttle(request, "judge0_callback")
    payload = await request.json()
    if not isinstance(payload, dict):
        raise APIError("INVALID_CALLBACK", "Callback payload must be a JSON object.", 422)
    return st.handle_judge0_result(secret, payload, "judge0_callback")


@router.post("/verification/reconcile")
def reconcile(request: Request, older_than_seconds: float = Query(default=20.0, ge=0)):
    auth.require_admin(request)
    return st.reconcile_pending(older_than_seconds)


@router.get("/badges/{badge_public_id}")
def public_badge(badge_public_id: str, request: Request):
    from contestiq_api.throttle import throttle

    throttle(request, "badge_view")
    badge = st.public_badge_view(badge_public_id)
    if badge is None:
        raise APIError("BADGE_NOT_FOUND", f"No badge found with id {badge_public_id}.", 404)
    return badge


@router.get("/reports/{report_id}")
def private_report(report_id: str, request: Request):
    user = _require_user(request)
    report = st.get_report(report_id)
    if report is None:
        raise APIError("REPORT_NOT_FOUND", f"No report found with id {report_id}.", 404)
    if user.get("role") != "admin" and user["user_id"] != report["user_id"]:
        raise APIError("FORBIDDEN", "You do not have access to this report.", 403)
    return {
        "report_id": report["report_id"],
        "session_id": report["session_id"],
        "created_at": report["created_at"],
        "content": report["content"],
    }
