-- 026_cf_verified_completion.sql
-- Canonical Solo completion history for both trusted SolveX practice judging
-- and server-verified Codeforces Accepted submissions.
--
-- `practice_completions` is deliberately retained as a compatibility ledger.
-- Existing rows are copied below; no legacy completion data is deleted.

-- Public handle-based queue/plan materializations keep owner_user_id NULL.
-- Authenticated materializations set it so one account can never reuse a
-- different owner's queue solely because both requests name the same handle.
alter table recommendation_runs
  add column if not exists owner_user_id uuid
  references users(user_id) on delete set null;
create index if not exists idx_recommendation_runs_owner
  on recommendation_runs (owner_user_id, handle, queue_date desc);

alter table training_plans
  add column if not exists owner_user_id uuid
  references users(user_id) on delete set null;
create index if not exists idx_training_plans_owner
  on training_plans (owner_user_id, handle, plan_type, start_date desc);

create table if not exists solo_problem_assignments (
  assignment_id uuid primary key,
  user_id uuid not null references users(user_id) on delete cascade,
  problem_id text not null references problems(problem_key),
  source text not null check (length(btrim(source)) > 0),
  queue_item_id text,
  assigned_at timestamptz not null default now(),
  opened_at timestamptz,
  status text not null default 'active'
    check (status in ('active', 'completed', 'superseded', 'dismissed')),
  completion_id uuid,
  check (opened_at is null or opened_at >= assigned_at)
);
create index if not exists idx_solo_problem_assignments_user
  on solo_problem_assignments (user_id, assigned_at desc);
create index if not exists idx_solo_problem_assignments_problem
  on solo_problem_assignments (problem_id, assigned_at desc);
create unique index if not exists idx_solo_problem_assignments_active
  on solo_problem_assignments (user_id, problem_id)
  where status = 'active';
create unique index if not exists idx_solo_problem_assignments_queue_item
  on solo_problem_assignments (user_id, source, queue_item_id)
  where queue_item_id is not null;

create table if not exists problem_completions (
  completion_id uuid primary key,
  user_id uuid not null references users(user_id) on delete cascade,
  problem_id text not null references problems(problem_key),
  completion_source text not null
    check (completion_source in ('solvex_practice_judge', 'codeforces_verified')),
  is_historical boolean not null default false,
  practice_submission_id uuid references practice_submissions(submission_id),
  codeforces_submission_id bigint,
  codeforces_handle text,
  contest_id integer,
  problem_index text,
  verdict text,
  programming_language text,
  codeforces_created_at timestamptz,
  verified_at timestamptz,
  assignment_id uuid references solo_problem_assignments(assignment_id)
    on delete set null,
  assigned_at timestamptz,
  queue_source text,
  queue_item_id text,
  completed_at timestamptz not null default now(),
  xp_awarded integer not null default 0 check (xp_awarded >= 0),
  history_updated boolean not null default false,
  daily_goal_updated boolean not null default false,
  streak_updated boolean not null default false,
  progress_updated boolean not null default false,
  queue_refreshed boolean not null default false,
  replacement_problem_id text references problems(problem_key),
  replacement_queue_item_id text,
  effects_applied_at timestamptz,
  unique (user_id, problem_id),
  check (not is_historical or completion_source = 'codeforces_verified'),
  check (not is_historical or xp_awarded = 0),
  check (is_historical or assigned_at is null or assigned_at <= completed_at),
  check (
    (completion_source = 'solvex_practice_judge'
      and practice_submission_id is not null
      and codeforces_submission_id is null
      and codeforces_handle is null
      and contest_id is null
      and problem_index is null
      and verdict is null
      and codeforces_created_at is null
      and verified_at is null)
    or
    (completion_source = 'codeforces_verified'
      and practice_submission_id is null
      and codeforces_submission_id is not null
      and codeforces_submission_id > 0
      and codeforces_handle is not null
      and length(btrim(codeforces_handle)) > 0
      and contest_id is not null
      and contest_id > 0
      and problem_index is not null
      and length(btrim(problem_index)) > 0
      and verdict = 'OK'
      and codeforces_created_at is not null
      and verified_at is not null)
  )
);
create index if not exists idx_problem_completions_user_history
  on problem_completions (user_id, completed_at desc);
create index if not exists idx_problem_completions_problem
  on problem_completions (problem_id, completed_at desc);
create unique index if not exists idx_problem_completions_cf_submission
  on problem_completions (codeforces_submission_id)
  where codeforces_submission_id is not null;

-- Preserve every legacy trusted-judge completion. The old schema did not
-- persist the daily-cap-adjusted XP amount, so the backfill intentionally
-- records zero rather than inventing an award. New writes persist exact XP.
insert into problem_completions (
  completion_id,
  user_id,
  problem_id,
  completion_source,
  is_historical,
  practice_submission_id,
  programming_language,
  queue_source,
  queue_item_id,
  completed_at,
  xp_awarded,
  history_updated,
  queue_refreshed,
  replacement_problem_id,
  replacement_queue_item_id
)
select
  pc.completion_id,
  pc.user_id,
  pc.problem_id,
  'solvex_practice_judge',
  false,
  pc.first_submission_id,
  ps.language,
  pc.source,
  ps.queue_item_id,
  pc.completed_at,
  0,
  true,
  (pco.recommendation_id is not null),
  pco.problem_id,
  pco.recommendation_id
from practice_completions pc
join practice_submissions ps
  on ps.submission_id = pc.first_submission_id
left join practice_continuations pco
  on pco.completion_id = pc.completion_id
on conflict (user_id, problem_id) do nothing;

-- Reuse the existing exactly-once continuation/replacement store for both
-- completion sources. The backfill above makes every legacy reference valid.
alter table practice_continuations
  drop constraint if exists practice_continuations_completion_id_fkey;
alter table practice_continuations
  add constraint practice_continuations_completion_id_fkey
  foreign key (completion_id) references problem_completions(completion_id)
  on delete cascade;

create table if not exists codeforces_completion_checks (
  check_id uuid primary key,
  user_id uuid not null references users(user_id) on delete cascade,
  problem_id text not null references problems(problem_key),
  codeforces_handle text not null check (length(btrim(codeforces_handle)) > 0),
  assignment_id uuid references solo_problem_assignments(assignment_id)
    on delete set null,
  completion_id uuid references problem_completions(completion_id)
    on delete set null,
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  cooldown_until timestamptz not null,
  result text not null default 'pending'
    check (result in ('pending', 'verified_ok', 'no_ok', 'cooldown', 'upstream_error')),
  response_source text
    check (response_source is null or response_source in ('cache', 'codeforces_api')),
  latest_submission_id bigint,
  latest_verdict text,
  matched_submission_id bigint,
  error_code text,
  check (cooldown_until >= requested_at),
  check (latest_submission_id is null or latest_submission_id > 0),
  check (matched_submission_id is null or matched_submission_id > 0),
  check (
    (result = 'pending' and completed_at is null)
    or (result <> 'pending' and completed_at is not null)
  )
);
create index if not exists idx_codeforces_completion_checks_latest
  on codeforces_completion_checks (user_id, problem_id, requested_at desc);
create index if not exists idx_codeforces_completion_checks_cooldown
  on codeforces_completion_checks (user_id, problem_id, cooldown_until desc);
create unique index if not exists idx_codeforces_completion_checks_pending
  on codeforces_completion_checks (user_id, problem_id)
  where result = 'pending';

-- Backend/service-role access only; no anon/authenticated policies.
alter table solo_problem_assignments enable row level security;
alter table problem_completions enable row level security;
alter table codeforces_completion_checks enable row level security;
