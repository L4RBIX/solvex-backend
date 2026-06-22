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
