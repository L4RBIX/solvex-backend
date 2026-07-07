-- 011_recommendations.sql
-- Recommendation engine and training planner (Phase 05).
-- Canonical production schema; local mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py — keep both in sync.

create table if not exists user_skill_profiles (
  handle text not null,
  skill_id text not null,
  user_id uuid,
  analysis_run_id uuid,
  global_rating_anchor int,
  skill_rating_raw int,
  skill_rating_shrunk int,
  uncertainty numeric,
  status text,
  severity int,
  confidence real,
  effective_exposure numeric,
  attempts int not null default 0,
  independent_solves int not null default 0,   -- solved episodes; public data cannot prove independence
  delayed_ac_count int not null default 0,
  recent_failures_28d int not null default 0,
  last_practiced_at timestamptz,
  review_due_at timestamptz,
  frustration_score numeric not null default 0,
  preference_bias numeric not null default 0,
  suppression_until timestamptz,
  updated_at timestamptz not null default now(),
  primary key (handle, skill_id)
);

create table if not exists recommendation_runs (
  run_id uuid primary key,
  handle text not null,
  analysis_run_id uuid,
  queue_date date not null,
  recent_struggle real not null default 0,
  warnings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_recommendation_runs on recommendation_runs (handle, queue_date desc);

create table if not exists recommendation_items (
  item_id uuid primary key,
  run_id uuid not null references recommendation_runs(run_id),
  slot int not null,
  mode text not null check (mode in (
    'review_or_warmup', 'core_repair', 'transfer', 'stretch', 'underexposed_exploration', 'calibration'
  )),
  problem_id text not null,
  skill_id text not null,
  target_rating int,
  problem_rating int,
  quality_score real,
  final_score real,
  why_selected text not null,
  item_status text not null default 'proposed'
);
create index if not exists idx_recommendation_items_run on recommendation_items (run_id, slot);

create table if not exists training_plans (
  plan_id uuid primary key,
  handle text not null,
  plan_type text not null check (plan_type in ('7_day', '14_day')),
  analysis_run_id uuid,
  start_date date not null,
  plan_status text not null default 'active',
  created_at timestamptz not null default now()
);
create index if not exists idx_training_plans on training_plans (handle, plan_type, start_date desc);

create table if not exists training_plan_days (
  plan_id uuid not null references training_plans(plan_id),
  day_number int not null,
  theme text not null,
  primary key (plan_id, day_number)
);

create table if not exists training_plan_items (
  item_id uuid primary key,
  plan_id uuid not null references training_plans(plan_id),
  day_number int not null,
  slot int not null,
  mode text not null,
  problem_id text not null,
  skill_id text not null,
  target_rating int,
  problem_rating int,
  why_selected text not null,
  item_status text not null default 'proposed'
);
create index if not exists idx_training_plan_items on training_plan_items (plan_id, day_number, slot);

create table if not exists recommendation_feedback (
  feedback_id uuid primary key,
  item_id uuid not null,
  handle text not null,
  problem_id text not null,
  feedback_type text not null check (feedback_type in (
    'too_easy', 'too_hard', 'already_seen', 'bad_problem', 'good_problem',
    'solved_independently', 'solved_with_editorial_self_reported', 'skipped', 'abandoned'
  )),
  comment text,
  created_at timestamptz not null default now()
);
create index if not exists idx_recommendation_feedback on recommendation_feedback (handle, problem_id);

create table if not exists problem_quality_stats (
  problem_id text primary key,
  feedback_positive int not null default 0,
  feedback_negative int not null default 0,
  feedback_wilson real,                   -- null = no feedback yet, neutral prior applies
  manual_curation real not null default 0.5,
  updated_at timestamptz not null default now()
);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table user_skill_profiles enable row level security;
alter table recommendation_runs enable row level security;
alter table recommendation_items enable row level security;
alter table training_plans enable row level security;
alter table training_plan_days enable row level security;
alter table training_plan_items enable row level security;
alter table recommendation_feedback enable row level security;
alter table problem_quality_stats enable row level security;
