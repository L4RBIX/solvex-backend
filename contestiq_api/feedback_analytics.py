from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contestiq_api.storage import FEEDBACK_DIR

FEEDBACK_VALUES = ["good_fit", "too_easy", "too_hard", "not_relevant", "already_seen", "confusing", "skipped"]
OUTCOME_VALUES = ["solved", "attempted_but_failed", "skipped", "opened_only", "unknown"]
SLOT_TYPES = ["repair", "focused_practice", "maintenance", "stretch", "exploration"]
MIN_REVIEW_SAMPLE = 5


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_feedback_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        _read_jsonl(FEEDBACK_DIR / "problem_feedback.jsonl"),
        _read_jsonl(FEEDBACK_DIR / "problem_outcomes.jsonl"),
        _read_jsonl(FEEDBACK_DIR / "queue_feedback.jsonl"),
    )


def _rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _feedback_summary(rows: list[dict[str, Any]], group_key: str, include_all_slots: bool = False) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = row.get(group_key)
        if key:
            groups[str(key)].append(row)
    keys = SLOT_TYPES if include_all_slots else sorted(groups)
    summary = {}
    for key in keys:
        group = groups.get(key, [])
        total = len(group)
        counts = Counter(row.get("feedback") for row in group)
        entry = {"count": total}
        for value in FEEDBACK_VALUES:
            entry[f"{value}_count"] = counts.get(value, 0)
        for value in ["good_fit", "too_easy", "too_hard", "not_relevant", "skipped"]:
            entry[f"{value}_rate"] = _rate(counts.get(value, 0), total)
        if total and total < MIN_REVIEW_SAMPLE:
            entry["low_sample_size"] = True
        summary[key] = entry
    return summary


def _outcome_summary(rows: list[dict[str, Any]], group_key: str, include_all_slots: bool = False) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = row.get(group_key)
        if key:
            groups[str(key)].append(row)
    keys = SLOT_TYPES if include_all_slots else sorted(groups)
    summary = {}
    for key in keys:
        group = groups.get(key, [])
        total = len(group)
        counts = Counter(row.get("outcome") for row in group)
        entry = {"count": total}
        for value in OUTCOME_VALUES:
            entry[f"{value}_count"] = counts.get(value, 0)
        entry["solved_rate"] = _rate(counts.get("solved", 0), total)
        entry["attempted_failed_rate"] = _rate(counts.get("attempted_but_failed", 0), total)
        entry["skipped_rate"] = _rate(counts.get("skipped", 0), total)
        entry["opened_only_rate"] = _rate(counts.get("opened_only", 0), total)
        if total and total < MIN_REVIEW_SAMPLE:
            entry["low_sample_size"] = True
        summary[key] = entry
    return summary


