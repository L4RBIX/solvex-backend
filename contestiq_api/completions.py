"""Canonical Solo assignments, completion history, and Codeforces verification.

Only two sources can create a durable completion:

* ``solvex_practice_judge`` after the existing private-pack judge passes; and
* ``codeforces_verified`` after a server-side ``user.status`` result for the
  authenticated account's verified handle contains an exact Accepted problem.

Historical is a classification of the latter source, never a third source.
Client handles, verdicts, and timestamps are deliberately absent from this API.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import uuid
from typing import Any

from contestiq_api import duels, entitlements, gamification, handles, product_events
from contestiq_api.cfdata import episodes, profiles, store
from contestiq_api.cfdata.client import CodeforcesClient, CodeforcesClientError
from contestiq_api.errors import APIError

PRACTICE_COMPLETION_SOURCE = "solvex_practice_judge"
CODEFORCES_COMPLETION_SOURCE = "codeforces_verified"
COMPLETION_EVENT = "practice_problem_completed"
CHECK_COOLDOWN_SECONDS = 30
# The lease outlives two 20-second transport attempts, rate-limit waiting, and
# exponential backoff. The user-facing cooldown is reset to 30 seconds when a
# check finishes.
CHECK_LEASE_SECONDS = 90
CHECK_SUBMISSION_LIMIT = 500
QUEUE_SOURCES = {
    "retry_queue",
    "daily_queue",
    "seven_day_plan",
    "fourteen_day_plan",
    "direct_arena",
}


def _now_dt() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def _epoch_time(value: Any) -> dt.datetime:
    return dt.datetime.fromtimestamp(int(value), tz=dt.timezone.utc)


def _problem(problem_id: str) -> dict[str, Any]:
    problem = store.get_problem(problem_id)
    if problem is None:
        raise APIError(
            "PROBLEM_NOT_FOUND",
            f"Problem {problem_id} is not available in the SolveX catalog.",
            404,
        )
    contest_id = problem.get("contest_id")
    index = problem.get("problem_index")
    if not isinstance(contest_id, int) or contest_id <= 0 or not isinstance(index, str) or not index:
        raise APIError(
            "PROBLEM_IDENTITY_UNAVAILABLE",
            f"Problem {problem_id} does not have a verifiable Codeforces identity.",
            409,
        )
    return problem


def _has_complete_active_pack(problem_id: str) -> bool:
    duels.seed_builtin_duel_problem_packs()
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM duel_problem_packs
            WHERE problem_id = ? AND active = 1
            ORDER BY version DESC
            """,
            (problem_id,),
        ).fetchall()
    if not rows:
        return False
    pack = dict(rows[0])
    return bool(
        duels._normalize_judge_tests(pack.get("judge_tests"))
        and duels._pack_has_complete_content(pack)
    )


def problem_capability(problem_id: str) -> dict[str, Any]:
    _problem(problem_id)
    practice_available = _has_complete_active_pack(problem_id)
    sources = [CODEFORCES_COMPLETION_SOURCE]
    if practice_available:
        sources.insert(0, PRACTICE_COMPLETION_SOURCE)
    return {
        "problem_id": problem_id,
        "practice_judge_available": practice_available,
        "primary_completion_source": sources[0],
        "completion_sources": sources,
    }


def _completion_row(user_id: str, problem_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM problem_completions WHERE user_id = ? AND problem_id = ?",
            (user_id, problem_id),
        ).fetchone()
    return dict(row) if row else None


def _completion_payload(row: dict[str, Any] | sqlite3.Row, *, already_completed: bool) -> dict[str, Any]:
    item = dict(row)
    return {
        "completion_id": item["completion_id"],
        "problem_id": item["problem_id"],
        "completion_source": item["completion_source"],
        "historical": bool(item["is_historical"]),
        "already_completed": already_completed,
        "completed_at": item["completed_at"],
        "verified_at": item.get("verified_at"),
        "assigned_at": item.get("assigned_at"),
        "xp_awarded": int(item.get("xp_awarded") or 0),
        "queue_source": item.get("queue_source") or "direct_arena",
        "codeforces_submission_id": item.get("codeforces_submission_id"),
        "programming_language": item.get("programming_language"),
    }


