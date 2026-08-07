"""Authoritative SolveX Solo-practice judging and endless continuation.

Solo practice is deliberately separate from generic `/api/execute`, PvP duel
state, SkillTrace badges, and official Codeforces submission history. Only an
active, reviewed server-owned pack can produce a practice completion.
"""

from __future__ import annotations

import asyncio
import copy
import datetime as dt
import hashlib
import json
import sqlite3
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from contestiq_api import duels, entitlements, gamification, product_events
from contestiq_api.cfdata import planner, store
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

COMPLETION_MODE = "solvex_practice"
JUDGING_MODE = "solvex_practice"
PRACTICE_EVENT = "practice_problem_completed"
LANGUAGE_IDS = {"cpp17": 54, "python3": 71}
JUDGED_STATUSES = {
    "accepted",
    "wrong_answer",
    "compilation_error",
    "runtime_error",
    "time_limit",
    "memory_limit",
}
STATUS_IDS = {
    "accepted": 3,
    "wrong_answer": 4,
    "time_limit": 5,
    "compilation_error": 6,
    "runtime_error": 11,
    "memory_limit": 12,
}
STALE_JUDGING_MINUTES = 15
CancellationCheck = Callable[[], Awaitable[bool]]


class ClaimRevoked(RuntimeError):
    """The request lease was terminalized by another worker."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_json(value: Any, fallback: Any) -> Any:
    if not isinstance(value, str):
        return value if value is not None else fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _source_hash(source_code: str) -> str:
    return hashlib.sha256(source_code.encode("utf-8")).hexdigest()


def _client_request_hash(request: dict[str, Any]) -> str:
    """Stable idempotency fingerprint independent of mutable server packs."""
    canonical = {
        "problem_id": request["problem_id"],
        "language": request["language"],
        "source_hash": _source_hash(request["source_code"]),
        "source": request["source"],
        "queue_item_id": request.get("queue_item_id"),
        "handle": (
            store.canonical_handle(request["handle"])
            if request.get("handle")
            else None
        ),
        "visible_problem_ids": sorted(set(request.get("visible_problem_ids") or [])),
        "completed_problem_ids": sorted(set(request.get("completed_problem_ids") or [])),
    }
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _request_hash(
    request: dict[str, Any],
    *,
    pack: dict[str, Any],
    effective_source: str,
    context_handle: str | None,
) -> str:
    """Bind an idempotency key to every outcome/attribution-affecting input."""
    canonical = {
        "problem_id": request["problem_id"],
        "language": request["language"],
        "source_hash": _source_hash(request["source_code"]),
        "requested_source": request["source"],
        "effective_source": effective_source,
        "queue_item_id": request.get("queue_item_id"),
        "handle": store.canonical_handle(context_handle) if context_handle else None,
        "visible_problem_ids": sorted(set(request.get("visible_problem_ids") or [])),
        "completed_problem_ids": sorted(set(request.get("completed_problem_ids") or [])),
        "pack_id": pack["pack_id"],
        "pack_version": int(pack["version"]),
        "test_set_hash": pack["test_set_hash"],
    }
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _active_pack(problem_id: str) -> dict[str, Any]:
    """Load exactly one active pack whose problem identity matches the route payload."""
    duels.seed_builtin_duel_problem_packs()
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT dpp.*, p.name, p.rating, p.tags
            FROM duel_problem_packs dpp
            JOIN problems p ON p.problem_key = dpp.problem_id
            WHERE dpp.problem_id = ? AND dpp.active = 1
            ORDER BY dpp.version DESC
            LIMIT 1
            """,
            (problem_id,),
        ).fetchone()
    if row is None:
        raise APIError(
            "PRACTICE_TESTS_UNAVAILABLE",
            f"Problem {problem_id} does not have an active reviewed SolveX practice test pack.",
            409,
        )
    pack = dict(row)
    tests = duels._normalize_judge_tests(pack.get("judge_tests"))
    if (
        pack.get("problem_id") != problem_id
        or not tests
        or not duels._pack_has_complete_content(pack)
    ):
        raise APIError(
            "PRACTICE_TESTS_UNAVAILABLE",
            f"Problem {problem_id} does not have a complete reviewed SolveX practice test pack.",
            409,
        )
    pack["tests"] = tests
    pack["test_set_hash"] = duels._tests_hash(tests)
    return pack


def _canceled_outcome() -> dict[str, Any]:
    return {
        "status": "canceled",
        "status_id": None,
        "judged": False,
        "passed": False,
        "runtime_ms": None,
        "memory_kb": None,
        "stderr": "",
        "compile_output": "",
        "message": "Practice submission was canceled. No completion was recorded.",
    }


