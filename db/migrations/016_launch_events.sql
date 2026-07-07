-- 016_launch_events.sql
-- Launch readiness (Phase 10): onboarding/retention product events and the
-- weekly progress report store. Canonical production schema; local mirror is
-- SQLite in backend/Trace_X_project/contestiq_api/cfdata/store.py.

create table if not exists product_events (
  event_id uuid primary key,
  event_type text not null,
  subject text not null,                -- user:<id> or handle:<handle>
  properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_product_events_type on product_events (event_type, created_at desc);
create index if not exists idx_product_events_subject on product_events (subject, created_at desc);
-- first_* onboarding events are recorded at most once per subject.
create unique index if not exists idx_product_events_once on product_events (event_type, subject)
  where event_type like 'first_%';

create table if not exists weekly_reports (
  report_id uuid primary key,
  handle text not null,
  week_start date not null,
  content jsonb not null,
  created_at timestamptz not null default now(),
  unique (handle, week_start)
);
create index if not exists idx_weekly_reports_handle on weekly_reports (handle, week_start desc);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table product_events enable row level security;
alter table weekly_reports enable row level security;
