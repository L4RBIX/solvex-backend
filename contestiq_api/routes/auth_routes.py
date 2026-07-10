"""v1 account + Codeforces handle-ownership endpoints (security hotfix).

Self-service account creation and CF handle verification. A bearer token is
the ONLY thing that identifies a SolveX account; a Codeforces handle is
public data that must be explicitly proven (see contestiq_api.handles)
before it carries any authorization weight for PvP/leaderboards/gamification.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from contestiq_api import auth, handles
from contestiq_api.throttle import throttle

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register")
def register(request: Request):
    """Create a fresh, anonymous SolveX account and return a bearer token.

    No email/password — the token itself is the credential (same model as
    admin-issued tokens). It proves nothing about any Codeforces identity;
    call /handles/claim to prove ownership of a CF handle before it can be
    used for PvP, private leaderboards, or XP tied to that handle.
    """
    throttle(request, "auth_register")
    return auth.create_user(role="user")


@router.get("/auth/me")
def me(user: dict[str, Any] = Depends(auth.require_user)):
    verified_handle = handles.verified_handle_for_user(user["user_id"])
    return {
        "user_id": user["user_id"],
        "role": user["role"],
        "handle": verified_handle,
        "handle_verified": verified_handle is not None,
    }


class ClaimHandleRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)


@router.post("/handles/claim")
def claim_handle(
    payload: ClaimHandleRequest,
    request: Request,
    user: dict[str, Any] = Depends(auth.require_user),
):
    throttle(request, "handle_claim")
    return handles.start_claim(user["user_id"], payload.handle)


@router.post("/handles/claim/{claim_id}/verify")
def verify_handle_claim(
    claim_id: str,
    request: Request,
    user: dict[str, Any] = Depends(auth.require_user),
):
    throttle(request, "handle_verify")
    return handles.verify_claim(user["user_id"], claim_id)


@router.get("/handles/me")
def my_handle_claims(user: dict[str, Any] = Depends(auth.require_user)):
    verified_handle = handles.verified_handle_for_user(user["user_id"])
    return {
        "handle": verified_handle,
        "handle_verified": verified_handle is not None,
        "claims": [
            {
                "claim_id": c["claim_id"],
                "handle": c["handle"],
                "status": c["status"],
                "created_at": c["created_at"],
                "expires_at": c["expires_at"],
            }
            for c in handles.list_claims_for_user(user["user_id"])
        ],
    }