async def _judge_pack(
    pack: dict[str, Any],
    language: str,
    source_code: str,
    is_cancelled: CancellationCheck | None = None,
) -> dict[str, Any]:
    """Judge against only server-loaded tests; never accepts a caller oracle."""
    settings = get_settings()
    if not settings.judge0_base_url:
        return {
            "status": "service_error",
            "status_id": None,
            "judged": False,
            "passed": False,
            "runtime_ms": None,
            "memory_kb": None,
            "stderr": "",
            "compile_output": "",
            "message": "Practice judging is temporarily unavailable. No completion was recorded.",
        }

    from contestiq_api import judge0_client

    results: list[dict[str, Any]] = []
    try:
        for test in pack["tests"]:
            if is_cancelled is not None and await is_cancelled():
                return _canceled_outcome()
            result = await judge0_client.run_submission(
                base_url=settings.judge0_base_url,
                api_key=settings.judge0_api_key,
                api_host=settings.judge0_api_host,
                language_id=LANGUAGE_IDS[language],
                source_code=source_code,
                stdin=test["input"],
                expected_output=test["expected_output"],
            )
            results.append(result)
            status = str(result.get("status") or "error")
            if status not in JUDGED_STATUSES:
                return {
                    "status": "service_error",
                    "status_id": result.get("status_id"),
                    "judged": False,
                    "passed": False,
                    "runtime_ms": None,
                    "memory_kb": None,
                    "stderr": "",
                    "compile_output": "",
                    "message": "Practice judging could not produce a verdict. No completion was recorded.",
                }
            if not (status == "accepted" and bool(result.get("passed"))):
                break
        if is_cancelled is not None and await is_cancelled():
            return _canceled_outcome()
    except asyncio.CancelledError:
        raise
    except Exception:
        # Transport, timeout, malformed upstream payload, and service failures
        # are neutral infrastructure outcomes—not user-code verdicts.
        return {
            "status": "service_error",
            "status_id": None,
            "judged": False,
            "passed": False,
            "runtime_ms": None,
            "memory_kb": None,
            "stderr": "",
            "compile_output": "",
            "message": "Practice judging is temporarily unavailable. No completion was recorded.",
        }

    last = results[-1]
    passed = len(results) == len(pack["tests"]) and all(
        item.get("status") == "accepted" and bool(item.get("passed")) for item in results
    )
    status = "accepted" if passed else str(last.get("status") or "service_error")
    status_id = last.get("status_id")
    if not isinstance(status_id, int):
        status_id = STATUS_IDS.get(status)
    runtime_values = [
        int(item["time_ms"]) for item in results if isinstance(item.get("time_ms"), (int, float))
    ]
    memory_values = [
        int(item["memory_kb"]) for item in results if isinstance(item.get("memory_kb"), (int, float))
    ]
    if passed:
        message = (
            "All SolveX server practice tests passed. "
            "SolveX practice judging — not official Codeforces judging."
        )
    else:
        message = {
            "wrong_answer": "Wrong Answer on a SolveX server practice test.",
            "compilation_error": "Compilation Error during SolveX practice judging.",
            "runtime_error": "Runtime Error during SolveX practice judging.",
            "time_limit": "Time Limit Exceeded during SolveX practice judging.",
            "memory_limit": "Memory Limit Exceeded during SolveX practice judging.",
        }.get(status, "The solution did not pass SolveX practice judging.")
    # User code can echo hidden stdin to stderr, and compiler diagnostics often
    # echo source lines. Practice responses deliberately keep both empty so an
    # exact idempotent response can be persisted without retaining source code.
    return {
        "status": status,
        "status_id": status_id,
        "judged": True,
        "passed": passed,
        "runtime_ms": sum(runtime_values) or None,
        "memory_kb": max(memory_values, default=0) or None,
        "stderr": "",
        "compile_output": "",
        "message": message,
    }


def _gamification_snapshot(caller: dict[str, Any]) -> dict[str, Any]:
    from contestiq_api import auth

    user = auth.get_user(caller["user_id"])
    plan = entitlements.effective_plan(user)
    events = product_events.events_for_account(caller["user_id"])
    snapshot = gamification.build_snapshot(caller["subject"], plan, events)
    return {
        "xp_total": snapshot["xp_total"],
        "streak": snapshot["streak"]["current"],
    }


def _completion_xp_awarded(caller: dict[str, Any], completion_id: str) -> int:
    """Replay XP attribution and return only this completion event's award."""
    from contestiq_api import auth

    user = auth.get_user(caller["user_id"])
    daily_cap = gamification.resolve_daily_cap(entitlements.effective_plan(user))
    events = gamification._meaningful(product_events.events_for_account(caller["user_id"]))
    awarded_keys: dict[Any, set[tuple[str, str | None]]] = {}
    day_totals: dict[Any, int] = {}
    for event in events:
        day = gamification._event_date(event)
        key = gamification._xp_award_key(event)
        seen = awarded_keys.setdefault(day, set())
        raw = gamification.XP_RULES[event["event_type"]]
        if key in seen:
            awarded = 0
        else:
            awarded = min(raw, max(0, daily_cap - day_totals.get(day, 0)))
            seen.add(key)
            day_totals[day] = day_totals.get(day, 0) + awarded
        properties = event.get("properties")
        if (
            event.get("event_type") == PRACTICE_EVENT
            and isinstance(properties, dict)
            and properties.get("completion_id") == completion_id
        ):
            return awarded
    return 0


