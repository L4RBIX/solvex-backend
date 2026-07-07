"""Verification sessions: assignment, snapshots, runs, hidden grading,
process-evidence scoring, badge decisions, and reports.

Process evidence uses ONLY these labels — never accusations:
strong_process_evidence, sufficient_process_evidence, limited_process_evidence,
verification_confidence_insufficient, unusual_solve_pattern_observed,
manual_review_recommended.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.skilltrace import challenges as challenge_bank
from contestiq_api.skilltrace import events, judge0

SESSION_MINUTES = 90
MAX_RUNS_PER_SESSION = 30

ALLOWED_LABELS = {
    "strong_process_evidence",
    "sufficient_process_evidence",
    "limited_process_evidence",
    "verification_confidence_insufficient",
    "unusual_solve_pattern_observed",
    "manual_review_recommended",
}


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def get_session(session_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM verification_sessions WHERE session_id = ?", (session_id,)).fetchone()
    return dict(row) if row else None


def assert_owner(session: dict[str, Any], user: dict[str, Any] | None) -> None:
    """BOLA guard: only the session owner (or an admin) may touch a session."""
    if user is not None and user.get("role") == "admin":
        return
    if user is None or user.get("user_id") != session["user_id"]:
        raise APIError("FORBIDDEN", "You do not have access to this verification session.", 403)


def _assert_active(session: dict[str, Any]) -> None:
    if session["session_status"] != "active":
        raise APIError("SESSION_NOT_ACTIVE", f"Session is {session['session_status']}.", 409)
    if store._now() > session["expires_at"]:
        with store.connect() as conn:
            conn.execute(
                "UPDATE verification_sessions SET session_status = 'expired' WHERE session_id = ?",
                (session["session_id"],),
            )
        raise APIError("SESSION_EXPIRED", "This verification session has expired.", 409)


# ─── Start ───────────────────────────────────────────────────────────────────


def start_session(user: dict[str, Any], skill_id: str, level: int | None, request_id: str | None) -> dict[str, Any]:
    challenge_bank.seed_challenges()
    challenge = challenge_bank.assign_challenge(skill_id, level)
    if challenge is None:
        raise APIError("NO_CHALLENGE_AVAILABLE", f"No active challenge exists for skill {skill_id}.", 404)

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO verification_sessions (session_id, user_id, handle, challenge_id, skill_id, level,"
            " session_status, started_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)",
            (
                session_id, user["user_id"], user.get("handle"), challenge["challenge_id"],
                challenge["skill_id"], challenge["level"], now.isoformat(),
                (now + timedelta(minutes=SESSION_MINUTES)).isoformat(),
            ),
        )
    events.append(session_id, "session_started",
                  {"user_id": user["user_id"], "skill_id": skill_id}, request_id=request_id)
    events.append(session_id, "problem_revealed",
                  {"challenge_id": challenge["challenge_id"], "version": challenge["version"]},
                  request_id=request_id)
    return {
        "session_id": session_id,
        "session_status": "active",
        "expires_at": (now + timedelta(minutes=SESSION_MINUTES)).isoformat(),
        "challenge": challenge_bank.public_challenge(challenge),
        "snapshot_hint": "Send code snapshots as you work; they form your process evidence.",
    }


# ─── Snapshots ───────────────────────────────────────────────────────────────


def record_snapshot(session: dict[str, Any], code: str, request_id: str | None) -> dict[str, Any]:
    _assert_active(session)
    content_hash = _source_hash(code)
    with store.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO code_snapshots (snapshot_id, session_id, content_hash, content, content_length, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session["session_id"], content_hash, code, len(code), store._now()),
        )
    # The ledger records only the hash + length — never code content.
    events.append(
        session["session_id"], "code_snapshot",
        {"content_hash": content_hash, "content_length": len(code)},
        actor_type="user", source_trust="browser", redaction_level="hash_only", request_id=request_id,
    )
    return {"status": "recorded", "content_hash": content_hash}


# ─── Runs (user-triggered, visible tests only) ───────────────────────────────


def create_run(session: dict[str, Any], language: str, source: str, stdin: str, request_id: str | None) -> dict[str, Any]:
    _assert_active(session)
    with store.connect() as conn:
        run_count = conn.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE session_id = ? AND kind = 'run'",
            (session["session_id"],),
        ).fetchone()[0]
    if run_count >= MAX_RUNS_PER_SESSION:
        raise APIError("RUN_LIMIT_REACHED", f"Run limit ({MAX_RUNS_PER_SESSION}) reached for this session.", 429)

    attempt_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO execution_attempts (attempt_id, session_id, kind, language, source_hash, created_at)"
            " VALUES (?, ?, 'run', ?, ?, ?)",
            (attempt_id, session["session_id"], language, _source_hash(source), store._now()),
        )
    events.append(session["session_id"], "run_attempt_created",
                  {"attempt_id": attempt_id, "language": language, "source_hash": _source_hash(source)},
                  actor_type="user", source_trust="browser", redaction_level="hash_only", request_id=request_id)

    submission = judge0.get_adapter().submit(attempt_id, 0, language, source, stdin, expected_output=None)
    events.append(session["session_id"], "judge0_submission_created",
                  {"attempt_id": attempt_id, "submission_id": submission["submission_id"], "kind": "run"},
                  request_id=request_id)
    return {"attempt_id": attempt_id, "submission_id": submission["submission_id"], "status": "submitted"}


# ─── Final submission → hidden tests ─────────────────────────────────────────


def submit_final(session: dict[str, Any], language: str, source: str, request_id: str | None) -> dict[str, Any]:
    _assert_active(session)
    tests = challenge_bank.hidden_tests_for(session["challenge_id"])
    if not tests:
        raise APIError("CHALLENGE_MISCONFIGURED", "Challenge has no hidden tests. Contact support.", 500)

    attempt_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO execution_attempts (attempt_id, session_id, kind, language, source_hash, created_at)"
            " VALUES (?, ?, 'hidden', ?, ?, ?)",
            (attempt_id, session["session_id"], language, _source_hash(source), store._now()),
        )
        conn.execute(
            "UPDATE verification_sessions SET session_status = 'judging' WHERE session_id = ?",
            (session["session_id"],),
        )
    events.append(session["session_id"], "hidden_tests_started",
                  {"attempt_id": attempt_id, "test_count": len(tests), "source_hash": _source_hash(source)},
                  redaction_level="hash_only", request_id=request_id)

    adapter = judge0.get_adapter()
    for index, test in enumerate(tests):
        submission = adapter.submit(attempt_id, index, language, source, test["input"], test["expected_output"])
        events.append(session["session_id"], "judge0_submission_created",
                      {"attempt_id": attempt_id, "submission_id": submission["submission_id"],
                       "kind": "hidden", "test_index": index}, request_id=request_id)
    return {"attempt_id": attempt_id, "status": "judging", "test_count": len(tests)}


# ─── Result handling (callback + reconciler) ─────────────────────────────────


def handle_judge0_result(secret: str, payload: dict[str, Any], source: str) -> dict[str, Any]:
    submission = judge0.get_submission_by_secret(secret)
    if submission is None:
        raise APIError("UNKNOWN_CALLBACK", "Callback secret does not match any submission.", 403)
    token = payload.get("token")
    if submission["judge0_token"] and token and token != submission["judge0_token"]:
        raise APIError("CALLBACK_TOKEN_MISMATCH", "Callback token does not match the submission.", 403)

    recorded = judge0.record_result(submission, payload, source)
    if not recorded:
        return {"status": "already_processed", "submission_id": submission["submission_id"]}

    attempt = _get_attempt(submission["attempt_id"])
    events.append(attempt["session_id"], "judge0_result_received",
                  {"submission_id": submission["submission_id"],
                   "status_id": int((payload.get("status") or {}).get("id") or 0),
                   "test_index": submission["test_index"], "kind": attempt["kind"]},
                  actor_type="judge0", source_trust=source, redaction_level="sanitized")
    _maybe_complete_attempt(attempt)
    return {"status": "processed", "submission_id": submission["submission_id"]}


def reconcile_pending(older_than_seconds: float = 20.0) -> dict[str, Any]:
    """Poll Judge0 for submissions whose callbacks never arrived."""
    adapter = judge0.get_adapter()
    reconciled = 0
    for submission in judge0.pending_submissions(older_than_seconds):
        if not submission["judge0_token"]:
            continue
        payload = adapter.poll(submission["judge0_token"])
        status_id = int((payload.get("status") or {}).get("id") or 0)
        if status_id < judge0.TERMINAL_STATUS_MIN:
            continue
        if judge0.record_result(submission, payload, "judge0_poll"):
            attempt = _get_attempt(submission["attempt_id"])
            events.append(attempt["session_id"], "judge0_result_received",
                          {"submission_id": submission["submission_id"], "status_id": status_id,
                           "test_index": submission["test_index"], "kind": attempt["kind"],
                           "recovered_by": "reconciler"},
                          actor_type="judge0", source_trust="judge0_poll", redaction_level="sanitized")
            _maybe_complete_attempt(attempt)
            reconciled += 1
    return {"reconciled": reconciled}


def _get_attempt(attempt_id: str) -> dict[str, Any]:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM execution_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
    assert row is not None
    return dict(row)


def _maybe_complete_attempt(attempt: dict[str, Any]) -> None:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT submission_status, passed FROM judge0_submissions WHERE attempt_id = ?",
            (attempt["attempt_id"],),
        ).fetchall()
    if not rows or any(row["submission_status"] != "done" for row in rows):
        return
    passed = sum(1 for row in rows if row["passed"])
    result = {"total": len(rows), "passed": passed, "pass_rate": round(passed / len(rows), 4)}
    with store.connect() as conn:
        conn.execute(
            "UPDATE execution_attempts SET attempt_status = 'completed', result = ?, completed_at = ?"
            " WHERE attempt_id = ?",
            (json.dumps(result, ensure_ascii=False), store._now(), attempt["attempt_id"]),
        )
    if attempt["kind"] == "hidden":
        session = get_session(attempt["session_id"])
        assert session is not None
        events.append(session["session_id"], "hidden_tests_completed", result)
        _finalize_session(session, result)


# ─── Scoring + badge policy ──────────────────────────────────────────────────


def _process_evidence(session_id: str) -> tuple[str, list[str]]:
    """Label the process trail. Observations only — never accusations."""
    trail = events.list_events(session_id)
    snapshots = sum(1 for e in trail if e["event_type"] == "code_snapshot")
    runs = sum(1 for e in trail if e["event_type"] == "run_attempt_created")
    notes: list[str] = []

    if snapshots == 0 and runs == 0:
        notes.append("unusual_solve_pattern_observed")
        notes.append("manual_review_recommended")
        return "verification_confidence_insufficient", notes
    if snapshots >= 5 and runs >= 2:
        return "strong_process_evidence", notes
    if snapshots >= 2 and runs >= 1:
        return "sufficient_process_evidence", notes
    return "limited_process_evidence", notes


def _finalize_session(session: dict[str, Any], hidden_result: dict[str, Any]) -> None:
    label, notes = _process_evidence(session["session_id"])
    chain_ok = events.verify_chain(session["session_id"])
    pass_rate = hidden_result["pass_rate"]

    reasons: list[str] = []
    if pass_rate < 1.0:
        reasons.append("hidden_tests_failed")
    if label in ("limited_process_evidence", "verification_confidence_insufficient"):
        reasons.append("insufficient_process_trail")
    if not chain_ok:
        reasons.append("event_chain_invalid")

    if not reasons:
        decision = "issued"
    elif "manual_review_recommended" in notes and pass_rate == 1.0:
        decision = "manual_review"
    else:
        decision = "not_issued"

    decision_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO badge_decisions (decision_id, session_id, decision, process_evidence_label,"
            " reasons, hidden_pass_rate, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (decision_id, session["session_id"], decision, label,
             json.dumps(reasons + notes, ensure_ascii=False), pass_rate, store._now()),
        )
        conn.execute(
            "UPDATE verification_sessions SET session_status = 'completed', completed_at = ?, final_label = ?"
            " WHERE session_id = ?",
            (store._now(), label, session["session_id"]),
        )
    events.append(session["session_id"], "badge_decision_created",
                  {"decision": decision, "label": label, "reasons": reasons + notes})
    if "manual_review_recommended" in notes:
        events.append(session["session_id"], "manual_review_requested", {"label": label})

    report_content = {
        "session_id": session["session_id"],
        "challenge_id": session["challenge_id"],
        "skill_id": session["skill_id"],
        "level": session["level"],
        "hidden_tests": hidden_result,
        "process_evidence_label": label,
        "decision": decision,
        "reasons": reasons + notes,
        "event_count": len(events.list_events(session["session_id"])),
        "event_chain_valid": chain_ok,
        "wording_note": (
            "Labels describe the strength of captured process evidence only. "
            "They are not claims about cheating, AI use, or copying."
        ),
    }
    report_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO private_reports (report_id, session_id, user_id, content, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (report_id, session["session_id"], session["user_id"],
             json.dumps(report_content, ensure_ascii=False), store._now()),
        )

    if decision == "issued":
        badge_public_id = secrets.token_hex(8)
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO public_badges (badge_public_id, session_id, handle, skill_id, level,"
                " evidence_label, badge_status, issued_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
                (badge_public_id, session["session_id"], session["handle"], session["skill_id"],
                 session["level"], label, store._now()),
            )
        events.append(session["session_id"], "badge_issued", {"badge_public_id": badge_public_id})
    else:
        events.append(session["session_id"], "badge_not_issued", {"reasons": reasons + notes})


# ─── Views ───────────────────────────────────────────────────────────────────


def session_view(session: dict[str, Any]) -> dict[str, Any]:
    """Owner view. Contains no hidden tests and no Judge0 credentials."""
    with store.connect() as conn:
        attempts = [dict(row) for row in conn.execute(
            "SELECT attempt_id, kind, language, attempt_status, result, created_at, completed_at"
            " FROM execution_attempts WHERE session_id = ? ORDER BY created_at",
            (session["session_id"],),
        ).fetchall()]
        decision = conn.execute(
            "SELECT decision, process_evidence_label, reasons, hidden_pass_rate FROM badge_decisions WHERE session_id = ?",
            (session["session_id"],),
        ).fetchone()
        badge = conn.execute(
            "SELECT badge_public_id, badge_status FROM public_badges WHERE session_id = ?",
            (session["session_id"],),
        ).fetchone()
        report = conn.execute(
            "SELECT report_id FROM private_reports WHERE session_id = ?", (session["session_id"],)
        ).fetchone()
    for attempt in attempts:
        if attempt["result"]:
            attempt["result"] = json.loads(attempt["result"])
    challenge = challenge_bank.get_challenge(session["challenge_id"])
    return {
        "session_id": session["session_id"],
        "session_status": session["session_status"],
        "skill_id": session["skill_id"],
        "level": session["level"],
        "started_at": session["started_at"],
        "expires_at": session["expires_at"],
        "completed_at": session["completed_at"],
        "challenge": challenge_bank.public_challenge(challenge) if challenge else None,
        "attempts": attempts,
        "decision": {**dict(decision), "reasons": json.loads(decision["reasons"])} if decision else None,
        "badge": dict(badge) if badge else None,
        "report_id": report["report_id"] if report else None,
    }


def public_badge_view(badge_public_id: str) -> dict[str, Any] | None:
    """Public projection: no code, no tests, no session internals, no user id."""
    with store.connect() as conn:
        badge = conn.execute(
            "SELECT * FROM public_badges WHERE badge_public_id = ?", (badge_public_id,)
        ).fetchone()
    if badge is None:
        return None
    return {
        "badge_public_id": badge["badge_public_id"],
        "handle": badge["handle"],
        "skill_id": badge["skill_id"],
        "level": badge["level"],
        "evidence_label": badge["evidence_label"],
        "badge_status": badge["badge_status"],
        "issued_at": badge["issued_at"],
        "interpretation": (
            "This badge records a SolveX-supervised verification session with the stated "
            "process-evidence level. It is not a general certificate of mastery."
        ),
    }


def get_report(report_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM private_reports WHERE report_id = ?", (report_id,)).fetchone()
    if row is None:
        return None
    report = dict(row)
    report["content"] = json.loads(report["content"])
    return report
