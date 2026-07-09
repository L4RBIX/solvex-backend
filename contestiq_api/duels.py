"""Friend 1v1 duels by invite link (Phase G4).

Invite-only private matches: same assigned CF problem, first accepted
submission wins. No matchmaking, no Elo, no tournaments, no chat.

Judging reuses Judge0 via the Arena execute path. CF catalog problems do not
store official tests, so submit accepts optional stdin/expected_output (same
as Arena sample judging). Source code is hashed only — never returned.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import secrets
import uuid
from typing import Any

from contestiq_api import product_events
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.leaderboards import resolve_caller

MODES: dict[str, dict[str, Any]] = {
    "rapid_10": {"duration_minutes": 10, "rating_offset": 0, "rating_window": 200},
    "classic_30": {"duration_minutes": 30, "rating_offset": 100, "rating_window": 300},
}

# G4.1 live room: synchronized start countdown and hint budget.
COUNTDOWN_SECONDS = 4
DUEL_HINTS_MAX = 3
# judging_at older than this is treated as a crashed judge run, not "judging".
JUDGING_STALE_SECONDS = 90

WAITING = "waiting"
ACTIVE = "active"
COMPLETED = "completed"
EXPIRED = "expired"
CANCELLED = "cancelled"

ROLE_CREATOR = "creator"
ROLE_CHALLENGER = "challenger"

FINAL_PENDING = "pending"
FINAL_ACCEPTED = "accepted"
FINAL_FAILED = "failed"
FINAL_NO_SUBMISSION = "no_submission"

FALLBACK_RATING_MIN = 900
FALLBACK_RATING_MAX = 1400
DEFAULT_ANCHOR_RATING = 1200

_LANGUAGE_IDS = {"cpp17": 54, "python3": 71}


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def _hash_source(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _excerpt(text: str | None, limit: int = 400) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _now_dt() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _problem_public(problem: dict[str, Any] | None, problem_id: str, rating: int | None) -> dict[str, Any]:
    if problem is None:
        return {
            "problem_id": problem_id,
            "name": problem_id,
            "rating": rating,
            "tags": [],
            "contest_id": None,
            "index": None,
            "url": None,
        }
    tags = problem.get("tags") or "[]"
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = []
    contest_id = problem.get("contest_id")
    index = problem.get("problem_index")
    url = None
    if contest_id and index:
        url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
    return {
        "problem_id": problem_id,
        "name": problem.get("name") or problem_id,
        "rating": problem.get("rating") if problem.get("rating") is not None else rating,
        "tags": tags,
        "contest_id": contest_id,
        "index": index,
        "url": url,
    }


def _creator_anchor_rating(handle: str | None) -> int:
    if not handle:
        return DEFAULT_ANCHOR_RATING
    user = store.get_user(handle)
    if user and user.get("rating"):
        return int(user["rating"])
    return DEFAULT_ANCHOR_RATING


def _solved_keys(handle: str | None) -> set[str]:
    if not handle:
        return set()
    canonical = store.canonical_handle(handle)
    with store.connect() as conn:
        try:
            rows = conn.execute(
                "SELECT DISTINCT problem_id FROM problem_episodes WHERE handle = ? AND eventual_ac = 1",
                (canonical,),
            ).fetchall()
            if rows:
                return {r[0] for r in rows}
        except Exception:
            pass
        try:
            rows = conn.execute(
                "SELECT DISTINCT problem_key FROM cf_submissions_normalized"
                " WHERE handle = ? AND verdict = 'OK'",
                (canonical,),
            ).fetchall()
            return {r[0] for r in rows}
        except Exception:
            return set()


def pick_problem(
    *,
    mode: str,
    duel_id: str,
    creator_handle: str | None,
) -> dict[str, Any]:
    """Deterministic problem pick seeded by duel_id from the mapped catalog."""
    cfg = MODES[mode]
    anchor = _creator_anchor_rating(creator_handle) + int(cfg["rating_offset"])
    window = int(cfg["rating_window"])
    lo, hi = max(800, anchor - window), anchor + window
    exclude = _solved_keys(creator_handle)

    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT p.problem_key, p.name, p.rating, p.tags, p.contest_id, p.problem_index,
                   (SELECT skill_id FROM problem_skill_map m
                    WHERE m.problem_id = p.problem_key
                    ORDER BY m.is_primary DESC, m.weight DESC LIMIT 1) AS skill_id
            FROM problems p
            WHERE p.rating IS NOT NULL
              AND EXISTS (SELECT 1 FROM problem_skill_map m WHERE m.problem_id = p.problem_key)
            ORDER BY p.problem_key
            """
        ).fetchall()

    candidates = [dict(r) for r in rows if r["problem_key"] not in exclude]
    if not candidates:
        candidates = [dict(r) for r in rows]

    band = [c for c in candidates if c["rating"] is not None and lo <= int(c["rating"]) <= hi]
    if not band:
        band = [
            c for c in candidates
            if c["rating"] is not None and FALLBACK_RATING_MIN <= int(c["rating"]) <= FALLBACK_RATING_MAX
        ]
    if not band:
        band = candidates
    if not band:
        raise APIError(
            "CATALOG_EMPTY",
            "Problem catalog is empty — sync the problemset and rebuild the skill map first.",
            503,
        )

    # Stable seeded selection: hash(duel_id) % len(band)
    seed = int(hashlib.sha256(duel_id.encode("utf-8")).hexdigest()[:8], 16)
    chosen = band[seed % len(band)]
    return {
        "problem_id": chosen["problem_key"],
        "problem_rating": chosen.get("rating"),
        "skill_id": chosen.get("skill_id"),
        "problem": chosen,
    }


