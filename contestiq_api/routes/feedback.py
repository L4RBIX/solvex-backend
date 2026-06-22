from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from contestiq_api.feedback import ProblemOutcome, QueueItemFeedback, QueueSessionFeedback
from contestiq_api.feedback_analytics import feedback_summary, feedback_summary_markdown
from contestiq_api.service import save_problem_feedback, save_problem_outcome, save_queue_feedback

router = APIRouter()


@router.post("/api/feedback/problem")
def problem_feedback(payload: QueueItemFeedback):
    return save_problem_feedback(payload)


@router.post("/api/outcome/problem")
def problem_outcome(payload: ProblemOutcome):
    return save_problem_outcome(payload)


@router.post("/api/feedback/queue")
def queue_feedback(payload: QueueSessionFeedback):
    return save_queue_feedback(payload)


@router.get("/api/feedback/summary")
def feedback_summary_endpoint():
    return feedback_summary()


@router.get("/api/feedback/summary.md", response_class=PlainTextResponse)
def feedback_summary_markdown_endpoint():
    return feedback_summary_markdown()