def _trusted_context(caller: dict[str, Any], request: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    from contestiq_api import practice

    context = practice._resolve_queue_context(
        request.get("queue_item_id"),
        caller=caller,
        public_handle=None,
    )
    if context is not None and context.get("problem_id") != request["problem_id"]:
        context = None
    source = str(context.get("source")) if context else str(request.get("source") or "direct_arena")
    if source not in QUEUE_SOURCES:
        source = "direct_arena"
    return source, context


def _open_assignment(
    caller: dict[str, Any],
    request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    problem_id = request["problem_id"]
    _problem(problem_id)
    source, context = _trusted_context(caller, request)
    now = store._now()
    assigned_at = str((context or {}).get("container_created_at") or now)

    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        completion = conn.execute(
            "SELECT * FROM problem_completions WHERE user_id = ? AND problem_id = ?",
            (caller["user_id"], problem_id),
        ).fetchone()
        assignment = conn.execute(
            """
            SELECT * FROM solo_problem_assignments
            WHERE user_id = ? AND problem_id = ?
              AND status IN ('active', 'completed')
            ORDER BY assigned_at, assignment_id
            LIMIT 1
            """,
            (caller["user_id"], problem_id),
        ).fetchone()
        if assignment is None:
            assignment_id = str(uuid.uuid4())
            status = "completed" if completion else "active"
            conn.execute(
                """
                INSERT INTO solo_problem_assignments (
                    assignment_id, user_id, problem_id, source, queue_item_id,
                    assigned_at, opened_at, status, completion_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    caller["user_id"],
                    problem_id,
                    source,
                    request.get("queue_item_id") if context else None,
                    assigned_at,
                    now,
                    status,
                    completion["completion_id"] if completion else None,
                ),
            )
        else:
            assignment_id = assignment["assignment_id"]
            conn.execute(
                """
                UPDATE solo_problem_assignments
                SET opened_at = COALESCE(opened_at, ?),
                    status = CASE WHEN ? IS NULL THEN status ELSE 'completed' END,
                    completion_id = COALESCE(completion_id, ?)
                WHERE assignment_id = ?
                """,
                (
                    now,
                    completion["completion_id"] if completion else None,
                    completion["completion_id"] if completion else None,
                    assignment_id,
                ),
            )
        assignment = conn.execute(
            "SELECT * FROM solo_problem_assignments WHERE assignment_id = ?",
            (assignment_id,),
        ).fetchone()
    assert assignment is not None
    return dict(assignment), dict(completion) if completion else None


def _assignment_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "assignment_id": row["assignment_id"],
        "problem_id": row["problem_id"],
        "source": row["source"],
        "queue_item_id": row.get("queue_item_id"),
        "assigned_at": row["assigned_at"],
        "opened_at": row.get("opened_at") or row["assigned_at"],
        "status": "completed" if row.get("status") == "completed" else "active",
    }


def open_problem(caller: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    assignment, completion = _open_assignment(caller, request)
    return {
        "assignment": _assignment_payload(assignment),
        "capability": problem_capability(request["problem_id"]),
        "completion": (
            _completion_payload(completion, already_completed=True)
            if completion is not None
            else None
        ),
    }


def _snapshot(caller: dict[str, Any]) -> dict[str, Any]:
    from contestiq_api import auth

    user = auth.get_user(caller["user_id"])
    plan = entitlements.effective_plan(user)
    snapshot = gamification.build_snapshot(
        caller["subject"],
        plan,
        product_events.events_for_account(caller["user_id"]),
    )
    return {
        "xp_total": snapshot["xp_total"],
        "streak": snapshot["streak"]["current"],
        "daily_goal": snapshot["daily_goal"],
    }


def _no_effects() -> dict[str, bool]:
    return {
        "solution_verified": False,
        "problem_marked_completed": False,
        "solved_history_updated": False,
        "xp_updated": False,
        "daily_goal_updated": False,
        "training_queue_refreshed": False,
    }


def _stored_effects(
    completion: dict[str, Any],
    *,
    already_completed: bool,
) -> dict[str, bool]:
    if already_completed:
        return {
            **_no_effects(),
            "solution_verified": True,
        }
    current = not bool(completion.get("is_historical"))
    return {
        "solution_verified": True,
        "problem_marked_completed": True,
        "solved_history_updated": bool(completion.get("history_updated")),
        "xp_updated": current and int(completion.get("xp_awarded") or 0) > 0,
        "daily_goal_updated": current and bool(completion.get("daily_goal_updated")),
        "training_queue_refreshed": bool(completion.get("queue_refreshed")),
    }


def _continuation_for_completion(completion_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM practice_continuations WHERE completion_id = ?",
            (completion_id,),
        ).fetchone()
    return dict(row) if row else None


def _response(
    caller: dict[str, Any],
    *,
    problem_id: str,
    status: str,
    message: str,
    latest_verdict: str | None = None,
    cooldown_seconds: int = 0,
    next_check_at: str | None = None,
    completion: dict[str, Any] | None = None,
    already_completed: bool = False,
) -> dict[str, Any]:
    from contestiq_api import practice

    continuation = (
        _continuation_for_completion(completion["completion_id"])
        if completion is not None
        else None
    )
    return {
        "problem_id": problem_id,
        "status": status,
        "message": message,
        "latest_verdict": latest_verdict,
        "cooldown_seconds": max(0, int(cooldown_seconds)),
        "next_check_at": next_check_at,
        "completion": (
            _completion_payload(completion, already_completed=already_completed)
            if completion is not None
            else None
        ),
        "progress": _snapshot(caller),
        "effects": (
            _stored_effects(completion, already_completed=already_completed)
            if completion is not None
            else _no_effects()
        ),
        "next_problem": practice._continuation_payload(continuation),
        "queue": (
            practice._queue_payload(continuation, already_completed=already_completed)
            if continuation is not None
            else (
                {
                    "exhausted": False,
                    "message": "Historical completion saved; no training replacement was generated.",
                }
                if completion is not None and bool(completion.get("is_historical"))
                else (
                    {
                        "exhausted": False,
                        "message": (
                            "Completion was saved, but replacement selection is temporarily unavailable. "
                            "Checking again will retry it."
                        ),
                    }
                    if completion is not None and not bool(completion.get("queue_refreshed"))
                    else practice._queue_payload(None, already_completed=already_completed)
                )
            )
        ),
    }


def _relevant_submissions(
    handle: str,
    contest_id: int,
    problem_index: str,
) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM cf_submissions_normalized
            WHERE handle = ? AND contest_id = ? AND problem_index = ?
            ORDER BY creation_time DESC, submission_id DESC
            """,
            (store.canonical_handle(handle), contest_id, problem_index),
        ).fetchall()
    return [dict(row) for row in rows]


def _accepted(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((row for row in rows if row.get("verdict") == "OK"), None)


def _acquire_check(
    *,
    caller: dict[str, Any],
    problem_id: str,
    handle: str,
    assignment_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    now_dt = _now_dt()
    now = now_dt.isoformat()
    cooldown_until = (now_dt + dt.timedelta(seconds=CHECK_LEASE_SECONDS)).isoformat()
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pending = conn.execute(
            """
            SELECT * FROM codeforces_completion_checks
            WHERE user_id = ? AND problem_id = ? AND result = 'pending'
            ORDER BY requested_at DESC LIMIT 1
            """,
            (caller["user_id"], problem_id),
        ).fetchone()
        if pending is not None:
            if _parse_time(pending["cooldown_until"]) > now_dt:
                return None, dict(pending)
            conn.execute(
                """
                UPDATE codeforces_completion_checks
                SET result = 'upstream_error', completed_at = ?, error_code = 'STALE_CHECK_LEASE'
                WHERE check_id = ? AND result = 'pending'
                """,
                (now, pending["check_id"]),
            )
        latest = conn.execute(
            """
            SELECT * FROM codeforces_completion_checks
            WHERE user_id = ? AND problem_id = ?
            ORDER BY requested_at DESC LIMIT 1
            """,
            (caller["user_id"], problem_id),
        ).fetchone()
        if latest is not None and _parse_time(latest["cooldown_until"]) > now_dt:
            return None, dict(latest)
        check_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO codeforces_completion_checks (
                check_id, user_id, problem_id, codeforces_handle, assignment_id,
                requested_at, cooldown_until, result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                check_id,
                caller["user_id"],
                problem_id,
                store.canonical_handle(handle),
                assignment_id,
                now,
                cooldown_until,
            ),
        )
        row = conn.execute(
            "SELECT * FROM codeforces_completion_checks WHERE check_id = ?",
            (check_id,),
        ).fetchone()
    return dict(row) if row else None, None


def _finish_check(
    check_id: str,
    *,
    result: str,
    response_source: str | None,
    latest: dict[str, Any] | None,
    matched: dict[str, Any] | None = None,
    completion_id: str | None = None,
    error_code: str | None = None,
) -> str:
    finished_at = _now_dt()
    cooldown_until = (finished_at + dt.timedelta(seconds=CHECK_COOLDOWN_SECONDS)).isoformat()
    with store.connect() as conn:
        conn.execute(
            """
            UPDATE codeforces_completion_checks
            SET result = ?, completed_at = ?, cooldown_until = ?, response_source = ?,
                latest_submission_id = ?, latest_verdict = ?,
                matched_submission_id = ?, completion_id = ?, error_code = ?
            WHERE check_id = ? AND result = 'pending'
            """,
            (
                result,
                finished_at.isoformat(),
                cooldown_until,
                response_source,
                latest.get("submission_id") if latest else None,
                latest.get("verdict") if latest else None,
                matched.get("submission_id") if matched else None,
                completion_id,
                error_code,
                check_id,
            ),
        )
    return cooldown_until


def _refresh_recent(handle: str) -> tuple[bool, str | None]:
    client = CodeforcesClient(max_retries=2)
    result = client.get_user_status(handle, from_index=1, count=CHECK_SUBMISSION_LIMIT)
    store.upsert_submissions(handle, list(result.data or []))
    try:
        episodes.rebuild_episodes(handle)
    except Exception:
        # Normalized submissions remain authoritative. Episode/profile refresh is
        # derived recommendation evidence and must not block completion.
        pass
    return bool(result.stale), result.fetched_at


def _server_visible_problem_ids(caller: dict[str, Any]) -> set[str]:
    visible: set[str] = set()
    today = _now_dt().date()
    plan_floor = (today - dt.timedelta(days=13)).isoformat()
    plan_ceiling = (today + dt.timedelta(days=13)).isoformat()
    with store.connect() as conn:
        visible.update(
            row["problem_id"]
            for row in conn.execute(
                """
                SELECT problem_id FROM solo_problem_assignments
                WHERE user_id = ? AND status = 'active'
                """,
                (caller["user_id"],),
            ).fetchall()
        )
        visible.update(
            row["problem_id"]
            for row in conn.execute(
                """
                SELECT problem_id FROM practice_continuations
                WHERE user_id = ? AND status = 'active' AND problem_id IS NOT NULL
                """,
                (caller["user_id"],),
            ).fetchall()
        )
        if caller.get("handle"):
            handle = store.canonical_handle(str(caller["handle"]))
            visible.update(
                row["problem_id"]
                for row in conn.execute(
                    """
                    SELECT ri.problem_id
                    FROM recommendation_items ri
                    JOIN recommendation_runs rr ON rr.run_id = ri.run_id
                    WHERE rr.handle = ? AND ri.item_status = 'proposed'
                      AND rr.owner_user_id = ? AND rr.queue_date = ?
                    """,
                    (handle, caller["user_id"], today.isoformat()),
                ).fetchall()
            )
            visible.update(
                row["problem_id"]
                for row in conn.execute(
                    """
                    SELECT tpi.problem_id
                    FROM training_plan_items tpi
                    JOIN training_plans tp ON tp.plan_id = tpi.plan_id
                    WHERE tp.handle = ? AND tpi.item_status = 'proposed'
                      AND tp.owner_user_id = ? AND tp.plan_status = 'active'
                      AND tp.start_date BETWEEN ? AND ?
                    """,
                    (handle, caller["user_id"], plan_floor, plan_ceiling),
                ).fetchall()
            )
    return visible


def _update_skill_evidence(
    conn: sqlite3.Connection,
    *,
    handle: str,
    problem_id: str,
    practiced_at: int,
) -> None:
    """Update recency only; never fabricate mastery, solve counts, or confidence."""
    skill_rows = conn.execute(
        "SELECT skill_id FROM problem_skill_map WHERE problem_id = ?",
        (problem_id,),
    ).fetchall()
    now = store._now()
    for skill_row in skill_rows:
        profile = conn.execute(
            "SELECT status, last_practiced_at FROM user_skill_profiles WHERE handle = ? AND skill_id = ?",
            (store.canonical_handle(handle), skill_row["skill_id"]),
        ).fetchone()
        if profile is None:
            continue
        previous = int(profile["last_practiced_at"] or 0)
        effective = max(previous, practiced_at)
        interval_days = profiles.REVIEW_INTERVAL_DAYS.get(profile["status"], 14)
        conn.execute(
            """
            UPDATE user_skill_profiles
            SET last_practiced_at = ?, review_due_at = ?, updated_at = ?
            WHERE handle = ? AND skill_id = ?
            """,
            (
                effective,
                effective + interval_days * profiles.DAY_SECONDS,
                now,
                store.canonical_handle(handle),
                skill_row["skill_id"],
            ),
        )


def _persist_codeforces_completion(
    *,
    caller: dict[str, Any],
    request: dict[str, Any],
    assignment: dict[str, Any],
    submission: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    from contestiq_api import practice

    problem_id = request["problem_id"]
    source, context = _trusted_context(caller, request)
    cf_created_dt = _epoch_time(submission["creation_time"])
    assigned_dt = _parse_time(assignment["assigned_at"])
    historical = cf_created_dt < assigned_dt
    completed_at = cf_created_dt.isoformat()
    verified_at = store._now()
    completion_id = str(uuid.uuid4())
    world = practice._selection_world(caller.get("handle"))
    visible = _server_visible_problem_ids(caller)
    daily_cap = practice._daily_cap_for_caller(caller)

    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT * FROM problem_completions WHERE user_id = ? AND problem_id = ?",
            (caller["user_id"], problem_id),
        ).fetchone()
        if existing is not None:
            return dict(existing), False

        conn.execute(
            """
            INSERT INTO problem_completions (
                completion_id, user_id, problem_id, completion_source,
                is_historical, codeforces_submission_id, codeforces_handle,
                contest_id, problem_index, verdict, programming_language,
                codeforces_created_at, verified_at, assignment_id, assigned_at,
                queue_source, queue_item_id, completed_at, xp_awarded,
                history_updated, daily_goal_updated, streak_updated,
                progress_updated, queue_refreshed, effects_applied_at
            ) VALUES (
                :completion_id, :user_id, :problem_id, 'codeforces_verified',
                :is_historical, :submission_id, :handle,
                :contest_id, :problem_index, 'OK', :language,
                :codeforces_created_at, :verified_at, :assignment_id, :assigned_at,
                :queue_source, :queue_item_id, :completed_at, 0,
                1, 0, 0, :progress_updated, 0, :effects_applied_at
            )
            """,
            {
                "completion_id": completion_id,
                "user_id": caller["user_id"],
                "problem_id": problem_id,
                "is_historical": 1 if historical else 0,
                "submission_id": int(submission["submission_id"]),
                "handle": store.canonical_handle(str(caller["handle"])),
                "contest_id": int(submission["contest_id"]),
                "problem_index": str(submission["problem_index"]),
                "language": submission.get("programming_language"),
                "codeforces_created_at": completed_at,
                "verified_at": verified_at,
                "assignment_id": assignment["assignment_id"],
                "assigned_at": assignment["assigned_at"],
                "queue_source": source,
                "queue_item_id": request.get("queue_item_id") if context else None,
                "completed_at": completed_at,
                "progress_updated": 0 if historical else 1,
                "effects_applied_at": verified_at,
            },
        )
        conn.execute(
            """
            UPDATE solo_problem_assignments
            SET status = 'completed', completion_id = ?
            WHERE assignment_id = ?
            """,
            (completion_id, assignment["assignment_id"]),
        )
        practice._mark_owned_items_completed(
            conn,
            user_id=caller["user_id"],
            verified_handle=caller.get("handle"),
            problem_id=problem_id,
        )
        if not historical:
            conn.execute(
                """
                INSERT OR IGNORE INTO product_events (
                    event_id, event_type, subject, properties, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    completion_id,
                    COMPLETION_EVENT,
                    caller["subject"],
                    json.dumps(
                        {
                            "completion_id": completion_id,
                            "problem_id": problem_id,
                            "completion_source": CODEFORCES_COMPLETION_SOURCE,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    # Rewards and streak/daily-goal effects happen when SolveX
                    # discovers the current solve. The historical truth remains
                    # `problem_completions.completed_at` above.
                    verified_at,
                ),
            )
            xp_awarded, daily_goal_updated, streak_updated = (
                practice._completion_event_effects_in_transaction(
                    conn,
                    caller=caller,
                    completion_id=completion_id,
                    daily_cap=daily_cap,
                )
            )
            _update_skill_evidence(
                conn,
                handle=str(caller["handle"]),
                problem_id=problem_id,
                practiced_at=int(submission["creation_time"]),
            )
        else:
            xp_awarded = 0
            daily_goal_updated = False
            streak_updated = False

        selection_failed = world is None
        continuation = None
        # Historical imports only remove/mark the solved item. They never
        # generate a new training task or continuation.
        if not historical and world is not None:
            try:
                candidate = practice._select_next(
                    conn,
                    world=world,
                    user_id=caller["user_id"],
                    problem_id=problem_id,
                    source=source,
                    context=context,
                    visible_problem_ids=visible,
                    guest_completed_problem_ids=set(),
                    require_private_pack=False,
                )
                continuation = practice._persist_continuation(
                    conn,
                    completion_id=completion_id,
                    user_id=caller["user_id"],
                    source=source,
                    source_queue_item_id=request.get("queue_item_id") if context else None,
                    candidate=candidate,
                )
            except Exception:
                selection_failed = True
        if continuation is not None:
            conn.execute(
                """
                UPDATE problem_completions
                SET xp_awarded = ?, daily_goal_updated = ?, streak_updated = ?,
                    queue_refreshed = 1, replacement_problem_id = ?,
                    replacement_queue_item_id = ?
                WHERE completion_id = ?
                """,
                (
                    xp_awarded,
                    1 if daily_goal_updated else 0,
                    1 if streak_updated else 0,
                    continuation["problem_id"],
                    continuation["recommendation_id"],
                    completion_id,
                ),
            )
        elif not historical:
            conn.execute(
                """
                UPDATE problem_completions
                SET xp_awarded = ?, daily_goal_updated = ?, streak_updated = ?
                WHERE completion_id = ?
                """,
                (
                    xp_awarded,
                    1 if daily_goal_updated else 0,
                    1 if streak_updated else 0,
                    completion_id,
                ),
            )
        if not historical and continuation is None and not selection_failed:
            # `_persist_continuation` writes an explicit exhausted row, so this
            # branch is defensive rather than a silent exhaustion claim.
            selection_failed = True
        row = conn.execute(
            "SELECT * FROM problem_completions WHERE completion_id = ?",
            (completion_id,),
        ).fetchone()
    assert row is not None
    return dict(row), True


def _repair_current_continuation(
    *,
    caller: dict[str, Any],
    request: dict[str, Any],
    completion: dict[str, Any],
) -> dict[str, Any]:
    """Retry an interrupted current-completion replacement idempotently.

    SolveX uses one canonical continuation feed across daily/retry/plan
    surfaces: source items are marked completed, while the persisted
    continuation carries the replacement and its source attribution. An
    explicit exhausted row is also a successful refresh.
    """
    from contestiq_api import practice

    if bool(completion.get("is_historical")) or bool(completion.get("queue_refreshed")):
        return completion
    world = practice._selection_world(caller.get("handle"))
    if world is None:
        return completion

    stored_request = {
        "problem_id": completion["problem_id"],
        "source": completion.get("queue_source") or "direct_arena",
        "queue_item_id": completion.get("queue_item_id"),
    }
    source, context = _trusted_context(caller, stored_request)
    visible = _server_visible_problem_ids(caller)
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute(
            "SELECT * FROM problem_completions WHERE completion_id = ? AND user_id = ?",
            (completion["completion_id"], caller["user_id"]),
        ).fetchone()
        if current is None or bool(current["is_historical"]) or bool(current["queue_refreshed"]):
            return dict(current) if current is not None else completion
        continuation = conn.execute(
            "SELECT * FROM practice_continuations WHERE completion_id = ?",
            (completion["completion_id"],),
        ).fetchone()
        if continuation is None:
            try:
                candidate = practice._select_next(
                    conn,
                    world=world,
                    user_id=caller["user_id"],
                    problem_id=completion["problem_id"],
                    source=source,
                    context=context,
                    visible_problem_ids=visible,
                    guest_completed_problem_ids=set(),
                    require_private_pack=False,
                )
                continuation = practice._persist_continuation(
                    conn,
                    completion_id=completion["completion_id"],
                    user_id=caller["user_id"],
                    source=source,
                    source_queue_item_id=completion.get("queue_item_id"),
                    candidate=candidate,
                )
            except Exception:
                return dict(current)
        conn.execute(
            """
            UPDATE problem_completions
            SET queue_refreshed = 1, replacement_problem_id = ?,
                replacement_queue_item_id = ?
            WHERE completion_id = ?
            """,
            (
                continuation["problem_id"],
                continuation["recommendation_id"],
                completion["completion_id"],
            ),
        )
        repaired = conn.execute(
            "SELECT * FROM problem_completions WHERE completion_id = ?",
            (completion["completion_id"],),
        ).fetchone()
    return dict(repaired) if repaired is not None else completion


def _remaining_seconds(until: str | None) -> int:
    if not until:
        return 0
    delta = (_parse_time(until) - _now_dt()).total_seconds()
    return max(0, int(delta + 0.999))


def check_codeforces(caller: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    problem = _problem(request["problem_id"])
    assignment, existing = _open_assignment(caller, request)
    if existing is not None:
        existing = _repair_current_continuation(
            caller=caller,
            request=request,
            completion=existing,
        )
        return _response(
            caller,
            problem_id=request["problem_id"],
            status="already_completed",
            message="Already completed. No duplicate rewards or history entries were created.",
            completion=existing,
            already_completed=True,
        )

    handle = handles.verified_handle_for_user(caller["user_id"])
    if handle is None:
        return _response(
            caller,
            problem_id=request["problem_id"],
            status="verification_required",
            message="Verify your Codeforces handle to track completion.",
        )

    contest_id = int(problem["contest_id"])
    problem_index = str(problem["problem_index"])
    cached = _relevant_submissions(handle, contest_id, problem_index)
    matched = _accepted(cached)
    matched_from_cache = matched is not None
    check_row: dict[str, Any] | None = None

    if matched is None:
        check_row, cooldown = _acquire_check(
            caller=caller,
            problem_id=request["problem_id"],
            handle=handle,
            assignment_id=assignment["assignment_id"],
        )
        if cooldown is not None:
            return _response(
                caller,
                problem_id=request["problem_id"],
                status="cooldown",
                message="Please wait before checking Codeforces again.",
                latest_verdict=cooldown.get("latest_verdict"),
                cooldown_seconds=_remaining_seconds(cooldown.get("cooldown_until")),
                next_check_at=cooldown.get("cooldown_until"),
            )
        assert check_row is not None
        try:
            stale, _fetched_at = _refresh_recent(handle)
        except CodeforcesClientError as exc:
            finalized_next_check_at = _finish_check(
                check_row["check_id"],
                result="upstream_error",
                response_source=None,
                latest=cached[0] if cached else None,
                error_code=exc.error_code,
            )
            return _response(
                caller,
                problem_id=request["problem_id"],
                status="unavailable",
                message="Codeforces status is temporarily unavailable. Your task remains unresolved.",
                latest_verdict=cached[0].get("verdict") if cached else None,
                cooldown_seconds=CHECK_COOLDOWN_SECONDS,
                next_check_at=finalized_next_check_at,
            )
        except Exception:
            finalized_next_check_at = _finish_check(
                check_row["check_id"],
                result="upstream_error",
                response_source=None,
                latest=cached[0] if cached else None,
                error_code="CODEFORCES_UNAVAILABLE",
            )
            return _response(
                caller,
                problem_id=request["problem_id"],
                status="unavailable",
                message="Codeforces status is temporarily unavailable. Your task remains unresolved.",
                latest_verdict=cached[0].get("verdict") if cached else None,
                cooldown_seconds=CHECK_COOLDOWN_SECONDS,
                next_check_at=finalized_next_check_at,
            )
        refreshed = _relevant_submissions(handle, contest_id, problem_index)
        matched = _accepted(refreshed)
        latest = refreshed[0] if refreshed else None
        if matched is None:
            if stale:
                finalized_next_check_at = _finish_check(
                    check_row["check_id"],
                    result="upstream_error",
                    response_source="cache",
                    latest=latest,
                    error_code="STALE_CACHE_NO_ACCEPTED",
                )
                return _response(
                    caller,
                    problem_id=request["problem_id"],
                    status="unavailable",
                    message="Codeforces could not be refreshed; cached data has no Accepted result yet.",
                    latest_verdict=latest.get("verdict") if latest else None,
                    cooldown_seconds=CHECK_COOLDOWN_SECONDS,
                    next_check_at=finalized_next_check_at,
                )
            finalized_next_check_at = _finish_check(
                check_row["check_id"],
                result="no_ok",
                response_source="codeforces_api",
                latest=latest,
            )
            return _response(
                caller,
                problem_id=request["problem_id"],
                status="pending",
                message="No verified Accepted submission was found for this exact problem.",
                latest_verdict=latest.get("verdict") if latest else None,
                cooldown_seconds=CHECK_COOLDOWN_SECONDS,
                next_check_at=finalized_next_check_at,
            )
    else:
        # Cached OK evidence was previously fetched server-side and is already
        # authoritative. Acquire an audit lease when no cooldown is active, but
        # never withhold a known Accepted result solely because of cooldown.
        check_row, _cooldown = _acquire_check(
            caller=caller,
            problem_id=request["problem_id"],
            handle=handle,
            assignment_id=assignment["assignment_id"],
        )

    assert matched is not None
    completion, recorded = _persist_codeforces_completion(
        caller={**caller, "handle": handle},
        request=request,
        assignment=assignment,
        submission=matched,
    )
    if not recorded:
        completion = _repair_current_continuation(
            caller={**caller, "handle": handle},
            request=request,
            completion=completion,
        )
    if check_row is not None:
        rows = _relevant_submissions(handle, contest_id, problem_index)
        _finish_check(
            check_row["check_id"],
            result="verified_ok",
            response_source="cache" if matched_from_cache else "codeforces_api",
            latest=rows[0] if rows else matched,
            matched=matched,
            completion_id=completion["completion_id"],
        )
    return _response(
        caller,
        problem_id=request["problem_id"],
        status="completed" if recorded else "already_completed",
        message=(
            "Verified Accepted on Codeforces. Completion and training progress were saved."
            if recorded and not bool(completion["is_historical"])
            else (
                "Historical Codeforces solve imported. No new XP, streak, or daily-goal credit was awarded."
                if recorded
                else "Already completed. No duplicate rewards or history entries were created."
            )
        ),
        latest_verdict="OK",
        completion=completion,
        already_completed=not recorded,
    )


def _json_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def history(
    caller: dict[str, Any],
    *,
    limit: int,
    offset: int,
    source: str = "all",
    historical: str = "all",
) -> dict[str, Any]:
    clauses = ["pc.user_id = ?"]
    params: list[Any] = [caller["user_id"]]
    if source in {PRACTICE_COMPLETION_SOURCE, CODEFORCES_COMPLETION_SOURCE}:
        clauses.append("pc.completion_source = ?")
        params.append(source)
    if historical == "current":
        clauses.append("pc.is_historical = 0")
    elif historical == "historical":
        clauses.append("pc.is_historical = 1")
    where = " AND ".join(clauses)

    with store.connect() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM problem_completions pc WHERE {where}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT pc.*, p.name, p.rating, p.tags
            FROM problem_completions pc
            JOIN problems p ON p.problem_key = pc.problem_id
            WHERE {where}
            ORDER BY pc.completed_at DESC, pc.completion_id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            if item["completion_source"] == PRACTICE_COMPLETION_SOURCE:
                attempts = conn.execute(
                    """
                    SELECT COUNT(*) FROM practice_submissions
                    WHERE user_id = ? AND problem_id = ? AND status != 'judging'
                    """,
                    (caller["user_id"], item["problem_id"]),
                ).fetchone()[0]
            else:
                attempts = conn.execute(
                    """
                    SELECT COUNT(*) FROM cf_submissions_normalized
                    WHERE handle = ? AND contest_id = ? AND problem_index = ?
                    """,
                    (item["codeforces_handle"], item["contest_id"], item["problem_index"]),
                ).fetchone()[0]
            index = str(item.get("problem_index") or "")
            contest_id = item.get("contest_id")
            if not contest_id or not index:
                problem = _problem(item["problem_id"])
                contest_id = problem["contest_id"]
                index = str(problem["problem_index"])
            items.append(
                {
                    "completion_id": item["completion_id"],
                    "problem_id": item["problem_id"],
                    "title": item.get("name") or item["problem_id"],
                    "rating": item.get("rating"),
                    "tags": _json_list(item.get("tags")),
                    "completion_source": item["completion_source"],
                    "historical": bool(item["is_historical"]),
                    "completed_at": item["completed_at"],
                    "verified_at": item.get("verified_at"),
                    "assigned_at": item.get("assigned_at"),
                    "codeforces_submission_id": item.get("codeforces_submission_id"),
                    "programming_language": item.get("programming_language"),
                    "attempts": int(attempts),
                    "queue_source": item.get("queue_source") or "direct_arena",
                    "xp_awarded": int(item.get("xp_awarded") or 0),
                    "official_url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
                    "arena_url": f"/arena?problem={item['problem_id']}",
                }
            )
    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "source": source if source in {PRACTICE_COMPLETION_SOURCE, CODEFORCES_COMPLETION_SOURCE} else "all",
        "historical": historical if historical in {"all", "current", "historical"} else "all",
        "items": items,
    }
