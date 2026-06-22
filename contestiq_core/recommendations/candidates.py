from __future__ import annotations

from contestiq_core.models import NormalizedProblem, RecommendationCandidate, SkillScore, UserProblemAttempt
from contestiq_core.recommendations.scoring import score_candidate, skill_ability
from contestiq_core.taxonomy.tag_mapping import map_cf_tags


def _eligible_for_slot(skill_score: SkillScore, slot_type: str) -> bool:
    if slot_type == "repair":
        return (
            skill_score.public_bucket == "Likely Needs Work"
            and skill_score.confidence_score >= 0.55
            and skill_score.n_eff >= 6.0
            and skill_score.distinct_problem_count >= 4
        )
    if slot_type == "focused_practice":
        return skill_score.focused_practice_eligible
    if slot_type == "exploration":
        return skill_score.public_bucket == "Limited Evidence"
    if slot_type == "maintenance":
        return skill_score.public_bucket == "Hidden"
    if slot_type == "stretch":
        return skill_score.public_bucket in {"Hidden", "Watchlist", "Likely Needs Work"}
    return False


def candidate_pool(
    problems: list[NormalizedProblem],
    attempts: list[UserProblemAttempt],
    skill_scores: list[SkillScore],
    slot_type: str,
    max_candidates: int = 200,
    overall_rating: int = 1200,
) -> list[RecommendationCandidate]:
    solved = {attempt.problem_key for attempt in attempts if attempt.has_ac}
    attempted = {attempt.problem_key for attempt in attempts}
    score_by_skill = {score.skill_id: score for score in skill_scores}
    ability_by_skill = {
        skill_id: skill_ability(skill_id, attempts, overall_rating)
        for skill_id in score_by_skill
    }
    results: list[RecommendationCandidate] = []
    for problem in problems:
        if problem.problem_key in solved:
            continue
        mappings = map_cf_tags(problem.tags)
        if not mappings or problem.rating is None:
            continue
        mapped_skill_candidates = sorted({item.skill_id for item in mappings})
        mapping_shares: dict[str, float] = {}
        tag_reliabilities: dict[str, float] = {}
        for item in mappings:
            mapping_shares[item.skill_id] = round(mapping_shares.get(item.skill_id, 0.0) + item.mapping_share, 3)
            tag_reliabilities[item.skill_id] = max(tag_reliabilities.get(item.skill_id, 0.0), item.tag_reliability)
        for mapping in mappings:
            skill_score = score_by_skill.get(mapping.skill_id)
            if not skill_score:
                continue
            if not _eligible_for_slot(skill_score, slot_type):
                continue
            ability = ability_by_skill[mapping.skill_id]
            final, components = score_candidate(problem, mapping, skill_score, slot_type, ability, problem.problem_key in attempted)
            if final <= 0:
                continue
            repair_eligible = _eligible_for_slot(skill_score, "repair")
            exploration_limited = slot_type == "exploration" and skill_score.public_bucket == "Limited Evidence"
            alternative_anchor_skills = [skill_id for skill_id in mapped_skill_candidates if skill_id != mapping.skill_id]
            anchor_visibility = (
                "user_visible"
                if skill_score.user_visible
                else ("debug_only_public_bucket" if skill_score.public_bucket != "Hidden" else "internal_hidden")
            )
            results.append(
                RecommendationCandidate(
                    problem_key=problem.problem_key,
                    problem_name=problem.name,
                    rating=problem.rating,
                    tags=problem.tags,
                    target_skill=mapping.skill_id,
                    slot_type=slot_type,  # type: ignore[arg-type]
                    final_score=final,
                    score_components=components,
                    solved_count=problem.solved_count,
                    anchor_skill=mapping.skill_id,
                    why_selected=f"Selected for {slot_type} because {mapping.skill_id} matched the problem tags with reliability {mapping.tag_reliability:.2f}.",
            why_safe_to_recommend=(
                        "Repair is allowed because public friction thresholds passed."
                        if slot_type == "repair"
                        else (
                            "Focused practice uses moderate high-confidence friction for training without a firm public weakness label."
                            if slot_type == "focused_practice"
                            else "This recommendation does not present a low-evidence skill as a public weakness."
                        )
                    ),
                    repair_confidence_eligible=repair_eligible,
                    exploration_due_to_limited_evidence=exploration_limited,
                    original_codeforces_tags=problem.tags,
                    mapped_skill_candidates=mapped_skill_candidates,
                    mapping_shares=mapping_shares,
                    tag_reliabilities=tag_reliabilities,
                    why_anchor_skill_was_chosen=(
                        f"{mapping.skill_id} was the scored anchor for this {slot_type} candidate; "
                        "alternatives are kept for audit rather than merged into the explanation."
                    ),
                    alternative_anchor_skills=alternative_anchor_skills,
                    whether_anchor_is_domain_or_overlay=mapping.kind,  # type: ignore[arg-type]
                    anchor_visibility_level=anchor_visibility,
                )
            )
    return sorted(results, key=lambda item: item.final_score, reverse=True)[:max_candidates]
