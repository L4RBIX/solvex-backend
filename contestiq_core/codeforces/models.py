from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CFProblem(BaseModel):
    contest_id: int | None = Field(default=None, alias="contestId")
    problemset_name: str | None = Field(default=None, alias="problemsetName")
    index: str | None = None
    name: str
    type: str | None = None
    points: float | None = None
    rating: int | None = None
    tags: list[str] = Field(default_factory=list)
    solved_count: int | None = Field(default=None, alias="solvedCount")

    model_config = {"populate_by_name": True}


class CFSubmission(BaseModel):
    id: int
    contest_id: int | None = Field(default=None, alias="contestId")
    creation_time_seconds: int = Field(alias="creationTimeSeconds")
    relative_time_seconds: int | None = Field(default=None, alias="relativeTimeSeconds")
    problem: CFProblem
    author: dict[str, Any] = Field(default_factory=dict)
    programming_language: str | None = Field(default=None, alias="programmingLanguage")
    verdict: str | None = None
    testset: str | None = None
    passed_test_count: int | None = Field(default=None, alias="passedTestCount")
    time_consumed_millis: int | None = Field(default=None, alias="timeConsumedMillis")
    memory_consumed_bytes: int | None = Field(default=None, alias="memoryConsumedBytes")

    model_config = {"populate_by_name": True}


class CFRatingChange(BaseModel):
    contest_id: int = Field(alias="contestId")
    contest_name: str = Field(alias="contestName")
    handle: str
    rank: int
    rating_update_time_seconds: int = Field(alias="ratingUpdateTimeSeconds")
    old_rating: int = Field(alias="oldRating")
    new_rating: int = Field(alias="newRating")

    model_config = {"populate_by_name": True}
