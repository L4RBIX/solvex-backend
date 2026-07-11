-- 023_duel_problem_packs.sql
-- Server-owned, versioned problem content and judging tests for PvP duels.
-- Hidden tests are snapshotted onto the match when it is created, so later
-- pack changes cannot give two participants different judging data.

create table if not exists duel_problem_packs (
  pack_id text primary key,
  problem_id text not null references problems(problem_key),
  version integer not null check (version > 0),
  statement_summary text not null,
  input_format text not null,
  output_format text not null,
  constraints_text text not null,
  sample_tests jsonb not null default '[]'::jsonb,
  judge_tests jsonb not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (problem_id, version)
);

create index if not exists idx_duel_problem_packs_active
  on duel_problem_packs (active, problem_id, version desc);

alter table duel_matches add column if not exists problem_pack_id text
  references duel_problem_packs(pack_id);
alter table duel_matches add column if not exists test_cases_json jsonb;
alter table duel_matches add column if not exists test_set_hash text;

alter table duel_problem_packs enable row level security;
