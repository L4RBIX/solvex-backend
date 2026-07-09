-- 018_duels.sql
-- Friend 1v1 duels by invite link (Phase G4). No matchmaking, no Elo, no
-- tournaments. Canonical production schema; local mirror is SQLite in
-- contestiq_api/cfdata/store.py.

create table if not exists duel_matches (
  duel_id uuid primary key,
  creator_subject text not null,
  creator_user_id uuid,
  creator_handle text,
  mode text not null,
  status text not null default 'waiting',
  problem_id text not null,
  problem_rating integer,
  skill_id text,
  invite_code_hash text unique not null,
  starts_at timestamptz,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  winner_subject text,
  result_reason text
);
create index if not exists idx_duel_matches_creator on duel_matches (creator_subject, created_at desc);
create index if not exists idx_duel_matches_status on duel_matches (status, expires_at);

create table if not exists duel_participants (
  duel_id uuid not null references duel_matches (duel_id) on delete cascade,
  subject text not null,
  user_id uuid,
  handle text,
  display_name text not null,
  role text not null,
  joined_at timestamptz not null default now(),
  ready_at timestamptz,
  final_status text not null default 'pending',
  accepted_at timestamptz,
  best_attempt_id uuid,
  primary key (duel_id, subject)
);
create index if not exists idx_duel_participants_user on duel_participants (user_id);
create index if not exists idx_duel_participants_handle on duel_participants (handle);

create table if not exists duel_submissions (
  submission_id uuid primary key,
  duel_id uuid not null references duel_matches (duel_id) on delete cascade,
  participant_subject text not null,
  language text not null,
  source_hash text not null,
  judge_status text not null,
  passed boolean not null default false,
  stdout_excerpt text,
  stderr_excerpt text,
  created_at timestamptz not null default now(),
  judged_at timestamptz,
  runtime_ms integer,
  memory_kb integer
);
create index if not exists idx_duel_submissions_duel on duel_submissions (duel_id, created_at);

alter table duel_matches enable row level security;
alter table duel_participants enable row level security;
alter table duel_submissions enable row level security;
