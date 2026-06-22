from __future__ import annotations

from dataclasses import dataclass, field

from contestiq_core.models import NormalizedProblem, UserProblemAttempt


@dataclass(frozen=True)
class ScenarioExpectation:
    key_skills: dict[str, str] = field(default_factory=dict)
    repair_eligible: dict[str, bool | None] = field(default_factory=dict)
    queue_modes: set[str] = field(default_factory=set)
    required_slots: set[str] = field(default_factory=set)
    forbidden_likely: set[str] = field(default_factory=set)
    notes: str = ""


@dataclass(frozen=True)
class CalibrationScenario:
    name: str
    attempts: list[UserProblemAttempt]
    problems: list[NormalizedProblem]
    overall_rating: int
    expected: ScenarioExpectation


def _attempt(
    key: str,
    tags: list[str],
    verdicts: list[str],
    rating: int = 1200,
    handle: str = "synthetic",
) -> UserProblemAttempt:
    has_ac = "OK" in verdicts
    ac_index = verdicts.index("OK") if has_ac else None
    base_time = 1700000000 + abs(hash(key)) % 100000
    return UserProblemAttempt(
        handle=handle,
        problem_key=key,
        problem_name=key,
        attempt_count=len(verdicts),
        has_ac=has_ac,
        verdict_sequence=verdicts,
        attempts_before_ac=ac_index,
        first_submission_time=base_time,
        first_ac_time=base_time + ac_index * 60 if ac_index is not None else None,
        last_submission_time=base_time + (len(verdicts) - 1) * 60,
        dominant_language="GNU C++17",
        participant_types=["PRACTICE"],
        problem_rating=rating,
        problem_tags=tags,
    )


def _problem(key: str, name: str, tags: list[str], rating: int, solved_count: int = 2500) -> NormalizedProblem:
    return NormalizedProblem(problem_key=key, name=name, rating=rating, tags=tags, solved_count=solved_count)


def _candidate_problems() -> list[NormalizedProblem]:
    return [
        _problem("rec_dp_1", "DP Repair", ["dp"], 1200),
        _problem("rec_dp_2", "DP Stretch", ["dp"], 1450),
        _problem("rec_graph_1", "Graph Repair", ["graphs"], 1200),
        _problem("rec_graph_2", "Shortest Path Practice", ["shortest paths"], 1350),
        _problem("rec_greedy_1", "Greedy Maintenance", ["greedy"], 1200),
        _problem("rec_geo_1", "Geometry Exploration", ["geometry"], 1200),
        _problem("rec_string_1", "String Practice", ["strings"], 1250),
        _problem("rec_math_1", "Number Theory Practice", ["number theory"], 1200),
        _problem("rec_tree_1", "Tree Practice", ["trees"], 1300),
        _problem("rec_bs_1", "Binary Search Practice", ["binary search"], 1250),
    ]


def sparse_profile() -> CalibrationScenario:
    attempts = [
        _attempt("sp_1", ["dp"], ["WRONG_ANSWER"], 1100),
        _attempt("sp_2", ["greedy"], ["OK"], 1000),
        _attempt("sp_3", ["graphs"], ["TIME_LIMIT_EXCEEDED"], 1300),
        _attempt("sp_4", ["math"], ["OK"], 1000),
    ]
    return CalibrationScenario(
        "sparse_profile",
        attempts,
        _candidate_problems(),
        1100,
        ScenarioExpectation(
            queue_modes={"calibration", "low_evidence_exploration"},
            forbidden_likely={"dynamic_programming", "graphs"},
            notes="Sparse history should suppress repair and public weakness claims.",
        ),
    )


def strong_clean_profile() -> CalibrationScenario:
    attempts = []
    domains = [(["dp"], 1500), (["graphs"], 1500), (["greedy"], 1400), (["data structures"], 1500), (["strings"], 1400)]
    for idx in range(45):
        tags, rating = domains[idx % len(domains)]
        attempts.append(_attempt(f"clean_{idx}", tags, ["OK"], rating + (idx % 3) * 100))
    return CalibrationScenario(
        "strong_clean_profile",
        attempts,
        _candidate_problems(),
        1500,
        ScenarioExpectation(
            queue_modes={"maintenance_stretch", "no_repair_needed"},
            forbidden_likely={"dynamic_programming", "graphs", "greedy_constructive"},
            notes="Clean broad success should not manufacture repair items.",
        ),
    )


def clear_dp_friction_in_range() -> CalibrationScenario:
    attempts = []
    for idx in range(8):
        attempts.append(_attempt(f"dp_fail_{idx}", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200 + (idx % 3) * 100))
    for idx in range(18):
        attempts.append(_attempt(f"greedy_ok_{idx}", ["greedy"], ["OK"], 1100 + (idx % 4) * 100))
    for idx in range(8):
        attempts.append(_attempt(f"str_ok_{idx}", ["strings"], ["OK"], 1100 + (idx % 3) * 100))
    return CalibrationScenario(
        "clear_dp_friction_in_range",
        attempts,
        _candidate_problems(),
        1250,
        ScenarioExpectation(
            key_skills={"dynamic_programming": "Likely Needs Work"},
            repair_eligible={"dynamic_programming": True},
            required_slots={"repair"},
            queue_modes={"standard", "recovery"},
            notes="Enough in-range DP failures plus stable other-domain success should create repair eligibility if thresholds are coherent.",
        ),
    )


