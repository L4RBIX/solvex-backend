from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)
    debug: bool = False
    force_refresh: bool = False


class WorkspaceHandleRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=24)
    notes: str | None = None


class ErrorResponse(BaseModel):
    status: str = "failed"
    error_code: str
    message: str
