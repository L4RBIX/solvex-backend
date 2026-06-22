from __future__ import annotations

import os
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from contestiq_api import MODEL_VERSION
from contestiq_api.errors import APIError
from contestiq_api.feedback import ProblemOutcome, QueueItemFeedback, QueueSessionFeedback, feedback_record
from contestiq_api.storage import append_jsonl, list_snapshots, load_analysis, save_analysis, save_snapshot
from contestiq_api.workspace import upsert_workspace_analysis
from contestiq_core.codeforces.client import CodeforcesAPIError
from contestiq_core.pipeline.analyze_handle import analyze_handle

HANDLE_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")

INTERNAL_TOP_LEVEL_FIELDS = {
    "normalized_history",
    "skill_evidence",
    "weakness_map",
    "skill_scores",
    "debug",
}

PUBLIC_QUEUE_ITEM_FIELDS = {
    "problem_key",
    "problem_name",
    "rating",
    "tags",
    "target_skill",
    "anchor_skill",
    "slot_type",
    "final_score",
    "explanation",
    "why_this_problem",
    "why_this_skill",
    "why_this_slot",
    "difficulty_reason",
    "safety_note",
    "risk_flags",
}

PUBLIC_DAILY_QUEUE_FIELDS = {
    "queue_mode",
    "queue_mode_reason",
    "evidence_quality_level",
    "items",
    "caveats",
}

PUBLIC_RISK_FLAGS = {"limited_evidence", "higher_challenge", "missing_rating"}


def validate_handle(handle: str) -> str:
    cleaned = handle.strip()
    if not HANDLE_RE.match(cleaned):
        raise APIError("INVALID_HANDLE", "Handle must be 3-24 characters using letters, numbers, underscore, hyphen, or dot.", 422)
    return cleaned


def _analysis_id(handle: str) -> str:
    return str(uuid.uuid4())


def _offline_sample_enabled() -> bool:
    return os.getenv("CONTESTIQ_API_OFFLINE_SAMPLE", "").lower() in {"1", "true", "yes"}


def _display_skill(skill_id: str) -> str:
    return skill_id.replace("_", " ").title()


def _risk_flags(item: dict[str, Any], include_debug: bool = False) -> list[str]:
    flags: list[str] = []
    if item.get("slot_type") == "exploration":
        flags.append("limited_evidence")
    if item.get("slot_type") == "stretch":
        flags.append("higher_challenge")
    if item.get("rating") is None:
        flags.append("missing_rating")
    if item.get("anchor_visibility_level") not in {None, "user_visible"}:
        flags.append("debug_anchor")
    if not include_debug:
        flags = [flag for flag in flags if flag in PUBLIC_RISK_FLAGS]
    return flags


def _enrich_queue_item(item: dict[str, Any], include_debug: bool = False) -> dict[str, Any]:
    slot = item.get("slot_type", "practice")
    skill = _display_skill(item.get("anchor_skill") or item.get("target_skill") or "skill")
    rating = item.get("rating")
    problem_name = item.get("problem_name", "this problem")
    if slot == "focused_practice":
        why_slot = "This is targeted practice for moderate evidence, not a firm weakness label."
    elif slot == "repair":
        why_slot = "This is a repair slot because the skill passed stricter public friction thresholds."
    elif slot == "exploration":
        why_slot = "This is exploration because evidence is limited or coverage is useful to broaden."
    elif slot == "stretch":
        why_slot = "This is a stretch slot, chosen slightly above the estimated current range."
    else:
        why_slot = "This is maintenance to keep an observed stable area active."
    difficulty = (
        f"Rated {rating}, selected near the slot's target range."
        if rating is not None
        else "No public rating is available, so difficulty confidence is lower."
    )
    return {
        **item,
        "why_this_problem": f"{problem_name} matched the queue slot and available Codeforces tag evidence.",
        "why_this_skill": f"{skill} is the single anchor skill for a clear training explanation.",
        "why_this_slot": why_slot,
        "difficulty_reason": difficulty,
        "safety_note": "Based only on Codeforces public outcome history; this is not a claim about mastery or solving process.",
        "risk_flags": _risk_flags(item, include_debug=include_debug),
    }


