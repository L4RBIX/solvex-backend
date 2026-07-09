-- 017_leaderboards.sql
-- Private weekly leaderboards (Phase G3): invite-only groups scored from
-- product_events via gamification rules. No global/public leaderboard.
-- Canonical production schema; local mirror is SQLite in cfdata/store.py.

create table if not exists leaderboard_groups (
  leaderboard_id uuid primary key,
  name text not null,
  owner_subject text not null,
  owner_user_id uuid,
  visibility text not null default 'private',
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists idx_leaderboard_groups_owner on leaderboard_groups (owner_user_id);

create table if not exists leaderboard_members (
  leaderboard_id uuid not null references leaderboard_groups (leaderboard_id) on delete cascade,
  member_subject text not null,
  user_id uuid,
  handle text,
  display_name text not null,
  member_role text not null default 'member',
  joined_at timestamptz not null default now(),
  primary key (leaderboard_id, member_subject)
);
create index if not exists idx_leaderboard_members_user on leaderboard_members (user_id);
create index if not exists idx_leaderboard_members_handle on leaderboard_members (handle);

create table if not exists leaderboard_invites (
  invite_id uuid primary key,
  leaderboard_id uuid not null references leaderboard_groups (leaderboard_id) on delete cascade,
  invite_code_hash text unique not null,
  created_by text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  revoked_at timestamptz
);
create index if not exists idx_leaderboard_invites_board on leaderboard_invites (leaderboard_id);

alter table leaderboard_groups enable row level security;
alter table leaderboard_members enable row level security;
alter table leaderboard_invites enable row level security;
