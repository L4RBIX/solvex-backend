"""Authoritative Solo-practice submission and account progress endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from contestiq_api import auth, completions, handles, practice
from contestiq_api.errors import APIError
from contestiq_api.routes.problems import normalize_problem_id
from contestiq_api.service import validate_handle
from contestiq_api.throttle import throttle

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])

PracticeSource = Literal[
    "retry_queue",
    "daily_queue",
    "seven_day_plan",
    "fourteen_day_plan",
    "direct_arena",
]

CompletionSource = Literal["solvex_practice_judge", "codeforces_verified"]


class DailyGoalItem(BaseModel):
    id: str
    label: str
    completed: bool


class CompletionDailyGoal(BaseModel):
    date: str
    completed: bool
    completed_count: int
    required_count: int
    items: list[DailyGoalItem]


class CompletionEffects(BaseModel):
    solution_verified: bool
    problem_marked_completed: bool
    solved_history_updated: bool
    xp_updated: bool
    daily_goal_updated: bool
    training_queue_refreshed: bool


def _normalized_problem_id(value: str) -> str:
    try:
        return normalize_problem_id(value)
    except APIError as exc:
        raise ValueError(exc.message) from exc


class PracticeSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    language: Literal["cpp17", "python3"]
    source_code: str = Field(min_length=1, max_length=100_000)
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    source: PracticeSource
    queue_item_id: str | None = Field(default=None, min_length=1, max_length=128)
    handle: str | None = Field(default=None, min_length=3, max_length=24)
    visible_problem_ids: list[str] = Field(default_factory=list, max_length=100)
    completed_problem_ids: list[str] = Field(default_factory=list, max_length=500)

    @field_validator("problem_id")
    @classmethod
    def normalize_problem(cls, value: str) -> str:
        return _normalized_problem_id(value)

    @field_validator("visible_problem_ids", "completed_problem_ids")
    @classmethod
    def normalize_problem_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(_normalized_problem_id(value) for value in values))

    @field_validator("source_code")
    @classmethod
    def nonempty_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_code cannot be blank")
        return value


class PracticeCompletion(BaseModel):
    completion_id: str | None = None
    persistent: bool
    recorded: bool
    already_completed: bool
    completed_at: str
    xp_awarded: int
    attempt_count: int
    source: PracticeSource


class PracticeProgressSnapshot(BaseModel):
    xp_total: int
    streak: int
    daily_goal: CompletionDailyGoal


class PracticeNextProblem(BaseModel):
    recommendation_id: str
    problem_id: str
    name: str
    rating: int | None
    tags: list[str]
    target_skill: str | None
    reason: str
    source: PracticeSource
    queue_item_id: str


class PracticeQueueState(BaseModel):
    exhausted: bool
    message: str


class PracticeSubmitResponse(BaseModel):
    request_id: str
    problem_id: str
    submission_id: str
    status: str
    status_id: int | None
    judging_mode: Literal["solvex_practice"]
    judged: bool
    passed: bool
    runtime_ms: int | None
    memory_kb: int | None
    message: str
    stderr: str
    compile_output: str
    completion: PracticeCompletion | None
    progress: PracticeProgressSnapshot | None
    effects: CompletionEffects
    next_problem: PracticeNextProblem | None
    queue: PracticeQueueState


class PracticeCompletionRecord(BaseModel):
    completion_id: str
    problem_id: str
    completion_mode: Literal["solvex_practice"]
    submission_id: str
    source: PracticeSource
    completed_at: str
    attempt_count: int


class PracticeProgressResponse(BaseModel):
    total_completed: int
    completed_problem_ids: list[str]
    completions: list[PracticeCompletionRecord]
    continuation_items: list[PracticeNextProblem]
    queue: PracticeQueueState


class ProblemCompletionCapability(BaseModel):
    problem_id: str
    practice_judge_available: bool
    primary_completion_source: CompletionSource
    completion_sources: list[CompletionSource]


class SoloOpenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    source: PracticeSource = "direct_arena"
    queue_item_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("problem_id")
    @classmethod
    def normalize_problem(cls, value: str) -> str:
        return _normalized_problem_id(value)


class SoloAssignment(BaseModel):
    assignment_id: str
    problem_id: str
    source: PracticeSource
    queue_item_id: str | None
    assigned_at: str
    opened_at: str
    status: Literal["active", "completed"]


class AuthoritativeCompletion(BaseModel):
    completion_id: str
    problem_id: str
    completion_source: CompletionSource
    historical: bool
    already_completed: bool
    completed_at: str
    verified_at: str | None
    assigned_at: str | None
    xp_awarded: int
    queue_source: PracticeSource
    codeforces_submission_id: int | None
    programming_language: str | None


class SoloOpenResponse(BaseModel):
    assignment: SoloAssignment
    capability: ProblemCompletionCapability
    completion: AuthoritativeCompletion | None


class CodeforcesCheckRequest(SoloOpenRequest):
    visible_problem_ids: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("visible_problem_ids")
    @classmethod
    def normalize_visible_problem_ids(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(_normalized_problem_id(value) for value in values))


class CompletionProgress(BaseModel):
    xp_total: int
    streak: int
    daily_goal: CompletionDailyGoal


class CodeforcesCheckResponse(BaseModel):
    problem_id: str
    status: Literal[
        "completed",
        "already_completed",
        "pending",
        "cooldown",
        "verification_required",
        "unavailable",
    ]
    message: str
    latest_verdict: str | None
    cooldown_seconds: int
    next_check_at: str | None
    completion: AuthoritativeCompletion | None
    progress: CompletionProgress
    effects: CompletionEffects
    next_problem: PracticeNextProblem | None
    queue: PracticeQueueState


class SolvedHistoryEntry(BaseModel):
    completion_id: str
    problem_id: str
    title: str
    rating: int | None
    tags: list[str]
    completion_source: CompletionSource
    historical: bool
    completed_at: str
    verified_at: str | None
    assigned_at: str | None
    codeforces_submission_id: int | None
    programming_language: str | None
    attempts: int
    queue_source: PracticeSource
    xp_awarded: int
    official_url: str
    arena_url: str


class SolvedHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    source: CompletionSource | Literal["all"]
    historical: Literal["all", "current", "historical"]
    items: list[SolvedHistoryEntry]


def _optional_subject(request: Request) -> dict[str, Any] | None:
    user = auth.current_user(request)
    if user is None:
        return None
    verified_handle = handles.verified_handle_for_user(user["user_id"])
    return {
        "user_id": user["user_id"],
        "subject": f"user:{user['user_id']}",
        "aliases": [
            f"user:{user['user_id']}",
            *([f"handle:{verified_handle}"] if verified_handle else []),
        ],
        "handle": verified_handle,
        "handle_verified": verified_handle is not None,
    }


@router.post("/submit", response_model=PracticeSubmitResponse)
async def submit_practice(payload: PracticeSubmitRequest, request: Request):
    throttle(request, "practice_submit")
    caller = _optional_subject(request)
    data = payload.model_dump()
    if data.get("handle"):
        data["handle"] = validate_handle(data["handle"])
    # Authenticated completion exclusions always come from the database.
    # Caller-provided completion IDs are only a guest/local continuation aid.
    if caller is not None:
        data["completed_problem_ids"] = []
        data["visible_problem_ids"] = []
    return await practice.submit(data, caller, is_cancelled=request.is_disconnected)


@router.get("/progress", response_model=PracticeProgressResponse)
def practice_progress(caller: dict[str, Any] = Depends(auth.require_user_subject)):
    return practice.progress(caller["user_id"])


@router.get(
    "/capability/{problem_id:path}",
    response_model=ProblemCompletionCapability,
)
def problem_completion_capability(problem_id: str):
    return completions.problem_capability(_normalized_problem_id(problem_id))


@router.post("/open", response_model=SoloOpenResponse)
def open_solo_problem(
    payload: SoloOpenRequest,
    caller: dict[str, Any] = Depends(auth.require_user_subject),
):
    return completions.open_problem(caller, payload.model_dump())


@router.post("/codeforces/check", response_model=CodeforcesCheckResponse)
def check_codeforces_completion(
    payload: CodeforcesCheckRequest,
    request: Request,
    caller: dict[str, Any] = Depends(auth.require_user_subject),
):
    throttle(request, "codeforces_completion_check")
    return completions.check_codeforces(caller, payload.model_dump())


@router.get("/history", response_model=SolvedHistoryResponse)
def solved_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    source: CompletionSource | Literal["all"] = Query(default="all"),
    historical: Literal["all", "current", "historical"] = Query(default="all"),
    caller: dict[str, Any] = Depends(auth.require_user_subject),
):
    return completions.history(
        caller,
        limit=limit,
        offset=offset,
        source=source,
        historical=historical,
    )