def _resolve_queue_context(
    queue_item_id: str | None,
    *,
    caller: dict[str, Any] | None,
    public_handle: str | None,
) -> dict[str, Any] | None:
    if not queue_item_id:
        return None
    with store.connect() as conn:
        item = conn.execute(
            """
            SELECT ri.item_id, ri.problem_id, ri.skill_id, ri.target_rating, ri.mode,
                   rr.handle, rr.run_id AS container_id
            FROM recommendation_items ri
            JOIN recommendation_runs rr ON rr.run_id = ri.run_id
            WHERE ri.item_id = ?
            """,
            (queue_item_id,),
        ).fetchone()
        kind = "daily"
        if item is None:
            item = conn.execute(
                """
                SELECT tpi.item_id, tpi.problem_id, tpi.skill_id, tpi.target_rating, tpi.mode,
                       tp.handle, tp.plan_id AS container_id, tp.plan_type
                FROM training_plan_items tpi
                JOIN training_plans tp ON tp.plan_id = tpi.plan_id
                WHERE tpi.item_id = ?
                """,
                (queue_item_id,),
            ).fetchone()
            kind = "plan"
        if item is None and caller is not None:
            item = conn.execute(
                """
                SELECT recommendation_id AS item_id, problem_id, target_skill AS skill_id,
                       rating AS target_rating, source, user_id
                FROM practice_continuations
                WHERE recommendation_id = ? AND user_id = ?
                """,
                (queue_item_id, caller["user_id"]),
            ).fetchone()
            kind = "continuation"
        if item is None:
            return None
        context = dict(item)

        owner_handle = context.get("handle")
        caller_handle = caller.get("handle") if caller else None
        if owner_handle:
            canonical_owner = store.canonical_handle(owner_handle)
            if caller is not None:
                # Account persistence may only borrow a queue/plan context
                # owned by the caller's verified handle. Unverified accounts
                # fall back to direct request context.
                if (
                    not caller_handle
                    or store.canonical_handle(caller_handle) != canonical_owner
                ):
                    return None
            elif public_handle and store.canonical_handle(public_handle) != canonical_owner:
                return None

        if kind == "daily":
            rows = conn.execute(
                "SELECT problem_id FROM recommendation_items WHERE run_id = ?",
                (context["container_id"],),
            ).fetchall()
            context["source"] = "daily_queue"
        elif kind == "plan":
            rows = conn.execute(
                "SELECT problem_id FROM training_plan_items WHERE plan_id = ?",
                (context["container_id"],),
            ).fetchall()
            context["source"] = (
                "fourteen_day_plan" if context.get("plan_type") == "14_day" else "seven_day_plan"
            )
        else:
            rows = []
        context["container_problem_ids"] = {row["problem_id"] for row in rows}
        return context


def _empty_world() -> dict[str, Any]:
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT p.problem_key, p.contest_id, p.rating, p.name, m.skill_id, m.weight
            FROM problems p
            JOIN problem_skill_map m ON m.problem_id = p.problem_key
            """
        ).fetchall()
    display_ready = store.list_display_ready_problem_ids(
        [dict(row)["problem_key"] for row in rows]
    )
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        item = dict(row)
        if item["problem_key"] not in display_ready:
            continue
        by_skill.setdefault(item["skill_id"], []).append(item)
    return {
        "handle": None,
        "profiles": {},
        "cutoff": 0,
        "solved": {},
        "recently_attempted": set(),
        "candidates_by_skill": by_skill,
        "suppressed": set(),
    }


def _selection_world(handle: str | None) -> dict[str, Any] | None:
    if not handle:
        return _empty_world()
    try:
        return planner._load_world(store.canonical_handle(handle))
    except Exception:
        # Never replace a failed personalized world with an unrestricted one:
        # that would drop solved/recent/suppressed exclusions. Completion still
        # succeeds, while continuation is reported as temporarily unavailable.
        return None


def _active_pack_problem_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT dpp.*
        FROM duel_problem_packs dpp
        JOIN problems p ON p.problem_key = dpp.problem_id
        WHERE dpp.active = 1
        ORDER BY dpp.problem_id, dpp.version DESC
        """
    ).fetchall()
    latest_by_problem: dict[str, dict[str, Any]] = {}
    for row in rows:
        pack = dict(row)
        latest_by_problem.setdefault(pack["problem_id"], pack)
    usable: set[str] = set()
    for problem_id, pack in latest_by_problem.items():
        if (
            duels._normalize_judge_tests(pack.get("judge_tests"))
            and duels._pack_has_complete_content(pack)
        ):
            usable.add(problem_id)
    # Continuations open Solo Arena via /api/v1/problems/{id}; require display-ready.
    return store.list_display_ready_problem_ids(list(usable))


