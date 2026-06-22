from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from contestiq_core.pipeline.analyze_handle import analyze_handle
from contestiq_core.storage.json_store import write_json


def _safe_filename(handle: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", handle).strip("_") or "handle"


def _read_handles(path: str | Path) -> list[str]:
    rows = Path(path).read_text(encoding="utf-8-sig").splitlines()
    return [row.strip().lstrip("\ufeff") for row in rows if row.strip() and not row.strip().startswith("#")]


def _summary_for_output(handle: str, output: dict[str, Any], error: str | None = None) -> dict[str, Any]:
    profile = output.get("profile_summary", {})
    weakness = output.get("weakness_map_user", {})
    queue = output.get("daily_queue", {})
    items = queue.get("items", [])
    slots = [item.get("slot_type") for item in items]
    return {
        "handle": handle,
        "overall_rating_prior": profile.get("overall_rating_prior"),
        "normalized_submissions": profile.get("normalized_submissions", 0),
        "user_problem_attempts": profile.get("user_problem_attempts", 0),
        "solved_problem_attempts": profile.get("solved_problem_attempts", 0),
        "number_of_likely_needs_work": len(weakness.get("likely_needs_work", [])),
        "number_of_watchlist": len(weakness.get("watchlist", [])),
        "number_of_limited_evidence": len(weakness.get("limited_evidence", [])),
        "queue_mode": queue.get("queue_mode") or queue.get("mode"),
        "queue_slots_present": sorted({slot for slot in slots if slot}),
        "repair_items_count": slots.count("repair"),
        "focused_practice_items_count": slots.count("focused_practice"),
        "exploration_items_count": slots.count("exploration"),
        "maintenance_items_count": slots.count("maintenance"),
        "stretch_items_count": slots.count("stretch"),
        "warnings": output.get("warnings", []),
        "pipeline_error": error,
    }


def _visible_map_lines(output: dict[str, Any]) -> list[str]:
    weakness = output.get("weakness_map_user", {})
    lines: list[str] = []
    for bucket in ["likely_needs_work", "watchlist", "limited_evidence"]:
        rows = weakness.get(bucket, [])
        if not rows:
            lines.append(f"- `{bucket}`: none")
            continue
        labels = ", ".join(f"{row['display_name']} ({row['confidence_band']})" for row in rows)
        lines.append(f"- `{bucket}`: {labels}")
    return lines


def _queue_lines(output: dict[str, Any]) -> list[str]:
    items = output.get("daily_queue", {}).get("items", [])
    if not items:
        return ["- no queue items generated"]
    return [
        f"- `{item['slot_type']}`: {item['problem_key']} {item['problem_name']} -> {item['anchor_skill']} (score {item['final_score']})"
        for item in items
    ]


def _diagnostic_aggregates(outputs: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    repair_reasons: dict[str, int] = {}
    user_domain_watchlist = 0
    user_overlay_watchlist = 0
    queue_domain_anchors = 0
    queue_overlay_anchors = 0
    sufficient_low_evidence: list[str] = []
    suspected: list[str] = []

    for row in rows:
        output = outputs.get(row["handle"], {})
        for skill in output.get("skill_scores", []):
            if not skill.get("repair_eligible", False):
                for reason in skill.get("repair_blocking_reasons", []):
                    repair_reasons[reason] = repair_reasons.get(reason, 0) + 1
            if skill.get("user_visible_bucket") == "Watchlist":
                if skill.get("whether_anchor_is_domain_or_overlay") == "technique":
                    user_overlay_watchlist += 1
                kind = "technique" if skill.get("skill_id") in {
                    "binary_search", "two_pointers", "prefix_sums", "bitmasks",
                    "divide_and_conquer", "meet_in_the_middle", "hashing", "matrices",
                } else "domain"
                if kind == "technique":
                    user_overlay_watchlist += 1
                else:
                    user_domain_watchlist += 1
        queue = output.get("daily_queue", {})
        if queue.get("has_sufficient_history") and queue.get("queue_mode") == "low_evidence_exploration":
            sufficient_low_evidence.append(row["handle"])
        for item in queue.get("items", []):
            if item.get("whether_anchor_is_domain_or_overlay") == "technique":
                queue_overlay_anchors += 1
            else:
                queue_domain_anchors += 1

    if sufficient_low_evidence:
        suspected.append("Some sufficient-history handles still routed to low_evidence_exploration.")
    if user_overlay_watchlist > user_domain_watchlist:
        suspected.append("User-facing watchlist is dominated by technique overlays.")
    if queue_overlay_anchors > queue_domain_anchors:
        suspected.append("Queue anchors are dominated by technique overlays.")

    return {
        "top_repair_blocking_reasons": sorted(repair_reasons.items(), key=lambda item: item[1], reverse=True)[:5],
        "user_visible_domain_watchlist_count": user_domain_watchlist,
        "user_visible_overlay_watchlist_count": user_overlay_watchlist,
        "queue_domain_anchor_count": queue_domain_anchors,
        "queue_overlay_anchor_count": queue_overlay_anchors,
        "sufficient_history_low_evidence_handles": sufficient_low_evidence,
        "suspected_model_issues": suspected,
    }


def _markdown_report(rows: list[dict[str, Any]], outputs: dict[str, dict[str, Any]]) -> str:
    diagnostics = _diagnostic_aggregates(outputs, rows)
    lines = [
        "# ContestIQ Real Handle Evaluation",
        "",
        "Local validation report for manual review. This report is not a public claim about mastery, verification, identity proof, or expected improvement.",
        "",
        "## Handles",
        "",
        "| Handle | Attempts | Solved | Likely | Watchlist | Limited | Queue Mode | Focused | Error |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['handle']} | {row['user_problem_attempts']} | {row['solved_problem_attempts']} | "
            f"{row['number_of_likely_needs_work']} | {row['number_of_watchlist']} | {row['number_of_limited_evidence']} | "
            f"{row['queue_mode'] or ''} | {row.get('focused_practice_items_count', 0)} | {row['pipeline_error'] or ''} |"
        )

    lines.extend(
        [
            "",
            "## Diagnostic Summary",
            "",
            "Why no repair items were selected:",
        ]
    )
    if diagnostics["top_repair_blocking_reasons"]:
        lines.extend([f"- {reason}: {count}" for reason, count in diagnostics["top_repair_blocking_reasons"]])
    else:
        lines.append("- No repair blocking reasons were available.")
    lines.extend(
        [
            "",
            "Top 5 repair blocking reasons across handles:",
            *([f"- {reason}: {count}" for reason, count in diagnostics["top_repair_blocking_reasons"]] or ["- none"]),
            "",
            f"User-facing domain watchlist items: {diagnostics['user_visible_domain_watchlist_count']}",
            f"User-facing overlay watchlist items: {diagnostics['user_visible_overlay_watchlist_count']}",
            f"Queue items anchored to domain skills: {diagnostics['queue_domain_anchor_count']}",
            f"Queue items anchored to overlay skills: {diagnostics['queue_overlay_anchor_count']}",
            "",
            "Handles with sufficient history but low_evidence_exploration mode:",
            *([f"- {handle}" for handle in diagnostics["sufficient_history_low_evidence_handles"]] or ["- none"]),
            "",
            "Suspected model issues:",
            *([f"- {issue}" for issue in diagnostics["suspected_model_issues"]] or ["- none flagged by aggregate diagnostics"]),
            "",
        ]
    )

    lines.extend(["", "## Per Handle Review", ""])
    for row in rows:
        handle = row["handle"]
        output = outputs.get(handle, {})
        lines.extend(
            [
                f"### {handle}",
                "",
                f"- Data quality: {row['normalized_submissions']} normalized submissions, {row['user_problem_attempts']} problem attempts, {row['solved_problem_attempts']} solved attempts.",
                f"- Public bucket counts: likely {row['number_of_likely_needs_work']}, watchlist {row['number_of_watchlist']}, limited {row['number_of_limited_evidence']}.",
                f"- Queue mode: `{row['queue_mode']}`.",
                "",
                "Visible weakness map:",
                *_visible_map_lines(output),
                "",
                "Daily queue:",
                *_queue_lines(output),
                "",
                "Warnings:",
            ]
        )
        warnings = row.get("warnings") or []
        lines.extend([f"- {warning}" for warning in warnings] or ["- none"])
        if row.get("pipeline_error"):
            lines.append(f"- pipeline error: {row['pipeline_error']}")
        lines.append("")

    lines.extend(
        [
            "## Manual Review Checklist",
            "",
            "- Are the public labels reasonable?",
            "- Is confidence too high?",
            "- Are low-evidence skills hidden or marked limited?",
            "- Are recommendations solved/attempted before?",
            "- Does queue_mode match evidence quality?",
            "- Are explanations safe and non-stigmatizing?",
            "",
        ]
    )
    return "\n".join(lines)


def batch_evaluate(
    handles_path: str | Path,
    out_dir: str | Path,
    debug: bool = False,
    offline_sample: bool = False,
    max_submissions: int | None = 5000,
) -> dict[str, Any]:
    handles = _read_handles(handles_path)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    outputs: dict[str, dict[str, Any]] = {}

    for handle in handles:
        safe = _safe_filename(handle)
        try:
            output = analyze_handle(handle, offline_sample=offline_sample, debug=debug, max_submissions=max_submissions)
            outputs[handle] = output
            write_json(target / f"{safe}_output.json", output)
            debug_output = output if debug else analyze_handle(handle, offline_sample=offline_sample, debug=True, max_submissions=max_submissions)
            write_json(target / f"{safe}_debug.json", debug_output)
            rows.append(_summary_for_output(handle, output))
        except Exception as exc:
            error_output = {"profile_summary": {"handle": handle}, "warnings": [], "pipeline_error": str(exc)}
            outputs[handle] = error_output
            write_json(target / f"{safe}_output.json", error_output)
            write_json(target / f"{safe}_debug.json", error_output)
            rows.append(_summary_for_output(handle, error_output, error=str(exc)))

    summary = {"handles": rows}
    summary["diagnostics"] = _diagnostic_aggregates(outputs, rows)
    write_json(target / "eval_summary.json", summary)
    (target / "eval_summary.md").write_text(_markdown_report(rows, outputs), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handles", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--offline-sample", action="store_true")
    parser.add_argument("--max-submissions", type=int, default=5000)
    args = parser.parse_args()
    summary = batch_evaluate(
        args.handles,
        args.out_dir,
        debug=args.debug,
        offline_sample=args.offline_sample,
        max_submissions=args.max_submissions,
    )
    print(f"Evaluated {len(summary['handles'])} handles into {Path(args.out_dir).resolve()}")


if __name__ == "__main__":
    main()
