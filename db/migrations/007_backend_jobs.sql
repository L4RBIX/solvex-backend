-- 007_backend_jobs.sql
-- Persistent backend job records (analysis requests, future sync/verification jobs).
-- Canonical production schema; the local dev/test mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/jobs.py — keep both in sync.

create table if not exists backend_jobs (
  id uuid primary key,
  job_type text not null,
  status text not null check (status in ('queued', 'running', 'success', 'failed', 'cancelled', 'stale_cache_used')),
  input jsonb not null,
  result_ref text,
  error_message text,
  idempotency_key text unique,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

-- Expected queries: poll by id (pk), find active jobs of a type, recency listings.
create index if not exists idx_backend_jobs_type_status on backend_jobs (job_type, status);
create index if not exists idx_backend_jobs_created_at on backend_jobs (created_at desc);

-- Backend-owned table: no anon/authenticated access. Service role bypasses RLS.
alter table backend_jobs enable row level security;
