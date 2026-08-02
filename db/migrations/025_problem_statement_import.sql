-- 025_problem_statement_import.sql
-- Bulk-import pipeline for PUBLIC problem statement content (the SolveX
-- "problem database v1" export: manifest + catalog + content + two review
-- queues, produced by an offline dataset build).
--
-- This is DISPLAY content only. The importer at
-- contestiq_api/cfdata/problem_import.py deliberately never reads the
-- `editorial` or `reference_code` fields from the source content — they
-- contain full solutions and are dropped at the parse boundary before this
-- schema is ever touched. This pipeline also never writes to
-- duel_problem_packs and never reads or writes judge_tests: judging content
-- and display content are, and must remain, two separate tables with two
-- separate trust boundaries.
--
-- problem_id is intentionally NOT foreign-keyed to problems(problem_key):
-- this dataset's catalog (11k+ Codeforces problems) is broader than whatever
-- has been synced locally via the CF problemset API at import time, and the
-- import must not fail wholesale just because that sync hasn't caught up.

create table if not exists problem_import_batches (
  batch_id text primary key,
  source_name text not null,
  source_sha256 text not null,
  manifest_version text,
  status text not null default 'running'
    check (status in ('running', 'completed', 'failed')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  total_catalog integer not null default 0,
  imported integer not null default 0,
  updated integer not null default 0,
  skipped integer not null default 0,
  quarantined integer not null default 0
);
create index if not exists idx_problem_import_batches_started
  on problem_import_batches (started_at desc);

create table if not exists problem_statements (
  problem_id text primary key,
  batch_id text not null references problem_import_batches(batch_id),
  content_hash text not null,
  title text,
  statement text,
  input_format text,
  output_format text,
  interaction_format text,
  notes text,
  samples jsonb not null default '[]'::jsonb,
  time_limit_seconds real,
  memory_limit_megabytes real,
  difficulty text,
  io_mode text check (io_mode in ('stdio', 'file')),
  is_interactive boolean not null default false,
  picture_count integer,
  has_missing_diagrams boolean not null default false,
  availability_status text not null
    check (availability_status in (
      'missing', 'asset_required', 'complete_interactive', 'partial', 'complete_standard'
    )),
  display_ready boolean not null default false,
  solve_ready boolean not null default false,
  unavailable_reason text,
  source_dataset text,
  source_urls jsonb not null default '[]'::jsonb,
  statement_relation text,
  shared_statement_from text,
  imported_at timestamptz not null default now()
);
create index if not exists idx_problem_statements_batch on problem_statements (batch_id);
create index if not exists idx_problem_statements_availability on problem_statements (availability_status);

create table if not exists problem_import_quarantine (
  id uuid primary key default gen_random_uuid(),
  batch_id text not null references problem_import_batches(batch_id),
  problem_id text,
  reason text not null,
  detail text,
  quarantined_at timestamptz not null default now()
);
create index if not exists idx_problem_import_quarantine_batch
  on problem_import_quarantine (batch_id, quarantined_at desc);

-- Service-role/backend access only, matching practice_* and product_events:
-- no anon/authenticated policies are intentionally defined.
alter table problem_import_batches enable row level security;
alter table problem_statements enable row level security;
alter table problem_import_quarantine enable row level security;
