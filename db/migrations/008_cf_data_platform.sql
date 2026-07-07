-- 008_cf_data_platform.sql
-- Codeforces data platform: raw API storage, normalized users/submissions/problems, sync jobs.
-- Canonical production schema; the local dev/test mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py — keep both in sync.

-- Every Codeforces API call (success or failure) is recorded for audit and stale-cache fallback.
create table if not exists cf_raw_api_responses (
  id uuid primary key,
  endpoint text not null,
  params_hash text not null,
  status text not null check (status in ('ok', 'failed', 'error')),
  raw_json jsonb,
  fetched_at timestamptz not null default now(),
  http_status int,
  error_message text
);
create index if not exists idx_cf_raw_lookup on cf_raw_api_responses (endpoint, params_hash, fetched_at desc);

create table if not exists cf_users (
  handle text primary key,              -- canonical lowercase
  display_handle text not null,
  rating int,
  max_rating int,
  rank text,
  max_rank text,
  country text,
  organization text,
  contribution int,
  registration_time bigint,
  raw_json jsonb,
  first_synced_at timestamptz,
  last_synced_at timestamptz,
  max_submission_id bigint,             -- incremental sync cursor
  submission_count int not null default 0
);

create table if not exists cf_user_rating_history (
  handle text not null,
  contest_id int not null,
  contest_name text,
  contest_rank int,
  old_rating int,
  new_rating int,
  rating_update_time bigint,
  primary key (handle, contest_id)
);

create table if not exists cf_submissions_raw (
  submission_id bigint primary key,
  handle text not null,
  raw_json jsonb not null,
  fetched_at timestamptz not null default now()
);
create index if not exists idx_cf_submissions_raw_handle on cf_submissions_raw (handle);

create table if not exists cf_submissions_normalized (
  submission_id bigint primary key,
  handle text not null,
  contest_id int,
  problem_index text,
  problem_key text not null,
  participant_type text,
  programming_language text,
  verdict text,
  passed_test_count int,
  time_consumed_ms int,
  memory_consumed_bytes bigint,
  creation_time bigint,
  relative_time_seconds bigint,
  problem_rating int,
  problem_tags_snapshot jsonb not null default '[]'::jsonb
);
create index if not exists idx_cf_submissions_norm_handle_time on cf_submissions_normalized (handle, creation_time desc);
create index if not exists idx_cf_submissions_norm_problem on cf_submissions_normalized (problem_key);

create table if not exists cf_problemset_raw (
  id uuid primary key,
  raw_json jsonb not null,
  fetched_at timestamptz not null default now(),
  problem_count int not null default 0
);
create index if not exists idx_cf_problemset_raw_fetched on cf_problemset_raw (fetched_at desc);

create table if not exists problems (
  problem_key text primary key,
  contest_id int,
  problem_index text,
  name text not null,
  rating int,                            -- nullable: many problems are unrated
  tags jsonb not null default '[]'::jsonb,
  problemset_name text,
  updated_at timestamptz not null default now()
);
create index if not exists idx_problems_rating on problems (rating);

create table if not exists problem_statistics (
  problem_key text primary key,
  solved_count int,
  updated_at timestamptz not null default now()
);

create table if not exists cf_sync_jobs (
  id uuid primary key,
  handle text,                           -- null for global problemset syncs
  sync_type text not null check (sync_type in ('full', 'incremental', 'problemset')),
  status text not null check (status in ('queued', 'running', 'success', 'failed', 'stale_cache_used')),
  stats jsonb not null default '{}'::jsonb,
  error_message text,
  idempotency_key text unique,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);
create index if not exists idx_cf_sync_jobs_handle on cf_sync_jobs (handle, created_at desc);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table cf_raw_api_responses enable row level security;
alter table cf_users enable row level security;
alter table cf_user_rating_history enable row level security;
alter table cf_submissions_raw enable row level security;
alter table cf_submissions_normalized enable row level security;
alter table cf_problemset_raw enable row level security;
alter table problems enable row level security;
alter table problem_statistics enable row level security;
alter table cf_sync_jobs enable row level security;