def _global(problem_feedback: list[dict[str, Any]], outcomes: list[dict[str, Any]], queue_feedback: list[dict[str, Any]]) -> dict[str, Any]:
    all_rows = problem_feedback + outcomes + queue_feedback
    return {
        "total_problem_feedback": len(problem_feedback),
        "total_problem_outcomes": len(outcomes),
        "total_queue_feedback": len(queue_feedback),
        "handles_count": len({row.get("handle") for row in all_rows if row.get("handle")}),
        "analysis_count": len({row.get("analysis_id") for row in all_rows if row.get("analysis_id")}),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _flag(name: str, group: str, count: int, rate: float, message: str, low_sample_size: bool = False) -> dict[str, Any]:
    return {
        "flag": name,
        "group": group,
        "count": count,
        "rate": rate,
        "low_sample_size": low_sample_size,
        "message": message,
    }


def _manual_review_flags(by_slot: dict[str, dict[str, Any]], by_skill: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for slot, entry in by_slot.items():
        count = entry["count"]
        if 0 < count < MIN_REVIEW_SAMPLE:
            flags.append(_flag("low_sample_size", slot, count, 0.0, "Feedback volume is too small for strong interpretation.", True))
            continue
        if count < MIN_REVIEW_SAMPLE:
            continue
        checks = [
            ("focused_practice", "too_hard_rate", "focused_practice_too_hard_rate_high", 0.5),
            ("stretch", "too_hard_rate", "stretch_too_hard_rate_high", 0.5),
            ("exploration", "not_relevant_rate", "exploration_not_relevant_rate_high", 0.5),
            ("maintenance", "too_easy_rate", "maintenance_too_easy_rate_high", 0.5),
        ]
        for expected_slot, rate_key, flag_name, threshold in checks:
            if slot == expected_slot and entry.get(rate_key, 0.0) >= threshold:
                flags.append(_flag(flag_name, slot, count, entry[rate_key], "Internal review suggested; do not treat this as automatic model failure."))
    for skill, entry in by_skill.items():
        count = entry["count"]
        if 0 < count < MIN_REVIEW_SAMPLE:
            flags.append(_flag("low_sample_size", skill, count, 0.0, "Skill feedback volume is too small for strong interpretation.", True))
        elif count >= MIN_REVIEW_SAMPLE and entry.get("not_relevant_rate", 0.0) >= 0.5:
            flags.append(_flag("skill_not_relevant_rate_high", skill, count, entry["not_relevant_rate"], "Internal review suggested for skill-to-problem matching."))
    if not flags:
        total = sum(entry["count"] for entry in by_slot.values())
        if total < MIN_REVIEW_SAMPLE:
            flags.append(_flag("insufficient_feedback_volume", "global", total, 0.0, "Not enough feedback has been collected for strong interpretation.", True))
    return flags


def feedback_summary() -> dict[str, Any]:
    problem_feedback, outcomes, queue_feedback = load_feedback_rows()
    global_summary = _global(problem_feedback, outcomes, queue_feedback)
    if not problem_feedback and not outcomes and not queue_feedback:
        return {
            "status": "no_feedback",
            "global": global_summary,
            "by_slot_type": {slot: _feedback_summary([], "slot_type", True)[slot] for slot in SLOT_TYPES},
            "by_anchor_skill": {},
            "outcomes_by_slot_type": {slot: _outcome_summary([], "slot_type", True)[slot] for slot in SLOT_TYPES},
            "outcomes_by_anchor_skill": {},
            "manual_review_flags": [
                _flag("insufficient_feedback_volume", "global", 0, 0.0, "No feedback has been collected yet.", True)
            ],
            "safe_interpretation": "This summary describes collected user feedback. It is not an automatic model update and does not prove recommendation effectiveness.",
        }
    by_slot = _feedback_summary(problem_feedback, "slot_type", include_all_slots=True)
    by_skill = _feedback_summary(problem_feedback, "anchor_skill", include_all_slots=False)
    outcomes_by_slot = _outcome_summary(outcomes, "slot_type", include_all_slots=True)
    outcomes_by_skill = _outcome_summary(outcomes, "anchor_skill", include_all_slots=False)
    return {
        "status": "available",
        "global": global_summary,
        "by_slot_type": by_slot,
        "by_anchor_skill": by_skill,
        "outcomes_by_slot_type": outcomes_by_slot,
        "outcomes_by_anchor_skill": outcomes_by_skill,
        "manual_review_flags": _manual_review_flags(by_slot, by_skill),
        "safe_interpretation": "This summary describes collected user feedback. It is not an automatic model update and does not prove recommendation effectiveness.",
    }


def feedback_summary_markdown() -> str:
    summary = feedback_summary()
    lines = [
        "# ContestIQ Feedback Analytics",
        "",
        summary["safe_interpretation"],
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Global",
    ]
    for key, value in summary["global"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## By Slot Type", ""])
    for slot, entry in summary["by_slot_type"].items():
        lines.append(f"- `{slot}`: count {entry['count']}, good_fit_rate {entry.get('good_fit_rate', 0)}, too_hard_rate {entry.get('too_hard_rate', 0)}")
    lines.extend(["", "## Manual Review Flags", ""])
    lines.extend([f"- `{flag['flag']}` on `{flag['group']}`: {flag['message']}" for flag in summary["manual_review_flags"]] or ["- none"])
    return "\n".join(lines)
