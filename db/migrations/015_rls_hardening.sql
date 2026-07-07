-- 015_rls_hardening.sql
-- Phase 09 security audit finding: migrations 005/006 created Copilot tables
-- without row level security. These tables hold per-user solving telemetry and
-- are accessed only via the backend service role — no anon/authenticated
-- policies are defined on purpose.

alter table user_solving_profiles enable row level security;
alter table solving_events enable row level security;
