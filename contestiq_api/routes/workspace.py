from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from contestiq_api import auth
from contestiq_api.models import WorkspaceHandleRequest
from contestiq_api.service import validate_handle
from contestiq_api.workspace import (
    delete_workspace_handle,
    list_workspace_handles,
    save_workspace_handle,
    workspace_dashboard,
)

router = APIRouter()


@router.get("/api/workspace/handles")
def workspace_handles(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return list_workspace_handles()


@router.post("/api/workspace/handles")
def save_workspace_saved_handle(
    payload: WorkspaceHandleRequest,
    _admin: dict[str, Any] = Depends(auth.require_admin),
):
    handle = validate_handle(payload.handle)
    return save_workspace_handle(handle, notes=payload.notes)


@router.delete("/api/workspace/handles/{handle}")
def delete_workspace_saved_handle(handle: str, _admin: dict[str, Any] = Depends(auth.require_admin)):
    cleaned = validate_handle(handle)
    return delete_workspace_handle(cleaned)


@router.get("/api/workspace/dashboard")
def workspace_training_dashboard(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return workspace_dashboard()
