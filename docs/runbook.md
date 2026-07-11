# SolveX Production Runbook

## Service overview

FastAPI backend (`contestiq_api.main:app`) — single source of truth for
analysis, recommendations, billing/entitlements, SkillTrace verification, and
B2B (teams/events). The current Railway production service uses persistent
SQLite at `DATABASE_PATH=/data/backend_jobs.db` on its mounted volume. The
additive SQLite schema mirror lives in `contestiq_api/cfdata/store.py`.
`db/migrations/*.sql` keeps PostgreSQL/RLS schema parity for a future or
alternate PostgreSQL deployment; apply those files in numeric order and never
edit an applied migration.

## Startup

```bash
cd backend/Trace_X_project
pip install -r requirements.txt
uvicorn contestiq_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Production (`APP_ENV=production`) fails fast unless:
- `ADMIN_API_KEY` is set (min 16 chars);
- Supabase JWT verification has `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`,
  `SUPABASE_JWT_AUDIENCE`, and `SUPABASE_JWKS_URL`;
- `BILLING_PROVIDER=stripe` also has `BILLING_API_KEY` + `BILLING_WEBHOOK_SECRET`.

Full env reference: `.env.example`. Never put backend keys in Vercel — only
public `NEXT_PUBLIC_*` configuration belongs in the frontend. Supabase
setup and auth rollback are documented in `docs/supabase_auth.md`.

## Health, metrics, traces

- `GET /api/v1/health` — liveness + Judge0 reachability + versions.
- `GET /api/v1/metrics` (admin: `X-Admin-Key`) — counters + p50/p95/p99 latencies:
  `analysis_latency_ms`, `cf_sync_duration_ms`, `recommendation_generation_latency_ms`,
  `empty_queue_total`, `judge0_callback_lag_ms`, `judge0_errors_total`,
  `payment_success_total`, `auth_denials_total_{401,403,429}`, per-group HTTP stats.
- Every response carries `X-Request-ID` and `X-Trace-Id` (send your own to correlate).
  Access logs are structured JSON on logger `solvex.api`; they never contain
  headers, tokens, code, or hidden tests.

### Alert suggestions

| Signal | Condition | First response |
|---|---|---|
| `auth_denials_total_429` spike | > 100/min | Check throttle buckets + attacking IPs |
| `judge0_errors_total` rising | > 5/min | Judge0 health, workers, disk |
| `judge0_callback_lag_ms` p95 | > 60 000 | Callback URL broken → run reconciler |
| `cf_sync_errors_total` rising | sustained | Codeforces down → circuit breaker handles it; verify stale-cache serving |
| `empty_queue_total` rising | sustained | Problem catalog stale → resync problemset |
| http 5xx rate | > 1% | Logs by request_id |

## Common incidents

**Codeforces is down / rate-limiting.** The client retries with backoff, the
circuit breaker opens after 5 consecutive failures (60 s cooldown), and stale
cached responses are served where available (`stale_cache_used` job status).
No action usually needed. Verify: `GET /api/v1/sync/codeforces/{handle}`.

**Judge0 callbacks not arriving.** Sessions stay in `judging`. Run the
reconciler: `POST /api/v1/verification/reconcile` (admin). If persistent,
check `JUDGE0_CALLBACK_BASE` is a publicly reachable URL for the Judge0 host.
Poll-only mode (empty callback base) is safe — just run the reconciler on a
schedule (cron every 1–5 min).

**Webhook replay / duplicates.** Safe by design: `(provider, event_id)` is the
webhook table PK; replays return `already_processed`. If a provider changes
event ids on retry, dedupe on their stable id before forwarding.

**Failed analysis/sync job.** `GET /api/v1/admin/jobs?status=failed`, then
`POST /api/v1/admin/jobs/{job_id}/retry` or `POST /api/v1/admin/resync/{handle}`.

**User locked out / entitlement wrong.** `GET /api/v1/admin/users?query=…`,
inspect `GET /api/v1/admin/users/{id}/billing`, fix with grant/revoke
endpoints. Every action lands in `admin_audit_logs`.

**Suspected leaked key.** Rotate immediately: `ADMIN_API_KEY` (env), user
tokens (delete row in `users` → user re-issued by admin), Judge0/DeepSeek keys
(provider dashboards). All keys are env-only; nothing is stored plaintext
(user/invite/link tokens are sha256-hashed).

## Rate limits and quotas

- Plan-based: `analysis_runs_per_day` (free 3), `verification_attempts_per_week`
  (free 1, premium 10) — `entitlements.PLAN_FEATURES`.
- Per-IP daily throttles: `throttle.DAILY_LIMITS` (execute 500, badge views
  2000, webhooks 5000, callbacks 20000, feedback 300, report exports 200).
- Per-session Judge0 run cap: 30 (soft under bursts — read-then-insert).
- Codeforces: global 1 request / 2 s (`CODEFORCES_RATE_LIMIT_SECONDS`).

## Deploy / migration procedure

1. CI green (lint, migration check, secret scan, full backend tests).
2. For the current Railway SQLite deployment, confirm the additive SQLite
   mirror passes `scripts/check_migrations.py`; startup creates missing tables
   in the existing persistent database. Do not change `DATABASE_PATH` or the
   mounted volume as part of a schema release.
3. If deploying the PostgreSQL variant, apply the new
   `db/migrations/NNN_*.sql` in order. RLS must stay enabled on every table.
4. Deploy backend; watch `/api/v1/health` and the 5xx rate for 10 minutes.
5. Frontend (Vercel) needs `NEXT_PUBLIC_API_URL` pointing at the backend.

## Load characteristics

See `docs/load_test_report.md` (in-process baseline: analysis p95 ~320 ms,
cached reads ~260 rps on SQLite, callback storms replay-safe). Re-run:
`python3.11 scripts/loadtest.py --scale 1.0`.

## Known unresolved risks

- Legacy public analysis and public share reads remain anonymous by design.
  Weekly reports, feedback mutations, Coach memory, and the shared support
  workspace now require bearer/ownership or admin authorization. Public
  Copilot chat remains available, but private memory is loaded and written
  only for the bearer-token account.
- Verified-handle reconciliation includes public telemetry created before the
  verification timestamp. Post-verification public-handle events are excluded
  from private XP/leaderboard computation; owned actions are recorded under
  `user:<id>`. Pre-verification telemetry cannot prove who clicked the public
  endpoint, so disputed history still requires explicit support review.
- There is no automatic verified-handle transfer/unbind. See
  `docs/identity_reconciliation.md` for the audited reconciliation limits.
- Per-handle sync lock is in-process; multi-instance deploys need a DB lock
  (active-job check gives partial protection).
- `pip-audit` step is report-only until dependency pins are reviewed.
- Stripe webhook signature verification must be implemented when Stripe goes
  live (`BILLING_WEBHOOK_SECRET` is validated as present in production, but the
  local/manual providers don't verify signatures).
