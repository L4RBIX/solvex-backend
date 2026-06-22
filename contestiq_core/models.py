from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SkillKind = Literal["domain", "technique"]
SlotType = Literal["repair", "focused_practice", "maintenance", "stretch", "exploration"]
QueueMode = Literal[
    "standard",
    "calibration",
    "low_evidence_exploration",
    "recovery",
    "empty_or_insufficient_data",
    "maintenance_stretch",
    "no_repair_needed",
    "balanced_training",
    "focused_practice",
]
PublicBucket = Literal["Likely Needs Work", "Watchlist", "Limited Evidence", "Hidden"]


class NormalizedProblem(BaseModel):
    problem_key: str
    contest_id: int | None = None
    problemset_name: str | None = None
    index: str | None = None
    name: str
    rating: int | None = None
    tags: list[str] = Field(default_factory=list)
    solved_count: int | None = None


class NormalizedSubmission(BaseModel):
    submission_id: int
    handle: str | None = None
    creation_time_seconds: int
    problem: NormalizedProblem
    programming_language: str | None = None
    verdict: str
    participant_type: str | None = None


class UserProblemAttempt(BaseModel):
    handle: str | None = None
    problem_key: str
    problem_name: str
    attempt_count: int
    has_ac: bool
    verdict_sequence: list[str]
    attempts_before_ac: int | None = None
    first_submission_time: int
    first_ac_time: int | None = None
    last_submission_time: int
    dominant_language: str | None = None
    participant_types: list[str] = Field(default_factory=list)
    problem_rating: int | None = None
    problem_tags: list[str] = Field(default_factory=list)


class SkillCategory(BaseModel):
    skill_id: str
    display_name: str
    kind: SkillKind
    parent_id: str | None = None


class SkillMapping(BaseModel):
    skill_id: str
    kind: SkillKind
    mapping_share: float
    tag_reliability: float
    source_tag: str


class SkillEvidence(BaseModel):
    skill_id: str
    problem_key: str
    outcome: Literal["positive", "friction", "mixed"]
    evidence_value: float
    outcome_weight: float
    difficulty_weight: float
    mapping_share: float
    tag_reliability: float
    attempt_modifier: float
    recency_weight: float
    problem_rating: int | None = None
    verdicts: list[str] = Field(default_factory=list)


class SkillScore(BaseModel):
    skill_id: str
    display_name: str
    severity: float
    confidence: float
    category: PublicBucket
    sample_size: int
    distinct_problems: int
    explanation: str
    components: dict[str, float] = Field(default_factory=dict)
    severity_score: float
    confidence_score: float
    confidence_band: str
    evidence_status: Literal["sufficient", "tentative", "underexposed", "none"]
    n_eff: float
    distinct_problem_count: int
    rating_bucket_count: int
    avg_tag_reliability: float
    recency_factor: float
    skill_success_rate: float | None = None
    user_baseline_success_rate: float | None = None
    success_gap: float
    attempts_friction: float
    repeated_failure: float
    verdict_friction: float
    ceiling_gap: float
    recent_decline: float
    public_bucket: PublicBucket
    suppression_reasons: list[str] = Field(default_factory=list)
    internal_bucket: PublicBucket
    user_visible_bucket: PublicBucket | None = None
    user_visible: bool = False
    visibility_reason: str = "Internal diagnostic only."
    repair_eligible: bool = False
    repair_blocking_reasons: list[str] = Field(default_factory=list)
    meets_confidence_threshold: bool = False
    meets_n_eff_threshold: bool = False
    meets_distinct_problem_threshold: bool = False
    is_underexposed: bool = True
    severity_above_repair_threshold: bool = False
    public_bucket_reason: str = ""
    priority_score: float = 0.0
    effective_repair_score: float | None = None
    focused_practice_eligible: bool = False
    focused_practice_blocking_reasons: list[str] = Field(default_factory=list)


class WeaknessSnapshot(BaseModel):
    likely_needs_work: list[SkillScore] = Field(default_factory=list)
    watchlist: list[SkillScore] = Field(default_factory=list)
    limited_evidence: list[SkillScore] = Field(default_factory=list)
    hidden: list[SkillScore] = Field(default_factory=list)


class RecommendationCandidate(BaseModel):
    problem_key: str
    problem_name: str
    rating: int | None
    tags: list[str]
    target_skill: str
    slot_type: SlotType
    final_score: float
    score_components: dict[str, float]
    solved_count: int | None = None
    anchor_skill: str
    why_selected: str
    why_safe_to_recommend: str
    repair_confidence_eligible: bool
    exploration_due_to_limited_evidence: bool
    original_codeforces_tags: list[str] = Field(default_factory=list)
    mapped_skill_candidates: list[str] = Field(default_factory=list)
    mapping_shares: dict[str, float] = Field(default_factory=dict)
    tag_reliabilities: dict[str, float] = Field(default_factory=dict)
    why_anchor_skill_was_chosen: str = ""
    alternative_anchor_skills: list[str] = Field(default_factory=list)
    whether_anchor_is_domain_or_overlay: SkillKind = "domain"
    anchor_visibility_level: str = "internal"


class QueueItem(RecommendationCandidate):
    explanation: str


class DailyQueue(BaseModel):
    mode: str = "standard"
    queue_mode: QueueMode = "standard"
    items: list[QueueItem]
    caveats: list[str] = Field(default_factory=list)
    queue_mode_reason: str = ""
    evidence_quality_level: str = ""
    repair_candidate_count: int = 0
    focused_practice_candidate_count: int = 0
    maintenance_candidate_count: int = 0
    stretch_candidate_count: int = 0
    exploration_candidate_count: int = 0
    has_sufficient_history: bool = False
    visible_limited_evidence_count: int = 0
    data_is_sparse: bool = True
