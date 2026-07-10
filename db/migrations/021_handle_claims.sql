-- 021_handle_claims.sql
-- Critical security fix: Codeforces handles are PUBLIC data and must never
-- be trusted as authentication. This adds a real ownership-verification
-- flow — an authenticated user proves control of a CF handle by placing a
-- short-lived code in their public profile, then it is bound to their
-- user_id here. Authorization for PvP/leaderboards/gamification must key off
-- users.user_id (bearer token) only; handle_owners is the single source of
-- truth for "which user_id, if any, has proven ownership of this handle".
-- Additive only — does not touch existing users/duel/leaderboard data.

create table if not exists handle_claims (
  claim_id uuid primary key,
  user_id uuid not null references users (user_id) on delete cascade,
  handle text not null,                 -- canonical (lowercased)
  verification_code text not null,
  status text not null default 'pending' check (status in ('pending', 'verified', 'expired', 'superseded')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  verified_at timestamptz
);
create index if not exists idx_handle_claims_user on handle_claims (user_id, created_at desc);
create index if not exists idx_handle_claims_handle on handle_claims (handle, status);

-- One verified owner per handle — enforced by primary key. A row here is the
-- ONLY thing that authorizes "this user_id may act as this CF handle".
create table if not exists handle_owners (
  handle text primary key,              -- canonical (lowercased)
  user_id uuid not null references users (user_id) on delete cascade,
  claim_id uuid references handle_claims (claim_id),
  bound_by text not null default 'self_verification',  -- 'self_verification' or 'admin_reconciliation'
  verified_at timestamptz not null
);
create index if not exists idx_handle_owners_user on handle_owners (user_id);

alter table handle_claims enable row level security;
alter table handle_owners enable row level security;
