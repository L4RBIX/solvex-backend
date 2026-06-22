from __future__ import annotations

from contestiq_core.taxonomy.skills import all_skills

FORBIDDEN_PHRASES = [
    "you are bad",
    "you are weak",
    "you mastered",
    "proves implementation weakness",
    "cheating",
    "independent solving",
    "guaranteed improvement",
    "optimal plan",
    "authenticity",
    "exact solve time",
]


def weakness_explanation(skill_id: str, category: str) -> str:
    display = all_skills().get(skill_id).display_name if skill_id in all_skills() else skill_id
    if category == "Likely Needs Work":
        return f"Recent Codeforces history suggests current friction in {display} at your present challenge range."
    if category == "Watchlist":
        return f"{display} shows tentative friction signals, but the evidence is not strong enough for a firm diagnosis."
    if category == "Limited Evidence":
        return f"There is limited {display} evidence, so ContestIQ cannot make a reliable diagnosis there yet."
    return f"{display} is not surfaced as current friction from the available Codeforces outcome history."


def caveats() -> list[str]:
    return [
        "Codeforces provides outcome/history data, not full solving process data.",
        "ContestIQ does not infer true start time, solo-work status, contest-integrity judgments, identity proof, or badge readiness from Codeforces-only data.",
        "Wrong-answer counts can signal friction, but Codeforces data alone cannot confirm the underlying cause.",
    ]


def contains_unsafe_language(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in FORBIDDEN_PHRASES)
