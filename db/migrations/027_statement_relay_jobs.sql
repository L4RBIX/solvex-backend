-- 027_statement_relay_jobs.sql
-- Leaseable statement-fetch jobs + relay heartbeats for the 24/7 fetch worker.
-- Display content only; judging/editorial boundaries unchanged.
-- Queue lease columns are applied via SQLite _COLUMN_MIGRATIONS on existing DBs.

create table if not exists statement_relay_heartbeats (
  relay_id text primary key,
  version text,
  last_seen_at timestamptz not null default now(),
  last_successful_fetch_at timestamptz,
  jobs_succeeded integer not null default 0,
  jobs_failed integer not null default 0,
  jobs_blocked integer not null default 0,
  note text
);

alter table statement_relay_heartbeats enable row level security;
