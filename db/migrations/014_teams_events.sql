-- 014_teams_events.sql
-- B2B layer (Phase 08): teams/coaches and organization event screening.
-- Canonical production schema; local mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py — keep both in sync.

create table if not exists teams (
  team_id uuid primary key,
  name text not null,
  owner_user_id uuid not null references users(user_id),
  created_at timestamptz not null default now()
);

create table if not exists team_members (
  team_id uuid not null references teams(team_id),
  user_id uuid not null references users(user_id),
  member_role text not null check (member_role in ('owner', 'coach', 'student')),
  handle text,
  joined_at timestamptz not null default now(),
  primary key (team_id, user_id)
);
create index if not exists idx_team_members_user on team_members (user_id);

create table if not exists team_invites (
  invite_id uuid primary key,
  team_id uuid not null references teams(team_id),
  token_hash text unique not null,       -- sha256; the raw invite token is shown once
  member_role text not null check (member_role in ('coach', 'student')),
  created_by uuid not null,
  expires_at timestamptz not null,
  accepted_by uuid,
  accepted_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists team_assignments (
  assignment_id uuid primary key,
  team_id uuid not null references teams(team_id),
  student_user_id uuid not null,
  assigned_by uuid not null,
  kind text not null check (kind in ('skill_focus', 'problems', 'verification')),
  skill_id text,
  problem_ids jsonb not null default '[]'::jsonb,
  challenge_skill_id text,
  due_date date,
  notes text,
  assignment_status text not null default 'assigned' check (assignment_status in ('assigned', 'completed', 'cancelled')),
  created_at timestamptz not null default now()
);
create index if not exists idx_team_assignments on team_assignments (team_id, student_user_id);

create table if not exists team_student_snapshots (
  snapshot_id uuid primary key,
  team_id uuid not null references teams(team_id),
  user_id uuid not null,
  handle text,
  analysis_run_id uuid,
  summary jsonb not null default '{}'::jsonb,
  captured_at timestamptz not null default now()
);
create index if not exists idx_team_student_snapshots on team_student_snapshots (team_id, user_id, captured_at desc);

create table if not exists organizations (
  org_id uuid primary key,
  name text not null,
  owner_user_id uuid not null references users(user_id),
  created_at timestamptz not null default now()
);

create table if not exists organization_members (
  org_id uuid not null references organizations(org_id),
  user_id uuid not null references users(user_id),
  member_role text not null check (member_role in ('owner', 'reviewer')),
  joined_at timestamptz not null default now(),
  primary key (org_id, user_id)
);
create index if not exists idx_organization_members_user on organization_members (user_id);

create table if not exists org_events (
  event_id uuid primary key,
  org_id uuid not null references organizations(org_id),
  name text not null,
  event_status text not null default 'active' check (event_status in ('active', 'expired', 'closed')),
  expires_at timestamptz not null,
  created_by uuid not null,
  created_at timestamptz not null default now()
);
create index if not exists idx_org_events on org_events (org_id, created_at desc);

create table if not exists event_requirements (
  event_id uuid not null references org_events(event_id),
  skill_id text not null,
  level int,
  min_evidence_label text not null default 'sufficient_process_evidence',
  primary key (event_id, skill_id)
);

create table if not exists event_applicants (
  applicant_id uuid primary key,
  event_id uuid not null references org_events(event_id),
  display_name text,
  email text,
  applicant_status text not null default 'invited' check (applicant_status in ('invited', 'started', 'completed', 'expired')),
  shadow_user_id uuid,                   -- scoped throwaway identity that drives the SkillTrace session
  session_id uuid,
  badge_public_id text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);
create index if not exists idx_event_applicants on event_applicants (event_id, created_at);

create table if not exists event_verification_links (
  link_id uuid primary key,
  event_id uuid not null references org_events(event_id),
  applicant_id uuid not null references event_applicants(applicant_id),
  token_hash text unique not null,       -- sha256; raw link token appears once
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists event_report_exports (
  export_id uuid primary key,
  event_id uuid not null references org_events(event_id),
  applicant_id uuid not null,
  exported_by text not null,
  export_format text not null default 'json',
  created_at timestamptz not null default now()
);
create index if not exists idx_event_report_exports on event_report_exports (event_id, created_at desc);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table teams enable row level security;
alter table team_members enable row level security;
alter table team_invites enable row level security;
alter table team_assignments enable row level security;
alter table team_student_snapshots enable row level security;
alter table organizations enable row level security;
alter table organization_members enable row level security;
alter table org_events enable row level security;
alter table event_requirements enable row level security;
alter table event_applicants enable row level security;
alter table event_verification_links enable row level security;
alter table event_report_exports enable row level security;
