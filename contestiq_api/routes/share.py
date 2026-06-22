from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from contestiq_api.share import create_share_for_handle, get_share_report, share_markdown

router = APIRouter()


@router.post("/api/analysis/{handle}/share")
def create_share(handle: str):
    return create_share_for_handle(handle)


@router.get("/api/share/{share_id}.md", response_class=PlainTextResponse)
def public_share_md(share_id: str):
    return share_markdown(share_id)


@router.get("/api/share/{share_id}")
def public_share(share_id: str):
    return get_share_report(share_id)