def public_analysis(analysis: dict[str, Any], include_debug: bool = False) -> dict[str, Any]:
    source = deepcopy(analysis)
    if not include_debug:
        for field in INTERNAL_TOP_LEVEL_FIELDS:
            source.pop(field, None)
    queue = source.get("daily_queue")
    if isinstance(queue, dict):
        enriched = [_enrich_queue_item(item, include_debug=include_debug) for item in queue.get("items", [])]
        if include_debug:
            queue["items"] = enriched
        else:
            public_queue = {key: queue.get(key) for key in PUBLIC_DAILY_QUEUE_FIELDS if key in queue}
            public_queue["items"] = [
                {key: item.get(key) for key in PUBLIC_QUEUE_ITEM_FIELDS if key in item}
                for item in enriched
            ]
            source["daily_queue"] = public_queue
    return source


def _api_envelope(handle: str, analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "completed",
        "analysis_id": _analysis_id(handle),
        "handle": handle,
        "model_version": MODEL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **analysis,
    }


def analyze_codeforces_handle(handle: str, debug: bool = False, force_refresh: bool = False) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    cached = load_analysis(cleaned)
    if cached is not None and cached.get("model_version") == MODEL_VERSION and not force_refresh:
        upsert_workspace_analysis(cleaned, cached)
        return public_analysis(cached, include_debug=debug)
    try:
        raw = analyze_handle(cleaned, offline_sample=_offline_sample_enabled(), debug=debug)
    except CodeforcesAPIError as exc:
        message = str(exc)
        if "429" in message or "rate limited" in message.lower():
            if cached is not None:
                result = public_analysis(cached, include_debug=debug)
                result["from_cache"] = True
                result["cache_warning"] = (
                    "Codeforces is rate-limiting requests. "
                    "Showing the latest cached analysis instead."
                )
                return result
            raise APIError(
                "CODEFORCES_RATE_LIMITED",
                "Codeforces is rate-limiting requests. Please wait 1–2 minutes and try again.",
                429,
            ) from exc
        if "502" in message or "bad gateway" in message.lower() or "unavailable" in message.lower():
            if cached is not None:
                result = public_analysis(cached, include_debug=debug)
                result["from_cache"] = True
                result["cache_warning"] = (
                    "Codeforces API is temporarily unavailable. "
                    "Showing the latest cached analysis instead."
                )
                return result
            raise APIError(
                "CODEFORCES_UNAVAILABLE",
                "Codeforces API is temporarily unavailable. Try again later.",
                502,
            ) from exc
        if "not found" in message.lower() or ("handle" in message.lower() and "not found" in message.lower()):
            raise APIError("CODEFORCES_HANDLE_NOT_FOUND", f"Codeforces handle was not found: {cleaned}", 404) from exc
        raise APIError("CODEFORCES_API_ERROR", message, 502) from exc
    except APIError:
        raise
    except Exception as exc:
        raise APIError("ANALYSIS_FAILED", f"Analysis failed for handle {cleaned}.", 500) from exc

    enveloped = _api_envelope(cleaned, raw)
    save_analysis(cleaned, enveloped)
    save_snapshot(cleaned, enveloped)
    upsert_workspace_analysis(cleaned, enveloped)
    return public_analysis(enveloped, include_debug=debug)


def get_saved_analysis(handle: str, include_debug: bool = False) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    cached = load_analysis(cleaned)
    if cached is None:
        raise APIError("ANALYSIS_NOT_FOUND", f"No saved analysis found for handle {cleaned}.", 404)
    if include_debug and "debug" not in cached:
        raise APIError("ANALYSIS_NOT_FOUND", f"No debug analysis is available for handle {cleaned}.", 404)
    return public_analysis(cached, include_debug=include_debug)