def underexposed_geometry() -> CalibrationScenario:
    attempts = [_attempt(f"greedy_geo_base_{idx}", ["greedy"], ["OK"], 1100) for idx in range(20)]
    attempts.append(_attempt("geo_one", ["geometry"], ["WRONG_ANSWER"], 1200))
    return CalibrationScenario(
        "underexposed_geometry",
        attempts,
        _candidate_problems(),
        1200,
        ScenarioExpectation(
            key_skills={"geometry": "Limited Evidence"},
            repair_eligible={"geometry": False},
            required_slots={"exploration"},
            notes="Single geometry signal should be limited evidence, not weakness.",
        ),
    )


def failed_far_above_rating_stretch() -> CalibrationScenario:
    attempts = [_attempt(f"base_ok_{idx}", ["greedy"], ["OK"], 1100) for idx in range(22)]
    for idx in range(5):
        attempts.append(_attempt(f"far_dp_{idx}", ["dp"], ["WRONG_ANSWER"], 2300 + idx * 100))
    return CalibrationScenario(
        "failed_far_above_rating_stretch",
        attempts,
        _candidate_problems(),
        1200,
        ScenarioExpectation(
            forbidden_likely={"dynamic_programming"},
            repair_eligible={"dynamic_programming": False},
            notes="Far-above-level failures should not create a confident public weakness by themselves.",
        ),
    )


def noisy_broad_tags_only() -> CalibrationScenario:
    attempts = []
    noisy_tags = [["implementation"], ["math"], ["brute force"], ["math", "brute force"]]
    for idx in range(28):
        verdicts = ["OK"] if idx % 2 == 0 else ["WRONG_ANSWER"]
        attempts.append(_attempt(f"noisy_{idx}", noisy_tags[idx % len(noisy_tags)], verdicts, 1100 + (idx % 4) * 100))
    return CalibrationScenario(
        "noisy_broad_tags_only",
        attempts,
        _candidate_problems(),
        1200,
        ScenarioExpectation(
            forbidden_likely={"math_number_theory", "sequence_search"},
            notes="Noisy/broad tags alone should not produce confident public weakness.",
        ),
    )


def single_domain_bias() -> CalibrationScenario:
    attempts = [_attempt(f"dp_only_{idx}", ["dp"], ["OK"], 1100 + (idx % 4) * 100) for idx in range(35)]
    return CalibrationScenario(
        "single_domain_bias",
        attempts,
        _candidate_problems(),
        1300,
        ScenarioExpectation(
            forbidden_likely={"graphs", "geometry", "strings"},
            required_slots={"exploration"},
            notes="Absence of attempts outside one domain should become exploration/limited evidence, not weakness.",
        ),
    )


def mixed_realistic_beginner() -> CalibrationScenario:
    attempts = []
    for idx in range(10):
        attempts.append(_attempt(f"graph_fail_{idx}", ["graphs"], ["WRONG_ANSWER", "TIME_LIMIT_EXCEEDED"], 1000 + (idx % 3) * 100))
    for idx in range(22):
        attempts.append(_attempt(f"greedy_beginner_ok_{idx}", ["greedy"], ["OK"], 900 + (idx % 4) * 100))
    for idx in range(18):
        verdicts = ["OK"] if idx % 3 else ["WRONG_ANSWER", "OK"]
        attempts.append(_attempt(f"impl_beginner_{idx}", ["implementation"], verdicts, 800 + (idx % 4) * 100))
    return CalibrationScenario(
        "mixed_realistic_beginner",
        attempts,
        _candidate_problems(),
        1100,
        ScenarioExpectation(
            key_skills={"graphs": "Likely Needs Work"},
            repair_eligible={"graphs": True},
            required_slots={"repair"},
            notes="A beginner profile with repeated in-range graph failures should surface graph repair if thresholds pass.",
        ),
    )


def moderate_realistic_friction() -> CalibrationScenario:
    attempts = []
    for idx in range(10):
        attempts.append(_attempt(f"dp_mixed_fail_{idx}", ["dp"], ["WRONG_ANSWER", "OK"], 1200 + (idx % 3) * 100))
    for idx in range(2):
        attempts.append(_attempt(f"dp_mixed_clean_{idx}", ["dp"], ["OK"], 1200 + (idx % 3) * 100))
    for idx in range(22):
        attempts.append(_attempt(f"greedy_mod_ok_{idx}", ["greedy"], ["OK"], 1100 + (idx % 4) * 100))
    for idx in range(10):
        attempts.append(_attempt(f"str_mod_ok_{idx}", ["strings"], ["OK"], 1100 + (idx % 3) * 100))
    return CalibrationScenario(
        "moderate_realistic_friction",
        attempts,
        _candidate_problems(),
        1250,
        ScenarioExpectation(
            key_skills={},
            repair_eligible={"dynamic_programming": False},
            required_slots={"focused_practice"},
            queue_modes={"focused_practice"},
            notes="Moderate high-confidence DP friction should create focused practice without a firm public weakness label.",
        ),
    )


def all_scenarios() -> list[CalibrationScenario]:
    return [
        sparse_profile(),
        strong_clean_profile(),
        clear_dp_friction_in_range(),
        moderate_realistic_friction(),
        underexposed_geometry(),
        failed_far_above_rating_stretch(),
        noisy_broad_tags_only(),
        single_domain_bias(),
        mixed_realistic_beginner(),
    ]
