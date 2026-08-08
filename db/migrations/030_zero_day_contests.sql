-- 030_zero_day_contests.sql
-- First-class CF contests + per-problem zero-day lifecycle timestamps.

create table if not exists cf_contests (
  contest_id integer primary key,
  name text not null,
  type text,
  phase text not null,
  frozen integer not null default 0,
  duration_seconds integer,
  start_time integer,
  relative_time_seconds integer,
  prepared_by text,
  website_url text,
  description text,
  difficulty integer,
  kind text,
  icpc_region text,
  country text,
  city text,
  season text,
  is_gym integer not null default 0,
  finished_at text,
  pipeline_status text not null default 'idle',
  pipeline_started_at text,
  pipeline_completed_at text,
  pipeline_error text,
  discovered_at text not null,
  updated_at text not null,
  raw_json text
);

create index if not exists idx_cf_contests_phase_start
  on cf_contests (phase, start_time desc);

create index if not exists idx_cf_contests_pipeline
  on cf_contests (pipeline_status, updated_at);

create table if not exists problem_lifecycle (
  problem_id text primary key,
  contest_id integer,
  stage text not null default 'DISCOVERED',
  support_class text,
  discovered_at text,
  catalog_imported_at text,
  statement_imported_at text,
  arena_ready_at text,
  local_test_ready_at text,
  pack_generation_at text,
  submit_ready_at text,
  fully_indexed_at text,
  unsupported_reason text,
  updated_at text not null
);

create index if not exists idx_problem_lifecycle_contest
  on problem_lifecycle (contest_id, stage);

create index if not exists idx_problem_lifecycle_stage
  on problem_lifecycle (stage, updated_at);

create table if not exists problem_similar (
  problem_id text not null,
  similar_problem_id text not null,
  score real not null,
  reasons text not null default '[]',
  updated_at text not null,
  primary key (problem_id, similar_problem_id)
);

create index if not exists idx_problem_similar_score
  on problem_similar (problem_id, score desc);

create table if not exists contest_pipeline_events (
  event_id text primary key,
  contest_id integer not null,
  event_type text not null,
  detail text not null default '{}',
  created_at text not null
);

create index if not exists idx_contest_pipeline_events_contest
  on contest_pipeline_events (contest_id, created_at desc);
