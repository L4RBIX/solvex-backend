from __future__ import annotations

import math
import time
from collections import defaultdict

from contestiq_core.config import DEFAULT_OVERALL_RATING
from contestiq_core.models import SkillEvidence, UserProblemAttempt
from contestiq_core.taxonomy.tag_mapping import map_cf_tags


def _difficulty_weight(problem_rating: int | None, overall_rating: int = DEFAULT_OVERALL_RATING) -> float:
    if problem_rating is None:
        return 0.75
    delta = problem_rating - overall_rating
    if delta < -500:
        return 0.45
    if delta > 450:
        return 0.55
    return max(0.55, min(1.25, 0.9 + delta / 1000))


def _recency_weight(timestamp: int, now: int | None = None) -> float:
    now = now or int(time.time())
    age_days = max(0, (now - timestamp) / 86400)
    return 0.55 + 0.45 * math.exp(-age_days / 180)


def _outcome_and_attempt(attempt: UserProblemAttempt) -> tuple[str, float, float]:
    if attempt.has_ac:
        before_ac = attempt.attempts_before_ac or 0
        if before_ac == 0:
            return "positive", 1.0, 1.0
        if before_ac <= 2:
            return "mixed", 0.55, 0.72
        return "mixed", 0.25, 0.48
    repeated = attempt.attempt_count >= 2
    return "friction", -0.75 if repeated else -0.35, 1.0 if repeated else 0.65


def build_skill_evidence(
    attempts: list[UserProblemAttempt],
    overall_rating: int = DEFAULT_OVERALL_RATING,
    now: int | None = None,
) -> list[SkillEvidence]:
    evidence: list[SkillEvidence] = []
    for attempt in attempts:
        mappings = map_cf_tags(attempt.problem_tags)
        if not mappings:
            continue
        outcome, outcome_weight, attempt_modifier = _outcome_and_attempt(attempt)
        difficulty_weight = _difficulty_weight(attempt.problem_rating, overall_rating)
        recency_weight = _recency_weight(attempt.last_submission_time, now)
        for mapping in mappings:
            value = (
                outcome_weight
                * difficulty_weight
                * mapping.mapping_share
                * mapping.tag_reliability
                * attempt_modifier
                * recency_weight
            )
            evidence.append(
                SkillEvidence(
                    skill_id=mapping.skill_id,
                    problem_key=attempt.problem_key,
                    outcome=outcome,  # type: ignore[arg-type]
                    evidence_value=value,
                    outcome_weight=outcome_weight,
                    difficulty_weight=difficulty_weight,
                    mapping_share=mapping.mapping_share,
                    tag_reliability=mapping.tag_reliability,
                    attempt_modifier=attempt_modifier,
                    recency_weight=recency_weight,
                    problem_rating=attempt.problem_rating,
                    verdicts=attempt.verdict_sequence,
                )
            )
    return evidence


def evidence_by_skill(evidence: list[SkillEvidence]) -> dict[str, list[SkillEvidence]]:
    grouped: dict[str, list[SkillEvidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.skill_id].append(item)
    return dict(grouped)