def _problem_skills(conn: sqlite3.Connection, problem_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT skill_id
        FROM problem_skill_map
        WHERE problem_id = ?
        ORDER BY is_primary DESC, weight DESC, skill_id
        """,
        (problem_id,),
    ).fetchall()
    return [row["skill_id"] for row in rows]


def _select_next(
    conn: sqlite3.Connection,
    *,
    world: dict[str, Any],
    user_id: str | None,
    problem_id: str,
    source: str,
    context: dict[str, Any] | None,
    visible_problem_ids: set[str],
    guest_completed_problem_ids: set[str],
) -> dict[str, Any] | None:
    exclusions = {problem_id, *visible_problem_ids}
    exclusions.update(context.get("container_problem_ids", set()) if context else set())
    if user_id:
        completion_rows = conn.execute(
            "SELECT problem_id FROM practice_completions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        continuation_rows = conn.execute(
            "SELECT problem_id FROM practice_continuations WHERE user_id = ? AND problem_id IS NOT NULL",
            (user_id,),
        ).fetchall()
        exclusions.update(row["problem_id"] for row in completion_rows)
        exclusions.update(row["problem_id"] for row in continuation_rows)
    else:
        exclusions.update(guest_completed_problem_ids)

    usable_ids = _active_pack_problem_ids(conn)
    scoped_world = copy.deepcopy(world)
    scoped_world["suppressed"] = set(scoped_world.get("suppressed", set())) | exclusions
    scoped_world["recently_attempted"] = set(scoped_world.get("recently_attempted", set()))
    scoped_world["solved"] = dict(scoped_world.get("solved", {}))
    scoped_world["candidates_by_skill"] = {
        skill: [row for row in rows if row["problem_key"] in usable_ids]
        for skill, rows in scoped_world.get("candidates_by_skill", {}).items()
    }

    current = conn.execute(
        "SELECT rating FROM problems WHERE problem_key = ?",
        (problem_id,),
    ).fetchone()
    target = context.get("target_rating") if context else None
    if not isinstance(target, int):
        target = int(current["rating"]) if current and current["rating"] is not None else 1200
    mode = str(context.get("mode") or "core_repair") if context else "core_repair"
    if mode not in planner.MODE_OFFSETS:
        mode = "core_repair"

    skill_order: list[str] = []
    preferred = context.get("skill_id") if context else None
    if isinstance(preferred, str) and preferred:
        skill_order.append(preferred)
    skill_order.extend(_problem_skills(conn, problem_id))
    skill_order.extend(sorted(scoped_world["candidates_by_skill"]))
    skill_order = list(dict.fromkeys(skill_order))

    for skill_id in skill_order:
        state = planner.SelectionState()
        state.used_problems.update(exclusions)
        picked = planner._pick(
            scoped_world,
            state,
            skill_id,
            mode,
            target,
            quality_conn=conn,
        )
        if picked is None:
            continue
        chosen_id = picked["problem"]["problem_key"]
        problem = conn.execute(
            "SELECT problem_key, name, rating, tags FROM problems WHERE problem_key = ?",
            (chosen_id,),
        ).fetchone()
        if problem is None:
            continue
        tags = _parse_json(problem["tags"], [])
        if not isinstance(tags, list):
            tags = []
        return {
            "problem_id": chosen_id,
            "name": problem["name"] or chosen_id,
            "rating": problem["rating"],
            "tags": [tag for tag in tags if isinstance(tag, str)],
            "target_skill": skill_id,
            "reason": (
                f"Continue {source.replace('_', ' ')} practice on {skill_id} "
                f"near rating {target}; selected from reviewed SolveX-judgeable problems."
            ),
        }
    return None


def _continuation_payload(row: dict[str, Any] | sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    if item.get("status") != "active" or not item.get("problem_id"):
        return None
    tags = _parse_json(item.get("tags"), [])
    return {
        "recommendation_id": item["recommendation_id"],
        "problem_id": item["problem_id"],
        "name": item.get("name") or item["problem_id"],
        "rating": item.get("rating"),
        "tags": tags if isinstance(tags, list) else [],
        "target_skill": item.get("target_skill"),
        "reason": item.get("reason") or "Continue with the next SolveX practice problem.",
        "source": item["source"],
        "queue_item_id": item["recommendation_id"],
    }


def _queue_payload(row: dict[str, Any] | sqlite3.Row | None, *, already_completed: bool = False) -> dict[str, Any]:
    if row is not None and bool(row["exhausted"]):
        return {
            "exhausted": True,
            "message": "No unseen server-judgeable practice problem currently matches these constraints.",
        }
    if row is not None and row["status"] == "active":
        return {"exhausted": False, "message": "A continuation problem is ready."}
    if already_completed:
        return {
            "exhausted": False,
            "message": "This problem was already completed; no duplicate continuation was generated.",
        }
    return {"exhausted": False, "message": "Complete this problem to continue training."}


def _context_handle(
    caller: dict[str, Any] | None,
    public_handle: str | None,
    context: dict[str, Any] | None,
) -> str | None:
    if caller and caller.get("handle"):
        return str(caller["handle"])
    if context and context.get("handle"):
        return str(context["handle"])
    return public_handle


def _attempt_is_stale(created_at: str) -> bool:
    try:
        parsed = dt.datetime.fromisoformat(created_at)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return True
    return dt.datetime.now(dt.timezone.utc) - parsed >= dt.timedelta(
        minutes=STALE_JUDGING_MINUTES
    )


def _recover_terminal_response(
    existing: dict[str, Any],
    caller: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct and cache a terminal response after a process crash."""
    outcome = {
        "status": existing["status"],
        "status_id": existing.get("status_id"),
        "judged": bool(existing.get("judged")),
        "passed": bool(existing.get("passed")),
        "runtime_ms": existing.get("runtime_ms"),
        "memory_kb": existing.get("memory_kb"),
        "stderr": "",
        "compile_output": "",
        "message": existing.get("message") or "Practice judging finished.",
    }
    request = {
        "request_id": existing["request_id"],
        "problem_id": existing["problem_id"],
    }
    response = _base_response(
        request=request,
        submission_id=existing["submission_id"],
        outcome=outcome,
        progress=_gamification_snapshot(caller),
    )
    completion_id = existing.get("completion_id")
    if outcome["passed"] and completion_id:
        with store.connect() as conn:
            completion = conn.execute(
                "SELECT * FROM practice_completions WHERE completion_id = ? AND user_id = ?",
                (completion_id, caller["user_id"]),
            ).fetchone()
            continuation = conn.execute(
                "SELECT * FROM practice_continuations WHERE completion_id = ? AND user_id = ?",
                (completion_id, caller["user_id"]),
            ).fetchone()
            attempt_count = conn.execute(
                """
                SELECT COUNT(*) FROM practice_submissions
                WHERE user_id = ? AND problem_id = ? AND status != 'judging'
                """,
                (caller["user_id"], existing["problem_id"]),
            ).fetchone()[0]
        if completion is not None:
            recorded = completion["first_submission_id"] == existing["submission_id"]
            response["completion"] = {
                "completion_id": completion["completion_id"],
                "persistent": True,
                "recorded": recorded,
                "already_completed": not recorded,
                "completed_at": completion["completed_at"],
                "xp_awarded": (
                    _completion_xp_awarded(caller, completion["completion_id"])
                    if recorded
                    else 0
                ),
                "attempt_count": attempt_count,
                "source": completion["source"],
            }
            response["next_problem"] = _continuation_payload(continuation)
            response["queue"] = (
                _queue_payload(continuation, already_completed=not recorded)
                if continuation is not None
                else {
                    "exhausted": False,
                    "message": (
                        "Completion was saved, but continuation selection is temporarily unavailable."
                    ),
                }
            )
    else:
        response["queue"] = {
            "exhausted": False,
            "message": (
                "Judging was not completed; the training queue was unchanged."
                if not outcome["judged"]
                else "The problem remains available for another attempt."
            ),
        }
    return _store_response(existing["submission_id"], response)


def _resolve_existing_attempt(
    existing: dict[str, Any],
    *,
    caller: dict[str, Any],
    client_request_hash: str,
) -> dict[str, Any]:
    if existing["client_request_hash"] != client_request_hash:
        raise APIError(
            "IDEMPOTENCY_KEY_REUSED",
            "This request_id was already used for a different practice submission.",
            409,
        )
    response = _parse_json(existing.get("response_json"), None)
    if isinstance(response, dict):
        return response
    if existing["status"] != "judging":
        return _recover_terminal_response(existing, caller)
    if not _attempt_is_stale(existing["created_at"]):
        raise APIError(
            "PRACTICE_SUBMISSION_IN_PROGRESS",
            "This practice submission request is already being judged.",
            409,
        )

    stale_outcome = _canceled_outcome()
    stale_outcome["status"] = "service_error"
    stale_outcome["message"] = (
        "The previous judging attempt did not finish. "
        "No completion was recorded; submit again with a new request_id."
    )
    with store.connect() as conn:
        cursor = conn.execute(
            """
            UPDATE practice_submissions
            SET status = 'service_error', status_id = NULL, judged = 0,
                passed = 0, runtime_ms = NULL, memory_kb = NULL,
                message = ?, judged_at = ?, claim_token = NULL
            WHERE submission_id = ? AND status = 'judging' AND response_json IS NULL
            """,
            (stale_outcome["message"], store._now(), existing["submission_id"]),
        )
        current = conn.execute(
            "SELECT * FROM practice_submissions WHERE submission_id = ?",
            (existing["submission_id"],),
        ).fetchone()
    if current is None:
        raise APIError("PRACTICE_SUBMISSION_CONFLICT", "Practice submission disappeared.", 409)
    current_dict = dict(current)
    if cursor.rowcount == 1 or current_dict["status"] != "judging":
        return _resolve_existing_attempt(
            current_dict,
            caller=caller,
            client_request_hash=client_request_hash,
        )
    # The original worker still owns the claim.
    raise APIError(
        "PRACTICE_SUBMISSION_IN_PROGRESS",
        "This practice submission request is already being judged.",
        409,
    )


def _preflight_replay(
    caller: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any] | None:
    with store.connect() as conn:
        existing = conn.execute(
            "SELECT * FROM practice_submissions WHERE user_id = ? AND request_id = ?",
            (caller["user_id"], request["request_id"]),
        ).fetchone()
    if existing is None:
        return None
    return _resolve_existing_attempt(
        dict(existing),
        caller=caller,
        client_request_hash=_client_request_hash(request),
    )


def _claim_attempt(
    *,
    caller: dict[str, Any],
    request: dict[str, Any],
    pack: dict[str, Any],
    effective_source: str,
    context_handle: str | None,
) -> tuple[str, dict[str, Any] | None, str | None]:
    submission_id = str(uuid.uuid4())
    claim_token = str(uuid.uuid4())
    source_hash = _source_hash(request["source_code"])
    client_request_hash = _client_request_hash(request)
    request_hash = _request_hash(
        request,
        pack=pack,
        effective_source=effective_source,
        context_handle=context_handle,
    )
    with store.connect() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO practice_submissions (
                submission_id, user_id, request_id, claim_token, problem_id, pack_id, pack_version,
                test_set_hash, language, source, source_hash, queue_item_id,
                client_request_hash, request_hash, handle_context, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'judging', ?)
            """,
            (
                submission_id,
                caller["user_id"],
                request["request_id"],
                claim_token,
                request["problem_id"],
                pack["pack_id"],
                int(pack["version"]),
                pack["test_set_hash"],
                request["language"],
                effective_source,
                source_hash,
                request.get("queue_item_id"),
                client_request_hash,
                request_hash,
                store.canonical_handle(context_handle) if context_handle else None,
                store._now(),
            ),
        )
        if cursor.rowcount == 1:
            return submission_id, None, claim_token
        existing = conn.execute(
            "SELECT * FROM practice_submissions WHERE user_id = ? AND request_id = ?",
            (caller["user_id"], request["request_id"]),
        ).fetchone()
    if existing is None:
        raise APIError("PRACTICE_SUBMISSION_CONFLICT", "Could not reserve this submission request.", 409)
    existing = dict(existing)
    return (
        existing["submission_id"],
        _resolve_existing_attempt(
            existing,
            caller=caller,
            client_request_hash=client_request_hash,
        ),
        None,
    )


def _set_attempt_verdict(
    conn: sqlite3.Connection,
    *,
    submission_id: str,
    claim_token: str,
    outcome: dict[str, Any],
    completion_id: str | None = None,
) -> bool:
    cursor = conn.execute(
        """
        UPDATE practice_submissions
        SET status = ?, status_id = ?, judged = ?, passed = ?, runtime_ms = ?,
            memory_kb = ?, message = ?, completion_id = ?, judged_at = ?,
            claim_token = NULL
        WHERE submission_id = ? AND status = 'judging' AND claim_token = ?
        """,
        (
            outcome["status"],
            outcome.get("status_id"),
            1 if outcome["judged"] else 0,
            1 if outcome["passed"] else 0,
            outcome.get("runtime_ms"),
            outcome.get("memory_kb"),
            outcome["message"],
            completion_id,
            store._now(),
            submission_id,
            claim_token,
        ),
    )
    return cursor.rowcount == 1


def _store_response(submission_id: str, response: dict[str, Any]) -> dict[str, Any]:
    """Persist and return one canonical terminal response.

    A terminal verdict and its response cache are necessarily separate for
    crash recovery. Serializing the first valid cache write under a SQLite
    write lock makes concurrent recovery/original workers return the same
    response instead of overwriting each other's progress snapshots.
    """
    durable = copy.deepcopy(response)
    # Defense in depth if client diagnostics are reintroduced later.
    durable["stderr"] = ""
    durable["compile_output"] = ""
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT response_json FROM practice_submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("practice submission disappeared before response finalization")
        existing = _parse_json(row["response_json"], None)
        if isinstance(existing, dict):
            return existing
        conn.execute(
            "UPDATE practice_submissions SET response_json = ? WHERE submission_id = ?",
            (_canonical_json(durable), submission_id),
        )
    return durable


def _mark_owned_items_completed(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    verified_handle: str | None,
    problem_id: str,
) -> None:
    conn.execute(
        """
        UPDATE practice_continuations
        SET status = 'completed'
        WHERE user_id = ? AND problem_id = ? AND status = 'active'
        """,
        (user_id, problem_id),
    )
    if not verified_handle:
        return
    handle = store.canonical_handle(verified_handle)
    conn.execute(
        """
        UPDATE recommendation_items
        SET item_status = 'completed'
        WHERE problem_id = ?
          AND run_id IN (SELECT run_id FROM recommendation_runs WHERE handle = ?)
        """,
        (problem_id, handle),
    )
    conn.execute(
        """
        UPDATE training_plan_items
        SET item_status = 'completed'
        WHERE problem_id = ?
          AND plan_id IN (SELECT plan_id FROM training_plans WHERE handle = ?)
        """,
        (problem_id, handle),
    )


def _persist_continuation(
    conn: sqlite3.Connection,
    *,
    completion_id: str,
    user_id: str,
    source: str,
    source_queue_item_id: str | None,
    candidate: dict[str, Any] | None,
) -> sqlite3.Row:
    recommendation_id = str(uuid.uuid4())
    exhausted = candidate is None
    conn.execute(
        """
        INSERT OR IGNORE INTO practice_continuations (
            recommendation_id, completion_id, user_id, source, source_queue_item_id,
            problem_id, name, rating, tags, target_skill, reason, status,
            exhausted, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation_id,
            completion_id,
            user_id,
            source,
            source_queue_item_id,
            candidate.get("problem_id") if candidate else None,
            candidate.get("name") if candidate else None,
            candidate.get("rating") if candidate else None,
            _canonical_json(candidate.get("tags", [])) if candidate else "[]",
            candidate.get("target_skill") if candidate else None,
            candidate.get("reason") if candidate else None,
            "exhausted" if exhausted else "active",
            1 if exhausted else 0,
            store._now(),
        ),
    )
    row = conn.execute(
        "SELECT * FROM practice_continuations WHERE completion_id = ?",
        (completion_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("practice continuation was not persisted")
    return row


def _monotonic_completion_time(
    conn: sqlite3.Connection,
    *,
    user_id: str,
) -> str:
    """Timestamp practice events in write-lock order for deterministic XP replay."""
    now = dt.datetime.now(dt.timezone.utc)
    row = conn.execute(
        "SELECT MAX(completed_at) FROM practice_completions WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    latest_value = row[0] if row else None
    if latest_value:
        try:
            latest = dt.datetime.fromisoformat(latest_value)
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=dt.timezone.utc)
            if now <= latest:
                now = latest + dt.timedelta(microseconds=1)
        except (TypeError, ValueError):
            pass
    return now.isoformat()


def _complete_authenticated(
    *,
    caller: dict[str, Any],
    request: dict[str, Any],
    submission_id: str,
    claim_token: str,
    outcome: dict[str, Any],
    source: str,
    context: dict[str, Any] | None,
    world: dict[str, Any] | None,
) -> dict[str, Any]:
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            """
            SELECT * FROM practice_completions
            WHERE user_id = ? AND problem_id = ? AND completion_mode = ?
            """,
            (caller["user_id"], request["problem_id"], COMPLETION_MODE),
        ).fetchone()
        recorded = existing is None
        if existing is not None:
            completion_id = existing["completion_id"]
            completed_at = existing["completed_at"]
            source = existing["source"]
        else:
            completion_id = str(uuid.uuid4())
            completed_at = _monotonic_completion_time(
                conn,
                user_id=caller["user_id"],
            )

        if not _set_attempt_verdict(
            conn,
            submission_id=submission_id,
            claim_token=claim_token,
            outcome=outcome,
            completion_id=completion_id,
        ):
            raise ClaimRevoked(submission_id)

        if recorded:
            conn.execute(
                """
                INSERT INTO practice_completions (
                    completion_id, user_id, problem_id, completion_mode,
                    first_submission_id, source, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    completion_id,
                    caller["user_id"],
                    request["problem_id"],
                    COMPLETION_MODE,
                    submission_id,
                    source,
                    completed_at,
                ),
            )

        continuation = conn.execute(
            "SELECT * FROM practice_continuations WHERE completion_id = ?",
            (completion_id,),
        ).fetchone()
        selection_failed = False
        if recorded:
            _mark_owned_items_completed(
                conn,
                user_id=caller["user_id"],
                verified_handle=caller.get("handle"),
                problem_id=request["problem_id"],
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO product_events (
                    event_id, event_type, subject, properties, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    completion_id,
                    PRACTICE_EVENT,
                    caller["subject"],
                    _canonical_json(
                        {
                            "completion_id": completion_id,
                            "problem_id": request["problem_id"],
                            "source": source,
                        }
                    ),
                    completed_at,
                ),
            )

        if continuation is None:
            if world is None:
                selection_failed = True
            else:
                try:
                    candidate = _select_next(
                        conn,
                        world=world,
                        user_id=caller["user_id"],
                        problem_id=request["problem_id"],
                        source=source,
                        context=context,
                        visible_problem_ids=set(request.get("visible_problem_ids") or []),
                        guest_completed_problem_ids=set(),
                    )
                except Exception:
                    selection_failed = True
            if not selection_failed:
                continuation = _persist_continuation(
                    conn,
                    completion_id=completion_id,
                    user_id=caller["user_id"],
                    source=source,
                    source_queue_item_id=request.get("queue_item_id"),
                    candidate=candidate,
                )

        attempt_count = conn.execute(
            """
            SELECT COUNT(*) FROM practice_submissions
            WHERE user_id = ? AND problem_id = ? AND status != 'judging'
            """,
            (caller["user_id"], request["problem_id"]),
        ).fetchone()[0]

    return {
        "completion_id": completion_id,
        "persistent": True,
        "recorded": recorded,
        "already_completed": not recorded,
        "completed_at": completed_at,
        "attempt_count": attempt_count,
        "source": source,
        "continuation": dict(continuation) if continuation is not None else None,
        "selection_failed": selection_failed,
    }


def _base_response(
    *,
    request: dict[str, Any],
    submission_id: str,
    outcome: dict[str, Any],
    progress: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "problem_id": request["problem_id"],
        "submission_id": submission_id,
        "status": outcome["status"],
        "status_id": outcome.get("status_id"),
        "judging_mode": JUDGING_MODE,
        "judged": outcome["judged"],
        "passed": outcome["passed"],
        "runtime_ms": outcome.get("runtime_ms"),
        "memory_kb": outcome.get("memory_kb"),
        "message": outcome["message"],
        "stderr": outcome.get("stderr") or "",
        "compile_output": outcome.get("compile_output") or "",
        "completion": None,
        "progress": progress,
        "next_problem": None,
        "queue": _queue_payload(None),
    }


async def submit(
    request: dict[str, Any],
    caller: dict[str, Any] | None,
    is_cancelled: CancellationCheck | None = None,
) -> dict[str, Any]:
    if caller:
        replay = _preflight_replay(caller, request)
        if replay is not None:
            return replay
    pack = _active_pack(request["problem_id"])
    context = _resolve_queue_context(
        request.get("queue_item_id"),
        caller=caller,
        public_handle=request.get("handle"),
    )
    if context and context.get("problem_id") != request["problem_id"]:
        context = None
    effective_source = str(context.get("source") if context else request["source"])
    handle = _context_handle(caller, request.get("handle"), context)
    claim_token: str | None = None

    if caller:
        submission_id, replay, claim_token = _claim_attempt(
            caller=caller,
            request=request,
            pack=pack,
            effective_source=effective_source,
            context_handle=handle,
        )
        if replay is not None:
            return replay
        if claim_token is None:
            raise RuntimeError("new practice submission did not receive a claim token")
    else:
        submission_id = str(uuid.uuid4())

    try:
        outcome = await _judge_pack(
            pack,
            request["language"],
            request["source_code"],
            is_cancelled=is_cancelled,
        )
    except asyncio.CancelledError:
        if caller:
            with store.connect() as conn:
                _set_attempt_verdict(
                    conn,
                    submission_id=submission_id,
                    claim_token=claim_token,
                    outcome=_canceled_outcome(),
                )
        raise
    progress_now = _gamification_snapshot(caller) if caller else None
    response = _base_response(
        request=request,
        submission_id=submission_id,
        outcome=outcome,
        progress=progress_now,
    )

    if not outcome["passed"]:
        if caller:
            with store.connect() as conn:
                finalized = _set_attempt_verdict(
                    conn,
                    submission_id=submission_id,
                    claim_token=claim_token,
                    outcome=outcome,
                )
            if not finalized:
                replay = _preflight_replay(caller, request)
                if replay is None:
                    raise ClaimRevoked(submission_id)
                return replay
            response["progress"] = _gamification_snapshot(caller)
        response["queue"] = {
            "exhausted": False,
            "message": (
                "Judging was not completed; the training queue was unchanged."
                if not outcome["judged"]
                else "The problem remains available for another attempt."
            ),
        }
        if caller:
            return _store_response(submission_id, response)
        return response

    world = _selection_world(handle)
    if is_cancelled is not None and await is_cancelled():
        outcome = _canceled_outcome()
        response = _base_response(
            request=request,
            submission_id=submission_id,
            outcome=outcome,
            progress=_gamification_snapshot(caller) if caller else None,
        )
        response["queue"] = {
            "exhausted": False,
            "message": "The canceled submission did not change the training queue.",
        }
        if caller:
            with store.connect() as conn:
                finalized = _set_attempt_verdict(
                    conn,
                    submission_id=submission_id,
                    claim_token=claim_token,
                    outcome=outcome,
                )
            if not finalized:
                replay = _preflight_replay(caller, request)
                if replay is None:
                    raise ClaimRevoked(submission_id)
                return replay
            return _store_response(submission_id, response)
        return response
    if caller:
        try:
            completion = _complete_authenticated(
                caller=caller,
                request=request,
                submission_id=submission_id,
                claim_token=claim_token,
                outcome=outcome,
                source=effective_source,
                context=context,
                world=world,
            )
        except ClaimRevoked:
            replay = _preflight_replay(caller, request)
            if replay is None:
                raise
            return replay
        progress_after = _gamification_snapshot(caller)
        xp_awarded = (
            _completion_xp_awarded(caller, completion["completion_id"])
            if completion["recorded"]
            else 0
        )
        continuation = completion.pop("continuation")
        selection_failed = completion.pop("selection_failed")
        response["completion"] = {**completion, "xp_awarded": xp_awarded}
        response["progress"] = progress_after
        response["next_problem"] = _continuation_payload(continuation)
        response["queue"] = (
            {
                "exhausted": False,
                "message": (
                    "Completion was saved, but continuation selection is temporarily unavailable."
                ),
            }
            if selection_failed
            else _queue_payload(
                continuation,
                already_completed=response["completion"]["already_completed"],
            )
        )
        return _store_response(submission_id, response)

    # Guests receive the same authoritative server verdict, but no backend
    # identity, completion, product event, or continuation row is invented.
    with store.connect() as conn:
        selection_failed = world is None
        candidate = None
        if world is not None:
            try:
                candidate = _select_next(
                    conn,
                    world=world,
                    user_id=None,
                    problem_id=request["problem_id"],
                    source=effective_source,
                    context=context,
                    visible_problem_ids=set(request.get("visible_problem_ids") or []),
                    guest_completed_problem_ids=set(request.get("completed_problem_ids") or []),
                )
            except Exception:
                selection_failed = True
    completed_at = store._now()
    response["completion"] = {
        "persistent": False,
        "recorded": False,
        "already_completed": False,
        "completed_at": completed_at,
        "xp_awarded": 0,
        "attempt_count": 1,
        "source": effective_source,
    }
    if selection_failed:
        response["queue"] = {
            "exhausted": False,
            "message": "Continuation selection is temporarily unavailable. Try again shortly.",
        }
    elif candidate:
        recommendation_id = str(uuid.uuid4())
        response["next_problem"] = {
            "recommendation_id": recommendation_id,
            **candidate,
            "source": effective_source,
            "queue_item_id": recommendation_id,
        }
        response["queue"] = {"exhausted": False, "message": "A guest continuation problem is ready."}
    else:
        response["queue"] = {
            "exhausted": True,
            "message": "No unseen server-judgeable practice problem currently matches these constraints.",
        }
    return response


def progress(user_id: str) -> dict[str, Any]:
    with store.connect() as conn:
        completions = conn.execute(
            """
            SELECT pc.completion_id, pc.problem_id, pc.completion_mode,
                   pc.first_submission_id AS submission_id, pc.source,
                   pc.completed_at,
                   (SELECT COUNT(*) FROM practice_submissions ps
                    WHERE ps.user_id = pc.user_id
                      AND ps.problem_id = pc.problem_id
                      AND ps.status != 'judging') AS attempt_count
            FROM practice_completions pc
            WHERE pc.user_id = ?
            ORDER BY pc.completed_at, pc.problem_id
            """,
            (user_id,),
        ).fetchall()
        continuations = conn.execute(
            """
            SELECT * FROM practice_continuations
            WHERE user_id = ?
            ORDER BY created_at, recommendation_id
            """,
            (user_id,),
        ).fetchall()
    completion_items = [dict(row) for row in completions]
    continuation_items = [dict(row) for row in continuations]
    active_continuations = [
        row
        for row in continuation_items
        if row["status"] == "active" and not bool(row["exhausted"])
    ]
    latest_completion_id = (
        completion_items[-1]["completion_id"] if completion_items else None
    )
    latest_continuation = next(
        (
            row
            for row in reversed(continuation_items)
            if row["completion_id"] == latest_completion_id
        ),
        None,
    )
    if active_continuations:
        queue = {
            "exhausted": False,
            "message": "A continuation problem is ready.",
        }
    elif latest_continuation is not None and bool(latest_continuation["exhausted"]):
        queue = _queue_payload(latest_continuation)
    elif completion_items:
        queue = {
            "exhausted": False,
            "message": (
                "Completion was saved, but continuation selection is temporarily unavailable."
            ),
        }
    else:
        queue = _queue_payload(None)
    return {
        "total_completed": len(completion_items),
        "completed_problem_ids": [item["problem_id"] for item in completion_items],
        "completions": completion_items,
        "continuation_items": [
            payload
            for row in active_continuations
            if (payload := _continuation_payload(row)) is not None
        ],
        "queue": queue,
    }
