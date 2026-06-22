from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Iterable

from contestiq_core.models import NormalizedProblem, NormalizedSubmission, UserProblemAttempt


def stable_problem_key(problem: dict | NormalizedProblem) -> str:
    contest_id = getattr(problem, "contest_id", None) if not isinstance(problem, dict) else problem.get("contestId") or problem.get("contest_id")
    index = getattr(problem, "index", None) if not isinstance(problem, dict) else problem.get("index")
    name = getattr(problem, "name", None) if not isinstance(problem, dict) else problem.get("name")
    problemset = getattr(problem, "problemset_name", None) if not isinstance(problem, dict) else problem.get("problemsetName") or problem.get("problemset_name")
    if contest_id is not None and index:
        return f"{contest_id}{index}"
    fallback = f"{problemset or 'problemset'}-{index or 'x'}-{name or 'unknown'}".lower()
    return re.sub(r"[^a-z0-9]+", "-", fallback).strip("-")


def normalize_problem(problem: dict, solved_count: int | None = None) -> NormalizedProblem:
    return NormalizedProblem(
        problem_key=stable_problem_key(problem),
        contest_id=problem.get("contestId"),
        problemset_name=problem.get("problemsetName"),
        index=problem.get("index"),
        name=problem.get("name", "Unknown"),
        rating=problem.get("rating"),
        tags=list(problem.get("tags") or []),
        solved_count=solved_count if solved_count is not None else problem.get("solvedCount"),
    )


def normalize_submission(raw: dict) -> NormalizedSubmission:
    problem = normalize_problem(raw["problem"])
    return NormalizedSubmission(
        submission_id=raw["id"],
        handle=(raw.get("author", {}).get("members") or [{}])[0].get("handle"),
        creation_time_seconds=raw["creationTimeSeconds"],
        problem=problem,
        programming_language=raw.get("programmingLanguage"),
        verdict=raw.get("verdict") or "UNKNOWN",
        participant_type=raw.get("author", {}).get("participantType"),
    )


def normalize_problemset(raw_problemset: dict) -> list[NormalizedProblem]:
    solved_counts = {
        stable_problem_key(row): row.get("solvedCount")
        for row in raw_problemset.get("problemStatistics", [])
    }
    return [
        normalize_problem(problem, solved_counts.get(stable_problem_key(problem)))
        for problem in raw_problemset.get("problems", [])
    ]


def normalize_submissions(raw_submissions: Iterable[dict]) -> list[NormalizedSubmission]:
    return [normalize_submission(row) for row in raw_submissions]


def rollup_user_problem_attempts(submissions: Iterable[NormalizedSubmission]) -> list[UserProblemAttempt]:
    grouped: dict[tuple[str | None, str], list[NormalizedSubmission]] = defaultdict(list)
    for submission in submissions:
        grouped[(submission.handle, submission.problem.problem_key)].append(submission)

    attempts: list[UserProblemAttempt] = []
    for (handle, problem_key), rows in grouped.items():
        rows.sort(key=lambda item: item.creation_time_seconds)
        verdicts = [row.verdict for row in rows]
        ac_index = next((idx for idx, verdict in enumerate(verdicts) if verdict == "OK"), None)
        languages = Counter(row.programming_language for row in rows if row.programming_language)
        participant_types = sorted({row.participant_type for row in rows if row.participant_type})
        problem = rows[0].problem
        attempts.append(
            UserProblemAttempt(
                handle=handle,
                problem_key=problem_key,
                problem_name=problem.name,
                attempt_count=len(rows),
                has_ac=ac_index is not None,
                verdict_sequence=verdicts,
                attempts_before_ac=ac_index if ac_index is not None else None,
                first_submission_time=rows[0].creation_time_seconds,
                first_ac_time=rows[ac_index].creation_time_seconds if ac_index is not None else None,
                last_submission_time=rows[-1].creation_time_seconds,
                dominant_language=languages.most_common(1)[0][0] if languages else None,
                participant_types=participant_types,
                problem_rating=problem.rating,
                problem_tags=problem.tags,
            )
        )
    return sorted(attempts, key=lambda item: item.last_submission_time, reverse=True)
