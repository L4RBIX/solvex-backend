# SolveX Production Runbook

## Service overview

FastAPI backend (`contestiq_api.main:app`) — single source of truth for
analysis, recommendations, billing/entitlements, SkillTrace verification, and
B2B (teams/events). Local persistence: SQLite (`DATABASE_PATH`); production:
Postgres/Supabase via `db/migrations/*.sql` (apply in numeric order; never
edit an applied migration — add a new one).

## Startup

```bash
cd backend/Trace_X_project
pip install -r requirements.txt
uvicorn contestiq_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Production (`APP_ENV=production`) fails fast unless:
- `ADMIN_API_KEY` is set (min 16 chars);
- `BILLING_PROVIDER=stripe` also has `BILLING_API_KEY` + `BILLING_WEBHOOK_SECRET`.

Full env reference: `.env.example`. Never put backend keys in Vercel — only
`NEXT_PUBLIC_API_URL` belongs in the frontend.

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

1. CI green (lint, migration check, secret scan, 300+ tests).
2. Apply new `db/migrations/NNN_*.sql` to Postgres in order (Supabase SQL editor
   or psql). Migrations are additive; RLS must stay enabled on every table.
3. Deploy backend; watch `/api/v1/health` and 5xx rate for 10 minutes.
4. Frontend (Vercel) needs `NEXT_PUBLIC_API_URL` pointing at the backend.

## Load characteristics

See `docs/load_test_report.md` (in-process baseline: analysis p95 ~320 ms,
cached reads ~260 rps on SQLite, callback storms replay-safe). Re-run:
`python3.11 scripts/loadtest.py --scale 1.0`.

## Known unresolved risks

- Legacy `/api/*` routes (analyze, workspace, share, copilot, coach) predate
  auth: anonymous, handle-based, public-CF-data only. Fold behind v1 auth or
  deprecate before broad launch.
- Recommendation feedback is anonymous (no handle ownership): throttled, but a
  motivated abuser with item ids could skew one handle's frustration scores.
  Real fix = handle claiming/linking (planned Phase 10).
- Per-handle sync lock is in-process; multi-instance deploys need a DB lock
  (active-job check gives partial protection).
- `pip-audit` step is report-only until dependency pins are reviewed.
- Stripe webhook signature verification must be implemented when Stripe goes
  live (`BILLING_WEBHOOK_SECRET` is validated as present in production, but the
  local/manual providers don't verify signatures).
