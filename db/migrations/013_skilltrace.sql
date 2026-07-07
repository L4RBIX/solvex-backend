-- 013_skilltrace.sql
-- SkillTrace verification engine (Phase 07): challenge bank, sessions, Judge0
-- submissions, append-only hash-chained event ledger, badges, private reports.
-- Canonical production schema; local mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py — keep both in sync.
--
-- SECURITY: challenge_test_sets holds hidden tests. It must NEVER be exposed
-- through any API response or client-readable policy. Backend service role only.

create table if not exists challenges (
  challenge_id text primary key,
  skill_id text not null,
  level int not null,
  title text not null,
  statement text not null,
  examples jsonb not null default '[]'::jsonb,     -- public examples only
  hidden_tests_ref text not null,                   -- opaque ref into challenge_test_sets
  checker_ref text,
  version int not null default 1,
  challenge_status text not null default 'active' check (challenge_status in ('active', 'leaked', 'deprecated')),
  created_at timestamptz not null default now()
);
create index if not exists idx_challenges_skill on challenges (skill_id, challenge_status, level);

create table if not exists challenge_test_sets (
  test_set_id text primary key,
  challenge_id text not null references challenges(challenge_id),
  is_hidden boolean not null default true,
  tests jsonb not null,                             -- [{input, expected_output}]
  version int not null default 1,
  created_at timestamptz not null default now()
);
create index if not exists idx_challenge_test_sets on challenge_test_sets (challenge_id);

create table if not exists verification_sessions (
  session_id uuid primary key,
  user_id uuid not null,
  handle text,
  challenge_id text not null references challenges(challenge_id),
  skill_id text not null,
  level int not null,
  session_status text not null default 'active' check (session_status in ('active', 'judging', 'completed', 'expired')),
  started_at timestamptz not null default now(),
  expires_at timestamptz not null,
  completed_at timestamptz,
  final_label text
);
create index if not exists idx_verification_sessions_user on verification_sessions (user_id, started_at desc);

create table if not exists execution_attempts (
  attempt_id uuid primary key,
  session_id uuid not null references verification_sessions(session_id),
  kind text not null check (kind in ('run', 'hidden')),
  language text not null,
  source_hash text not null,
  attempt_status text not null default 'pending' check (attempt_status in ('pending', 'completed', 'error')),
  result jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);
create index if not exists idx_execution_attempts_session on execution_attempts (session_id, created_at);

create table if not exists judge0_submissions (
  submission_id uuid primary key,
  attempt_id uuid not null references execution_attempts(attempt_id),
  test_index int not null default 0,
  judge0_token text unique,
  callback_secret text not null,                   -- per-submission secret in the callback URL
  submission_status text not null default 'submitted' check (submission_status in ('submitted', 'done', 'error')),
  status_id int,
  passed boolean,
  time_ms int,
  memory_kb int,
  stdout_redacted text,                            -- hidden-test outputs are never stored verbatim
  stderr_redacted text,
  callback_received_at timestamptz,
  polled_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists idx_judge0_submissions_attempt on judge0_submissions (attempt_id);
create index if not exists idx_judge0_submissions_pending on judge0_submissions (submission_status, created_at);

-- Append-only, server-sequenced, hash-chained ledger. Rows are never updated.
create table if not exists session_events (
  event_id uuid primary key,
  session_id uuid not null references verification_sessions(session_id),
  seq int not null,
  event_type text not null,
  actor_type text not null check (actor_type in ('user', 'server', 'judge0')),
  source_trust text not null check (source_trust in ('server', 'browser', 'judge0_callback', 'judge0_poll')),
  occurred_at timestamptz,
  received_at timestamptz not null default now(),
  payload jsonb not null default '{}'::jsonb,
  payload_redaction_level text not null default 'none' check (payload_redaction_level in ('none', 'hash_only', 'sanitized')),
  prev_event_hash text,
  event_hash text not null,
  trace_id text,
  request_id text,
  unique (session_id, seq)
);
create index if not exists idx_session_events on session_events (session_id, seq);

create table if not exists code_snapshots (
  snapshot_id uuid primary key,
  session_id uuid not null references verification_sessions(session_id),
  content_hash text not null,
  content text not null,
  content_length int not null,
  created_at timestamptz not null default now(),
  unique (session_id, content_hash)
);

create table if not exists badge_decisions (
  decision_id uuid primary key,
  session_id uuid not null unique references verification_sessions(session_id),
  decision text not null check (decision in ('issued', 'not_issued', 'manual_review')),
  process_evidence_label text not null,
  reasons jsonb not null default '[]'::jsonb,
  hidden_pass_rate real,
  created_at timestamptz not null default now()
);

create table if not exists public_badges (
  badge_public_id text primary key,
  session_id uuid not null unique references verification_sessions(session_id),
  handle text,
  skill_id text not null,
  level int not null,
  evidence_label text not null,
  badge_status text not null default 'active' check (badge_status in ('active', 'revoked')),
  issued_at timestamptz not null default now()
);

create table if not exists private_reports (
  report_id uuid primary key,
  session_id uuid not null unique references verification_sessions(session_id),
  user_id uuid not null,
  content jsonb not null,
  created_at timestamptz not null default now()
);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table challenges enable row level security;
alter table challenge_test_sets enable row level security;
alter table verification_sessions enable row level security;
alter table execution_attempts enable row level security;
alter table judge0_submissions enable row level security;
alter table session_events enable row level security;
alter table code_snapshots enable row level security;
alter table badge_decisions enable row level security;
alter table public_badges enable row level security;
alter table private_reports enable row level security;
