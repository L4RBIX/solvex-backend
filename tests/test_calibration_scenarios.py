from contestiq_core.diagnosis.explanations import FORBIDDEN_PHRASES
from contestiq_core.evaluation.scenarios import all_scenarios
from contestiq_core.pipeline.run_calibration_scenarios import run_calibration_scenarios, run_scenario


def _skills(output):
    return {score["skill_id"]: score for score in output["skill_scores"]}


def _slots(output):
    return {item["slot_type"] for item in output["daily_queue"]["items"]}


def test_sparse_profile_calibrates_instead_of_repair():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "sparse_profile"))
    assert not output["weakness_map_user"]["likely_needs_work"]
    assert not any(item["slot_type"] == "repair" for item in output["daily_queue"]["items"])
    assert output["daily_queue"]["queue_mode"] in {"calibration", "low_evidence_exploration"}


def test_strong_clean_profile_has_no_repair():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "strong_clean_profile"))
    assert not output["weakness_map_user"]["likely_needs_work"]
    assert sum(1 for item in output["daily_queue"]["items"] if item["slot_type"] == "repair") == 0
    assert output["daily_queue"]["queue_mode"] in {"maintenance_stretch", "no_repair_needed"}


def test_clear_dp_friction_in_range_expected_behavior():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "clear_dp_friction_in_range"))
    dp = _skills(output)["dynamic_programming"]
    assert dp["public_bucket"] in {"Likely Needs Work", "Watchlist"}
    if dp["repair_eligible"]:
        assert "repair" in _slots(output)
        assert output["daily_queue"]["queue_mode"] != "maintenance_stretch"
    else:
        assert dp["priority_score"] > 0
        assert dp["repair_blocking_reasons"]


def test_moderate_realistic_friction_triggers_focused_practice_not_likely():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "moderate_realistic_friction"))
    dp = _skills(output)["dynamic_programming"]
    assert dp["focused_practice_eligible"]
    assert not dp["repair_eligible"]
    assert dp["public_bucket"] != "Likely Needs Work"
    assert output["daily_queue"]["queue_mode"] == "focused_practice"
    assert output["daily_queue"]["items"][0]["slot_type"] == "focused_practice"


def test_underexposed_geometry_is_limited_not_repair():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "underexposed_geometry"))
    geometry = _skills(output)["geometry"]
    assert geometry["public_bucket"] == "Limited Evidence"
    assert not geometry["repair_eligible"]
    assert "exploration" in _slots(output)


def test_failed_far_above_rating_stretch_avoids_false_weakness():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "failed_far_above_rating_stretch"))
    dp = _skills(output)["dynamic_programming"]
    assert dp["public_bucket"] != "Likely Needs Work"
    assert not dp["repair_eligible"]


def test_noisy_broad_tags_only_avoids_confident_public_weakness():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "noisy_broad_tags_only"))
    skills = _skills(output)
    assert skills["math_number_theory"]["public_bucket"] != "Likely Needs Work"
    assert skills["sequence_search"]["public_bucket"] != "Likely Needs Work"
    assert not skills["math_number_theory"]["focused_practice_eligible"]
    assert not any(item["slot_type"] == "focused_practice" for item in output["daily_queue"]["items"])


def test_single_domain_bias_absence_is_not_weakness():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "single_domain_bias"))
    skills = _skills(output)
    assert skills["graphs"]["public_bucket"] != "Likely Needs Work"
    assert skills["geometry"]["public_bucket"] != "Likely Needs Work"
    assert "exploration" in _slots(output)


def test_mixed_realistic_beginner_graph_pattern():
    output = run_scenario(next(s for s in all_scenarios() if s.name == "mixed_realistic_beginner"))
    graphs = _skills(output)["graphs"]
    assert graphs["public_bucket"] in {"Likely Needs Work", "Watchlist"}
    if graphs["repair_eligible"]:
        assert "repair" in _slots(output)
    else:
        assert graphs["repair_blocking_reasons"]


def test_calibration_outputs_have_no_banned_wording():
    text = ""
    for scenario in all_scenarios():
        output = run_scenario(scenario, debug=True)
        text += str(output).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text


def test_calibration_cli_outputs_summary_files(tmp_path):
    summary = run_calibration_scenarios(tmp_path, debug=True)
    assert (tmp_path / "calibration_summary.json").exists()
    assert (tmp_path / "calibration_summary.md").exists()
    assert len(summary["scenarios"]) >= 8
