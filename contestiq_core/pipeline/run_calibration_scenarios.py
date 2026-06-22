from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from contestiq_core.config import MODEL_THRESHOLDS
from contestiq_core.diagnosis.explanations import caveats
from contestiq_core.diagnosis.weakness import build_weakness_snapshot
from contestiq_core.evaluation.scenarios import CalibrationScenario, all_scenarios
from contestiq_core.evidence.skill_evidence import build_skill_evidence
from contestiq_core.pipeline.analyze_handle import build_user_weakness_map, overlay_watchlist_debug
from contestiq_core.recommendations.queue import build_daily_queue
from contestiq_core.storage.json_store import write_json


def _skill_map(skill_scores) -> dict[str, Any]:
    return {score.skill_id: score for score in skill_scores}


def _evaluate_expectations(scenario: CalibrationScenario, output: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    skills = {score["skill_id"]: score for score in output["skill_scores"]}
    queue = output["daily_queue"]
    likely_ids = {row["skill_id"] for row in output["weakness_map_user"]["likely_needs_work"]}
    slots = {item["slot_type"] for item in queue["items"]}

    for skill_id, expected_bucket in scenario.expected.key_skills.items():
        actual = skills[skill_id]["public_bucket"]
        if actual != expected_bucket:
            failures.append(f"{skill_id} expected bucket {expected_bucket}, got {actual}")
    for skill_id in scenario.expected.forbidden_likely:
        if skill_id in likely_ids or skills[skill_id]["public_bucket"] == "Likely Needs Work":
            failures.append(f"{skill_id} should not be Likely Needs Work")
    for skill_id, expected in scenario.expected.repair_eligible.items():
        if expected is None:
            continue
        actual = skills[skill_id]["repair_eligible"]
        if actual != expected:
            failures.append(f"{skill_id} repair_eligible expected {expected}, got {actual}")
    if scenario.expected.queue_modes and queue["queue_mode"] not in scenario.expected.queue_modes:
        failures.append(f"queue_mode expected one of {sorted(scenario.expected.queue_modes)}, got {queue['queue_mode']}")
    for slot in scenario.expected.required_slots:
        if slot not in slots:
            failures.append(f"required slot {slot} missing from queue")
    return not failures, failures


def run_scenario(scenario: CalibrationScenario, debug: bool = False) -> dict[str, Any]:
    evidence = build_skill_evidence(scenario.attempts, overall_rating=scenario.overall_rating)
    weakness_map, skill_scores = build_weakness_snapshot(evidence)
    queue = build_daily_queue(scenario.problems, scenario.attempts, skill_scores, overall_rating=scenario.overall_rating)
    solved = sum(1 for attempt in scenario.attempts if attempt.has_ac)
    output = {
        "scenario": scenario.name,
        "expected_behavior": {
            "key_skills": scenario.expected.key_skills,
            "repair_eligible": scenario.expected.repair_eligible,
            "queue_modes": sorted(scenario.expected.queue_modes),
            "required_slots": sorted(scenario.expected.required_slots),
            "forbidden_likely": sorted(scenario.expected.forbidden_likely),
            "notes": scenario.expected.notes,
        },
        "profile_summary": {
            "handle": scenario.name,
            "overall_rating_prior": scenario.overall_rating,
            "normalized_submissions": sum(attempt.attempt_count for attempt in scenario.attempts),
            "user_problem_attempts": len(scenario.attempts),
            "solved_problem_attempts": solved,
        },
        "weakness_map": weakness_map.model_dump(),
        "weakness_map_user": build_user_weakness_map(skill_scores),
        "skill_scores": [score.model_dump() for score in skill_scores],
        "daily_queue": queue.model_dump(),
        "explanations": {
            "safe_wording_policy": "Weakness means current friction evidence, not a trait statement.",
            "caveats": caveats(),
        },
        "thresholds": MODEL_THRESHOLDS.model_dump(),
        "manual_notes": "",
    }
    passed, failures = _evaluate_expectations(scenario, output)
    output["calibration_result"] = {"passed": passed, "failures": failures}
    if debug:
        output["debug"] = {
            "skill_diagnostics": [
                {
                    "skill_id": score.skill_id,
                    "public_bucket": score.public_bucket,
                    "severity_score": score.severity_score,
                    "confidence_score": score.confidence_score,
                    "repair_eligible": score.repair_eligible,
                    "repair_blocking_reasons": score.repair_blocking_reasons,
                    "priority_score": score.priority_score,
                }
                for score in skill_scores
            ],
            "public_overlay_watchlist_items": overlay_watchlist_debug(skill_scores),
        }
    return output


def _key_skill_lines(output: dict[str, Any]) -> list[str]:
    skills = {score["skill_id"]: score for score in output["skill_scores"]}
    key_ids = set(output["expected_behavior"]["key_skills"]) | set(output["expected_behavior"]["repair_eligible"]) | set(output["expected_behavior"]["forbidden_likely"])
    if not key_ids:
        key_ids = {"dynamic_programming", "graphs", "geometry", "math_number_theory", "sequence_search"}
    lines = []
    for skill_id in sorted(key_ids):
        score = skills[skill_id]
        lines.append(
            f"- `{skill_id}`: bucket `{score['public_bucket']}`, severity {score['severity_score']}, "
            f"confidence {score['confidence_score']}, repair {score['repair_eligible']}, blockers {score['repair_blocking_reasons']}"
        )
    return lines


def _markdown(outputs: list[dict[str, Any]]) -> str:
    lines = [
        "# ContestIQ Calibration Scenario Suite",
        "",
        "Synthetic model-validation report. This is for calibration review, not public claims.",
        "",
        "| Scenario | Expected Behavior | Actual Queue Mode | Pass |",
        "|---|---|---|---|",
    ]
    for output in outputs:
        expected = output["expected_behavior"]["notes"]
        lines.append(f"| {output['scenario']} | {expected} | {output['daily_queue']['queue_mode']} | {output['calibration_result']['passed']} |")
    lines.append("")
    for output in outputs:
        lines.extend(
            [
                f"## {output['scenario']}",
                "",
                f"Expected: {output['expected_behavior']['notes']}",
                f"Actual queue mode: `{output['daily_queue']['queue_mode']}`",
                f"Pass: `{output['calibration_result']['passed']}`",
                "",
                "Failures:",
                *([f"- {failure}" for failure in output["calibration_result"]["failures"]] or ["- none"]),
                "",
                "Key severity/confidence values:",
                *_key_skill_lines(output),
                "",
                "Queue slots:",
                *[
                    f"- `{item['slot_type']}` {item['problem_key']} -> {item['anchor_skill']} score {item['final_score']}"
                    for item in output["daily_queue"]["items"]
                ],
                "",
                "Manual notes:",
                "- ",
                "",
            ]
        )
    return "\n".join(lines)


def run_calibration_scenarios(out_dir: str | Path, debug: bool = False) -> dict[str, Any]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs = [run_scenario(scenario, debug=debug) for scenario in all_scenarios()]
    for output in outputs:
        write_json(target / f"{output['scenario']}_output.json", output)
        if debug:
            write_json(target / f"{output['scenario']}_debug.json", output)
    summary = {
        "scenarios": [
            {
                "scenario": output["scenario"],
                "passed": output["calibration_result"]["passed"],
                "failures": output["calibration_result"]["failures"],
                "queue_mode": output["daily_queue"]["queue_mode"],
                "repair_items_count": sum(1 for item in output["daily_queue"]["items"] if item["slot_type"] == "repair"),
                "focused_practice_items_count": sum(1 for item in output["daily_queue"]["items"] if item["slot_type"] == "focused_practice"),
                "likely_needs_work": [row["skill_id"] for row in output["weakness_map_user"]["likely_needs_work"]],
                "watchlist": [row["skill_id"] for row in output["weakness_map_user"]["watchlist"]],
                "limited_evidence": [row["skill_id"] for row in output["weakness_map_user"]["limited_evidence"]],
            }
            for output in outputs
        ],
        "thresholds": MODEL_THRESHOLDS.model_dump(),
    }
    write_json(target / "calibration_summary.json", summary)
    (target / "calibration_summary.md").write_text(_markdown(outputs), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    summary = run_calibration_scenarios(args.out, debug=args.debug)
    passed = sum(1 for row in summary["scenarios"] if row["passed"])
    print(f"Ran {len(summary['scenarios'])} calibration scenarios into {Path(args.out).resolve()} ({passed} passed)")


if __name__ == "__main__":
    main()