def weakness_map_only(handle: str) -> dict[str, Any]:
    analysis = get_saved_analysis(handle, include_debug=False)
    return {
        "handle": analysis["handle"],
        "weakness_map_user": analysis.get("weakness_map_user", {}),
        "warnings": analysis.get("warnings", []),
    }


def daily_queue_only(handle: str) -> dict[str, Any]:
    analysis = get_saved_analysis(handle, include_debug=False)
    return {
        "handle": analysis["handle"],
        "daily_queue": analysis.get("daily_queue", {}),
        "warnings": analysis.get("warnings", []),
    }


def save_problem_feedback(payload: QueueItemFeedback) -> dict[str, str]:
    validate_handle(payload.handle)
    record = feedback_record(payload)
    append_jsonl("problem_feedback.jsonl", record)
    return {"status": "saved", "feedback_id": record["feedback_id"]}


def save_problem_outcome(payload: ProblemOutcome) -> dict[str, str]:
    validate_handle(payload.handle)
    record = feedback_record(payload)
    append_jsonl("problem_outcomes.jsonl", record)
    return {"status": "saved", "feedback_id": record["feedback_id"]}


def save_queue_feedback(payload: QueueSessionFeedback) -> dict[str, str]:
    validate_handle(payload.handle)
    record = feedback_record(payload)
    append_jsonl("queue_feedback.jsonl", record)
    return {"status": "saved", "feedback_id": record["feedback_id"]}


def _bucket_ids(snapshot: dict[str, Any], bucket: str) -> set[str]:
    return {
        row.get("skill_id")
        for row in snapshot.get("weakness_map_user", {}).get(bucket, [])
        if row.get("skill_id")
    }


def progress_for_handle(handle: str) -> dict[str, Any]:
    cleaned = validate_handle(handle)
    snapshots = list_snapshots(cleaned)
    if len(snapshots) < 2:
        latest = snapshots[-1] if snapshots else None
        return {
            "handle": cleaned,
            "status": "not_enough_history",
            "latest_analysis_id": latest.get("analysis_id") if latest else None,
            "previous_analysis_id": None,
            "summary": {
                "queue_mode_changed": False,
                "watchlist_added": [],
                "watchlist_removed": [],
                "likely_needs_work_added": [],
                "likely_needs_work_removed": [],
                "limited_evidence_added": [],
                "limited_evidence_removed": [],
            },
            "safe_interpretation": "ContestIQ needs at least two saved analyses to compare public friction signals. This is based only on Codeforces public history.",
        }
    previous, latest = snapshots[-2], snapshots[-1]
    summary = {
        "queue_mode_changed": previous.get("daily_queue", {}).get("queue_mode") != latest.get("daily_queue", {}).get("queue_mode"),
        "watchlist_added": sorted(_bucket_ids(latest, "watchlist") - _bucket_ids(previous, "watchlist")),
        "watchlist_removed": sorted(_bucket_ids(previous, "watchlist") - _bucket_ids(latest, "watchlist")),
        "likely_needs_work_added": sorted(_bucket_ids(latest, "likely_needs_work") - _bucket_ids(previous, "likely_needs_work")),
        "likely_needs_work_removed": sorted(_bucket_ids(previous, "likely_needs_work") - _bucket_ids(latest, "likely_needs_work")),
        "limited_evidence_added": sorted(_bucket_ids(latest, "limited_evidence") - _bucket_ids(previous, "limited_evidence")),
        "limited_evidence_removed": sorted(_bucket_ids(previous, "limited_evidence") - _bucket_ids(latest, "limited_evidence")),
    }
    return {
        "handle": cleaned,
        "status": "available",
        "latest_analysis_id": latest.get("analysis_id"),
        "previous_analysis_id": previous.get("analysis_id"),
        "summary": summary,
        "safe_interpretation": "The latest analysis shows changes in public friction signals. This is based only on Codeforces public history.",
    }
