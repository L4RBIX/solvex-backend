-- 028_practice_pack_quality.sql
-- Versioned quality metadata for server-owned practice/PvP packs.
-- Hidden judge_tests remain in duel_problem_packs; this migration never
-- exposes them via public APIs.

alter table duel_problem_packs
  add column if not exists review_state text not null default 'reviewed';

alter table duel_problem_packs
  add column if not exists checker_type text not null default 'exact';

alter table duel_problem_packs
  add column if not exists oracle_strategy text;

alter table duel_problem_packs
  add column if not exists provenance jsonb not null default '{}'::jsonb;

alter table duel_problem_packs
  add column if not exists quality_report jsonb not null default '{}'::jsonb;

alter table duel_problem_packs
  add column if not exists mutation_score real;

alter table duel_problem_packs
  add column if not exists test_count integer;

alter table duel_problem_packs
  add column if not exists activated_at timestamptz;

-- Candidate / validation queue for automatic pack backfill.
create table if not exists practice_pack_jobs (
  job_id text primary key,
  problem_id text not null references problems(problem_key),
  status text not null default 'pending',
  support_class text,
  attempt_count integer not null default 0,
  last_error text,
  quality_report jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (problem_id)
);

create index if not exists idx_practice_pack_jobs_status
  on practice_pack_jobs (status, updated_at);

alter table practice_pack_jobs enable row level security;
