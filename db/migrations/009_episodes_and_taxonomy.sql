-- 009_episodes_and_taxonomy.sql
-- Problem episodes (one diagnostic unit per user+problem) and versioned skill taxonomy.
-- Canonical production schema; local dev/test mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py (timestamps stored there
-- as epoch seconds; here as timestamptz) — keep both in sync.

create table if not exists problem_episodes (
  episode_id uuid primary key,          -- deterministic uuid5(handle, problem_id): rebuilds are idempotent
  user_id uuid,                          -- linked once auth users exist (Phase 06+)
  handle text not null,
  problem_id text not null,
  first_submission_id bigint,
  first_attempt_at timestamptz,
  first_ac_submission_id bigint,
  first_ac_at timestamptz,
  last_submission_at timestamptz,
  total_submissions int not null,
  failed_before_ac int not null,
  final_status text not null check (final_status in ('clean_solve', 'solved_with_friction', 'delayed_ac', 'abandoned')),
  eventual_ac boolean not null,
  participant_type_primary text,
  context_type text check (context_type in ('contest', 'virtual', 'practice', 'other')),
  problem_rating int,
  user_rating_at_time int,
  rating_anchor_source text check (rating_anchor_source in ('rating_history', 'current_rating', 'global_default')),
  rating_gap int,
  rating_band text not null check (rating_band in ('consolidation', 'on_level', 'stretch', 'out_of_band', 'unknown_difficulty')),
  verdict_sequence jsonb not null default '[]'::jsonb,
  passed_test_progression jsonb not null default '[]'::jsonb,
  episode_hash text not null,
  unique (handle, problem_id)
);
create index if not exists idx_problem_episodes_handle on problem_episodes (handle, last_submission_at desc);
create index if not exists idx_problem_episodes_problem on problem_episodes (problem_id);

create table if not exists taxonomy_versions (
  version text primary key,
  description text,
  skill_count int not null,
  created_at timestamptz not null default now()
);

create table if not exists skill_taxonomy (
  skill_id text not null,
  taxonomy_version text not null references taxonomy_versions(version),
  parent_id text,
  display_name text not null,
  level int not null,                    -- 0 = top-level skill, 1 = leaf
  primary key (skill_id, taxonomy_version)
);
create index if not exists idx_skill_taxonomy_parent on skill_taxonomy (taxonomy_version, parent_id);

create table if not exists problem_skill_map (
  problem_id text not null,
  skill_id text not null,
  taxonomy_version text not null,
  weight real not null,                  -- normalized across a problem's skills, sums to ~1
  confidence real not null,
  mapping_source text not null check (mapping_source in ('cf_tag_rule', 'manual', 'llm_suggestion', 'empirical')),
  is_primary boolean not null default false,
  reviewed_by text,
  reviewed_at timestamptz,
  primary key (problem_id, skill_id, taxonomy_version)
);
create index if not exists idx_problem_skill_map_skill on problem_skill_map (taxonomy_version, skill_id);

create table if not exists mapping_review_queue (
  problem_id text not null,
  tag text not null,
  reason text not null,
  taxonomy_version text not null,
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  primary key (problem_id, tag, taxonomy_version)
);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table problem_episodes enable row level security;
alter table taxonomy_versions enable row level security;
alter table skill_taxonomy enable row level security;
alter table problem_skill_map enable row level security;
alter table mapping_review_queue enable row level security;
