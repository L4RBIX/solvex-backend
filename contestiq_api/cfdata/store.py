"""Codeforces data platform storage.

SQLite locally (shares the Phase 01 DATABASE_PATH file); the canonical
Postgres/Supabase schema is db/migrations/008_cf_data_platform.sql — keep the
two in sync. All writes are upserts so re-running a sync never duplicates rows.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contestiq_api.settings import get_settings
from contestiq_core.codeforces.normalizer import stable_problem_key

SYNC_STATUSES = {"queued", "running", "success", "failed", "stale_cache_used"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cf_raw_api_responses (
    id TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    params_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    raw_json TEXT,
    fetched_at TEXT NOT NULL,
    http_status INTEGER,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_cf_raw_lookup ON cf_raw_api_responses (endpoint, params_hash, fetched_at DESC);

CREATE TABLE IF NOT EXISTS cf_users (
    handle TEXT PRIMARY KEY,
    display_handle TEXT NOT NULL,
    rating INTEGER,
    max_rating INTEGER,
    rank TEXT,
    max_rank TEXT,
    country TEXT,
    organization TEXT,
    contribution INTEGER,
    registration_time INTEGER,
    raw_json TEXT,
    first_synced_at TEXT,
    last_synced_at TEXT,
    max_submission_id INTEGER,
    submission_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cf_user_rating_history (
    handle TEXT NOT NULL,
    contest_id INTEGER NOT NULL,
    contest_name TEXT,
    contest_rank INTEGER,
    old_rating INTEGER,
    new_rating INTEGER,
    rating_update_time INTEGER,
    PRIMARY KEY (handle, contest_id)
);

CREATE TABLE IF NOT EXISTS cf_submissions_raw (
    submission_id INTEGER PRIMARY KEY,
    handle TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cf_submissions_raw_handle ON cf_submissions_raw (handle);

CREATE TABLE IF NOT EXISTS cf_submissions_normalized (
    submission_id INTEGER PRIMARY KEY,
    handle TEXT NOT NULL,
    contest_id INTEGER,
    problem_index TEXT,
    problem_key TEXT NOT NULL,
    participant_type TEXT,
    programming_language TEXT,
    verdict TEXT,
    passed_test_count INTEGER,
    time_consumed_ms INTEGER,
    memory_consumed_bytes INTEGER,
    creation_time INTEGER,
    relative_time_seconds INTEGER,
    problem_rating INTEGER,
    problem_tags_snapshot TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_cf_submissions_norm_handle_time ON cf_submissions_normalized (handle, creation_time DESC);
CREATE INDEX IF NOT EXISTS idx_cf_submissions_norm_problem ON cf_submissions_normalized (problem_key);

CREATE TABLE IF NOT EXISTS cf_problemset_raw (
    id TEXT PRIMARY KEY,
    raw_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    problem_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_cf_problemset_raw_fetched ON cf_problemset_raw (fetched_at DESC);

CREATE TABLE IF NOT EXISTS problems (
    problem_key TEXT PRIMARY KEY,
    contest_id INTEGER,
    problem_index TEXT,
    name TEXT NOT NULL,
    rating INTEGER,
    tags TEXT NOT NULL DEFAULT '[]',
    problemset_name TEXT,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_problems_rating ON problems (rating);

CREATE TABLE IF NOT EXISTS problem_statistics (
    problem_key TEXT PRIMARY KEY,
    solved_count INTEGER,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_episodes (
    episode_id TEXT PRIMARY KEY,
    user_id TEXT,
    handle TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    first_submission_id INTEGER,
    first_attempt_at INTEGER,
    first_ac_submission_id INTEGER,
    first_ac_at INTEGER,
    last_submission_at INTEGER,
    total_submissions INTEGER NOT NULL,
    failed_before_ac INTEGER NOT NULL,
    final_status TEXT NOT NULL,
    eventual_ac INTEGER NOT NULL,
    participant_type_primary TEXT,
    context_type TEXT,
    problem_rating INTEGER,
    user_rating_at_time INTEGER,
    rating_anchor_source TEXT,
    rating_gap INTEGER,
    rating_band TEXT NOT NULL,
    verdict_sequence TEXT NOT NULL DEFAULT '[]',
    passed_test_progression TEXT NOT NULL DEFAULT '[]',
    episode_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_problem_episodes_handle ON problem_episodes (handle, last_submission_at DESC);
CREATE INDEX IF NOT EXISTS idx_problem_episodes_problem ON problem_episodes (problem_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_problem_episodes_identity ON problem_episodes (handle, problem_id);

CREATE TABLE IF NOT EXISTS taxonomy_versions (
    version TEXT PRIMARY KEY,
    description TEXT,
    skill_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_taxonomy (
    skill_id TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    parent_id TEXT,
    display_name TEXT NOT NULL,
    level INTEGER NOT NULL,
    PRIMARY KEY (skill_id, taxonomy_version)
);
CREATE INDEX IF NOT EXISTS idx_skill_taxonomy_parent ON skill_taxonomy (taxonomy_version, parent_id);

CREATE TABLE IF NOT EXISTS problem_skill_map (
    problem_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    weight REAL NOT NULL,
    confidence REAL NOT NULL,
    mapping_source TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    reviewed_by TEXT,
    reviewed_at TEXT,
    PRIMARY KEY (problem_id, skill_id, taxonomy_version)
);
CREATE INDEX IF NOT EXISTS idx_problem_skill_map_skill ON problem_skill_map (taxonomy_version, skill_id);

CREATE TABLE IF NOT EXISTS mapping_review_queue (
    problem_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    reason TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    PRIMARY KEY (problem_id, tag, taxonomy_version)
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    analysis_version TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    problem_catalog_version TEXT NOT NULL,
    data_cutoff_time INTEGER,
    input_data_hash TEXT NOT NULL,
    global_rating INTEGER,
    global_rating_source TEXT,
    episode_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_handle ON analysis_runs (handle, created_at DESC);

CREATE TABLE IF NOT EXISTS analysis_skill_scores (
    run_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    severity INTEGER NOT NULL,
    underexposure REAL NOT NULL,
    estimated_skill_rating INTEGER,
    estimated_skill_rating_low INTEGER,
    estimated_skill_rating_high INTEGER,
    explanation TEXT NOT NULL,
    PRIMARY KEY (run_id, skill_id)
);

CREATE TABLE IF NOT EXISTS analysis_skill_evidence (
    run_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY (run_id, skill_id)
);

CREATE TABLE IF NOT EXISTS analysis_warnings (
    run_id TEXT NOT NULL,
    skill_id TEXT NOT NULL DEFAULT '*',
    warning TEXT NOT NULL,
    PRIMARY KEY (run_id, skill_id, warning)
);

CREATE TABLE IF NOT EXISTS analysis_problem_evidence (
    run_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    mapping_weight REAL NOT NULL,
    recency_weight REAL NOT NULL,
    final_status TEXT NOT NULL,
    problem_rating INTEGER,
    PRIMARY KEY (run_id, skill_id, episode_id)
);

CREATE TABLE IF NOT EXISTS user_skill_history (
    handle TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    status TEXT NOT NULL,
    severity INTEGER NOT NULL,
    confidence REAL NOT NULL,
    estimated_skill_rating INTEGER,
    created_at TEXT NOT NULL,
    PRIMARY KEY (handle, skill_id, run_id)
);
CREATE INDEX IF NOT EXISTS idx_user_skill_history ON user_skill_history (handle, skill_id, created_at DESC);

CREATE TABLE IF NOT EXISTS user_skill_profiles (
    handle TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    user_id TEXT,
    analysis_run_id TEXT,
    global_rating_anchor INTEGER,
    skill_rating_raw INTEGER,
    skill_rating_shrunk INTEGER,
    uncertainty REAL,
    status TEXT,
    severity INTEGER,
    confidence REAL,
    effective_exposure REAL,
    attempts INTEGER NOT NULL DEFAULT 0,
    independent_solves INTEGER NOT NULL DEFAULT 0,
    delayed_ac_count INTEGER NOT NULL DEFAULT 0,
    recent_failures_28d INTEGER NOT NULL DEFAULT 0,
    last_practiced_at INTEGER,
    review_due_at INTEGER,
    frustration_score REAL NOT NULL DEFAULT 0,
    preference_bias REAL NOT NULL DEFAULT 0,
    suppression_until TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (handle, skill_id)
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
    run_id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    analysis_run_id TEXT,
    queue_date TEXT NOT NULL,
    recent_struggle REAL NOT NULL DEFAULT 0,
    warnings TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recommendation_runs ON recommendation_runs (handle, queue_date DESC);

CREATE TABLE IF NOT EXISTS recommendation_items (
    item_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    slot INTEGER NOT NULL,
    mode TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    target_rating INTEGER,
    problem_rating INTEGER,
    quality_score REAL,
    final_score REAL,
    why_selected TEXT NOT NULL,
    item_status TEXT NOT NULL DEFAULT 'proposed'
);
CREATE INDEX IF NOT EXISTS idx_recommendation_items_run ON recommendation_items (run_id, slot);

CREATE TABLE IF NOT EXISTS training_plans (
    plan_id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    analysis_run_id TEXT,
    start_date TEXT NOT NULL,
    plan_status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_training_plans ON training_plans (handle, plan_type, start_date DESC);

CREATE TABLE IF NOT EXISTS training_plan_days (
    plan_id TEXT NOT NULL,
    day_number INTEGER NOT NULL,
    theme TEXT NOT NULL,
    PRIMARY KEY (plan_id, day_number)
);

CREATE TABLE IF NOT EXISTS training_plan_items (
    item_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    day_number INTEGER NOT NULL,
    slot INTEGER NOT NULL,
    mode TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    target_rating INTEGER,
    problem_rating INTEGER,
    why_selected TEXT NOT NULL,
    item_status TEXT NOT NULL DEFAULT 'proposed'
);
CREATE INDEX IF NOT EXISTS idx_training_plan_items ON training_plan_items (plan_id, day_number, slot);

CREATE TABLE IF NOT EXISTS recommendation_feedback (
    feedback_id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    handle TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback ON recommendation_feedback (handle, problem_id);

CREATE TABLE IF NOT EXISTS problem_quality_stats (
    problem_id TEXT PRIMARY KEY,
    feedback_positive INTEGER NOT NULL DEFAULT 0,
    feedback_negative INTEGER NOT NULL DEFAULT 0,
    feedback_wilson REAL,
    manual_curation REAL NOT NULL DEFAULT 0.5,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    handle TEXT,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    token_hash TEXT UNIQUE,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_handle ON users (handle);

CREATE TABLE IF NOT EXISTS billing_customers (
    customer_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    external_customer_id TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_billing_customers_user ON billing_customers (user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    plan TEXT NOT NULL,
    subscription_status TEXT NOT NULL,
    external_subscription_id TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions (user_id);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    plan TEXT,
    amount_cents INTEGER,
    currency TEXT,
    payment_status TEXT NOT NULL,
    external_payment_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments (user_id);

CREATE TABLE IF NOT EXISTS payment_webhook_events (
    event_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    event_type TEXT,
    payload TEXT NOT NULL,
    result TEXT,
    processed_at TEXT NOT NULL,
    PRIMARY KEY (provider, event_id)
);

CREATE TABLE IF NOT EXISTS entitlement_grants (
    grant_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    source TEXT NOT NULL,
    reference TEXT,
    granted_by TEXT,
    granted_at TEXT NOT NULL,
    expires_at TEXT,
    revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_entitlement_grants_user ON entitlement_grants (user_id, plan);

CREATE TABLE IF NOT EXISTS usage_limits (
    subject TEXT NOT NULL,
    feature TEXT NOT NULL,
    window_start TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (subject, feature, window_start)
);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    audit_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    details TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_logs (created_at DESC);

CREATE TABLE IF NOT EXISTS challenges (
    challenge_id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    examples TEXT NOT NULL DEFAULT '[]',
    hidden_tests_ref TEXT NOT NULL,
    checker_ref TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    challenge_status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_challenges_skill ON challenges (skill_id, challenge_status, level);

CREATE TABLE IF NOT EXISTS challenge_test_sets (
    test_set_id TEXT PRIMARY KEY,
    challenge_id TEXT NOT NULL,
    is_hidden INTEGER NOT NULL DEFAULT 1,
    tests TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_challenge_test_sets ON challenge_test_sets (challenge_id);

CREATE TABLE IF NOT EXISTS verification_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    handle TEXT,
    challenge_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    session_status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    completed_at TEXT,
    final_label TEXT
);
CREATE INDEX IF NOT EXISTS idx_verification_sessions_user ON verification_sessions (user_id, started_at DESC);

CREATE TABLE IF NOT EXISTS execution_attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    language TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    attempt_status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_execution_attempts_session ON execution_attempts (session_id, created_at);

CREATE TABLE IF NOT EXISTS judge0_submissions (
    submission_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    test_index INTEGER NOT NULL DEFAULT 0,
    judge0_token TEXT UNIQUE,
    callback_secret TEXT NOT NULL,
    submission_status TEXT NOT NULL DEFAULT 'submitted',
    status_id INTEGER,
    passed INTEGER,
    time_ms INTEGER,
    memory_kb INTEGER,
    stdout_redacted TEXT,
    stderr_redacted TEXT,
    callback_received_at TEXT,
    polled_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_judge0_submissions_attempt ON judge0_submissions (attempt_id);
CREATE INDEX IF NOT EXISTS idx_judge0_submissions_pending ON judge0_submissions (submission_status, created_at);

CREATE TABLE IF NOT EXISTS session_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    source_trust TEXT NOT NULL,
    occurred_at TEXT,
    received_at TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    payload_redaction_level TEXT NOT NULL DEFAULT 'none',
    prev_event_hash TEXT,
    event_hash TEXT NOT NULL,
    trace_id TEXT,
    request_id TEXT,
    UNIQUE (session_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_session_events ON session_events (session_id, seq);

CREATE TABLE IF NOT EXISTS code_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (session_id, content_hash)
);

CREATE TABLE IF NOT EXISTS badge_decisions (
    decision_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    decision TEXT NOT NULL,
    process_evidence_label TEXT NOT NULL,
    reasons TEXT NOT NULL DEFAULT '[]',
    hidden_pass_rate REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public_badges (
    badge_public_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    handle TEXT,
    skill_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    evidence_label TEXT NOT NULL,
    badge_status TEXT NOT NULL DEFAULT 'active',
    issued_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS private_reports (
    report_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    member_role TEXT NOT NULL,
    handle TEXT,
    joined_at TEXT NOT NULL,
    PRIMARY KEY (team_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members (user_id);

CREATE TABLE IF NOT EXISTS team_invites (
    invite_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    member_role TEXT NOT NULL,
    created_by TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    accepted_by TEXT,
    accepted_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_assignments (
    assignment_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    student_user_id TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    kind TEXT NOT NULL,
    skill_id TEXT,
    problem_ids TEXT NOT NULL DEFAULT '[]',
    challenge_skill_id TEXT,
    due_date TEXT,
    notes TEXT,
    assignment_status TEXT NOT NULL DEFAULT 'assigned',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_team_assignments ON team_assignments (team_id, student_user_id);

CREATE TABLE IF NOT EXISTS team_student_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    handle TEXT,
    analysis_run_id TEXT,
    summary TEXT NOT NULL DEFAULT '{}',
    captured_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_team_student_snapshots ON team_student_snapshots (team_id, user_id, captured_at DESC);

CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organization_members (
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    member_role TEXT NOT NULL,
    joined_at TEXT NOT NULL,
    PRIMARY KEY (org_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_organization_members_user ON organization_members (user_id);

CREATE TABLE IF NOT EXISTS org_events (
    event_id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    event_status TEXT NOT NULL DEFAULT 'active',
    expires_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_org_events ON org_events (org_id, created_at DESC);

CREATE TABLE IF NOT EXISTS event_requirements (
    event_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    level INTEGER,
    min_evidence_label TEXT NOT NULL DEFAULT 'sufficient_process_evidence',
    PRIMARY KEY (event_id, skill_id)
);

CREATE TABLE IF NOT EXISTS event_applicants (
    applicant_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    display_name TEXT,
    email TEXT,
    applicant_status TEXT NOT NULL DEFAULT 'invited',
    shadow_user_id TEXT,
    session_id TEXT,
    badge_public_id TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_event_applicants ON event_applicants (event_id, created_at);

CREATE TABLE IF NOT EXISTS event_verification_links (
    link_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    applicant_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_report_exports (
    export_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    applicant_id TEXT NOT NULL,
    exported_by TEXT NOT NULL,
    export_format TEXT NOT NULL DEFAULT 'json',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_event_report_exports ON event_report_exports (event_id, created_at DESC);

CREATE TABLE IF NOT EXISTS product_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    properties TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_product_events_type ON product_events (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_events_subject ON product_events (subject, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_events_once ON product_events (event_type, subject)
    WHERE event_type LIKE 'first_%';

CREATE TABLE IF NOT EXISTS weekly_reports (
    report_id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    week_start TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (handle, week_start)
);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_handle ON weekly_reports (handle, week_start DESC);

CREATE TABLE IF NOT EXISTS leaderboard_groups (
    leaderboard_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_subject TEXT NOT NULL,
    owner_user_id TEXT,
    visibility TEXT NOT NULL DEFAULT 'private',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leaderboard_groups_owner ON leaderboard_groups (owner_user_id);

CREATE TABLE IF NOT EXISTS leaderboard_members (
    leaderboard_id TEXT NOT NULL,
    member_subject TEXT NOT NULL,
    user_id TEXT,
    handle TEXT,
    display_name TEXT NOT NULL,
    member_role TEXT NOT NULL DEFAULT 'member',
    joined_at TEXT NOT NULL,
    PRIMARY KEY (leaderboard_id, member_subject)
);
CREATE INDEX IF NOT EXISTS idx_leaderboard_members_user ON leaderboard_members (user_id);
CREATE INDEX IF NOT EXISTS idx_leaderboard_members_handle ON leaderboard_members (handle);

CREATE TABLE IF NOT EXISTS leaderboard_invites (
    invite_id TEXT PRIMARY KEY,
    leaderboard_id TEXT NOT NULL,
    invite_code_hash TEXT UNIQUE NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_leaderboard_invites_board ON leaderboard_invites (leaderboard_id);

CREATE TABLE IF NOT EXISTS duel_matches (
    duel_id TEXT PRIMARY KEY,
    creator_subject TEXT NOT NULL,
    creator_user_id TEXT,
    creator_handle TEXT,
    mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'waiting',
    problem_id TEXT NOT NULL,
    problem_rating INTEGER,
    skill_id TEXT,
    invite_code_hash TEXT UNIQUE NOT NULL,
    starts_at TEXT,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    winner_subject TEXT,
    result_reason TEXT,
    countdown_started_at TEXT,
    winner_decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_duel_matches_creator ON duel_matches (creator_subject, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_duel_matches_status ON duel_matches (status, expires_at);

CREATE TABLE IF NOT EXISTS duel_participants (
    duel_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    user_id TEXT,
    handle TEXT,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    joined_at TEXT NOT NULL,
    ready_at TEXT,
    final_status TEXT NOT NULL DEFAULT 'pending',
    accepted_at TEXT,
    best_attempt_id TEXT,
    hint_count INTEGER NOT NULL DEFAULT 0,
    wrong_attempts INTEGER NOT NULL DEFAULT 0,
    judging_at TEXT,
    last_seen_at TEXT,
    arena_opened_at TEXT,
    PRIMARY KEY (duel_id, subject)
);
CREATE INDEX IF NOT EXISTS idx_duel_participants_user ON duel_participants (user_id);
CREATE INDEX IF NOT EXISTS idx_duel_participants_handle ON duel_participants (handle);

CREATE TABLE IF NOT EXISTS duel_hints (
    hint_id TEXT PRIMARY KEY,
    duel_id TEXT NOT NULL,
    participant_subject TEXT NOT NULL,
    hint_number INTEGER NOT NULL,
    hint_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_duel_hints_duel ON duel_hints (duel_id, participant_subject, hint_number);

CREATE TABLE IF NOT EXISTS duel_submissions (
    submission_id TEXT PRIMARY KEY,
    duel_id TEXT NOT NULL,
    participant_subject TEXT NOT NULL,
    language TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    judge_status TEXT NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    stdout_excerpt TEXT,
    stderr_excerpt TEXT,
    created_at TEXT NOT NULL,
    judged_at TEXT,
    runtime_ms INTEGER,
    memory_kb INTEGER
);
CREATE INDEX IF NOT EXISTS idx_duel_submissions_duel ON duel_submissions (duel_id, created_at);

CREATE TABLE IF NOT EXISTS cf_sync_jobs (
    id TEXT PRIMARY KEY,
    handle TEXT,
    sync_type TEXT NOT NULL,
    status TEXT NOT NULL,
    stats TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cf_sync_jobs_handle ON cf_sync_jobs (handle, created_at DESC);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_handle(handle: str) -> str:
    return handle.strip().lower()


def params_hash(params: dict[str, Any] | None) -> str:
    canonical = json.dumps(params or {}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Columns added after a table already shipped (mirrors db/migrations/019+).
# CREATE TABLE IF NOT EXISTS never alters existing tables, so pre-existing
# databases (e.g. the Railway volume) get them via ALTER TABLE here.
_COLUMN_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "duel_participants": [
        ("hint_count", "INTEGER NOT NULL DEFAULT 0"),
        ("wrong_attempts", "INTEGER NOT NULL DEFAULT 0"),
        ("judging_at", "TEXT"),
        ("last_seen_at", "TEXT"),
        ("arena_opened_at", "TEXT"),
    ],
    "duel_matches": [
        ("countdown_started_at", "TEXT"),
        ("winner_decided_at", "TEXT"),
    ],
}

_column_migrations_done: set[str] = set()


def _apply_column_migrations(conn: sqlite3.Connection, path: str) -> None:
    if path in _column_migrations_done:
        return
    for table, columns in _COLUMN_MIGRATIONS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    conn.commit()
    _column_migrations_done.add(path)


def connect() -> sqlite3.Connection:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)  # tolerate concurrent writers
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    _apply_column_migrations(conn, str(path.resolve()))
    return conn


# ─── Raw API responses ───────────────────────────────────────────────────────


def record_raw_response(
    endpoint: str,
    params: dict[str, Any] | None,
    status: str,
    raw_json: Any = None,
    http_status: int | None = None,
    error_message: str | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO cf_raw_api_responses (id, endpoint, params_hash, status, raw_json, fetched_at, http_status, error_message)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                endpoint,
                params_hash(params),
                status,
                json.dumps(raw_json, ensure_ascii=False) if raw_json is not None else None,
                _now(),
                http_status,
                error_message,
            ),
        )


def latest_ok_raw_response(endpoint: str, params: dict[str, Any] | None) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM cf_raw_api_responses WHERE endpoint = ? AND params_hash = ? AND status = 'ok'"
            " ORDER BY fetched_at DESC LIMIT 1",
            (endpoint, params_hash(params)),
        ).fetchone()
    if row is None or row["raw_json"] is None:
        return None
    return {"data": json.loads(row["raw_json"]), "fetched_at": row["fetched_at"]}


# ─── Users and rating history ────────────────────────────────────────────────


def upsert_user(user_info: dict[str, Any]) -> str:
    handle = canonical_handle(user_info.get("handle", ""))
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO cf_users (handle, display_handle, rating, max_rating, rank, max_rank, country,
                                  organization, contribution, registration_time, raw_json, first_synced_at, last_synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(handle) DO UPDATE SET
                display_handle=excluded.display_handle,
                rating=excluded.rating,
                max_rating=excluded.max_rating,
                rank=excluded.rank,
                max_rank=excluded.max_rank,
                country=excluded.country,
                organization=excluded.organization,
                contribution=excluded.contribution,
                registration_time=excluded.registration_time,
                raw_json=excluded.raw_json,
                last_synced_at=excluded.last_synced_at
            """,
            (
                handle,
                user_info.get("handle", handle),
                user_info.get("rating"),
                user_info.get("maxRating"),
                user_info.get("rank"),
                user_info.get("maxRank"),
                user_info.get("country"),
                user_info.get("organization"),
                user_info.get("contribution"),
                user_info.get("registrationTimeSeconds"),
                json.dumps(user_info, ensure_ascii=False),
                now,
                now,
            ),
        )
    return handle


