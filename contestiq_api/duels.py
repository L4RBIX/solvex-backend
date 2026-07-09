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
    """Mark active/waiting duels expired (draw) when past expires_at."""
    if duel["status"] in (COMPLETED, EXPIRED, CANCELLED):
        return duel
    expires = _parse_iso(duel.get("expires_at"))
    if expires is None or _now_dt() < expires:
        return duel

    participants = list_participants(duel["duel_id"])
    accepted = [p for p in participants if p.get("accepted_at")]
    now = store._now()
    if len(accepted) == 1:
        winner = accepted[0]["subject"]
        reason = "opponent_timeout"
        status = COMPLETED
    elif len(accepted) >= 2:
        accepted.sort(key=lambda p: p["accepted_at"])
        winner = accepted[0]["subject"]
        reason = "first_accepted"
        status = COMPLETED
    else:
        winner = None
        reason = "expired_draw"
        status = EXPIRED

    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_matches SET status = ?, completed_at = ?, winner_subject = ?, result_reason = ?"
            " WHERE duel_id = ? AND status NOT IN ('completed', 'expired', 'cancelled')",
            (status, now, winner, reason, duel["duel_id"]),
        )
        for p in participants:
            if p.get("final_status") == FINAL_PENDING:
                final = FINAL_ACCEPTED if p.get("accepted_at") else FINAL_NO_SUBMISSION
                conn.execute(
                    "UPDATE duel_participants SET final_status = ? WHERE duel_id = ? AND subject = ?",
                    (final, duel["duel_id"], p["subject"]),
                )

    if status == COMPLETED:
        _emit_completion_events(duel["duel_id"], winner)

    refreshed = get_duel(duel["duel_id"])
    return refreshed or duel


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


def start_duel(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    require_participant(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    if duel is None:
        raise APIError("DUEL_NOT_FOUND", "Duel not found.", 404)
    duel = _maybe_expire(duel)
    if duel["status"] == ACTIVE:
        return public_detail(duel_id, subject_aliases)
    if duel["status"] != WAITING:
        raise APIError("DUEL_NOT_STARTABLE", "This duel cannot be started.", 409)

    participants = list_participants(duel_id)
    if len(participants) < 2:
        raise APIError("WAITING_FOR_OPPONENT", "Need two participants before starting.", 409)

    cfg = MODES[duel["mode"]]
    starts = _now_dt()
    expires = starts + dt.timedelta(minutes=int(cfg["duration_minutes"]))
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_matches SET status = ?, starts_at = ?, expires_at = ? WHERE duel_id = ?",
            (ACTIVE, starts.isoformat(), expires.isoformat(), duel_id),
        )
        for p in participants:
            conn.execute(
                "UPDATE duel_participants SET ready_at = ? WHERE duel_id = ? AND subject = ?",
                (starts.isoformat(), duel_id, p["subject"]),
            )

    for p in participants:
        product_events.track("duel_started", p["subject"], {"duel_id": duel_id})

    return public_detail(duel_id, subject_aliases)


def _decide_winner_if_ready(duel_id: str) -> None:
    duel = get_duel(duel_id)
    if duel is None or duel["status"] != ACTIVE:
        return
    participants = list_participants(duel_id)
    accepted = [p for p in participants if p.get("accepted_at")]
    if not accepted:
        return
    # First accepted wins immediately (even if opponent hasn't submitted).
    accepted.sort(key=lambda p: p["accepted_at"])
    winner = accepted[0]["subject"]
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "UPDATE duel_matches SET status = ?, completed_at = ?, winner_subject = ?, result_reason = ?"
            " WHERE duel_id = ? AND status = ?",
            (COMPLETED, now, winner, "first_accepted", duel_id, ACTIVE),
        )
        for p in participants:
            final = FINAL_ACCEPTED if p.get("accepted_at") else FINAL_NO_SUBMISSION
            conn.execute(
                "UPDATE duel_participants SET final_status = ? WHERE duel_id = ? AND subject = ?",
                (final, duel_id, p["subject"]),
            )
    _emit_completion_events(duel_id, winner)


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
    if language not in _LANGUAGE_IDS:
        raise APIError("UNSUPPORTED_LANGUAGE", "Supported languages: cpp17, python3.", 422)
    if not source_code.strip():
        raise APIError("EMPTY_SOURCE", "source_code cannot be empty.", 422)

    from contestiq_api.judge0_client import run_submission
    from contestiq_api.settings import get_settings

    settings = get_settings()
    if not settings.judge0_base_url:
        raise APIError("JUDGE0_NOT_CONFIGURED", "Judge0 is not configured.", 503)

    result = await run_submission(
        base_url=settings.judge0_base_url,
        api_key=settings.judge0_api_key,
        api_host=settings.judge0_api_host,
        language_id=_LANGUAGE_IDS[language],
        source_code=source_code,
        stdin=stdin,
        expected_output=expected_output,
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
        elif not passed and participant.get("final_status") == FINAL_PENDING:
            conn.execute(
                "UPDATE duel_participants SET final_status = ?, best_attempt_id = COALESCE(best_attempt_id, ?)"
                " WHERE duel_id = ? AND subject = ?",
                (FINAL_FAILED, submission_id, duel_id, participant["subject"]),
            )

    if passed:
        _decide_winner_if_ready(duel_id)

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
                "accepted_at": p.get("accepted_at"),
                "joined_at": p["joined_at"],
                "submission_count": sub_counts.get(p["subject"], 0),
                "is_viewer": viewer is not None and p["subject"] == viewer["subject"],
                "is_winner": duel.get("winner_subject") == p["subject"],
            }
            for p in participants
        ],
    }


def result_view(duel_id: str, subject_aliases: list[str]) -> dict[str, Any]:
    detail = public_detail(duel_id, subject_aliases)
    duel = get_duel(duel_id)
    assert duel is not None
    duel = _maybe_expire(duel)
    if duel["status"] not in (COMPLETED, EXPIRED):
        raise APIError("DUEL_NOT_FINISHED", "Duel result is not ready yet.", 409)
    return {
        "duel_id": duel_id,
        "status": duel["status"],
        "winner_subject": duel.get("winner_subject"),
        "result_reason": duel.get("result_reason"),
        "completed_at": duel.get("completed_at"),
        "participants": detail["participants"],
        "problem": detail["problem"],
        "viewer_won": bool(
            duel.get("winner_subject")
            and any(p["is_viewer"] and p["is_winner"] for p in detail["participants"])
        ),
        "is_draw": duel.get("winner_subject") is None,
    }
