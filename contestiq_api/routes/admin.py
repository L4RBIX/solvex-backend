"""v1 admin endpoints (Phase 06). Every action is authorized AND audited."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from contestiq_api import auth, billing as billing_mod, entitlements, handles
from contestiq_api.cfdata import store, sync as cf_sync, weakness
from contestiq_api.errors import APIError
from contestiq_api.versions import TAXONOMY_VERSION

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(auth.require_admin)])


class CreateUserRequest(BaseModel):
    handle: str | None = None
    email: str | None = None
    role: str = "user"


class GrantRequest(BaseModel):
    plan: str
    expires_at: str | None = None
    reference: str | None = None


class RevokeRequest(BaseModel):
    plan: str


class MarkProblemBadRequest(BaseModel):
    reason: str | None = None


class BindHandleRequest(BaseModel):
    user_id: str
    handle: str = Field(min_length=3, max_length=24)


class SkillMapEntry(BaseModel):
    skill_id: str
    weight: float = Field(gt=0, le=1)
    confidence: float = Field(gt=0, le=1)


class EditSkillMapRequest(BaseModel):
    skills: list[SkillMapEntry] = Field(min_length=1, max_length=8)


# ─── Users and entitlements ──────────────────────────────────────────────────


@router.post("/users")
def create_user(payload: CreateUserRequest, admin: dict[str, Any] = Depends(auth.require_admin)):
    user = auth.create_user(handle=payload.handle, email=payload.email, role=payload.role)
    auth.audit(admin["actor"], "create_user", user["user_id"], {"handle": payload.handle, "role": payload.role})
    return user  # includes api_token exactly once


@router.get("/users")
def search_users(query: str = Query(min_length=1, max_length=100), admin: dict[str, Any] = Depends(auth.require_admin)):
    auth.audit(admin["actor"], "search_users", None, {"query": query})
    return {"users": auth.search_users(query)}


@router.post("/handles/bind")
def bind_handle(payload: BindHandleRequest, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Audited reconciliation operation (security hotfix, req. 12): bind a CF
    handle to a user_id WITHOUT the self-service verification flow. For
    support cases, or explicitly re-attributing pre-fix historical
    handle-tagged data after manual investigation — never automatic, and
    always logged. Rejects if another user already verified this handle."""
    return handles.admin_bind(payload.user_id, payload.handle, audit_actor=admin["actor"])


@router.post("/users/{user_id}/grant-entitlement")
def grant(user_id: str, payload: GrantRequest, admin: dict[str, Any] = Depends(auth.require_admin)):
    if auth.get_user(user_id) is None:
        raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)
    result = entitlements.grant_entitlement(
        user_id, payload.plan, source="manual", granted_by=admin["actor"],
        reference=payload.reference, expires_at=payload.expires_at,
    )
    auth.audit(admin["actor"], "grant_entitlement", user_id, {"plan": payload.plan, "expires_at": payload.expires_at})
    return result


@router.post("/users/{user_id}/revoke-entitlement")
def revoke(user_id: str, payload: RevokeRequest, admin: dict[str, Any] = Depends(auth.require_admin)):
    if auth.get_user(user_id) is None:
        raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)
    revoked = entitlements.revoke_entitlement(user_id, payload.plan)
    auth.audit(admin["actor"], "revoke_entitlement", user_id, {"plan": payload.plan, "revoked_grants": revoked})
    return {"user_id": user_id, "plan": payload.plan, "revoked_grants": revoked}


@router.get("/users/{user_id}/billing")
def user_billing(user_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    if auth.get_user(user_id) is None:
        raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)
    auth.audit(admin["actor"], "view_billing", user_id, {})
    summary = billing_mod.billing_summary(user_id)
    summary["usage"] = entitlements.usage_summary(f"user:{user_id}")
    return summary


# ─── Storage / persistence ───────────────────────────────────────────────────


