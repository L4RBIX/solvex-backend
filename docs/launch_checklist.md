# SolveX Launch Checklist (Phase 10)

Companion to `docs/runbook.md` (operations) and `docs/load_test_report.md`
(capacity baseline). This document covers configuration, packaging, first
money, and rollback.

## 1. Environments

| Setting | Staging | Production |
|---|---|---|
| `APP_ENV` | `staging` | `production` (fails fast without secrets) |
| `DATABASE_PATH` / Postgres | staging Supabase project | production Supabase project |
| `ADMIN_API_KEY` | distinct random ≥16 chars | distinct random ≥16 chars (required) |
| `CORS_ORIGINS` | staging Vercel URL | production domain(s) only |
| `BILLING_PROVIDER` | `local` | `manual` (beta) → `stripe` when keys exist |
| `BILLING_API_KEY` / `BILLING_WEBHOOK_SECRET` | empty | required if provider=stripe |
| `JUDGE0_BASE_URL` + keys | staging Judge0 | production Judge0 (never exposed to browser) |
| `JUDGE0_CALLBACK_BASE` | staging backend URL | `https://api.<domain>` (public) |
| `RATE_LIMIT_ANALYZE_SECONDS` | 0 | 30 |
| `LOG_LEVEL` | DEBUG/INFO | INFO |
| Frontend (`Vercel`) | `NEXT_PUBLIC_API_URL` → staging API | → production API. Nothing else. |

Secrets live only in the platform env managers (Railway/Vercel). CI runs
`scripts/scan_secrets.py` + gitleaks on every push.

## 2. Deploy steps

1. CI green (lint, migration check, secret scan, 300+ tests, typecheck).
2. Apply `db/migrations/*.sql` in numeric order to the target Postgres
   (Supabase SQL editor). Verify with `scripts/check_migrations.py` locally first.
3. Seed once per environment: `POST /api/v1/taxonomy/seed`,
   `POST /api/v1/sync/problemset`, `POST /api/v1/skill-map/rebuild` (admin key).
4. Deploy backend: `uvicorn contestiq_api.main:app --workers 2` (or platform
   equivalent). Sync/analysis run in-request today — 2–4 workers is enough for
   beta scale (see load report).
5. Scheduled jobs (platform cron or GitHub Actions cron hitting admin endpoints):
   - every 2 min: `POST /api/v1/verification/reconcile` (missed Judge0 callbacks);
   - daily: `POST /api/v1/sync/problemset` (TTL makes this cheap);
   - weekly (Mon 06:00 UTC): `POST /api/v1/admin/jobs/weekly-reports`.
6. Backups: Supabase PITR/daily snapshots on (production); if running SQLite
   anywhere, cron-copy `DATABASE_PATH` off-box daily.
7. Smoke: `/api/v1/health`, one full analyze→queue→plan on a test handle, one
   verification session against production Judge0, `/api/v1/metrics`.

## 3. Product packaging (enforced server-side, `entitlements.PLAN_FEATURES`)

- **Free**: connect handle, top-3 weak skills, 2-item queue, day-1 plan preview,
  1 verification attempt/week, 3 analyses/day.
- **Premium ($5/mo, `premium_student`)**: full weakness map + skill ratings,
  full queue, 7/14-day plans, weekly report, 10 verification credits/week,
  shareable badges.
- **Team ($50/mo)**: premium features + coach dashboard, member progress,
  assignments, exports.
- **Event ($200/event)**: applicant links, verification dashboard, audited
  report exports, expiring windows.

## 4. First-money workflow (no code changes required)

1. `POST /api/v1/admin/users {"handle": "...", "email": "..."}` → send the user
   their API token (shown once).
2. User pays via the agreed channel (manual beta) — record:
   user runs `POST /api/v1/billing/checkout {"plan": "premium_student"}` which
   creates the pending payment (invoice reference = payment_id).
3. Confirm payment: either `POST /api/v1/billing/webhook/manual` with
   `{"event_id": "...", "type": "payment.completed", "payment_id": "..."}`
   or grant directly: `POST /api/v1/admin/users/{id}/grant-entitlement
   {"plan": "premium_student", "expires_at": "..."}`.
4. Verify: user's `GET /api/v1/me/entitlements` shows the plan.
5. Failed payment: leave pending; nothing was granted. Dispute/refund:
   `POST /api/v1/admin/payments/{payment_id}/refund` (marks refunded AND
   revokes the plan). Everything is audited.

Team buyer: create user → grant `team` → they create the team and invites.
Event buyer: create user → grant `event` → they create org, event, links.

## 5. Support playbook (admin endpoints, all audited)

| Case | Action |
|---|---|
| Failed Codeforces sync | `GET /admin/jobs?status=failed` → `POST /admin/resync/{handle}` |
| Wrong/odd recommendation | `POST /admin/problems/{id}/mark-bad`, edit skill map, force queue regen |
| Manual premium grant | `POST /admin/users/{id}/grant-entitlement` |
| Revoke a badge | `POST /admin/badges/{badge_public_id}/revoke` (public view shows revoked) |
| Leaked challenge | `POST /admin/challenges/{id}/mark-leaked` (excluded from assignment) |
| Payment dispute | `POST /admin/payments/{id}/refund` (refund + revoke) |
| Data export request | `GET /admin/users/{id}/export` (JSON of all user-owned rows) |
| Deletion request | `DELETE /admin/users/{id}` (user + grants + payments + sessions + ledgers) |

## 6. Launch metrics

`GET /api/v1/admin/launch-dashboard` — signups, handle connections, analyses,
queues, plans, feedback, premium conversions + rate, churn, team invites,
event applicant completion, badge issuance rate, 7-day retention proxy.
Operational metrics: `GET /api/v1/metrics`. Alerts: see runbook table.

## 7. Rollback plan

- Backend: redeploy the previous image/commit (platform one-click). The API is
  stateless; all state is in the DB.
- Migrations are additive-only (new tables/columns/RLS): old code runs safely
  against a newer schema, so DB rollback is normally unnecessary. Never drop
  columns in the same release that stops using them.
- If a migration must be reverted: restore from Supabase PITR to
  pre-migration timestamp (accepting data loss window) — last resort.
- Feature-level rollback: `FEATURE_FLAGS` env (settings.flag_enabled) for
  gating new behavior; entitlement revoke for per-user rollback.

## 8. Data deletion/export policy

- Export and deletion are admin-served (endpoints above), audited, and cover:
  account, grants, payments/billing, team memberships/assignments, skill
  profiles, verification sessions (including event ledgers, snapshots,
  Judge0 rows, badges, private reports), and product events.
- Not deleted: Codeforces public data keyed by handle (public information),
  anonymized aggregate metrics, and admin audit entries (legal/audit basis;
  they reference the user id, not personal content).
- Target SLA for requests: 30 days; process both via the support playbook.
