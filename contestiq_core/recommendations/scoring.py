from __future__ import annotations

from statistics import mean

from contestiq_core.models import NormalizedProblem, SkillMapping, SkillScore, UserProblemAttempt


SLOT_BANDS = {
    "repair": (-150, 25),
    "focused_practice": (-100, 75),
    "maintenance": (-25, 100),
    "stretch": (75, 225),
    "exploration": (-75, 75),
}


def skill_ability(skill_id: str, attempts: list[UserProblemAttempt], overall_rating: int = 1200) -> int:
    from contestiq_core.taxonomy.tag_mapping import map_cf_tags

    solved_ratings = []
    for attempt in attempts:
        if not attempt.has_ac or attempt.problem_rating is None:
            continue
        if any(mapping.skill_id == skill_id for mapping in map_cf_tags(attempt.problem_tags)):
            solved_ratings.append(attempt.problem_rating)
    if not solved_ratings:
        return overall_rating
    skill_mean = mean(solved_ratings)
    confidence = min(0.8, len(solved_ratings) / 8)
    return round(confidence * skill_mean + (1 - confidence) * overall_rating)


def _difficulty_fit(rating: int | None, ability: int, slot_type: str) -> float:
    if rating is None:
        return 0.25
    low, high = SLOT_BANDS[slot_type]
    delta = rating - ability
    if low <= delta <= high:
        return 1.0
    distance = min(abs(delta - low), abs(delta - high))
    return max(0.0, 1.0 - distance / 400)


def score_candidate(
    problem: NormalizedProblem,
    mapping: SkillMapping,
    skill_score: SkillScore,
    slot_type: str,
    ability: int,
    previously_attempted: bool,
) -> tuple[float, dict[str, float]]:
    priority = skill_score.severity * skill_score.confidence
    if slot_type == "exploration" and skill_score.category == "Limited Evidence":
        priority = max(priority, 0.45)
    if slot_type == "focused_practice" and skill_score.focused_practice_eligible:
        priority = max(priority, skill_score.priority_score)
    if slot_type == "maintenance" and skill_score.public_bucket == "Hidden":
        priority = max(priority, 0.42)
    if slot_type == "stretch":
        priority = max(priority, 0.35)
    components = {
        "SkillPriority": min(1.0, priority),
        "SkillMatch": mapping.mapping_share * mapping.tag_reliability,
        "DifficultyFit": _difficulty_fit(problem.rating, ability, slot_type),
        "PrereqReady": 0.8 if problem.rating and problem.rating <= ability + 250 else 0.45,
        "SuccessFit": 0.75 if slot_type not in {"stretch", "focused_practice"} else (0.68 if slot_type == "focused_practice" else 0.55),
        "LearningValue": 0.75 if skill_score.public_bucket != "Hidden" else 0.55,
        "Novelty": 0.25 if previously_attempted else 0.9,
        "Quality": min(1.0, (problem.solved_count or 0) / 5000) if problem.solved_count else 0.45,
        "DiversityGain": 0.6,
        "GoalFit": 0.7,
        "RecentRepeatPenalty": 1.0 if previously_attempted else 0.0,
        "MultiTagNoisePenalty": max(0.0, (len(problem.tags) - 4) / 8),
        "FatigueRisk": 0.65 if problem.rating and problem.rating > ability + 275 else 0.1,
    }
    score = (
        0.26 * components["SkillPriority"]
        + 0.18 * components["SkillMatch"]
        + 0.16 * components["DifficultyFit"]
        + 0.10 * components["PrereqReady"]
        + 0.08 * components["SuccessFit"]
        + 0.07 * components["LearningValue"]
        + 0.05 * components["Novelty"]
        + 0.04 * components["Quality"]
        + 0.03 * components["DiversityGain"]
        + 0.03 * components["GoalFit"]
        - 0.10 * components["RecentRepeatPenalty"]
        - 0.06 * components["MultiTagNoisePenalty"]
        - 0.04 * components["FatigueRisk"]
    )
    return round(max(0.0, min(1.0, score)), 4), components
