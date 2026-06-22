from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from contestiq_api import MODEL_VERSION

FeedbackValue = Literal["good_fit", "too_easy", "too_hard", "not_relevant", "already_seen", "confusing", "skipped"]
OutcomeValue = Literal["solved", "attempted_but_failed", "skipped", "opened_only", "unknown"]


class QueueItemFeedback(BaseModel):
    analysis_id: str
    handle: str
    problem_key: str
    slot_type: str
    anchor_skill: str
    feedback: FeedbackValue
    comment: str | None = Field(default=None, max_length=1000)


class ProblemOutcome(BaseModel):
    analysis_id: str
    handle: str
    problem_key: str
    slot_type: str
    anchor_skill: str
    outcome: OutcomeValue
    comment: str | None = Field(default=None, max_length=1000)


class QueueSessionFeedback(BaseModel):
    analysis_id: str
    handle: str
    queue_rating: FeedbackValue
    comment: str | None = Field(default=None, max_length=1000)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def feedback_record(payload: BaseModel) -> dict:
    return {
        "feedback_id": str(uuid4()),
        "timestamp": timestamp(),
        "model_version": MODEL_VERSION,
        **payload.model_dump(),
    }
