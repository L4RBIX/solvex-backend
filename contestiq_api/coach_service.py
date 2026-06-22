"""Personal AI Coach Memory — profile aggregation and solving-event persistence."""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ─── Error type detection (rule-based, deterministic) ─────────────────────────

_COMPILE_PATTERNS: list[tuple[list[str], str]] = [
    (
        ["was not declared", "undeclared identifier", "not declared in this scope", "'", "' was not declared"],
        "undeclared_variable",
    ),
    (
        ["expected ';'", "expected ','", "expected '{'", "expected ')'", "expected 'identifier'", "stray '"],
        "syntax",
    ),
    (
        ["integer overflow", "signed integer overflow", "overflow in implicit constant conversion"],
        "overflow",
    ),
    (
        ["cannot convert", "invalid conversion", "no matching function", "invalid operands"],
        "type_error",
    ),
]

_RUNTIME_PATTERNS: list[tuple[list[str], str]] = [
    (["segmentation fault", "sigsegv", "signal 11"], "index_error"),
    (["stack overflow", "stack smashing detected"], "index_error"),
    (["floating point exception", "sigfpe", "divide by zero"], "overflow"),
    (["double free or corruption", "heap use after free"], "index_error"),
]


def detect_error_type(
    compile_output: str,
    stderr: str,
    status: str,
) -> str | None:
    """Classify the dominant error type from raw outputs. Returns None if benign."""
    status_norm = status.lower().replace(" ", "_")

    if "time_limit" in status_norm or "tle" in status_norm:
        return "complexity"

    combined_compile = (compile_output or "").lower()
    for patterns, etype in _COMPILE_PATTERNS:
        if any(p in combined_compile for p in patterns):
            return etype

    combined_runtime = (stderr or "").lower()
    for patterns, etype in _RUNTIME_PATTERNS:
        if any(p in combined_runtime for p in patterns):
            return etype

    if "wrong_answer" in status_norm or "wrong answer" in status_norm:
        return "edge_case"
    if "runtime_error" in status_norm or "runtime error" in status_norm:
        return "index_error"
    if "compilation_error" in status_norm or "compile" in status_norm:
        return "syntax"

    return None


# ─── Language detection ────────────────────────────────────────────────────────

def detect_preferred_language(messages: list[str]) -> str:
    """Check Cyrillic character ratio across message text to infer preferred language."""
    text = " ".join(m for m in messages if m)
    total = len(text)
    if total == 0:
        return "english"
    cyrillic = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    if cyrillic / total > 0.08:
        return "russian"
    return "english"


# ─── Help style inference ──────────────────────────────────────────────────────

def infer_help_style(events: list[dict]) -> str:
    """Map average help_level from copilot events to a style label."""
    copilot_events = [e for e in events if e.get("event_type") == "copilot_question"]
    if not copilot_events:
        return "tiny_hints"
    levels = [e.get("metadata", {}).get("help_level", 2) for e in copilot_events]
    avg = sum(levels) / len(levels)
    if avg <= 1.5:
        return "tiny_hints"
    if avg <= 2.5:
        return "conceptual"
    if avg <= 3.5:
        return "debug_guidance"
    if avg <= 4.5:
        return "detailed"
    return "solution_heavy"


# ─── Supabase REST helpers ─────────────────────────────────────────────────────

async def _sb_get(
    settings: Any,
    path: str,
    params: dict | None = None,
) -> list[dict] | None:
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    url = f"{settings.supabase_url}/rest/v1/{path}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params or {})
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("coach supabase get failed (%s): %s", path, exc)
            return None


async def _sb_post(
    settings: Any,
    path: str,
    rows: list[dict] | dict,
    prefer: str = "return=minimal",
) -> None:
    if not settings.supabase_url or not settings.supabase_service_key:
        return
    url = f"{settings.supabase_url}/rest/v1/{path}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, headers=headers, json=rows)
        except Exception as exc:
            logger.warning("coach supabase post failed (%s): %s", path, exc)