def get_duel(duel_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM duel_matches WHERE duel_id = ?", (duel_id,)).fetchone()
    return dict(row) if row else None


def list_participants(duel_id: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM duel_participants WHERE duel_id = ? ORDER BY joined_at",
            (duel_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_participant(duel_id: str, subject: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM duel_participants WHERE duel_id = ? AND subject = ?",
            (duel_id, subject),
        ).fetchone()
    return dict(row) if row else None


def is_participant(duel_id: str, subject_aliases: list[str]) -> dict[str, Any] | None:
    if not subject_aliases:
        return None
    placeholders = ", ".join("?" for _ in subject_aliases)
    with store.connect() as conn:
        row = conn.execute(
            f"SELECT * FROM duel_participants WHERE duel_id = ? AND subject IN ({placeholders})"
            " ORDER BY joined_at ASC LIMIT 1",
            (duel_id, *subject_aliases),
        ).fetchone()
    return dict(row) if row else None


def require_participant(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    member = is_participant(duel_id, subject_aliases)
    if member is None:
        raise APIError("FORBIDDEN", "You are not a participant in this duel.", 403)
    return member


def _maybe_expire(duel: dict[str, Any]) -> dict[str, Any]:
    """Finalize active/waiting duels past expires_at (winner v2 or draw)."""
    if duel["status"] in (COMPLETED, EXPIRED, CANCELLED):
        return duel
    expires = _parse_iso(duel.get("expires_at"))
    if expires is None or _now_dt() < expires:
        return duel
    _finalize_duel(duel["duel_id"], at_timeout=True)
    refreshed = get_duel(duel["duel_id"])
    return refreshed or duel


def _rank_key(p: dict[str, Any]) -> tuple[int, str, int]:
    """Winner v2 tie-break order: fewer hints, earlier AC, fewer wrong attempts."""
    return (
        int(p.get("hint_count") or 0),
        p.get("accepted_at") or "",
        int(p.get("wrong_attempts") or 0),
    )


def _finalize_duel(duel_id: str, *, at_timeout: bool) -> bool:
    """Decide the winner (v2 rules) and close the duel exactly once.

    Rules: accepted beats not-accepted; both accepted → fewer hints, then
    earlier accepted_at, then fewer wrong attempts. A lone acceptor does not
    win before timeout while the opponent still holds fewer hints (they could
    still accept and take the fewer-hints tie-break). Runtime/memory never
    decide. Returns True only when this call closed the duel — the caller may
    then rely on completion events having been emitted exactly once.
    """
    duel = get_duel(duel_id)
    if duel is None or duel["status"] in (COMPLETED, EXPIRED, CANCELLED):
        return False
    participants = list_participants(duel_id)
    accepted = [p for p in participants if p.get("accepted_at")]

    if not accepted:
        if not at_timeout:
            return False
        status, winner, reason = EXPIRED, None, "expired_draw"
    elif len(accepted) == 1:
        acc = accepted[0]
        opp = next((p for p in participants if p["subject"] != acc["subject"]), None)
        if (
            not at_timeout
            and opp is not None
            and int(acc.get("hint_count") or 0) > int(opp.get("hint_count") or 0)
        ):
            return False  # opponent can still accept with fewer hints and win
        status, winner = COMPLETED, acc["subject"]
        reason = "opponent_timeout" if at_timeout else "first_accepted"
    else:
        ranked = sorted(accepted, key=_rank_key)
        first, second = ranked[0], ranked[1]
        if _rank_key(first) == _rank_key(second):
            status, winner, reason = COMPLETED, None, "tie_draw"
        else:
            status, winner = COMPLETED, first["subject"]
            if int(first.get("hint_count") or 0) != int(second.get("hint_count") or 0):
                reason = "fewer_hints"
            elif (first.get("accepted_at") or "") != (second.get("accepted_at") or ""):
                reason = "first_accepted"
            else:
                reason = "fewer_wrong_attempts"

    now = store._now()
    with store.connect() as conn:
        cursor = conn.execute(
            "UPDATE duel_matches SET status = ?, completed_at = ?, winner_subject = ?,"
            " result_reason = ?, winner_decided_at = ?"
            " WHERE duel_id = ? AND status NOT IN ('completed', 'expired', 'cancelled')",
            (status, now, winner, reason, now, duel_id),
        )
        if cursor.rowcount != 1:
            return False  # another request already closed it — events stay single-shot
        for p in participants:
            if p.get("accepted_at"):
                final = FINAL_ACCEPTED
            elif p.get("final_status") == FINAL_FAILED:
                final = FINAL_FAILED
            else:
                final = FINAL_NO_SUBMISSION
            conn.execute(
                "UPDATE duel_participants SET final_status = ? WHERE duel_id = ? AND subject = ?",
                (final, duel_id, p["subject"]),
            )

    if status == COMPLETED:
        _emit_completion_events(duel_id, winner)
    return True


def _emit_completion_events(duel_id: str, winner_subject: str | None) -> None:
    participants = list_participants(duel_id)
    for p in participants:
        product_events.track("duel_completed", p["subject"], {"duel_id": duel_id})
        if winner_subject and p["subject"] == winner_subject:
            product_events.track("duel_won", p["subject"], {"duel_id": duel_id})


def create_duel(
    caller: dict[str, Any],
    *,
    mode: str,
    display_name: str,
) -> dict[str, Any]:
    if mode not in MODES:
        raise APIError("INVALID_MODE", "mode must be rapid_10 or classic_30.", 422)

    duel_id = str(uuid.uuid4())
    picked = pick_problem(mode=mode, duel_id=duel_id, creator_handle=caller.get("handle"))
    invite_code = secrets.token_urlsafe(12)
    now = store._now()
    # Waiting room expires in 24h; active duration starts on start().
    waiting_expires = (_now_dt() + dt.timedelta(hours=24)).isoformat()
    handle = caller.get("handle")
    if handle:
        handle = store.canonical_handle(handle)

    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO duel_matches (
                duel_id, creator_subject, creator_user_id, creator_handle, mode, status,
                problem_id, problem_rating, skill_id, invite_code_hash, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                duel_id, caller["subject"], caller.get("user_id"), handle, mode, WAITING,
                picked["problem_id"], picked["problem_rating"], picked["skill_id"],
                _hash_code(invite_code), waiting_expires, now,
            ),
        )
        conn.execute(
            """
            INSERT INTO duel_participants (
                duel_id, subject, user_id, handle, display_name, role, joined_at, final_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                duel_id, caller["subject"], caller.get("user_id"), handle,
                display_name.strip(), ROLE_CREATOR, now, FINAL_PENDING,
            ),
        )

    product_events.track("duel_created", caller["subject"], {"duel_id": duel_id, "mode": mode})

    problem = store.get_problem(picked["problem_id"])
    return {
        "duel_id": duel_id,
        "mode": mode,
        "status": WAITING,
        "problem": _problem_public(problem, picked["problem_id"], picked["problem_rating"]),
        "invite_code": invite_code,
        "expires_at": waiting_expires,
        "created_at": now,
    }


def invite_preview(invite_code: str) -> dict[str, Any]:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM duel_matches WHERE invite_code_hash = ?",
            (_hash_code(invite_code),),
        ).fetchone()
    if row is None:
        raise APIError("INVITE_INVALID", "Invite code is not valid.", 404)
    duel = _maybe_expire(dict(row))
    if duel["status"] in (COMPLETED, EXPIRED, CANCELLED):
        raise APIError("DUEL_CLOSED", "This duel is no longer joinable.", 410)

    participants = list_participants(duel["duel_id"])
    creator = next((p for p in participants if p["role"] == ROLE_CREATOR), None)
    problem = store.get_problem(duel["problem_id"])
    return {
        "duel_id": duel["duel_id"],
        "mode": duel["mode"],
        "status": duel["status"],
        "creator_display_name": creator["display_name"] if creator else "Creator",
        "problem": _problem_public(problem, duel["problem_id"], duel.get("problem_rating")),
        "expires_at": duel["expires_at"],
        "participants_count": len(participants),
    }


def join_duel(caller: dict[str, Any], invite_code: str, display_name: str) -> dict[str, Any]:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM duel_matches WHERE invite_code_hash = ?",
            (_hash_code(invite_code),),
        ).fetchone()
    if row is None:
        raise APIError("INVITE_INVALID", "Invite code is not valid.", 404)
    duel = _maybe_expire(dict(row))
    if duel["status"] != WAITING:
        raise APIError("DUEL_NOT_JOINABLE", "This duel cannot be joined right now.", 409)

    existing = is_participant(duel["duel_id"], caller["aliases"])
    if existing is not None:
        return {"duel_id": duel["duel_id"], "status": duel["status"], "already_member": True, "role": existing["role"]}

    participants = list_participants(duel["duel_id"])
    if len(participants) >= 2:
        raise APIError("DUEL_FULL", "This duel already has two participants.", 409)

    handle = caller.get("handle")
    if handle:
        handle = store.canonical_handle(handle)
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO duel_participants (
                duel_id, subject, user_id, handle, display_name, role, joined_at, final_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                duel["duel_id"], caller["subject"], caller.get("user_id"), handle,
                display_name.strip(), ROLE_CHALLENGER, now, FINAL_PENDING,
            ),
        )

    product_events.track("duel_joined", caller["subject"], {"duel_id": duel["duel_id"]})
    return {"duel_id": duel["duel_id"], "status": WAITING, "already_member": False, "role": ROLE_CHALLENGER}


def arena_path(duel_id: str) -> str:
    return f"/arena?duel={duel_id}"


def _activate(duel_id: str) -> None:
    """Transition waiting → active with a synchronized countdown window."""
    duel = get_duel(duel_id)
    if duel is None or duel["status"] != WAITING:
        return
    cfg = MODES[duel["mode"]]
    now = _now_dt()
    starts = now + dt.timedelta(seconds=COUNTDOWN_SECONDS)
    expires = starts + dt.timedelta(minutes=int(cfg["duration_minutes"]))
    with store.connect() as conn:
        cursor = conn.execute(
            "UPDATE duel_matches SET status = ?, countdown_started_at = ?, starts_at = ?, expires_at = ?"
            " WHERE duel_id = ? AND status = ?",
            (ACTIVE, now.isoformat(), starts.isoformat(), expires.isoformat(), duel_id, WAITING),
        )
        if cursor.rowcount != 1:
            return  # someone else activated concurrently
    for p in list_participants(duel_id):
        product_events.track("duel_started", p["subject"], {"duel_id": duel_id})


def mark_ready(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    """Mark the calling participant ready; auto-start when both are ready."""
    participant = require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    if duel["status"] == ACTIVE:
        return duel_state(duel_id, subject_aliases)
    if duel["status"] != WAITING:
        raise APIError("DUEL_NOT_READYABLE", "This duel is no longer waiting for players.", 409)

    if not participant.get("ready_at"):
        with store.connect() as conn:
            conn.execute(
                "UPDATE duel_participants SET ready_at = ? WHERE duel_id = ? AND subject = ? AND ready_at IS NULL",
                (store._now(), duel_id, participant["subject"]),
            )
        product_events.track("duel_ready", participant["subject"], {"duel_id": duel_id})

    participants = list_participants(duel_id)
    if len(participants) >= 2 and all(p.get("ready_at") for p in participants):
        _activate(duel_id)
    return duel_state(duel_id, subject_aliases)


def start_duel(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    if duel["status"] == ACTIVE:
        detail = public_detail(duel_id, subject_aliases)
        detail["arena_path"] = arena_path(duel_id)
        return detail
    if duel["status"] != WAITING:
        raise APIError("DUEL_NOT_STARTABLE", "This duel cannot be started.", 409)

    participants = list_participants(duel_id)
    if len(participants) < 2:
        raise APIError("WAITING_FOR_OPPONENT", "Need two participants before starting.", 409)
    if not all(p.get("ready_at") for p in participants):
        raise APIError("PLAYERS_NOT_READY", "Both players must be ready before the duel can start.", 409)

    _activate(duel_id)
    detail = public_detail(duel_id, subject_aliases)
    detail["arena_path"] = arena_path(duel_id)
    return detail


def open_arena(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    """Telemetry: participant opened the duel Arena. Idempotent."""
    participant = require_participant(duel_id, subject_aliases)
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET last_seen_at = ?,"
            " arena_opened_at = COALESCE(arena_opened_at, ?)"
            " WHERE duel_id = ? AND subject = ?",
            (now, now, duel_id, participant["subject"]),
        )
    if not participant.get("arena_opened_at"):
        product_events.track("duel_arena_opened", participant["subject"], {"duel_id": duel_id})
    refreshed = get_participant(duel_id, participant["subject"])
    return {
        "duel_id": duel_id,
        "arena_opened_at": (refreshed or participant).get("arena_opened_at"),
    }


# Safe, generic nudges — never editorial content or solution steps.
def _hint_texts(problem_public: dict[str, Any]) -> list[str]:
    tags = problem_public.get("tags") or []
    tag_text = ", ".join(str(t) for t in tags[:3]) if tags else "the core technique this problem tests"
    return [
        "Re-read the constraints. The input bounds usually reveal the intended time "
        "complexity — rule out approaches that are too slow before you write code.",
        f"This problem centres on: {tag_text}. Ask which quantity stays invariant (or "
        "monotonic) while you process the input — that invariant is usually the backbone "
        "of the solution.",
        "Work through the smallest cases by hand and look for a pattern. Then check the "
        "edge cases explicitly: minimum input size, all-equal values, and extreme bounds.",
    ]


def use_hint(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    """Serve the participant's next safe hint and count it (winner v2 penalty)."""
    participant = require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    if duel["status"] != ACTIVE:
        raise APIError("DUEL_NOT_ACTIVE", "Hints are only available while the duel is active.", 409)
    starts = _parse_iso(duel.get("starts_at"))
    if starts is not None and _now_dt() < starts:
        raise APIError("DUEL_COUNTDOWN", "The duel is still counting down.", 409)

    problem = store.get_problem(duel["problem_id"])
    texts = _hint_texts(_problem_public(problem, duel["problem_id"], duel.get("problem_rating")))
    used = int(participant.get("hint_count") or 0)
    if used >= DUEL_HINTS_MAX:
        return {
            "duel_id": duel_id,
            "hint_number": used,
            "hint_text": texts[-1],
            "hints_used": used,
            "hints_remaining": 0,
            "note": "No hints left — fewer hints wins ties.",
        }

    hint_number = used + 1
    text = texts[hint_number - 1]
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET hint_count = hint_count + 1 WHERE duel_id = ? AND subject = ?",
            (duel_id, participant["subject"]),
        )
        conn.execute(
            "INSERT INTO duel_hints (hint_id, duel_id, participant_subject, hint_number, hint_text, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), duel_id, participant["subject"], hint_number, text, now),
        )
    product_events.track(
        "duel_hint_used", participant["subject"], {"duel_id": duel_id, "hint_number": hint_number}
    )
    # A hint can settle a pending decision: if the opponent already accepted and
    # no longer trails on hints, they win now.
    _finalize_duel(duel_id, at_timeout=False)
    return {
        "duel_id": duel_id,
        "hint_number": hint_number,
        "hint_text": text,
        "hints_used": hint_number,
        "hints_remaining": DUEL_HINTS_MAX - hint_number,
        "note": "Hints help, but fewer hints wins ties.",
    }


async def submit_solution(
    duel_id: str,
    subject_aliases: list[str],
    *,
    language: str,
    source_code: str,
    stdin: str = "",
    expected_output: str | None = None,
) -> dict[str, Any]:
    participant = require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    if duel["status"] != ACTIVE:
        raise APIError("DUEL_NOT_ACTIVE", "Submissions are only accepted while the duel is active.", 409)
    starts = _parse_iso(duel.get("starts_at"))
    if starts is not None and _now_dt() < starts:
        raise APIError("DUEL_COUNTDOWN", "The duel is still counting down.", 409)
    if language not in _LANGUAGE_IDS:
        raise APIError("UNSUPPORTED_LANGUAGE", "Supported languages: cpp17, python3.", 422)
    if not source_code.strip():
        raise APIError("EMPTY_SOURCE", "source_code cannot be empty.", 422)
    # Without an expected output, any program that merely runs would count as
    # accepted — no basis for a duel verdict. (CF catalog stores no official
    # tests; this stays sample/custom-test judging and the UI says so.)
    if expected_output is None or not expected_output.strip():
        raise APIError(
            "EXPECTED_OUTPUT_REQUIRED",
            "Duel judging compares your program's output against an expected output — provide a test with its expected output.",
            422,
        )

    from contestiq_api.judge0_client import run_submission
    from contestiq_api.settings import get_settings

    settings = get_settings()
    if not settings.judge0_base_url:
        raise APIError("JUDGE0_NOT_CONFIGURED", "Judge0 is not configured.", 503)

    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET judging_at = ?, last_seen_at = ? WHERE duel_id = ? AND subject = ?",
            (store._now(), store._now(), duel_id, participant["subject"]),
        )
    try:
        result = await run_submission(
            base_url=settings.judge0_base_url,
            api_key=settings.judge0_api_key,
            api_host=settings.judge0_api_host,
            language_id=_LANGUAGE_IDS[language],
            source_code=source_code,
            stdin=stdin,
            expected_output=expected_output,
        )
    finally:
        with store.connect() as conn:
            conn.execute(
                "UPDATE duel_participants SET judging_at = NULL WHERE duel_id = ? AND subject = ?",
                (duel_id, participant["subject"]),
            )
    passed = bool(result.get("passed")) or result.get("status") == "accepted"
    submission_id = str(uuid.uuid4())
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO duel_submissions (
                submission_id, duel_id, participant_subject, language, source_hash,
                judge_status, passed, stdout_excerpt, stderr_excerpt, created_at, judged_at,
                runtime_ms, memory_kb
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id, duel_id, participant["subject"], language, _hash_source(source_code),
                result.get("status") or "error", 1 if passed else 0,
                _excerpt(result.get("stdout")), _excerpt(result.get("stderr") or result.get("compile_output")),
                now, now, result.get("time_ms"), result.get("memory_kb"),
            ),
        )
        if passed and not participant.get("accepted_at"):
            conn.execute(
                "UPDATE duel_participants SET accepted_at = ?, best_attempt_id = ?, final_status = ?"
                " WHERE duel_id = ? AND subject = ?",
                (now, submission_id, FINAL_ACCEPTED, duel_id, participant["subject"]),
            )
        elif not passed and not participant.get("accepted_at"):
            conn.execute(
                "UPDATE duel_participants SET wrong_attempts = wrong_attempts + 1,"
                " final_status = CASE WHEN final_status = 'pending' THEN 'failed' ELSE final_status END,"
                " best_attempt_id = COALESCE(best_attempt_id, ?)"
                " WHERE duel_id = ? AND subject = ?",
                (submission_id, duel_id, participant["subject"]),
            )

    if passed:
        _finalize_duel(duel_id, at_timeout=False)

    return {
        "submission_id": submission_id,
        "judge_status": result.get("status"),
        "passed": passed,
        "runtime_ms": result.get("time_ms"),
        "memory_kb": result.get("memory_kb"),
        "message": result.get("message") or result.get("status"),
        "duel": public_detail(duel_id, subject_aliases),
    }


def list_duels_for_caller(subject_aliases: list[str]) -> list[dict[str, Any]]:
    if not subject_aliases:
        return []
    placeholders = ", ".join("?" for _ in subject_aliases)
    with store.connect() as conn:
        rows = conn.execute(
            f"""
            SELECT d.duel_id, d.mode, d.status, d.problem_id, d.problem_rating, d.created_at,
                   d.expires_at, d.winner_subject, d.result_reason, p.role, p.display_name
            FROM duel_matches d
            JOIN duel_participants p ON p.duel_id = d.duel_id
            WHERE p.subject IN ({placeholders})
            ORDER BY d.created_at DESC
            LIMIT 50
            """,
            subject_aliases,
        ).fetchall()
    return [
        {
            "duel_id": r["duel_id"],
            "mode": r["mode"],
            "status": r["status"],
            "problem_id": r["problem_id"],
            "problem_rating": r["problem_rating"],
            "role": r["role"],
            "created_at": r["created_at"],
            "expires_at": r["expires_at"],
            "winner_subject": r["winner_subject"],
            "result_reason": r["result_reason"],
        }
        for r in rows
    ]


def public_detail(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    participants = list_participants(duel_id)
    problem = store.get_problem(duel["problem_id"])
    viewer = is_participant(duel_id, subject_aliases)

    with store.connect() as conn:
        sub_counts = {
            row["participant_subject"]: row["cnt"]
            for row in conn.execute(
                "SELECT participant_subject, COUNT(*) AS cnt FROM duel_submissions"
                " WHERE duel_id = ? GROUP BY participant_subject",
                (duel_id,),
            ).fetchall()
        }

    return {
        "duel_id": duel["duel_id"],
        "mode": duel["mode"],
        "status": duel["status"],
        "problem": _problem_public(problem, duel["problem_id"], duel.get("problem_rating")),
        "skill_id": duel.get("skill_id"),
        "starts_at": duel.get("starts_at"),
        "expires_at": duel["expires_at"],
        "created_at": duel["created_at"],
        "completed_at": duel.get("completed_at"),
        "winner_subject": duel.get("winner_subject"),
        "result_reason": duel.get("result_reason"),
        "viewer_subject": viewer["subject"] if viewer else None,
        "viewer_role": viewer["role"] if viewer else None,
        "participants": [
            {
                "display_name": p["display_name"],
                "handle": p.get("handle"),
                "role": p["role"],
                "final_status": p["final_status"],
                "ready": bool(p.get("ready_at")),
                "accepted_at": p.get("accepted_at"),
                "joined_at": p["joined_at"],
                "submission_count": sub_counts.get(p["subject"], 0),
                "hint_count": int(p.get("hint_count") or 0),
                "wrong_attempts": int(p.get("wrong_attempts") or 0),
                "is_viewer": viewer is not None and p["subject"] == viewer["subject"],
                "is_winner": duel.get("winner_subject") == p["subject"],
            }
            for p in participants
        ],
    }


def _is_judging(p: dict[str, Any]) -> bool:
    judging_at = _parse_iso(p.get("judging_at"))
    if judging_at is None:
        return False
    return (_now_dt() - judging_at).total_seconds() <= JUDGING_STALE_SECONDS


def _seconds_to_accept(duel: dict[str, Any], p: dict[str, Any]) -> float | None:
    starts = _parse_iso(duel.get("starts_at"))
    accepted = _parse_iso(p.get("accepted_at"))
    if starts is None or accepted is None:
        return None
    return max(0.0, round((accepted - starts).total_seconds(), 1))


def duel_state(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    """Lightweight participant-only polling payload for the live room + Arena.

    Contains everything the room/Arena needs each 1–2s tick and nothing
    sensitive: no source code, no invite hash, no Judge0 config, no hidden
    tests (the catalog has none). Also bumps the viewer's last_seen_at.
    """
    viewer = require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)

    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_participants SET last_seen_at = ? WHERE duel_id = ? AND subject = ?",
            (store._now(), duel_id, viewer["subject"]),
        )
        sub_counts = {
            row["participant_subject"]: row["cnt"]
            for row in conn.execute(
                "SELECT participant_subject, COUNT(*) AS cnt FROM duel_submissions"
                " WHERE duel_id = ? GROUP BY participant_subject",
                (duel_id,),
            ).fetchall()
        }

    participants = list_participants(duel_id)
    problem = store.get_problem(duel["problem_id"])
    winner_subject = duel.get("winner_subject")

    participant_states = [
        {
            "display_name": p["display_name"],
            "handle": p.get("handle"),
            "role": p["role"],
            "is_viewer": p["subject"] == viewer["subject"],
            "ready": bool(p.get("ready_at")),
            "ready_at": p.get("ready_at"),
            "joined_at": p["joined_at"],
            "arena_opened": bool(p.get("arena_opened_at")),
            "submission_count": sub_counts.get(p["subject"], 0),
            "wrong_attempts": int(p.get("wrong_attempts") or 0),
            "hint_count": int(p.get("hint_count") or 0),
            "judging": _is_judging(p),
            "accepted": bool(p.get("accepted_at")),
            "accepted_at": p.get("accepted_at"),
            "seconds_to_accept": _seconds_to_accept(duel, p),
            "final_status": p["final_status"],
            "is_winner": winner_subject == p["subject"],
        }
        for p in participants
    ]

    state: dict[str, Any] = {
        "duel_id": duel_id,
        "mode": duel["mode"],
        "status": duel["status"],
        "server_time": store._now(),
        "countdown_seconds": COUNTDOWN_SECONDS,
        "countdown_started_at": duel.get("countdown_started_at"),
        "starts_at": duel.get("starts_at"),
        "expires_at": duel["expires_at"],
        "arena_path": arena_path(duel_id),
        "duration_minutes": int(MODES[duel["mode"]]["duration_minutes"]),
        "hints_max": DUEL_HINTS_MAX,
        # Honest judging label: the CF catalog stores no official tests.
        "judging_mode": "sample",
        "judging_note": "Practice duel uses sample/custom test judging — not official Codeforces tests.",
        "problem": _problem_public(problem, duel["problem_id"], duel.get("problem_rating")),
        "skill_id": duel.get("skill_id"),
        "participants": participant_states,
        "result": None,
    }

    if duel["status"] in (COMPLETED, EXPIRED, CANCELLED):
        viewer_state = next((p for p in participant_states if p["is_viewer"]), None)
        winner_state = next((p for p in participant_states if p["is_winner"]), None)
        viewer_won = bool(winner_subject and viewer_state and viewer_state["is_winner"])
        is_draw = winner_subject is None
        state["result"] = {
            "status": duel["status"],
            "winner_display_name": winner_state["display_name"] if winner_state else None,
            "result_reason": duel.get("result_reason"),
            "completed_at": duel.get("completed_at"),
            "viewer_won": viewer_won,
            "is_draw": is_draw,
            # Mirrors gamification XP_RULES: duel_completed 10, duel_won +15.
            "xp_awarded": (10 + (15 if viewer_won else 0)) if duel["status"] == COMPLETED else 0,
        }
    return state


def result_view(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    detail = public_detail(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    assert duel is not None
    duel = _maybe_expire(duel)
    if duel["status"] not in (COMPLETED, EXPIRED):
        raise APIError("DUEL_NOT_FINISHED", "Duel result is not ready yet.", 409)
    winner = next((p for p in detail["participants"] if p["is_winner"]), None)
    viewer_won = bool(
        duel.get("winner_subject")
        and any(p["is_viewer"] and p["is_winner"] for p in detail["participants"])
    )
    return {
        "duel_id": duel_id,
        "status": duel["status"],
        "winner_subject": duel.get("winner_subject"),
        "winner_display_name": winner["display_name"] if winner else None,
        "result_reason": duel.get("result_reason"),
        "completed_at": duel.get("completed_at"),
        "participants": detail["participants"],
        "problem": detail["problem"],
        "viewer_won": viewer_won,
        "is_draw": duel.get("winner_subject") is None,
        "xp_awarded": (10 + (15 if viewer_won else 0)) if duel["status"] == COMPLETED else 0,
    }
