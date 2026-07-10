from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from contestiq_api import auth, handles
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle
from contestiq_api.share import create_share_for_handle, get_share_report, share_markdown

router = APIRouter()


@router.post("/api/analysis/{handle}/share")
def create_share(handle: str, user: dict[str, Any] = Depends(auth.require_user)):
    cleaned = validate_handle(handle)
    if handles.owner_user_id_for_handle(cleaned) != user["user_id"]:
        raise APIError(
            "HANDLE_NOT_VERIFIED",
            "Verify ownership of this Codeforces handle before publishing its report.",
            403,
        )
    return create_share_for_handle(cleaned)


@router.get("/api/share/{share_id}.md", response_class=PlainTextResponse)
def public_share_md(share_id: str):
    return share_markdown(share_id)


@router.get("/api/share/{share_id}")
def public_share(share_id: str):
    return get_share_report(share_id)
