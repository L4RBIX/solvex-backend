# ContestIQ API Deployment Notes

ContestIQ Phase 1 currently uses local JSON storage and has no authentication. These notes are for running the FastAPI backend safely during development or an early internal deployment.

## Local Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn contestiq_api.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## Production-Style Run

```bash
uvicorn contestiq_api.main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

- `APP_ENV`: `development` or `production`. Defaults to `development`.
- `ENABLE_DEBUG_ENDPOINT`: `true` or `false`. Defaults to `true` in development and `false` in production.
- `CORS_ORIGINS`: comma-separated allowed origins.
- `RATE_LIMIT_ANALYZE_SECONDS`: simple in-memory cooldown for `POST /api/analyze`.
- `PORT`: optional port value for hosting platforms.

Example:

```bash
APP_ENV=production
ENABLE_DEBUG_ENDPOINT=false
CORS_ORIGINS=https://your-frontend.example
RATE_LIMIT_ANALYZE_SECONDS=30
PORT=8000
```

## Debug Endpoint

`GET /api/analysis/{handle}/debug` can expose internal diagnostics when enabled. Keep it disabled in production-like environments.

## CORS

Local frontend origins are allowed by default:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

Set `CORS_ORIGINS` explicitly for deployed frontends.

## Rate Limiting

`POST /api/analyze` has a basic in-memory rate limit controlled by `RATE_LIMIT_ANALYZE_SECONDS`. This helps reduce accidental repeated API calls. It is not a full abuse-prevention system.

## Local JSON Storage

The backend writes local data under `api_cache/`, including analyses, snapshots, feedback, shares, and workspace handles.

On platforms such as Render or Railway, local filesystem data may be ephemeral unless persistent storage is configured. Do not treat local JSON storage as durable production persistence.

## Persistent Storage on Railway

The backend's SQLite database (`DATABASE_PATH`, default `api_cache/backend_jobs.db`) is the **single shared store** for everything: users/entitlements, analysis runs, backend jobs, `product_events`, and — critically — the Codeforces **problem catalog** (`problems`) and the derived **`problem_skill_map`**. The recommendation/plan engine reads candidates from `problem_skill_map`, so if that table is empty, the daily queue and 7/14-day plans come back empty even when a user has hundreds of analyzed episodes.

Railway's default filesystem is **ephemeral**: every redeploy starts from a clean container, so a relative `DATABASE_PATH` (the default) is wiped on every deploy. This is the root cause of "empty daily queue despite many episodes" bugs seen after a redeploy.

### One-time setup: attach a persistent volume

1. In the Railway dashboard, open the backend service.
2. Go to **Settings → Volumes** and click **New Volume**.
3. Set the **mount path** to `/data`.
4. Attach the volume to the backend service and deploy so the mount takes effect.
5. In **Variables**, set:
   ```
   DATABASE_PATH=/data/backend_jobs.db
   ```
6. Redeploy. From now on, the SQLite file lives on the volume and survives every future redeploy — no code changes are needed beyond this env var (`contestiq_api/settings.py` already reads `DATABASE_PATH` and `cfdata/store.py` creates the parent directory automatically if it's missing).

### Seeding after attaching the volume (or after any deploy that starts from a fresh/empty DB)

A brand-new volume starts empty, so the catalog and skill map still need to be seeded once:

```bash
python3.11 scripts/seed_production_catalog.py --base-url https://<your-railway-domain> --admin-key "$ADMIN_API_KEY"
```

This calls `POST /api/v1/sync/problemset` (fetches the Codeforces problem catalog) and `POST /api/v1/skill-map/rebuild` (derives `problem_skill_map` from it) and prints a summary. Both endpoints are idempotent — safe to re-run any time.

Alternatively, run the two admin calls directly:

```bash
curl -X POST https://<your-railway-domain>/api/v1/sync/problemset -d '{}' -H "Content-Type: application/json"
curl -X POST https://<your-railway-domain>/api/v1/skill-map/rebuild -d '{}' -H "Content-Type: application/json"
```

### Verifying persistence

```bash
curl -H "X-Admin-Key: $ADMIN_API_KEY" https://<your-railway-domain>/api/v1/admin/storage-health
```

Returns:

```json
{
  "database_path": "/data/backend_jobs.db",
  "database_path_looks_persistent": true,
  "problemset_count": 11282,
  "problem_skill_map_count": 30826,
  "latest_problemset_sync_at": "2026-07-09T12:59:50Z",
  "catalog_ready": true
}
```

`catalog_ready: false` (or zero counts) right after a redeploy, with `database_path_looks_persistent: false`, means the volume/env var isn't wired up yet. The same diagnostics are also logged once at process startup (look for the `storage_diagnostics` log line), so a "problem catalog is empty" warning on every boot is a strong signal the volume isn't attached.

### Optional: auto-seed on startup

By default, the backend never runs the Codeforces sync automatically — only the two admin/seed calls above do. To opt into automatic recovery (useful for a volume that occasionally starts empty, e.g. before it's first provisioned), set:

```
FEATURE_FLAGS=auto_seed_catalog_on_startup
```

With this flag, the backend checks the catalog/skill-map counts once at startup and, **only if both are empty**, seeds them in a background task (it never blocks startup or re-runs while data already exists, and it never runs at all without this flag).

## Scope Warnings

This deployment does not include:

- authentication
- Supabase persistence
- SkillTrace
- Judge0
- verification badges
- payments
- organization dashboard
- frontend

Share reports and workspace dashboards are training aids based on public Codeforces history. They are not verification results.
