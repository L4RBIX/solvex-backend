-- 012_billing_entitlements.sql
-- Users, billing, entitlements, usage limits, and admin audit (Phase 06).
-- Canonical production schema; local mirror is SQLite in
-- backend/Trace_X_project/contestiq_api/cfdata/store.py — keep both in sync.

create table if not exists users (
  user_id uuid primary key,
  handle text,
  email text,
  role text not null default 'user' check (role in ('user', 'admin')),
  token_hash text unique,               -- sha256 of the bearer token; raw token is never stored
  created_at timestamptz not null default now()
);
create index if not exists idx_users_handle on users (handle);

create table if not exists billing_customers (
  customer_id uuid primary key,
  user_id uuid not null references users(user_id),
  provider text not null,
  external_customer_id text,
  created_at timestamptz not null default now()
);
create index if not exists idx_billing_customers_user on billing_customers (user_id);

create table if not exists subscriptions (
  subscription_id uuid primary key,
  user_id uuid not null references users(user_id),
  provider text not null,
  plan text not null,
  subscription_status text not null,
  external_subscription_id text,
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_subscriptions_user on subscriptions (user_id);

create table if not exists payments (
  payment_id uuid primary key,
  user_id uuid not null references users(user_id),
  provider text not null,
  plan text,
  amount_cents int,
  currency text,
  payment_status text not null check (payment_status in ('pending', 'completed', 'failed', 'refunded')),
  external_payment_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_payments_user on payments (user_id);

-- Webhook idempotency: (provider, event_id) is the primary key, so a replayed
-- event can never be processed twice.
create table if not exists payment_webhook_events (
  event_id text not null,
  provider text not null,
  event_type text,
  payload jsonb not null,
  result text,
  processed_at timestamptz not null default now(),
  primary key (provider, event_id)
);

create table if not exists entitlement_grants (
  grant_id uuid primary key,
  user_id uuid not null references users(user_id),
  plan text not null check (plan in ('free', 'premium_student', 'team', 'event', 'admin')),
  source text not null check (source in ('manual', 'webhook', 'local', 'stripe')),
  reference text,
  granted_by text,
  granted_at timestamptz not null default now(),
  expires_at timestamptz,
  revoked_at timestamptz
);
create index if not exists idx_entitlement_grants_user on entitlement_grants (user_id, plan);

create table if not exists usage_limits (
  subject text not null,                -- user:<id> or anon:<ip>
  feature text not null,
  window_start date not null,
  used int not null default 0,
  primary key (subject, feature, window_start)
);

create table if not exists admin_audit_logs (
  audit_id uuid primary key,
  actor text not null,
  action text not null,
  target text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_admin_audit_created on admin_audit_logs (created_at desc);

-- Backend-owned tables: no anon/authenticated access. Service role bypasses RLS.
alter table users enable row level security;
alter table billing_customers enable row level security;
alter table subscriptions enable row level security;
alter table payments enable row level security;
alter table payment_webhook_events enable row level security;
alter table entitlement_grants enable row level security;
alter table usage_limits enable row level security;
alter table admin_audit_logs enable row level security;
