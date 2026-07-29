-- 024_practice_completion_loop.sql
-- Authoritative SolveX Solo-practice judging and completion persistence.
--
-- These tables are backend-owned. They intentionally store only a source
-- hash and sanitized verdict metadata: source code, compiler diagnostics,
-- and server judge tests never enter this persistence layer.

create table if not exists practice_submissions (
  submission_id uuid primary key,
  user_id uuid not null references users(user_id) on delete cascade,
  request_id text not null,
  claim_token text,
  problem_id text not null references problems(problem_key),
  pack_id text not null references duel_problem_packs(pack_id),
  pack_version integer not null check (pack_version > 0),
  test_set_hash text not null,
  language text not null check (language in ('cpp17', 'python3')),
  source text not null check (
    source in (
      'retry_queue',
      'daily_queue',
      'seven_day_plan',
      'fourteen_day_plan',
      'direct_arena'
    )
  ),
  source_hash text not null,
  client_request_hash text not null,
  request_hash text not null,
  queue_item_id text,
  handle_context text,
  status text not null default 'judging',
  status_id integer,
  judged boolean not null default false,
  passed boolean not null default false,
  runtime_ms integer,
  memory_kb integer,
  message text not null default '',
  completion_id uuid,
  response_json jsonb,
  created_at timestamptz not null default now(),
  judged_at timestamptz,
  unique (user_id, request_id)
);
create index if not exists idx_practice_submissions_user_problem
  on practice_submissions (user_id, problem_id, created_at desc);

create table if not exists practice_completions (
  completion_id uuid primary key,
  user_id uuid not null references users(user_id) on delete cascade,
  problem_id text not null references problems(problem_key),
  completion_mode text not null default 'solvex_practice'
    check (completion_mode = 'solvex_practice'),
  first_submission_id uuid not null references practice_submissions(submission_id),
  source text not null check (
    source in (
      'retry_queue',
      'daily_queue',
      'seven_day_plan',
      'fourteen_day_plan',
      'direct_arena'
    )
  ),
  completed_at timestamptz not null default now(),
  unique (user_id, problem_id, completion_mode)
);
create index if not exists idx_practice_completions_user
  on practice_completions (user_id, completed_at desc);

create table if not exists practice_continuations (
  recommendation_id uuid primary key,
  completion_id uuid not null unique
    references practice_completions(completion_id) on delete cascade,
  user_id uuid not null references users(user_id) on delete cascade,
  source text not null,
  source_queue_item_id text,
  problem_id text references problems(problem_key),
  name text,
  rating integer,
  tags jsonb not null default '[]'::jsonb,
  target_skill text,
  reason text,
  status text not null default 'active'
    check (status in ('active', 'completed', 'exhausted')),
  exhausted boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_practice_continuations_user_status
  on practice_continuations (user_id, status, created_at desc);
create unique index if not exists idx_practice_continuations_user_problem_once
  on practice_continuations (user_id, problem_id)
  where problem_id is not null;

-- Service-role/backend access only. No anon/authenticated policies are
-- intentionally defined, matching product_events and solving telemetry.
alter table practice_submissions enable row level security;
alter table practice_completions enable row level security;
alter table practice_continuations enable row level security;
