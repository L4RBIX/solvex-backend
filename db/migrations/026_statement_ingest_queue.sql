-- 026_statement_ingest_queue.sql
-- Runtime queue for automatic Codeforces HTML statement ingestion.
-- Display content only: the worker feeds problem_import.apply_statement_content
-- and never writes editorials, solutions, or duel/judge packs.

create table if not exists statement_ingest_queue (
  problem_id text primary key,
  status text not null
    check (status in (
      'pending', 'processing', 'succeeded', 'partial',
      'asset_required', 'failed', 'retrying'
    )),
  attempts integer not null default 0,
  priority_contest_id integer not null default 0,
  reason text,
  last_error text,
  next_attempt_at timestamptz,
  discovered_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists idx_statement_ingest_queue_status_next
  on statement_ingest_queue (status, next_attempt_at, priority_contest_id desc);

alter table statement_ingest_queue enable row level security;