async def _sb_patch(
    settings: Any,
    path: str,
    data: dict,
    match_params: dict,
) -> None:
    if not settings.supabase_url or not settings.supabase_service_key:
        return
    url = f"{settings.supabase_url}/rest/v1/{path}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.patch(url, headers=headers, json=data, params=match_params)
        except Exception as exc:
            logger.warning("coach supabase patch failed (%s): %s", path, exc)


# ─── Profile load ──────────────────────────────────────────────────────────────

async def load_profile(
    settings: Any,
    *,
    user_id: str | None,
    anonymous_user_key: str | None,
) -> dict | None:
    """Return user_solving_profile row or None if not found / Supabase unconfigured."""
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    if not user_id and not anonymous_user_key:
        return None

    params: dict[str, str] = {"select": "*", "limit": "1"}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    elif anonymous_user_key:
        params["anonymous_user_key"] = f"eq.{anonymous_user_key}"

    rows = await _sb_get(settings, "user_solving_profiles", params)
    if rows and isinstance(rows, list) and len(rows) > 0:
        return rows[0]
    return None


# ─── Profile → prompt block ────────────────────────────────────────────────────

_STYLE_DESC: dict[str, str] = {
    "tiny_hints":     "tiny one-sentence hints (do not reveal approach or algorithm)",
    "conceptual":     "conceptual explanations without code",
    "debug_guidance": "step-by-step debug guidance",
    "detailed":       "detailed explanations and pseudocode",
    "solution_heavy": "full solutions (user tends to request them — be cautious)",
}

_ERROR_DESC: dict[str, str] = {
    "undeclared_variable": "undeclared variables",
    "syntax":              "syntax errors (missing semicolons, braces)",
    "overflow":            "integer overflow",
    "type_error":          "type conversion errors",
    "index_error":         "array out-of-bounds / null pointer",
    "edge_case":           "missing edge cases",
    "complexity":          "time complexity / TLE",
    "wrong_formula":       "wrong formula",
    "unknown":             "various errors",
}


def format_profile_for_prompt(profile: dict) -> str:
    """Format the profile as a concise block injected before the user context (≤1200 chars)."""
    lines: list[str] = ["[User Solving Profile]"]

    lang = profile.get("preferred_language")
    if lang and lang != "english":
        lines.append(f"- Preferred language: {lang.capitalize()} — respond in {lang.capitalize()} if possible.")

    style = profile.get("preferred_help_style")
    if style and style in _STYLE_DESC:
        lines.append(f"- Coaching style: {_STYLE_DESC[style]}.")

    errors: list[dict] = profile.get("common_error_patterns") or []
    if errors:
        top2 = errors[:2]
        desc_parts = []
        for e in top2:
            if isinstance(e, dict):
                label = _ERROR_DESC.get(e.get("type", ""), e.get("type", "?"))
                cnt = e.get("count", 1)
                desc_parts.append(f"{label} ({cnt}×)")
            else:
                desc_parts.append(str(e))
        lines.append(f"- Recurring mistakes: {', '.join(desc_parts)}. Check for these first.")

    wa: list[str] = profile.get("common_wa_patterns") or []
    if wa:
        labels = [_ERROR_DESC.get(t, t) for t in wa[:2]]
        lines.append(f"- Frequent WA sources: {', '.join(labels)}.")

    weak: list[str] = profile.get("weak_tags") or []
    if weak:
        lines.append(f"- Weak topics: {', '.join(weak[:4])}. Give extra guidance here.")

    notes: list[str] = profile.get("coaching_notes") or []
    if notes:
        lines.append(f"- Coach note: {notes[0]}")

    summary = profile.get("summary")
    if summary and len(summary) < 300:
        lines.append(f"- Summary: {summary}")

    block = "\n".join(lines)
    return block[:1200]


# ─── Deterministic summary generation ─────────────────────────────────────────