def get_user(handle: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM cf_users WHERE handle = ?", (canonical_handle(handle),)
        ).fetchone()
    return dict(row) if row else None


def update_user_sync_cursor(handle: str, max_submission_id: int | None) -> None:
    canonical = canonical_handle(handle)
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM cf_submissions_normalized WHERE handle = ?", (canonical,)
        ).fetchone()[0]
        # NULLIF keeps the cursor NULL until a real submission id has been seen.
        conn.execute(
            "UPDATE cf_users SET max_submission_id = NULLIF(MAX(COALESCE(max_submission_id, 0), COALESCE(?, 0)), 0),"
            " submission_count = ?, last_synced_at = ? WHERE handle = ?",
            (max_submission_id, count, _now(), canonical),
        )


def upsert_rating_history(handle: str, rows: list[dict[str, Any]]) -> int:
    canonical = canonical_handle(handle)
    with connect() as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO cf_user_rating_history (handle, contest_id, contest_name, contest_rank, old_rating, new_rating, rating_update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(handle, contest_id) DO UPDATE SET
                    contest_name=excluded.contest_name,
                    contest_rank=excluded.contest_rank,
                    old_rating=excluded.old_rating,
                    new_rating=excluded.new_rating,
                    rating_update_time=excluded.rating_update_time
                """,
                (
                    canonical,
                    row.get("contestId"),
                    row.get("contestName"),
                    row.get("rank"),
                    row.get("oldRating"),
                    row.get("newRating"),
                    row.get("ratingUpdateTimeSeconds"),
                ),
            )
        count = conn.execute(
            "SELECT COUNT(*) FROM cf_user_rating_history WHERE handle = ?", (canonical,)
        ).fetchone()[0]
    return count


# ─── Submissions ─────────────────────────────────────────────────────────────


def normalize_submission_row(handle: str, raw: dict[str, Any]) -> dict[str, Any]:
    problem = raw.get("problem", {})
    return {
        "submission_id": raw["id"],
        "handle": canonical_handle(handle),
        "contest_id": problem.get("contestId") or raw.get("contestId"),
        "problem_index": problem.get("index"),
        "problem_key": stable_problem_key(problem),
        "participant_type": (raw.get("author") or {}).get("participantType"),
        "programming_language": raw.get("programmingLanguage"),
        "verdict": raw.get("verdict") or "UNKNOWN",
        "passed_test_count": raw.get("passedTestCount"),
        "time_consumed_ms": raw.get("timeConsumedMillis"),
        "memory_consumed_bytes": raw.get("memoryConsumedBytes"),
        "creation_time": raw.get("creationTimeSeconds"),
        "relative_time_seconds": raw.get("relativeTimeSeconds"),
        "problem_rating": problem.get("rating"),
        "problem_tags_snapshot": json.dumps(problem.get("tags") or [], ensure_ascii=False),
    }


def upsert_submissions(handle: str, raw_submissions: list[dict[str, Any]]) -> dict[str, int]:
    canonical = canonical_handle(handle)
    now = _now()
    inserted = 0
    with connect() as conn:
        for raw in raw_submissions:
            normalized = normalize_submission_row(canonical, raw)
            cursor = conn.execute(
                "INSERT OR IGNORE INTO cf_submissions_raw (submission_id, handle, raw_json, fetched_at) VALUES (?, ?, ?, ?)",
                (raw["id"], canonical, json.dumps(raw, ensure_ascii=False), now),
            )
            inserted += cursor.rowcount
            conn.execute(
                """
                INSERT INTO cf_submissions_normalized (
                    submission_id, handle, contest_id, problem_index, problem_key, participant_type,
                    programming_language, verdict, passed_test_count, time_consumed_ms,
                    memory_consumed_bytes, creation_time, relative_time_seconds, problem_rating, problem_tags_snapshot
                ) VALUES (:submission_id, :handle, :contest_id, :problem_index, :problem_key, :participant_type,
                          :programming_language, :verdict, :passed_test_count, :time_consumed_ms,
                          :memory_consumed_bytes, :creation_time, :relative_time_seconds, :problem_rating, :problem_tags_snapshot)
                ON CONFLICT(submission_id) DO UPDATE SET
                    verdict=excluded.verdict,
                    passed_test_count=excluded.passed_test_count,
                    time_consumed_ms=excluded.time_consumed_ms,
                    memory_consumed_bytes=excluded.memory_consumed_bytes,
                    problem_rating=excluded.problem_rating,
                    problem_tags_snapshot=excluded.problem_tags_snapshot
                """,
                normalized,
            )
    return {"fetched": len(raw_submissions), "new": inserted}


def submission_counts(handle: str) -> dict[str, int]:
    canonical = canonical_handle(handle)
    with connect() as conn:
        raw = conn.execute("SELECT COUNT(*) FROM cf_submissions_raw WHERE handle = ?", (canonical,)).fetchone()[0]
        normalized = conn.execute(
            "SELECT COUNT(*) FROM cf_submissions_normalized WHERE handle = ?", (canonical,)
        ).fetchone()[0]
    return {"raw": raw, "normalized": normalized}


def get_normalized_submission(submission_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM cf_submissions_normalized WHERE submission_id = ?", (submission_id,)
        ).fetchone()
    return dict(row) if row else None


# ─── Problemset ──────────────────────────────────────────────────────────────


def save_problemset_snapshot(raw: dict[str, Any]) -> dict[str, int]:
    now = _now()
    problems = raw.get("problems", [])
    stats = raw.get("problemStatistics", [])
    with connect() as conn:
        conn.execute(
            "INSERT INTO cf_problemset_raw (id, raw_json, fetched_at, problem_count) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), json.dumps(raw, ensure_ascii=False), now, len(problems)),
        )
        for problem in problems:
            conn.execute(
                """
                INSERT INTO problems (problem_key, contest_id, problem_index, name, rating, tags, problemset_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(problem_key) DO UPDATE SET
                    contest_id=excluded.contest_id,
                    problem_index=excluded.problem_index,
                    name=excluded.name,
                    rating=excluded.rating,
                    tags=excluded.tags,
                    problemset_name=excluded.problemset_name,
                    updated_at=excluded.updated_at
                """,
                (
                    stable_problem_key(problem),
                    problem.get("contestId"),
                    problem.get("index"),
                    problem.get("name", "Unknown"),
                    problem.get("rating"),
                    json.dumps(problem.get("tags") or [], ensure_ascii=False),
                    problem.get("problemsetName"),
                    now,
                ),
            )
        for stat in stats:
            conn.execute(
                """
                INSERT INTO problem_statistics (problem_key, solved_count, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(problem_key) DO UPDATE SET
                    solved_count=excluded.solved_count,
                    updated_at=excluded.updated_at
                """,
                (stable_problem_key(stat), stat.get("solvedCount"), now),
            )
    return {"problems": len(problems), "statistics": len(stats)}


def latest_problemset_snapshot() -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, fetched_at, problem_count FROM cf_problemset_raw ORDER BY fetched_at DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def problem_counts() -> dict[str, int]:
    with connect() as conn:
        problems = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        stats = conn.execute("SELECT COUNT(*) FROM problem_statistics").fetchone()[0]
    return {"problems": problems, "statistics": stats}


def storage_diagnostics() -> dict[str, Any]:
    """Snapshot of the exact data a Railway redeploy silently wipes when
    DATABASE_PATH is not pointed at a persistent volume: the shared problem
    catalog and the derived problem_skill_map. Zero counts here (with an
    otherwise-healthy process) are the signature of that bug — the daily
    queue/plan endpoints will return no candidates until both are reseeded.
    """
    with connect() as conn:
        problemset_count = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        skill_map_count = conn.execute("SELECT COUNT(*) FROM problem_skill_map").fetchone()[0]
    snapshot = latest_problemset_snapshot()
    return {
        "problemset_count": problemset_count,
        "problem_skill_map_count": skill_map_count,
        "latest_problemset_sync_at": snapshot["fetched_at"] if snapshot else None,
    }


def get_problem(problem_key: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM problems WHERE problem_key = ?", (problem_key,)).fetchone()
    return dict(row) if row else None


# ─── Sync jobs ───────────────────────────────────────────────────────────────


def create_sync_job(sync_type: str, handle: str | None, idempotency_key: str | None = None) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    with connect() as conn:
        try:
            conn.execute(
                "INSERT INTO cf_sync_jobs (id, handle, sync_type, status, created_at, idempotency_key) VALUES (?, ?, ?, 'queued', ?, ?)",
                (job_id, canonical_handle(handle) if handle else None, sync_type, _now(), idempotency_key),
            )
        except sqlite3.IntegrityError:
            existing = find_sync_job_by_idempotency_key(idempotency_key) if idempotency_key else None
            if existing is not None:
                return existing
            raise
    job = get_sync_job(job_id)
    assert job is not None
    return job


def get_sync_job(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM cf_sync_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    job = dict(row)
    job["stats"] = json.loads(job["stats"] or "{}")
    return job


def find_sync_job_by_idempotency_key(key: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT id FROM cf_sync_jobs WHERE idempotency_key = ?", (key,)).fetchone()
    return get_sync_job(row["id"]) if row else None


def find_active_sync_job(handle: str | None, sync_type: str | None = None) -> dict[str, Any] | None:
    query = "SELECT id FROM cf_sync_jobs WHERE status IN ('queued', 'running')"
    params: list[Any] = []
    if handle is not None:
        query += " AND handle = ?"
        params.append(canonical_handle(handle))
    else:
        query += " AND handle IS NULL"
    if sync_type is not None:
        query += " AND sync_type = ?"
        params.append(sync_type)
    query += " ORDER BY created_at DESC LIMIT 1"
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
    return get_sync_job(row["id"]) if row else None


def list_sync_jobs(handle: str, limit: int = 5) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id FROM cf_sync_jobs WHERE handle = ? ORDER BY created_at DESC LIMIT ?",
            (canonical_handle(handle), limit),
        ).fetchall()
    return [job for row in rows if (job := get_sync_job(row["id"])) is not None]


def mark_sync_running(job_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE cf_sync_jobs SET status = 'running', started_at = ? WHERE id = ?", (_now(), job_id))


def finish_sync_job(job_id: str, status: str, stats: dict[str, Any] | None = None, error_message: str | None = None) -> None:
    if status not in SYNC_STATUSES - {"queued", "running"}:
        raise ValueError(f"Invalid terminal sync status: {status}")
    with connect() as conn:
        conn.execute(
            "UPDATE cf_sync_jobs SET status = ?, stats = ?, error_message = ?, completed_at = ? WHERE id = ?",
            (status, json.dumps(stats or {}, ensure_ascii=False), error_message, _now(), job_id),
        )
