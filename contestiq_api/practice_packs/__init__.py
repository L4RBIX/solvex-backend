"""SolveX practice pack generation, validation, and activation."""

from contestiq_api.practice_packs.classify import (
    AUTO_PACK_POSSIBLE,
    REVIEW_PACK_POSSIBLE,
    UNSUPPORTED,
    classify_problem,
)
from contestiq_api.practice_packs.pipeline import (
    activate_oracle_packs,
    coverage_snapshot,
    ensure_auto_packs_seeded,
    problem_has_active_pack,
    seed_auto_practice_packs,
    submit_capable_problem_ids,
)

__all__ = [
    "AUTO_PACK_POSSIBLE",
    "REVIEW_PACK_POSSIBLE",
    "UNSUPPORTED",
    "activate_oracle_packs",
    "classify_problem",
    "coverage_snapshot",
    "ensure_auto_packs_seeded",
    "problem_has_active_pack",
    "seed_auto_practice_packs",
    "submit_capable_problem_ids",
]