def _generate_deterministic_summary(
    *,
    common_errors: list[dict],
    weak_tags: list[str],
    preferred_language: str,
    preferred_help_style: str,
    common_wa_patterns: list[str],
) -> str:
    parts: list[str] = []

    if common_errors:
        top = common_errors[0]
        etype = top.get("type", "unknown") if isinstance(top, dict) else str(top)
        label = _ERROR_DESC.get(etype, etype)
        cnt = top.get("count", 0) if isinstance(top, dict) else 0
        if cnt >= 2:
            parts.append(f"Often struggles with {label} ({cnt} occurrences).")

    if weak_tags:
        parts.append(f"Recent weak topics: {', '.join(weak_tags[:3])}.")

    if preferred_language and preferred_language != "english":
        parts.append(f"Usually asks in {preferred_language.capitalize()}.")

    style_sentence: dict[str, str] = {
        "tiny_hints":     "Responds best to one-sentence hints.",
        "conceptual":     "Prefers conceptual guidance over code.",
        "debug_guidance": "Benefits from step-by-step debugging.",
        "detailed":       "Wants detailed walkthroughs.",
        "solution_heavy": "Tends to ask for complete solutions.",
    }
    if preferred_help_style in style_sentence:
        parts.append(style_sentence[preferred_help_style])

    if common_wa_patterns:
        labels = [_ERROR_DESC.get(t, t) for t in common_wa_patterns[:2]]
        parts.append(f"Common WA sources: {', '.join(labels)}.")

    if not parts:
        return "Not enough data yet — profile will improve as more problems are attempted."
    return " ".join(parts)


# ─── AI summary (optional, cost-controlled) ───────────────────────────────────

async def _generate_ai_summary(
    settings: Any,
    base_summary: str,
    recent_events: list[dict],
) -> str:
    """Call DeepSeek once (max 300 tokens) to compress the profile into a coaching note."""
    digest = "\n".join(
        f"  [{e.get('event_type', '?')}] {e.get('short_summary', '')} (error: {e.get('error_type', '?')})"
        for e in recent_events[:10]
    )
    prompt = (
        "You are helping create a personalised coach profile for a competitive programmer.\n"
        f"Base summary: {base_summary}\n"
        f"Recent events:\n{digest}\n\n"
        "Write a 2-3 sentence coaching note about their weak areas and learning style. "
        "Be specific and actionable. Under 150 words."
    )
    url = f"{settings.deepseek_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


# ─── Profile updater (main service call) ──────────────────────────────────────

