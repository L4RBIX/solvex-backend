from __future__ import annotations

from contestiq_core.diagnosis.explanations import caveats
from contestiq_core.models import DailyQueue, NormalizedProblem, QueueItem, SkillScore, UserProblemAttempt
from contestiq_core.recommendations.candidates import candidate_pool
from contestiq_core.recommendations.explanations import recommendation_explanation


def _pick(candidates, used_problem_keys: set[str], used_skills: set[str]):
    for candidate in candidates:
        if candidate.problem_key not in used_problem_keys and candidate.target_skill not in used_skills:
            return candidate
    for candidate in candidates:
        if candidate.problem_key not in used_problem_keys:
            return candidate
    return candidates[0] if candidates else None


def _queue_mode(
    items: list[QueueItem],
    attempts: list[UserProblemAttempt],
    visible_limited_evidence_count: int,
) -> tuple[str, str, str, bool, bool]:
    solved = sum(1 for attempt in attempts if attempt.has_ac)
    has_sufficient_history = len(attempts) >= 30 and solved >= 20
    data_is_sparse = len(attempts) < 10 or solved < 5
    if not attempts or not items:
        return "empty_or_insufficient_data", "No usable attempts or queue candidates were available.", "empty", has_sufficient_history, True
    if data_is_sparse:
        return "calibration", "Submission history is too small for normal routing.", "sparse", has_sufficient_history, data_is_sparse
    repair_count = sum(1 for item in items if item.slot_type == "repair")
    focused_count = sum(1 for item in items if item.slot_type == "focused_practice")
    exploration_count = sum(1 for item in items if item.slot_type == "exploration")
    maintenance_count = sum(1 for item in items if item.slot_type == "maintenance")
    stretch_count = sum(1 for item in items if item.slot_type == "stretch")
    if repair_count == 0 and not has_sufficient_history and exploration_count >= max(1, len(items) // 2):
        return "low_evidence_exploration", "Exploration dominates and history is not sufficient for normal routing.", "limited", has_sufficient_history, data_is_sparse
    if repair_count == 0 and visible_limited_evidence_count > 0 and exploration_count == len(items):
        return "low_evidence_exploration", "All queue items are exploration and visible evidence is limited.", "limited", has_sufficient_history, data_is_sparse
    if repair_count == 0 and focused_count > 0:
        return "focused_practice", "No hard repair-safe skill passed thresholds; moderate high-confidence friction is routed to focused practice.", "sufficient", has_sufficient_history, data_is_sparse
    if repair_count == 0:
        if maintenance_count or stretch_count:
            return "maintenance_stretch", "No repair-safe skill passed thresholds; queue uses maintenance/stretch/exploration without public weakness claims.", "sufficient", has_sufficient_history, data_is_sparse
        return "no_repair_needed", "No repair-safe skill or maintenance/stretch candidate was available.", "sufficient", has_sufficient_history, data_is_sparse
    if any(item.slot_type == "stretch" for item in items) and repair_count > 0:
        return "standard", "Repair, stretch, and supporting slots are available.", "sufficient", has_sufficient_history, data_is_sparse
    return "recovery", "Repair is available but queue lacks a full standard mix.", "sufficient", has_sufficient_history, data_is_sparse


def build_daily_queue(
    problems: list[NormalizedProblem],
    attempts: list[UserProblemAttempt],
    skill_scores: list[SkillScore],
    overall_rating: int = 1200,
) -> DailyQueue:
    used_problems: set[str] = set()
    used_skills: set[str] = set()
    items: list[QueueItem] = []
    pools = {
        slot: candidate_pool(problems, attempts, skill_scores, slot, overall_rating=overall_rating)
        for slot in ["repair", "focused_practice", "maintenance", "stretch", "exploration"]
    }
    plan = ["repair", "maintenance", "stretch"] if pools["repair"] else ["focused_practice", "maintenance", "stretch"]
    if not any(score.public_bucket == "Hidden" for score in skill_scores):
        plan[1] = "exploration"

    for slot in plan:
        candidates = pools[slot]
        picked = _pick(candidates, used_problems, used_skills)
        if not picked and slot == "maintenance":
            picked = _pick(pools["exploration"], used_problems, used_skills)
        if not picked:
            continue
        used_problems.add(picked.problem_key)
        used_skills.add(picked.target_skill)
        items.append(QueueItem(**picked.model_dump(), explanation=recommendation_explanation(picked)))

    for fallback_slot in ["focused_practice", "exploration", "maintenance", "stretch"]:
        if len(items) >= 3:
            break
        candidates = pools[fallback_slot]
        picked = _pick(candidates, used_problems, used_skills)
        if not picked:
            continue
        used_problems.add(picked.problem_key)
        used_skills.add(picked.target_skill)
        items.append(QueueItem(**picked.model_dump(), explanation=recommendation_explanation(picked)))

    visible_limited = sum(1 for score in skill_scores if score.user_visible and score.user_visible_bucket == "Limited Evidence")
    mode, reason, evidence_level, sufficient_history, sparse = _queue_mode(items, attempts, visible_limited)
    return DailyQueue(
        mode=mode,
        queue_mode=mode,
        items=items,
        caveats=caveats(),
        queue_mode_reason=reason,
        evidence_quality_level=evidence_level,
        repair_candidate_count=len(pools["repair"]),
        focused_practice_candidate_count=len(pools["focused_practice"]),
        maintenance_candidate_count=len(pools["maintenance"]),
        stretch_candidate_count=len(pools["stretch"]),
        exploration_candidate_count=len(pools["exploration"]),
        has_sufficient_history=sufficient_history,
        visible_limited_evidence_count=visible_limited,
        data_is_sparse=sparse,
    )
