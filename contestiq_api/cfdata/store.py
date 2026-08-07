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
    winner_decided_at TEXT,
    test_input TEXT,
    test_expected_output TEXT,
    test_locked_by TEXT,
    test_locked_at TEXT,
    problem_pack_id TEXT,
    test_cases_json TEXT,
    test_set_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_duel_matches_creator ON duel_matches (creator_subject, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_duel_matches_status ON duel_matches (status, expires_at);

CREATE TABLE IF NOT EXISTS duel_problem_packs (
    pack_id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    statement_summary TEXT NOT NULL,
    input_format TEXT NOT NULL,
    output_format TEXT NOT NULL,
    constraints_text TEXT NOT NULL,
    sample_tests TEXT NOT NULL DEFAULT '[]',
    judge_tests TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(problem_id, version)
);
CREATE INDEX IF NOT EXISTS idx_duel_problem_packs_active
    ON duel_problem_packs (active, problem_id, version DESC);

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

CREATE TABLE IF NOT EXISTS handle_claims (
    claim_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    handle TEXT NOT NULL,
    verification_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'verified', 'expired', 'superseded')),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    verified_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_handle_claims_user ON handle_claims (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_handle_claims_handle ON handle_claims (handle, status);

CREATE TABLE IF NOT EXISTS handle_owners (
    handle TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    claim_id TEXT REFERENCES handle_claims(claim_id),
    bound_by TEXT NOT NULL DEFAULT 'self_verification',
    verified_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_handle_owners_user ON handle_owners (user_id);

CREATE TABLE IF NOT EXISTS auth_identities (
    identity_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    provider_subject TEXT NOT NULL,
    email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(provider, provider_subject)
);
CREATE INDEX IF NOT EXISTS idx_auth_identities_user ON auth_identities (user_id);

CREATE TABLE IF NOT EXISTS practice_submissions (
    submission_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    claim_token TEXT,
    problem_id TEXT NOT NULL,
    pack_id TEXT NOT NULL,
    pack_version INTEGER NOT NULL,
    test_set_hash TEXT NOT NULL,
    language TEXT NOT NULL,
    source TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    client_request_hash TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    queue_item_id TEXT,
    handle_context TEXT,
    status TEXT NOT NULL DEFAULT 'judging',
    status_id INTEGER,
    judged INTEGER NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    runtime_ms INTEGER,
    memory_kb INTEGER,
    message TEXT NOT NULL DEFAULT '',
    completion_id TEXT,
    response_json TEXT,
    created_at TEXT NOT NULL,
    judged_at TEXT,
    UNIQUE(user_id, request_id)
);
CREATE INDEX IF NOT EXISTS idx_practice_submissions_user_problem
    ON practice_submissions (user_id, problem_id, created_at DESC);

CREATE TABLE IF NOT EXISTS practice_completions (
    completion_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    completion_mode TEXT NOT NULL DEFAULT 'solvex_practice',
    first_submission_id TEXT NOT NULL,
    source TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    UNIQUE(user_id, problem_id, completion_mode)
);
CREATE INDEX IF NOT EXISTS idx_practice_completions_user
    ON practice_completions (user_id, completed_at DESC);

CREATE TABLE IF NOT EXISTS practice_continuations (
    recommendation_id TEXT PRIMARY KEY,
    completion_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_queue_item_id TEXT,
    problem_id TEXT,
    name TEXT,
    rating INTEGER,
    tags TEXT NOT NULL DEFAULT '[]',
    target_skill TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    exhausted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_practice_continuations_user_status
    ON practice_continuations (user_id, status, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_practice_continuations_user_problem_once
    ON practice_continuations (user_id, problem_id)
    WHERE problem_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS problem_import_batches (
    batch_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    manifest_version TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_catalog INTEGER NOT NULL DEFAULT 0,
    imported INTEGER NOT NULL DEFAULT 0,
    updated INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    quarantined INTEGER NOT NULL DEFAULT 0,
    catalog_rows_created INTEGER NOT NULL DEFAULT 0,
    catalog_rows_existing_skipped INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_problem_import_batches_started ON problem_import_batches (started_at DESC);

-- Display content ONLY, mirrors db/migrations/025_problem_statement_import.sql.
-- See contestiq_api/cfdata/problem_import.py: `editorial` and `reference_code`
-- are dropped at the parse boundary and never reach this table, and this
-- pipeline never touches duel_problem_packs or judge_tests.
CREATE TABLE IF NOT EXISTS problem_statements (
    problem_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    title TEXT,
    statement TEXT,
    input_format TEXT,
    output_format TEXT,
    interaction_format TEXT,
    notes TEXT,
    samples TEXT NOT NULL DEFAULT '[]',
    time_limit_seconds REAL,
    memory_limit_megabytes REAL,
    difficulty TEXT,
    io_mode TEXT,
    is_interactive INTEGER NOT NULL DEFAULT 0,
    picture_count INTEGER,
    has_missing_diagrams INTEGER NOT NULL DEFAULT 0,
    availability_status TEXT NOT NULL,
    display_ready INTEGER NOT NULL DEFAULT 0,
    solve_ready INTEGER NOT NULL DEFAULT 0,
    unavailable_reason TEXT,
    source_dataset TEXT,
    source_urls TEXT NOT NULL DEFAULT '[]',
    statement_relation TEXT,
    shared_statement_from TEXT,
    imported_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_problem_statements_batch ON problem_statements (batch_id);
CREATE INDEX IF NOT EXISTS idx_problem_statements_availability ON problem_statements (availability_status);

CREATE TABLE IF NOT EXISTS problem_import_quarantine (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    problem_id TEXT,
    reason TEXT NOT NULL,
    detail TEXT,
    quarantined_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_problem_import_quarantine_batch ON problem_import_quarantine (batch_id, quarantined_at DESC);

-- Runtime queue for automatic CF HTML statement ingestion (026).
CREATE TABLE IF NOT EXISTS statement_ingest_queue (
    problem_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    priority_contest_id INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    last_error TEXT,
    next_attempt_at TEXT,
    discovered_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL,
    leased_until TEXT,
    leased_by TEXT,
    failure_class TEXT,
    last_http_status INTEGER,
    last_fetch_url TEXT,
    fetch_content_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_statement_ingest_queue_status_next
    ON statement_ingest_queue (status, next_attempt_at, priority_contest_id DESC);

CREATE TABLE IF NOT EXISTS statement_relay_heartbeats (
    relay_id TEXT PRIMARY KEY,
    version TEXT,
    last_seen_at TEXT NOT NULL,
    last_successful_fetch_at TEXT,
    jobs_succeeded INTEGER NOT NULL DEFAULT 0,
    jobs_failed INTEGER NOT NULL DEFAULT 0,
    jobs_blocked INTEGER NOT NULL DEFAULT 0,
    note TEXT
);
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
        ("test_input", "TEXT"),
        ("test_expected_output", "TEXT"),
        ("test_locked_by", "TEXT"),
        ("test_locked_at", "TEXT"),
        ("problem_pack_id", "TEXT"),
        ("test_cases_json", "TEXT"),
        ("test_set_hash", "TEXT"),
    ],
    "statement_ingest_queue": [
        ("leased_until", "TEXT"),
        ("leased_by", "TEXT"),
        ("failure_class", "TEXT"),
        ("last_http_status", "INTEGER"),
        ("last_fetch_url", "TEXT"),
        ("fetch_content_hash", "TEXT"),
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
    # Safe to create after lease columns exist on upgraded DBs.
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_statement_ingest_queue_lease
        ON statement_ingest_queue (status, next_attempt_at, priority_contest_id DESC)
        """
    )
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


def save_problemset_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    """Upsert CF ``problemset.problems`` into the canonical catalog.

    Never deletes historical rows. Returns counts plus newly inserted keys so
    callers can enqueue statement-pending stubs without a second scan.
    """
    now = _now()
    problems = raw.get("problems", [])
    stats = raw.get("problemStatistics", [])
    new_problem_ids: list[str] = []
    updated_problems = 0
    unchanged_problems = 0
    skipped_malformed = 0

    with connect() as conn:
        conn.execute(
            "INSERT INTO cf_problemset_raw (id, raw_json, fetched_at, problem_count) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), json.dumps(raw, ensure_ascii=False), now, len(problems)),
        )
        for problem in problems:
            if not isinstance(problem, dict):
                skipped_malformed += 1
                continue
            contest_id = problem.get("contestId")
            problem_index = problem.get("index")
            if contest_id is None or not isinstance(problem_index, str) or not problem_index.strip():
                skipped_malformed += 1
                continue
            try:
                key = stable_problem_key(problem)
            except Exception:
                skipped_malformed += 1
                continue
            # Canonical CF identities are contestId+index only — reject fallback keys.
            expected = f"{contest_id}{problem_index.strip()}"
            if not key or key != expected:
                skipped_malformed += 1
                continue

            name = problem.get("name") or "Unknown"
            rating = problem.get("rating")
            tags_json = json.dumps(problem.get("tags") or [], ensure_ascii=False)
            problemset_name = problem.get("problemsetName")

            existing = conn.execute(
                "SELECT name, rating, tags, contest_id, problem_index, problemset_name FROM problems WHERE problem_key = ?",
                (key,),
            ).fetchone()
            if existing is None:
                new_problem_ids.append(key)
            else:
                existing_tags = existing["tags"] or "[]"
                same = (
                    existing["name"] == name
                    and existing["rating"] == rating
                    and existing_tags == tags_json
                    and existing["contest_id"] == contest_id
                    and existing["problem_index"] == problem_index
                    and existing["problemset_name"] == problemset_name
                )
                if same:
                    unchanged_problems += 1
                else:
                    updated_problems += 1

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
                    key,
                    contest_id,
                    problem_index,
                    name,
                    rating,
                    tags_json,
                    problemset_name,
                    now,
                ),
            )
        for stat in stats:
            if not isinstance(stat, dict):
                continue
            try:
                key = stable_problem_key(stat)
            except Exception:
                continue
            if not key:
                continue
            conn.execute(
                """
                INSERT INTO problem_statistics (problem_key, solved_count, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(problem_key) DO UPDATE SET
                    solved_count=excluded.solved_count,
                    updated_at=excluded.updated_at
                """,
                (key, stat.get("solvedCount"), now),
            )

    stub_count = ensure_statement_pending_stubs(new_problem_ids)
    try:
        from contestiq_api.cfdata import statement_ingest

        if new_problem_ids:
            statement_ingest.enqueue_statement_ingestion(
                list(new_problem_ids), reason="catalog_sync"
            )
    except Exception:
        pass
    return {
        "problems": len(problems),
        "statistics": len(stats),
        "new_problems": len(new_problem_ids),
        "updated_problems": updated_problems,
        "unchanged_problems": unchanged_problems,
        "skipped_malformed": skipped_malformed,
        "new_problem_ids": new_problem_ids,
        "statement_stubs_created": stub_count,
    }


def ensure_statement_pending_stubs(problem_ids: list[str]) -> int:
    """Insert ``missing`` statement rows for new catalog IDs lacking content.

    Catalog membership must not depend on statement ingestion. These stubs keep
    availability explicit (pending/missing, not Arena-capable) until a verified
    archive import fills display-ready content. Existing statement rows are never
    overwritten.
    """
    if not problem_ids:
        return 0
    now = _now()
    batch_id = "cf-catalog-sync"
    created = 0
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_import_batches
                (batch_id, source_name, source_sha256, status, started_at)
            VALUES (?, 'codeforces-catalog-sync', 'n/a', 'completed', ?)
            """,
            (batch_id, now),
        )
        for problem_id in problem_ids:
            if not problem_id:
                continue
            existing = conn.execute(
                "SELECT 1 FROM problem_statements WHERE problem_id = ?",
                (problem_id,),
            ).fetchone()
            if existing is not None:
                continue
            conn.execute(
                """
                INSERT INTO problem_statements (
                    problem_id, batch_id, content_hash, title, statement,
                    input_format, output_format, interaction_format, notes, samples,
                    time_limit_seconds, memory_limit_megabytes, difficulty, io_mode,
                    is_interactive, picture_count, has_missing_diagrams,
                    availability_status, display_ready, solve_ready, unavailable_reason,
                    source_dataset, source_urls, statement_relation, shared_statement_from,
                    imported_at
                ) VALUES (
                    ?, ?, ?, NULL, NULL,
                    NULL, NULL, NULL, NULL, '[]',
                    NULL, NULL, NULL, NULL,
                    0, NULL, 0,
                    'missing', 0, 0, 'Statement not available in SolveX yet.',
                    NULL, '[]', NULL, NULL, ?
                )
                """,
                (problem_id, batch_id, f"pending-{problem_id}", now),
            )
            created += 1
    return created


def list_problem_keys() -> set[str]:
    with connect() as conn:
        rows = conn.execute("SELECT problem_key FROM problems").fetchall()
    return {row["problem_key"] for row in rows}


def catalog_parity_report(cf_problem_ids: set[str] | list[str]) -> dict[str, Any]:
    """Compare an authoritative CF identity set against the local catalog."""
    cf_ids = {str(pid) for pid in cf_problem_ids if pid}
    local = list_problem_keys()
    cf_only = sorted(cf_ids - local)
    solvex_only = sorted(local - cf_ids)
    return {
        "cf_total": len(cf_ids),
        "solvex_total": len(local),
        "matched": len(cf_ids & local),
        "missing_from_solvex": len(cf_only),
        "extra_historical_solvex": len(solvex_only),
        "cf_only_ids": cf_only,
        "solvex_only_ids": solvex_only,
        "missing_from_solvex_after": len(cf_only),
    }


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


def find_problems_by_name_rating(name: str, rating: Any = None) -> list[dict[str, Any]]:
    """Lookup catalog rows by case-insensitive name, optionally exact rating.

    Used to remap Div1/Div2/Technocup mirror submission IDs onto the single
    ``problemset.problems`` identity stored in SolveX.
    """
    normalized = (name or "").strip().lower()
    if not normalized:
        return []
    with connect() as conn:
        if rating is None:
            rows = conn.execute(
                """
                SELECT problem_key, contest_id, problem_index, name, rating, tags
                FROM problems
                WHERE lower(name) = ?
                """,
                (normalized,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT problem_key, contest_id, problem_index, name, rating, tags
                FROM problems
                WHERE lower(name) = ? AND rating = ?
                """,
                (normalized, rating),
            ).fetchall()
    return [dict(row) for row in rows]


def get_active_public_problem_content(problem_key: str) -> dict[str, Any] | None:
    """Return only authored fields safe for the public problem catalog API.

    Hidden judge tests and internal pack identifiers are intentionally absent
    from the SELECT list so callers cannot serialize them accidentally.
    """
    with connect() as conn:
        row = conn.execute(
            """
            SELECT version, statement_summary, input_format, output_format,
                   constraints_text, sample_tests
            FROM duel_problem_packs
            WHERE problem_id = ? AND active = 1
            ORDER BY version DESC
            LIMIT 1
            """,
            (problem_key,),
        ).fetchone()
    return dict(row) if row else None


def get_problem_statement(problem_id: str) -> dict[str, Any] | None:
    """Return only PUBLIC display content imported by problem_import.py.

    Columns are listed explicitly (never `SELECT *`): `editorial` and
    `reference_code` from the source dataset were never imported into this
    table in the first place (see contestiq_api/cfdata/problem_import.py),
    and there are no judge-test or duel/pack columns on this table at all —
    this reader must stay that way even if the table gains columns later.
    """
    with connect() as conn:
        row = conn.execute(
            """
            SELECT problem_id, title, statement, input_format, output_format,
                   interaction_format, notes, samples, time_limit_seconds,
                   memory_limit_megabytes, difficulty, io_mode, is_interactive,
                   has_missing_diagrams, availability_status, display_ready,
                   solve_ready, unavailable_reason, source_dataset, source_urls,
                   statement_relation, shared_statement_from
            FROM problem_statements
            WHERE problem_id = ?
            """,
            (problem_id,),
        ).fetchone()
    return dict(row) if row else None


def is_problem_statement_display_ready(problem_id: str) -> bool:
    """True when Arena can show a verified imported statement for ``problem_id``."""
    with connect() as conn:
        row = conn.execute(
            """
            SELECT display_ready, statement
            FROM problem_statements
            WHERE problem_id = ?
            """,
            (problem_id,),
        ).fetchone()
    if row is None:
        return False
    if not bool(row["display_ready"]):
        return False
    statement = row["statement"] or ""
    return bool(str(statement).strip())


def list_display_ready_problem_ids(problem_ids: list[str] | None = None) -> set[str]:
    """Return the subset of IDs (or all catalog statements) that are display-ready."""
    with connect() as conn:
        if problem_ids is None:
            rows = conn.execute(
                """
                SELECT problem_id FROM problem_statements
                WHERE display_ready = 1
                  AND statement IS NOT NULL
                  AND TRIM(statement) != ''
                """
            ).fetchall()
            return {row["problem_id"] for row in rows}
        ready: set[str] = set()
        chunk = 400
        for offset in range(0, len(problem_ids), chunk):
            batch = [pid for pid in problem_ids[offset : offset + chunk] if pid]
            if not batch:
                continue
            placeholders = ",".join("?" for _ in batch)
            rows = conn.execute(
                f"""
                SELECT problem_id FROM problem_statements
                WHERE problem_id IN ({placeholders})
                  AND display_ready = 1
                  AND statement IS NOT NULL
                  AND TRIM(statement) != ''
                """,
                batch,
            ).fetchall()
            ready.update(row["problem_id"] for row in rows)
        return ready


def arena_catalog_coverage_stats() -> dict[str, Any]:
    """Counts for scripts/audit_arena_catalog_coverage.py and ops diagnostics."""
    with connect() as conn:
        total_problems = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        statement_rows = conn.execute("SELECT COUNT(*) FROM problem_statements").fetchone()[0]
        display_ready = conn.execute(
            """
            SELECT COUNT(*) FROM problem_statements
            WHERE display_ready = 1 AND statement IS NOT NULL AND TRIM(statement) != ''
            """
        ).fetchone()[0]
        solve_ready = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE solve_ready = 1"
        ).fetchone()[0]
        by_status = {
            row["availability_status"]: row["c"]
            for row in conn.execute(
                """
                SELECT availability_status, COUNT(*) AS c
                FROM problem_statements
                GROUP BY availability_status
                """
            ).fetchall()
        }
        missing_content = conn.execute(
            """
            SELECT COUNT(*) FROM problems p
            LEFT JOIN problem_statements s ON s.problem_id = p.problem_key
            WHERE s.problem_id IS NULL
               OR s.display_ready = 0
               OR s.statement IS NULL
               OR TRIM(s.statement) = ''
            """
        ).fetchone()[0]
        sample_missing = [
            row["problem_key"]
            for row in conn.execute(
                """
                SELECT p.problem_key FROM problems p
                LEFT JOIN problem_statements s ON s.problem_id = p.problem_key
                WHERE s.problem_id IS NULL
                   OR s.display_ready = 0
                   OR s.statement IS NULL
                   OR TRIM(s.statement) = ''
                ORDER BY p.contest_id DESC, p.problem_index
                LIMIT 40
                """
            ).fetchall()
        ]
        probe_2228b = conn.execute(
            """
            SELECT p.problem_key AS in_catalog,
                   s.problem_id AS statement_row,
                   s.availability_status,
                   s.display_ready,
                   CASE
                     WHEN s.statement IS NOT NULL AND TRIM(s.statement) != '' THEN 1
                     ELSE 0
                   END AS has_statement_text
            FROM problems p
            LEFT JOIN problem_statements s ON s.problem_id = p.problem_key
            WHERE p.problem_key = '2228B'
            """
        ).fetchone()
    return {
        "total_canonical_problems": int(total_problems),
        "with_statement_row": int(statement_rows),
        "display_ready": int(display_ready),
        "solve_ready": int(solve_ready),
        "missing_or_not_display_ready": int(missing_content),
        "availability_status_counts": by_status,
        "sample_missing_ids": sample_missing,
        "probe_2228B": dict(probe_2228b) if probe_2228b else None,
    }


# ─── Statement ingest queue ───────────────────────────────────────────────────


def _contest_id_from_problem_id(problem_id: str) -> int:
    digits = []
    for ch in problem_id:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    try:
        return int("".join(digits)) if digits else 0
    except ValueError:
        return 0


def list_non_display_ready_problem_ids() -> list[str]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT problem_id
            FROM problem_statements
            WHERE display_ready = 0
               OR statement IS NULL
               OR TRIM(COALESCE(statement, '')) = ''
            """
        ).fetchall()
    return [row["problem_id"] for row in rows]


def enqueue_statement_ingest(problem_ids: list[str], *, reason: str = "manual") -> int:
    """Insert or re-queue problem IDs. Does not reset terminal succeeded rows unless missing again."""
    if not problem_ids:
        return 0
    now = _now()
    touched = 0
    with connect() as conn:
        for problem_id in problem_ids:
            if not problem_id:
                continue
            priority = _contest_id_from_problem_id(problem_id)
            existing = conn.execute(
                "SELECT status FROM statement_ingest_queue WHERE problem_id = ?",
                (problem_id,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO statement_ingest_queue (
                        problem_id, status, attempts, priority_contest_id, reason,
                        last_error, next_attempt_at, discovered_at, started_at,
                        completed_at, updated_at
                    ) VALUES (?, 'pending', 0, ?, ?, NULL, ?, ?, NULL, NULL, ?)
                    """,
                    (problem_id, priority, reason, now, now, now),
                )
                touched += 1
                continue
            status = existing["status"]
            if status in {"pending", "processing", "retrying"}:
                continue
            # Re-queue failed / partial / asset_required for another pass when asked.
            if status in {"failed", "partial", "asset_required", "succeeded"}:
                # Only re-queue succeeded if statement is still not display-ready.
                if status == "succeeded":
                    stmt = conn.execute(
                        "SELECT display_ready, statement FROM problem_statements WHERE problem_id = ?",
                        (problem_id,),
                    ).fetchone()
                    if stmt is not None and bool(stmt["display_ready"]) and (stmt["statement"] or "").strip():
                        continue
                conn.execute(
                    """
                    UPDATE statement_ingest_queue
                    SET status = 'pending',
                        reason = ?,
                        last_error = NULL,
                        next_attempt_at = ?,
                        completed_at = NULL,
                        updated_at = ?
                    WHERE problem_id = ?
                    """,
                    (reason, now, now, problem_id),
                )
                touched += 1
    return touched


def claim_statement_ingest_batch(
    *,
    limit: int = 25,
    problem_ids: list[str] | None = None,
    now_iso: str | None = None,
    leased_by: str | None = None,
    lease_seconds: int = 600,
) -> list[str]:
    now = now_iso or _now()
    claimed: list[str] = []
    lease_until = None
    if leased_by:
        from datetime import datetime, timedelta, timezone

        try:
            base = datetime.fromisoformat(now.replace("Z", "+00:00"))
        except ValueError:
            base = datetime.now(timezone.utc)
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        lease_until = (base + timedelta(seconds=int(lease_seconds))).isoformat()

    with connect() as conn:
        if problem_ids:
            rows = []
            for problem_id in problem_ids:
                row = conn.execute(
                    """
                    SELECT problem_id, status, next_attempt_at, leased_until
                    FROM statement_ingest_queue
                    WHERE problem_id = ?
                    """,
                    (problem_id,),
                ).fetchone()
                if row is not None:
                    rows.append(row)
                else:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO statement_ingest_queue (
                            problem_id, status, attempts, priority_contest_id, reason,
                            last_error, next_attempt_at, discovered_at, started_at,
                            completed_at, updated_at
                        ) VALUES (?, 'pending', 0, ?, 'explicit', NULL, ?, ?, NULL, NULL, ?)
                        """,
                        (
                            problem_id,
                            _contest_id_from_problem_id(problem_id),
                            now,
                            now,
                            now,
                        ),
                    )
                    row = conn.execute(
                        "SELECT problem_id, status, next_attempt_at, leased_until FROM statement_ingest_queue WHERE problem_id = ?",
                        (problem_id,),
                    ).fetchone()
                    if row is not None:
                        rows.append(row)
        else:
            rows = conn.execute(
                """
                SELECT problem_id, status, next_attempt_at, leased_until
                FROM statement_ingest_queue
                WHERE status IN ('pending', 'retrying')
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                  AND (leased_until IS NULL OR leased_until <= ?)
                ORDER BY priority_contest_id DESC, problem_id DESC
                LIMIT ?
                """,
                (now, now, int(limit)),
            ).fetchall()

        for row in rows:
            if len(claimed) >= int(limit):
                break
            status = row["status"]
            next_at = row["next_attempt_at"]
            leased_until_existing = row["leased_until"] if "leased_until" in row.keys() else None
            if status not in {"pending", "retrying", "failed", "partial", "asset_required"}:
                if problem_ids is None:
                    continue
            if next_at and next_at > now and problem_ids is None:
                continue
            if leased_until_existing and leased_until_existing > now and problem_ids is None:
                continue
            conn.execute(
                """
                UPDATE statement_ingest_queue
                SET status = 'processing',
                    started_at = ?,
                    updated_at = ?,
                    attempts = attempts + 1,
                    leased_until = ?,
                    leased_by = ?
                WHERE problem_id = ?
                """,
                (now, now, lease_until, leased_by, row["problem_id"]),
            )
            claimed.append(row["problem_id"])
    return claimed


def lease_next_statement_jobs(
    *,
    limit: int = 1,
    relay_id: str,
    lease_seconds: int = 600,
    now_iso: str | None = None,
) -> list[dict[str, Any]]:
    """Atomically lease up to ``limit`` pending jobs for a relay worker."""
    now = now_iso or _now()
    # Expire abandoned leases back to pending/retrying.
    with connect() as conn:
        conn.execute(
            """
            UPDATE statement_ingest_queue
            SET status = CASE WHEN attempts > 0 THEN 'retrying' ELSE 'pending' END,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = ?
            WHERE status = 'processing'
              AND leased_until IS NOT NULL
              AND leased_until <= ?
            """,
            (now, now),
        )
    claimed_ids = claim_statement_ingest_batch(
        limit=limit,
        leased_by=relay_id,
        lease_seconds=lease_seconds,
        now_iso=now,
    )
    jobs: list[dict[str, Any]] = []
    with connect() as conn:
        for problem_id in claimed_ids:
            row = conn.execute(
                """
                SELECT problem_id, attempts, leased_until, priority_contest_id
                FROM statement_ingest_queue WHERE problem_id = ?
                """,
                (problem_id,),
            ).fetchone()
            if row is None:
                continue
            contest_id = int(row["priority_contest_id"] or _contest_id_from_problem_id(problem_id))
            index = problem_id[len(str(contest_id)) :]
            jobs.append(
                {
                    "problem_id": problem_id,
                    "contest_id": contest_id,
                    "index": index,
                    "official_url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
                    "attempt": int(row["attempts"] or 1),
                    "leased_until": row["leased_until"],
                    "leased_by": relay_id,
                }
            )
    return jobs


def record_statement_job_result(
    problem_id: str,
    *,
    relay_id: str,
    ok: bool,
    html: str | None = None,
    http_status: int | None = None,
    final_url: str | None = None,
    error: str | None = None,
    failure_class: str | None = None,
    content_hash: str | None = None,
    now_iso: str | None = None,
) -> dict[str, Any]:
    now = now_iso or _now()
    with connect() as conn:
        row = conn.execute(
            "SELECT attempts, leased_by FROM statement_ingest_queue WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
        if row is None:
            return {"accepted": False, "reason": "unknown_job"}
        # Allow result if lease holder matches OR lease expired (recovery).
        leased_by = row["leased_by"]
        if leased_by and leased_by != relay_id:
            lease = conn.execute(
                "SELECT leased_until FROM statement_ingest_queue WHERE problem_id = ?",
                (problem_id,),
            ).fetchone()
            leased_until = lease["leased_until"] if lease else None
            if leased_until and leased_until > now:
                return {"accepted": False, "reason": "lease_held_by_other"}

        conn.execute(
            """
            UPDATE statement_ingest_queue
            SET last_http_status = ?,
                last_fetch_url = ?,
                fetch_content_hash = ?,
                failure_class = ?,
                last_error = ?,
                updated_at = ?,
                leased_until = NULL,
                leased_by = NULL
            WHERE problem_id = ?
            """,
            (http_status, final_url, content_hash, failure_class, error, now, problem_id),
        )
    return {"accepted": True, "ok": ok, "attempts": int(row["attempts"] or 0)}


def upsert_relay_heartbeat(
    relay_id: str,
    *,
    version: str | None = None,
    note: str | None = None,
    successful_fetch: bool = False,
    failed: bool = False,
    blocked: bool = False,
    now_iso: str | None = None,
) -> None:
    now = now_iso or _now()
    with connect() as conn:
        existing = conn.execute(
            "SELECT * FROM statement_relay_heartbeats WHERE relay_id = ?",
            (relay_id,),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO statement_relay_heartbeats (
                    relay_id, version, last_seen_at, last_successful_fetch_at,
                    jobs_succeeded, jobs_failed, jobs_blocked, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    relay_id,
                    version,
                    now,
                    now if successful_fetch else None,
                    1 if successful_fetch else 0,
                    1 if failed else 0,
                    1 if blocked else 0,
                    note,
                ),
            )
            return
        conn.execute(
            """
            UPDATE statement_relay_heartbeats
            SET version = COALESCE(?, version),
                last_seen_at = ?,
                last_successful_fetch_at = CASE WHEN ? THEN ? ELSE last_successful_fetch_at END,
                jobs_succeeded = jobs_succeeded + ?,
                jobs_failed = jobs_failed + ?,
                jobs_blocked = jobs_blocked + ?,
                note = COALESCE(?, note)
            WHERE relay_id = ?
            """,
            (
                version,
                now,
                1 if successful_fetch else 0,
                now,
                1 if successful_fetch else 0,
                1 if failed else 0,
                1 if blocked else 0,
                note,
                relay_id,
            ),
        )


def statement_relay_observability(now_iso: str | None = None) -> dict[str, Any]:
    now = now_iso or _now()
    with connect() as conn:
        queue = statement_ingest_queue_stats()
        leased = conn.execute(
            """
            SELECT COUNT(*) AS c FROM statement_ingest_queue
            WHERE status = 'processing' AND leased_until IS NOT NULL AND leased_until > ?
            """,
            (now,),
        ).fetchone()["c"]
        oldest = conn.execute(
            """
            SELECT problem_id, discovered_at FROM statement_ingest_queue
            WHERE status IN ('pending', 'retrying')
            ORDER BY discovered_at ASC LIMIT 1
            """
        ).fetchone()
        heartbeats = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM statement_relay_heartbeats ORDER BY last_seen_at DESC"
            ).fetchall()
        ]
    relay_status = "offline"
    last_heartbeat = heartbeats[0] if heartbeats else None
    if last_heartbeat:
        from datetime import datetime, timezone

        try:
            seen = datetime.fromisoformat(str(last_heartbeat["last_seen_at"]).replace("Z", "+00:00"))
            if seen.tzinfo is None:
                seen = seen.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - seen).total_seconds()
            if age <= 180:
                relay_status = "healthy"
            elif age <= 900:
                relay_status = "degraded"
            else:
                relay_status = "offline"
        except ValueError:
            relay_status = "degraded"
    return {
        "pending_jobs": int(queue.get("pending", 0)) + int(queue.get("retrying", 0)),
        "leased_jobs": int(leased),
        "queue": queue,
        "oldest_pending_job": dict(oldest) if oldest else None,
        "last_relay_heartbeat": last_heartbeat,
        "relays": heartbeats,
        "relay_status": relay_status,
    }


def finish_statement_ingest(
    problem_id: str,
    *,
    status: str,
    detail: str | None = None,
    now_iso: str | None = None,
) -> None:
    now = now_iso or _now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE statement_ingest_queue
            SET status = ?,
                last_error = ?,
                completed_at = ?,
                updated_at = ?,
                next_attempt_at = NULL
            WHERE problem_id = ?
            """,
            (status, detail, now, now, problem_id),
        )


def get_statement_ingest_attempts(problem_id: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT attempts FROM statement_ingest_queue WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
    return int(row["attempts"]) if row else 0


def bump_statement_ingest_failure(
    problem_id: str,
    *,
    error: str,
    next_attempt_at: str,
    now_iso: str | None = None,
) -> int:
    now = now_iso or _now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE statement_ingest_queue
            SET status = 'retrying',
                last_error = ?,
                next_attempt_at = ?,
                updated_at = ?
            WHERE problem_id = ?
            """,
            (error, next_attempt_at, now, problem_id),
        )
        row = conn.execute(
            "SELECT attempts FROM statement_ingest_queue WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
    return int(row["attempts"]) if row else 0


def statement_ingest_queue_stats() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT status, COUNT(*) AS c
            FROM statement_ingest_queue
            GROUP BY status
            """
        ).fetchall()
        pending_ready = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM statement_ingest_queue
            WHERE status IN ('pending', 'retrying')
              AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            """,
            (_now(),),
        ).fetchone()["c"]
    by_status = {row["status"]: int(row["c"]) for row in rows}
    return {
        "by_status": by_status,
        "pending": int(by_status.get("pending", 0)),
        "processing": int(by_status.get("processing", 0)),
        "succeeded": int(by_status.get("succeeded", 0)),
        "partial": int(by_status.get("partial", 0)),
        "asset_required": int(by_status.get("asset_required", 0)),
        "failed": int(by_status.get("failed", 0)),
        "retrying": int(by_status.get("retrying", 0)),
        "due_now": int(pending_ready),
    }


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