async def update_user_solving_profile(
    settings: Any,
    *,
    user_id: str | None,
    anonymous_user_key: str | None,
) -> dict | None:
    """
    Load last 100 solving events, aggregate patterns, update user_solving_profiles.
    Returns the updated profile dict or None if Supabase is unconfigured.
    """
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    if not user_id and not anonymous_user_key:
        return None

    # ── Load recent events ────────────────────────────────────────────────────
    params: dict[str, str] = {
        "select": "*",
        "order": "created_at.desc",
        "limit": "100",
    }
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    elif anonymous_user_key:
        params["anonymous_user_key"] = f"eq.{anonymous_user_key}"

    events: list[dict] = await _sb_get(settings, "solving_events", params) or []
    if not isinstance(events, list):
        events = []

    # ── Error pattern aggregation ─────────────────────────────────────────────
    error_counter: Counter[str] = Counter()
    for ev in events:
        etype = ev.get("error_type")
        if etype:
            error_counter[etype] += 1

    common_error_patterns = [
        {"type": etype, "count": count}
        for etype, count in error_counter.most_common(5)
    ]

    # ── Tag aggregation (weak = failed, strong = accepted) ────────────────────
    _failed = {"wrong_answer", "runtime_error", "compilation_error", "time_limit", "tle"}
    weak_counter: Counter[str] = Counter()
    strong_counter: Counter[str] = Counter()

    for ev in events:
        tags: list[str] = ev.get("problem_tags") or []
        etype = ev.get("event_type", "")
        last_status = (ev.get("metadata") or {}).get("last_status", "").lower().replace(" ", "_")

        failed = etype in _failed or last_status in _failed
        if failed:
            for t in tags:
                weak_counter[t] += 1
        elif etype == "accepted":
            for t in tags:
                strong_counter[t] += 1

    weak_tags = [t for t, _ in weak_counter.most_common(6)]
    strong_tags = [t for t, _ in strong_counter.most_common(6)]

    # ── WA pattern aggregation ────────────────────────────────────────────────
    wa_counter: Counter[str] = Counter()
    for ev in events:
        if ev.get("event_type") in ("wrong_answer",) or (
            (ev.get("metadata") or {}).get("last_status", "").lower() in ("wrong_answer", "wrong answer")
        ):
            wa_counter[ev.get("error_type") or "unknown"] += 1
    common_wa_patterns = [t for t, _ in wa_counter.most_common(3)]

    # ── Language / style inference ────────────────────────────────────────────
    messages = [
        ev.get("short_summary") or ""
        for ev in events
        if ev.get("event_type") == "copilot_question"
    ]
    preferred_language = detect_preferred_language(messages)
    preferred_help_style = infer_help_style(events)

    # ── Repeated mistakes list ────────────────────────────────────────────────
    repeated_mistakes: list[str] = []
    for ep in common_error_patterns:
        if ep.get("count", 0) >= 2:
            label = _ERROR_DESC.get(ep["type"], ep["type"])
            repeated_mistakes.append(f"{label} appeared {ep['count']} times")

    # ── Auto coaching notes ───────────────────────────────────────────────────
    coaching_notes: list[str] = []
    if error_counter.get("undeclared_variable", 0) >= 2:
        coaching_notes.append("Remind to declare/initialise variables before use.")
    if wa_counter.get("edge_case", 0) >= 2:
        coaching_notes.append("Suggest testing n=0, n=1, n=2 manually before each submission.")
    if error_counter.get("complexity", 0) >= 2:
        coaching_notes.append("Encourage thinking about time complexity before writing code.")
    if error_counter.get("index_error", 0) >= 2:
        coaching_notes.append("Remind to check array bounds and avoid null pointer dereferences.")

    # ── Confidence score ──────────────────────────────────────────────────────
    confidence_score = round(min(1.0, len(events) / 20.0), 3)

    # ── Summary generation ────────────────────────────────────────────────────
    summary = _generate_deterministic_summary(
        common_errors=common_error_patterns,
        weak_tags=weak_tags,
        preferred_language=preferred_language,
        preferred_help_style=preferred_help_style,
        common_wa_patterns=common_wa_patterns,
    )

    if getattr(settings, "enable_ai_profile_summary", False) and events and settings.deepseek_api_key:
        try:
            summary = await _generate_ai_summary(settings, summary, events[:10])
        except Exception as exc:
            logger.warning("ai profile summary failed: %s", exc)

    # ── Upsert into DB ────────────────────────────────────────────────────────
    now_iso = datetime.now(timezone.utc).isoformat()
    profile_payload: dict = {
        "anonymous_user_key": anonymous_user_key,
        "user_id": user_id,
        "preferred_language": preferred_language,
        "preferred_help_style": preferred_help_style,
        "common_error_patterns": common_error_patterns,
        "common_wa_patterns": common_wa_patterns,
        "weak_tags": weak_tags,
        "strong_tags": strong_tags,
        "repeated_mistakes": repeated_mistakes,
        "coaching_notes": coaching_notes,
        "summary": summary,
        "confidence_score": confidence_score,
        "last_updated_at": now_iso,
    }

    existing = await load_profile(settings, user_id=user_id, anonymous_user_key=anonymous_user_key)
    if existing:
        update_data = {k: v for k, v in profile_payload.items() if k not in ("anonymous_user_key", "user_id")}
        match_params: dict[str, str] = {}
        if user_id:
            match_params["user_id"] = f"eq.{user_id}"
        elif anonymous_user_key:
            match_params["anonymous_user_key"] = f"eq.{anonymous_user_key}"
        await _sb_patch(settings, "user_solving_profiles", update_data, match_params)
        return {**existing, **profile_payload}
    else:
        profile_payload["id"] = str(uuid.uuid4())
        profile_payload["created_at"] = now_iso
        await _sb_post(settings, "user_solving_profiles", [profile_payload])
        return profile_payload


# ─── Solving event persistence ────────────────────────────────────────────────

async def save_solving_event(settings: Any, event: dict) -> None:
    """Best-effort insert of a single solving event row."""
    await _sb_post(settings, "solving_events", [event])