@router.get("/storage-health")
def storage_health(admin: dict[str, Any] = Depends(auth.require_admin)):
    """Diagnose the exact failure mode behind "empty daily queue despite many
    episodes" on Railway: an ephemeral SQLite DATABASE_PATH that gets wiped on
    every redeploy, silently emptying the shared problem catalog and skill
    map (which are not part of db/migrations — they're seeded data, not
    schema). Call this right after a deploy; if `catalog_ready` is false, run
    scripts/seed_production_catalog.py or POST /api/v1/sync/problemset then
    POST /api/v1/skill-map/rebuild.
    """
    from contestiq_api.settings import database_path_looks_persistent, get_settings

    settings = get_settings()
    diag = store.storage_diagnostics()
    return {
        "database_path": settings.database_path,
        "database_path_looks_persistent": database_path_looks_persistent(settings.database_path),
        **diag,
        "catalog_ready": diag["problemset_count"] > 0 and diag["problem_skill_map_count"] > 0,
    }


# ─── Jobs ────────────────────────────────────────────────────────────────────


@router.get("/jobs")
def list_jobs(status: str | None = None, limit: int = Query(default=50, ge=1, le=200),
              admin: dict[str, Any] = Depends(auth.require_admin)):
    from contestiq_api import jobs as backend_jobs

    query = "SELECT * FROM backend_jobs"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with backend_jobs._connect() as conn:
        backend = [backend_jobs.public_job(backend_jobs._row_to_job(row)) for row in conn.execute(query, params).fetchall()]

    sync_query = "SELECT id FROM cf_sync_jobs"
    sync_params: list[Any] = []
    if status:
        sync_query += " WHERE status = ?"
        sync_params.append(status)
    sync_query += " ORDER BY created_at DESC LIMIT ?"
    sync_params.append(limit)
    with store.connect() as conn:
        sync_jobs = [store.get_sync_job(row["id"]) for row in conn.execute(sync_query, sync_params).fetchall()]

    auth.audit(admin["actor"], "list_jobs", None, {"status": status})
    return {"backend_jobs": backend, "sync_jobs": sync_jobs}


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    from contestiq_api import jobs as backend_jobs
    from contestiq_api.routes.v1 import _run_analysis_job

    job = backend_jobs.get_job(job_id)
    if job is not None:
        if job["status"] in ("queued", "running"):
            raise APIError("JOB_NOT_RETRYABLE", "Job is still active.", 409)
        new_job = backend_jobs.create_job(job["job_type"], job["input"])
        auth.audit(admin["actor"], "retry_job", job_id, {"new_job_id": new_job["id"], "job_type": job["job_type"]})
        if job["job_type"] == "analysis":
            new_job = _run_analysis_job(new_job)
        return {"retried_job_id": job_id, "job": backend_jobs.public_job(new_job)}

    sync_job = store.get_sync_job(job_id)
    if sync_job is not None:
        if sync_job["status"] in ("queued", "running"):
            raise APIError("JOB_NOT_RETRYABLE", "Job is still active.", 409)
        auth.audit(admin["actor"], "retry_job", job_id, {"job_type": f"sync:{sync_job['sync_type']}"})
        if sync_job["sync_type"] == "problemset":
            return {"retried_job_id": job_id, "job": cf_sync.sync_problemset(force=True)}
        return {"retried_job_id": job_id, "job": cf_sync.sync_handle(sync_job["handle"], force_full=False)}

    raise APIError("JOB_NOT_FOUND", f"No job found with id {job_id}.", 404)


