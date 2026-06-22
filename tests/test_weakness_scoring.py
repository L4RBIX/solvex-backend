from contestiq_core.diagnosis.explanations import FORBIDDEN_PHRASES, contains_unsafe_language
from contestiq_core.diagnosis.weakness import build_weakness_snapshot, severity_score
from contestiq_core.evidence.skill_evidence import build_skill_evidence
from contestiq_core.models import UserProblemAttempt


def _attempt(problem_key, tags, verdicts, rating=1200, has_ac=False):
    return UserProblemAttempt(
        problem_key=problem_key,
        problem_name=problem_key,
        attempt_count=len(verdicts),
        has_ac=has_ac,
        verdict_sequence=verdicts,
        attempts_before_ac=(len(verdicts) - 1 if has_ac else None),
        first_submission_time=1700000000,
        first_ac_time=(1700000000 if has_ac else None),
        last_submission_time=1700000000,
        problem_rating=rating,
        problem_tags=tags,
    )


def test_skill_with_n_eff_below_6_cannot_be_likely_needs_work():
    attempts = [_attempt(f"{idx}A", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200 + idx * 100) for idx in range(4)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    dp = next(score for score in scores if score.skill_id == "dynamic_programming")
    assert dp.n_eff < 6
    assert dp.public_bucket != "Likely Needs Work"
    assert "effective sample size below public weakness threshold" in dp.suppression_reasons


def test_skill_with_distinct_problems_below_4_cannot_be_likely_needs_work():
    attempts = [_attempt(f"{idx}A", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200) for idx in range(3)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    dp = next(score for score in scores if score.skill_id == "dynamic_programming")
    assert dp.distinct_problem_count < 4
    assert dp.public_bucket != "Likely Needs Work"


def test_underexposure_goes_to_limited_evidence():
    attempts = [_attempt("1A", ["geometry"], ["WRONG_ANSWER"], 1200)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    geometry = next(score for score in scores if score.skill_id == "geometry")
    assert geometry.public_bucket == "Limited Evidence"


def test_low_confidence_skill_can_only_be_watchlist_or_limited_evidence():
    attempts = [_attempt(f"{idx}A", ["brute force"], ["WRONG_ANSWER"], 1200) for idx in range(5)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    sequence = next(score for score in scores if score.skill_id == "sequence_search")
    assert sequence.confidence_score < 0.55
    assert sequence.public_bucket in {"Watchlist", "Limited Evidence"}


def test_raw_success_rate_alone_cannot_create_public_weakness_claim():
    attempts = [_attempt(f"{idx}A", ["dp"], ["WRONG_ANSWER"], 2200) for idx in range(3)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, overall_rating=1200, now=1700000100))
    dp = next(score for score in scores if score.skill_id == "dynamic_programming")
    assert dp.skill_success_rate == 0
    assert dp.public_bucket != "Likely Needs Work"


def test_failed_far_above_rating_stretch_attempts_are_not_heavily_penalized():
    far = build_skill_evidence([_attempt("far", ["dp"], ["WRONG_ANSWER"], 2600)], overall_rating=1200, now=1700000100)[0]
    near = build_skill_evidence([_attempt("near", ["dp"], ["WRONG_ANSWER"], 1200)], overall_rating=1200, now=1700000100)[0]
    assert abs(far.evidence_value) < abs(near.evidence_value)
    severity, components = severity_score([far], baseline_success_rate=0.5)
    assert components["ceiling_gap"] == 0
    assert severity < 0.6


def test_safe_explanation_language():
    attempts = [_attempt(f"{idx}A", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200 + idx * 100) for idx in range(4)]
    snapshot, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    text = " ".join(score.explanation for score in scores)
    text += " " + " ".join(snapshot.model_dump_json().split())
    assert not contains_unsafe_language(text)
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text.lower()
