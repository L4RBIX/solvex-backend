from contestiq_core.models import RecommendationCandidate
from contestiq_core.taxonomy.skills import all_skills


def recommendation_explanation(candidate: RecommendationCandidate) -> str:
    skill = all_skills().get(candidate.target_skill)
    display = skill.display_name if skill else candidate.target_skill
    slot = candidate.slot_type
    if slot == "repair":
        return f"Recommended as a repair problem anchored on {display}, chosen near the current challenge range with outcome-only evidence caveats."
    if slot == "focused_practice":
        return f"Recommended as focused practice: recent Codeforces history shows moderate friction in {display} with enough evidence to make this useful for training, but not strong enough for a firm weakness label."
    if slot == "stretch":
        return f"Recommended as a stretch problem anchored on {display}, slightly above the estimated skill-specific ability."
    if slot == "exploration":
        return f"Recommended as exploration for {display}, where current evidence is limited rather than diagnosed as weakness."
    return f"Recommended as maintenance for {display}, to keep a stable skill active without making a stronger claim than the data supports."
