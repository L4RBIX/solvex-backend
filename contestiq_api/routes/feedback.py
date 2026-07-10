from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from contestiq_api import auth, handles
from contestiq_api.errors import APIError
from contestiq_api.feedback import ProblemOutcome, QueueItemFeedback, QueueSessionFeedback
from contestiq_api.feedback_analytics import feedback_summary, feedback_summary_markdown
from contestiq_api.service import (
    save_problem_feedback,
    save_problem_outcome,
    save_queue_feedback,
    validate_handle,
)

router = APIRouter()


@router.post("/api/feedback/problem")
def problem_feedback(payload: QueueItemFeedback, user: dict[str, Any] = Depends(auth.require_user)):
    _require_verified_owner(payload.handle, user)
    return save_problem_feedback(payload)


@router.post("/api/outcome/problem")
def problem_outcome(payload: ProblemOutcome, user: dict[str, Any] = Depends(auth.require_user)):
    _require_verified_owner(payload.handle, user)
    return save_problem_outcome(payload)


@router.post("/api/feedback/queue")
def queue_feedback(payload: QueueSessionFeedback, user: dict[str, Any] = Depends(auth.require_user)):
    _require_verified_owner(payload.handle, user)
    return save_queue_feedback(payload)


@router.get("/api/feedback/summary")
def feedback_summary_endpoint(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return feedback_summary()


@router.get("/api/feedback/summary.md", response_class=PlainTextResponse)
def feedback_summary_markdown_endpoint(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return feedback_summary_markdown()


def _require_verified_owner(handle: str, user: dict[str, Any]) -> None:
    cleaned = validate_handle(handle)
    if handles.owner_user_id_for_handle(cleaned) != user["user_id"]:
        raise APIError(
            "HANDLE_NOT_VERIFIED",
            "Verify ownership of this Codeforces handle before submitting account-bound feedback.",
            403,
        )
