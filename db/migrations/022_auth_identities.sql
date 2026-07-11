-- 022_auth_identities.sql
-- Maps a cryptographically verified external authentication identity to the
-- stable internal SolveX user used by all private authorization. A public
-- Codeforces handle is deliberately absent from this mapping.

create table if not exists auth_identities (
  identity_id uuid primary key,
  user_id uuid not null references users (user_id) on delete cascade,
  provider text not null,
  provider_subject text not null,
  email text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider, provider_subject)
);

create index if not exists idx_auth_identities_user on auth_identities (user_id);

alter table auth_identities enable row level security;
