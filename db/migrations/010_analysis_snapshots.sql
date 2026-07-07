-- 010_analysis_snapshots.sql
-- Immutable weakness-analysis snapshots. Runs are never mutated after completion;
-- a re-analysis inserts a new run. Canonical production schema; local mirror is
-- SQLite in backend/Trace_X_project/contestiq_api/cfdata/store.py — keep in sync.

create table if not exists analysis_runs (
  run_id uuid primary key,
  handle text not null,
  analysis_version text not null,
  taxonomy_version text not null,
  problem_catalog_version text not null,
  data_cutoff_time bigint,               -- epoch seconds of newest submission considered
  input_data_hash text not null,         -- sha256 over episode hashes + skill map + global rating
  global_rating int,
  global_rating_source text check (global_rating_source in ('cf_users', 'global_default')),
  episode_count int not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists idx_analysis_runs_handle on analysis_runs (handle, created_at desc);

create table if not exists analysis_skill_scores (
  run_id uuid not null references analysis_runs(run_id),
  skill_id text not null,
  status text not null check (status in (
    'strength', 'likely_strength', 'likely_weakness', 'possible_weakness',
    'underexposed', 'insufficient_evidence', 'historical_weakness_recent_improvement',
    'maintenance_needed', 'calibration_needed'
  )),
  confidence real not null,
  severity int not null,
  underexposure real not null,
  estimated_skill_rating int,
  estimated_skill_rating_low int,
  estimated_skill_rating_high int,
  explanation text not null,
  primary key (run_id, skill_id)
);

create table if not exists analysis_skill_evidence (
  run_id uuid not null references analysis_runs(run_id),
  skill_id text not null,
  evidence jsonb not null,
  primary key (run_id, skill_id)
);

create table if not exists analysis_warnings (
  run_id uuid not null references analysis_runs(run_id),
  skill_id text not null default '*',    -- '*' marks run-level warnings
  warning text not null,
  primary key (run_id, skill_id, warning)
);

create table if not exists analysis_problem_evidence (
  run_id uuid not null references analysis_runs(run_id),
  skill_id text not null,
  episode_id uuid not null,
  problem_id text not null,
  mapping_weight real not null,
  recency_weight real not null,
  final_status text not null,
  problem_rating int,
  primary key (run_id, skill_id, episode_id)
);

create table if not exists user_skill_history (
  handle text not null,
  skill_id text not null,
  run_id uuid not null references analysis_runs(run_id),
  status text not null,
  severity int not null,
  confidence real not null,
  estimated_skill_rating int,
  created_at timestamptz not null default now(),
  primary key (handle, skill_id, run_id)
);
create index if not exists idx_user_skill_history on user_skill_history (handle, skill_id, created_at desc);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table analysis_runs enable row level security;
alter table analysis_skill_scores enable row level security;
alter table analysis_skill_evidence enable row level security;
alter table analysis_warnings enable row level security;
alter table analysis_problem_evidence enable row level security;
alter table user_skill_history enable row level security;
