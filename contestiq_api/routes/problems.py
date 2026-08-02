"""Public, read-only metadata for Codeforces problems in the SolveX catalog."""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError

router = APIRouter(prefix="/api/v1/problems", tags=["problems"])

_PROBLEM_ID_RE = re.compile(r"^([1-9]\d*)([A-Za-z][A-Za-z0-9]*)$")
_MAX_PROBLEM_ID_LENGTH = 32


class PublicProblemSample(BaseModel):
    input: str
    output: str
    note: str | None = None


class PublicAuthoredContent(BaseModel):
    summary: str
    input_format: str
    output_format: str
    constraints: str
    samples: list[PublicProblemSample]


class StatementExample(BaseModel):
    input: str
    output: str


class StatementAvailability(BaseModel):
    status: str
    display_ready: bool
    solve_ready: bool
    unavailable_reason: str | None = None


class StatementSource(BaseModel):
    dataset: str | None = None
    urls: list[str] = []


class PublicStatementContent(BaseModel):
    """Imported PUBLIC display content from problem_statements (see
    contestiq_api/cfdata/problem_import.py). NEVER add editorial, reference
    solutions, judge tests, or any duel/pack identifier to this model —
    problem_statements has no such columns in the first place."""

    title: str | None = None
    statement: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    interaction_format: str | None = None
    examples: list[StatementExample] = []
    notes: str | None = None
    time_limit_seconds: float | None = None
    memory_limit_megabytes: float | None = None
    difficulty: str | None = None
    io_mode: str | None = None
    is_interactive: bool
    has_missing_diagrams: bool
    availability: StatementAvailability
    source: StatementSource


class PublicProblemResponse(BaseModel):
    problem_id: str
    contest_id: int
    index: str
    name: str
    rating: int | None
    tags: list[str]
    official_url: str
    content_available: bool
    authored_content: PublicAuthoredContent | None
    statement_content: PublicStatementContent | None = None


def normalize_problem_id(raw_problem_id: str) -> str:
    candidate = raw_problem_id.strip()
    if not candidate or len(candidate) > _MAX_PROBLEM_ID_LENGTH:
        raise APIError(
            "INVALID_PROBLEM_ID",
            "Problem ID must use a positive contest ID followed by an alphanumeric index.",
            400,
        )
    match = _PROBLEM_ID_RE.fullmatch(candidate)
    if match is None:
        raise APIError(
            "INVALID_PROBLEM_ID",
            "Problem ID must use a positive contest ID followed by an alphanumeric index.",
            400,
        )
    contest_id = int(match.group(1))
    index = match.group(2).upper()
    return f"{contest_id}{index}"


def _parse_tags(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if not isinstance(value, list):
        return []
    return [tag for tag in value if isinstance(tag, str)]


def _parse_public_samples(value: Any) -> list[PublicProblemSample]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if not isinstance(value, list):
        return []

    samples: list[PublicProblemSample] = []
    for item in value[:10]:
        if not isinstance(item, dict):
            continue
        sample_input = item.get("input")
        sample_output = item.get("output")
        if not isinstance(sample_input, str) or not isinstance(sample_output, str):
            continue
        note = item.get("note") if isinstance(item.get("note"), str) else None
        samples.append(PublicProblemSample(input=sample_input, output=sample_output, note=note))
    return samples


def _authored_content(pack: dict[str, Any] | None) -> PublicAuthoredContent | None:
    if pack is None:
        return None
    required = ("statement_summary", "input_format", "output_format", "constraints_text")
    if any(not isinstance(pack.get(field), str) or not pack[field].strip() for field in required):
        return None
    return PublicAuthoredContent(
        summary=pack["statement_summary"],
        input_format=pack["input_format"],
        output_format=pack["output_format"],
        constraints=pack["constraints_text"],
        samples=_parse_public_samples(pack.get("sample_tests")),
    )


def _parse_json_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return value if isinstance(value, list) else []


def _statement_content(row: dict[str, Any] | None) -> PublicStatementContent | None:
    if row is None:
        return None

    examples: list[StatementExample] = []
    for item in _parse_json_list(row.get("samples"))[:50]:
        if isinstance(item, dict) and isinstance(item.get("input"), str) and isinstance(item.get("output"), str):
            examples.append(StatementExample(input=item["input"], output=item["output"]))

    urls = [u for u in _parse_json_list(row.get("source_urls")) if isinstance(u, str)]

    return PublicStatementContent(
        title=row.get("title"),
        statement=row.get("statement"),
        input_format=row.get("input_format"),
        output_format=row.get("output_format"),
        interaction_format=row.get("interaction_format"),
        examples=examples,
        notes=row.get("notes"),
        time_limit_seconds=row.get("time_limit_seconds"),
        memory_limit_megabytes=row.get("memory_limit_megabytes"),
        difficulty=row.get("difficulty"),
        io_mode=row.get("io_mode"),
        is_interactive=bool(row.get("is_interactive")),
        has_missing_diagrams=bool(row.get("has_missing_diagrams")),
        availability=StatementAvailability(
            status=row.get("availability_status") or "missing",
            display_ready=bool(row.get("display_ready")),
            solve_ready=bool(row.get("solve_ready")),
            unavailable_reason=row.get("unavailable_reason"),
        ),
        source=StatementSource(dataset=row.get("source_dataset"), urls=urls),
    )


def _problem_response(raw_problem_id: str) -> PublicProblemResponse:
    problem_id = normalize_problem_id(raw_problem_id)
    problem = store.get_problem(problem_id)
    if problem is None:
        raise APIError(
            "PROBLEM_NOT_FOUND",
            f"Problem {problem_id} is not available in the SolveX catalog.",
            404,
        )

    contest_id = problem.get("contest_id")
    problem_index = problem.get("problem_index")
    if not isinstance(contest_id, int) or not isinstance(problem_index, str):
        raise APIError(
            "PROBLEM_NOT_FOUND",
            f"Problem {problem_id} is not available in the SolveX Codeforces catalog.",
            404,
        )

    index = problem_index.upper()
    authored_content = _authored_content(store.get_active_public_problem_content(problem_id))
    statement_content = _statement_content(store.get_problem_statement(problem_id))
    return PublicProblemResponse(
        problem_id=problem_id,
        contest_id=contest_id,
        index=index,
        name=problem.get("name") or problem_id,
        rating=problem.get("rating"),
        tags=_parse_tags(problem.get("tags")),
        official_url=f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
        content_available=authored_content is not None,
        authored_content=authored_content,
        statement_content=statement_content,
    )


@router.get("", response_model=PublicProblemResponse)
def missing_problem_id():
    raise APIError(
        "INVALID_PROBLEM_ID",
        "Problem ID must use a positive contest ID followed by an alphanumeric index.",
        400,
    )


@router.get("/{problem_id:path}", response_model=PublicProblemResponse)
def public_problem(problem_id: str):
    return _problem_response(problem_id)