@router.post("/resync/{handle}")
def force_resync(handle: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    from contestiq_api.service import validate_handle

    cleaned = validate_handle(handle)
    auth.audit(admin["actor"], "force_resync", cleaned, {})
    job = cf_sync.sync_handle(cleaned, force_full=True)
    return {"job": job}


# ─── Analysis snapshots ──────────────────────────────────────────────────────


@router.get("/analysis/{handle}/latest")
def latest_analysis_snapshot(handle: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    run_id = weakness.latest_run_id(handle)
    if run_id is None:
        raise APIError("ANALYSIS_RUN_NOT_FOUND", f"No analysis run found for {handle}.", 404)
    auth.audit(admin["actor"], "view_analysis_snapshot", handle, {"run_id": run_id})
    return weakness.get_run(run_id)


@router.get("/analysis/{handle}/runs")
def list_analysis_runs(handle: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT run_id, analysis_version, taxonomy_version, input_data_hash, episode_count, created_at"
            " FROM analysis_runs WHERE handle = ? ORDER BY created_at DESC LIMIT 20",
            (store.canonical_handle(handle),),
        ).fetchall()
    auth.audit(admin["actor"], "list_analysis_runs", handle, {})
    return {"handle": handle, "runs": [dict(row) for row in rows]}


# ─── Problem curation ────────────────────────────────────────────────────────


@router.post("/problems/{problem_id}/mark-bad")
def mark_problem_bad(problem_id: str, payload: MarkProblemBadRequest,
                     admin: dict[str, Any] = Depends(auth.require_admin)):
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO problem_quality_stats (problem_id, manual_curation, updated_at) VALUES (?, 0.0, ?)"
            " ON CONFLICT(problem_id) DO UPDATE SET manual_curation = 0.0, updated_at = excluded.updated_at",
            (problem_id, store._now()),
        )
    auth.audit(admin["actor"], "mark_problem_bad", problem_id, {"reason": payload.reason})
    return {"problem_id": problem_id, "manual_curation": 0.0}


@router.post("/problems/{problem_id}/skill-map")
def edit_problem_skill_map(problem_id: str, payload: EditSkillMapRequest,
                           admin: dict[str, Any] = Depends(auth.require_admin)):
    with store.connect() as conn:
        known = {
            row["skill_id"]
            for row in conn.execute(
                "SELECT skill_id FROM skill_taxonomy WHERE taxonomy_version = ?", (TAXONOMY_VERSION,)
            ).fetchall()
        }
        unknown = [entry.skill_id for entry in payload.skills if entry.skill_id not in known]
        if unknown:
            raise APIError("UNKNOWN_SKILL", f"Skills not in {TAXONOMY_VERSION}: {', '.join(unknown)}", 422)
        conn.execute(
            "DELETE FROM problem_skill_map WHERE problem_id = ? AND taxonomy_version = ?",
            (problem_id, TAXONOMY_VERSION),
        )
        total = sum(entry.weight for entry in payload.skills)
        primary = max(payload.skills, key=lambda e: (e.weight, e.confidence, e.skill_id)).skill_id
        for entry in payload.skills:
            conn.execute(
                "INSERT INTO problem_skill_map (problem_id, skill_id, taxonomy_version, weight, confidence,"
                " mapping_source, is_primary, reviewed_by, reviewed_at)"
                " VALUES (?, ?, ?, ?, ?, 'manual', ?, ?, ?)",
                (problem_id, entry.skill_id, TAXONOMY_VERSION, round(entry.weight / total, 6), entry.confidence,
                 1 if entry.skill_id == primary else 0, admin["actor"], store._now()),
            )
        conn.execute(
            "UPDATE mapping_review_queue SET resolved_at = ? WHERE problem_id = ? AND taxonomy_version = ?",
            (store._now(), problem_id, TAXONOMY_VERSION),
        )
    auth.audit(admin["actor"], "edit_problem_skill_map", problem_id,
               {"skills": [entry.model_dump() for entry in payload.skills]})
    return {"problem_id": problem_id, "skills": [entry.model_dump() for entry in payload.skills]}


@router.post("/jobs/weekly-reports")
def run_weekly_reports(admin: dict[str, Any] = Depends(auth.require_admin)):
    from contestiq_api import weekly

    result = weekly.generate_all_weekly_reports()
    auth.audit(admin["actor"], "run_weekly_reports", None, result)
    return result


# ─── Support workflows (Phase 10) ────────────────────────────────────────────


@router.post("/badges/{badge_public_id}/revoke")
def revoke_badge(badge_public_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    with store.connect() as conn:
        cursor = conn.execute(
            "UPDATE public_badges SET badge_status = 'revoked' WHERE badge_public_id = ?", (badge_public_id,)
        )
    if cursor.rowcount == 0:
        raise APIError("BADGE_NOT_FOUND", f"No badge found with id {badge_public_id}.", 404)
    auth.audit(admin["actor"], "revoke_badge", badge_public_id, {})
    return {"badge_public_id": badge_public_id, "badge_status": "revoked"}


@router.post("/challenges/{challenge_id}/mark-leaked")
def mark_challenge_leaked(challenge_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Leaked challenges are excluded from assignment (assign filters status='active')."""
    with store.connect() as conn:
        cursor = conn.execute(
            "UPDATE challenges SET challenge_status = 'leaked' WHERE challenge_id = ?", (challenge_id,)
        )
    if cursor.rowcount == 0:
        raise APIError("CHALLENGE_NOT_FOUND", f"No challenge found with id {challenge_id}.", 404)
    auth.audit(admin["actor"], "mark_challenge_leaked", challenge_id, {})
    return {"challenge_id": challenge_id, "challenge_status": "leaked"}


@router.post("/payments/{payment_id}/refund")
def refund_payment(payment_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Payment dispute flow: mark refunded and revoke the plan it purchased."""
    with store.connect() as conn:
        payment = conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone()
        if payment is None:
            raise APIError("PAYMENT_NOT_FOUND", f"No payment found with id {payment_id}.", 404)
        payment = dict(payment)
        conn.execute(
            "UPDATE payments SET payment_status = 'refunded', updated_at = ? WHERE payment_id = ?",
            (store._now(), payment_id),
        )
    revoked = 0
    if payment["plan"]:
        revoked = entitlements.revoke_entitlement(payment["user_id"], payment["plan"])
    auth.audit(admin["actor"], "refund_payment", payment_id,
               {"user_id": payment["user_id"], "plan": payment["plan"], "revoked_grants": revoked})
    return {"payment_id": payment_id, "payment_status": "refunded", "revoked_grants": revoked}


_USER_DATA_TABLES = [  # (table, user id column)
    # Ownership references claims, so deletion must process this row first.
    ("handle_owners", "user_id"),
    ("handle_claims", "user_id"),
    ("entitlement_grants", "user_id"),
    ("payments", "user_id"),
    ("billing_customers", "user_id"),
    ("subscriptions", "user_id"),
    ("team_members", "user_id"),
    ("team_assignments", "student_user_id"),
    ("user_skill_profiles", "user_id"),
    ("private_reports", "user_id"),
    ("verification_sessions", "user_id"),
]


@router.get("/users/{user_id}/export")
def export_user_data(user_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Data export request: JSON dump of every user-owned row."""
    user = auth.get_user(user_id)
    if user is None:
        raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)
    user.pop("token_hash", None)
    export: dict[str, Any] = {"user": user}
    with store.connect() as conn:
        for table, column in _USER_DATA_TABLES:
            rows = conn.execute(f"SELECT * FROM {table} WHERE {column} = ?", (user_id,)).fetchall()
            export[table] = [dict(row) for row in rows]
            if table == "handle_claims":
                # A pending verification code is a short-lived credential,
                # not useful account-export data.  Preserve the row and its
                # lifecycle metadata while never returning the code itself.
                for claim in export[table]:
                    claim["verification_code"] = "[REDACTED]"
        session_ids = [row["session_id"] for row in export.get("verification_sessions", [])]
        export["session_events_count"] = 0
        for session_id in session_ids:
            export["session_events_count"] += conn.execute(
                "SELECT COUNT(*) FROM session_events WHERE session_id = ?", (session_id,)
            ).fetchone()[0]
    export["product_events"] = []
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT event_type, created_at FROM product_events WHERE subject = ?", (f"user:{user_id}",)
        ).fetchall()
        export["product_events"] = [dict(row) for row in rows]
    auth.audit(admin["actor"], "export_user_data", user_id, {})
    return export


@router.delete("/users/{user_id}")
def delete_user(user_id: str, admin: dict[str, Any] = Depends(auth.require_admin)):
    """Deletion request: remove the user and every user-owned row, including
    verification sessions and their ledgers/snapshots."""
    user = auth.get_user(user_id)
    if user is None:
        raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)
    deleted: dict[str, int] = {}
    with store.connect() as conn:
        session_ids = [row["session_id"] for row in conn.execute(
            "SELECT session_id FROM verification_sessions WHERE user_id = ?", (user_id,)).fetchall()]
        for session_id in session_ids:
            for table in ("session_events", "code_snapshots", "badge_decisions", "public_badges"):
                conn.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))
            attempt_ids = [row["attempt_id"] for row in conn.execute(
                "SELECT attempt_id FROM execution_attempts WHERE session_id = ?", (session_id,)).fetchall()]
            for attempt_id in attempt_ids:
                conn.execute("DELETE FROM judge0_submissions WHERE attempt_id = ?", (attempt_id,))
            conn.execute("DELETE FROM execution_attempts WHERE session_id = ?", (session_id,))
        for table, column in _USER_DATA_TABLES:
            cursor = conn.execute(f"DELETE FROM {table} WHERE {column} = ?", (user_id,))
            deleted[table] = cursor.rowcount
        conn.execute("DELETE FROM product_events WHERE subject = ?", (f"user:{user_id}",))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    auth.audit(admin["actor"], "delete_user", user_id, {"deleted": deleted, "sessions": len(session_ids)})
    return {"user_id": user_id, "status": "deleted", "deleted": deleted}


@router.get("/launch-dashboard")
def launch_dashboard(admin: dict[str, Any] = Depends(auth.require_admin)):
    """Launch metrics in one view (counts from source tables + product events)."""
    from contestiq_api import product_events

    with store.connect() as conn:
        def scalar(sql: str, params: tuple = ()) -> int:
            return conn.execute(sql, params).fetchone()[0]

        signup_count = scalar("SELECT COUNT(*) FROM users")
        handle_connected = scalar("SELECT COUNT(*) FROM users WHERE handle IS NOT NULL")
        analyses = scalar("SELECT COUNT(*) FROM analysis_runs")
        analyzed_handles = scalar("SELECT COUNT(DISTINCT handle) FROM analysis_runs")
        queues = scalar("SELECT COUNT(*) FROM recommendation_runs")
        plans = scalar("SELECT COUNT(*) FROM training_plans")
        feedback_count = scalar("SELECT COUNT(*) FROM recommendation_feedback")
        active_premium = scalar(
            "SELECT COUNT(DISTINCT user_id) FROM entitlement_grants WHERE revoked_at IS NULL"
            " AND (expires_at IS NULL OR expires_at > ?)", (store._now(),))
        churned = scalar("SELECT COUNT(DISTINCT user_id) FROM entitlement_grants WHERE revoked_at IS NOT NULL")
        team_invites_accepted = scalar("SELECT COUNT(*) FROM team_invites WHERE accepted_by IS NOT NULL")
        applicants_total = scalar("SELECT COUNT(*) FROM event_applicants")
        applicants_completed = scalar(
            "SELECT COUNT(*) FROM event_applicants ea WHERE EXISTS"
            " (SELECT 1 FROM badge_decisions bd WHERE bd.session_id = ea.session_id)")
        sessions_completed = scalar("SELECT COUNT(*) FROM verification_sessions WHERE session_status = 'completed'")
        badges_issued = scalar("SELECT COUNT(*) FROM public_badges")
        retained = scalar(
            "SELECT COUNT(*) FROM (SELECT subject FROM product_events"
            " WHERE created_at >= datetime('now', '-7 days')"
            " GROUP BY subject HAVING COUNT(DISTINCT date(created_at)) >= 2)")

    return {
        "signup_count": signup_count,
        "handle_connected": handle_connected,
        "analysis_completed": analyses,
        "analyzed_handles": analyzed_handles,
        "queues_generated": queues,
        "plans_created": plans,
        "recommendation_feedback": feedback_count,
        "first_analysis_completed": product_events.count("first_analysis_completed"),
        "first_queue_generated": product_events.count("first_queue_generated"),
        "premium_conversions": product_events.count("premium_conversion"),
        "active_premium_users": active_premium,
        "free_to_premium_conversion": round(active_premium / signup_count, 4) if signup_count else 0.0,
        "paid_churn_users": churned,
        "team_invites_accepted": team_invites_accepted,
        "event_applicants": applicants_total,
        "event_applicant_completion_rate": round(applicants_completed / applicants_total, 4) if applicants_total else 0.0,
        "verification_sessions_completed": sessions_completed,
        "badges_issued": badges_issued,
        "badge_issuance_rate": round(badges_issued / sessions_completed, 4) if sessions_completed else 0.0,
        "seven_day_retention_subjects": retained,
        "note": "Retention counts subjects with product events on 2+ distinct days in the last 7 days.",
    }


@router.get("/audit-log")
def audit_log(limit: int = Query(default=50, ge=1, le=500), admin: dict[str, Any] = Depends(auth.require_admin)):
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM admin_audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    entries = []
    for row in rows:
        entry = dict(row)
        entry["details"] = json.loads(entry["details"])
        entries.append(entry)
    return {"entries": entries}
