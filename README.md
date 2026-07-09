# ContestIQ ML Core v1

ContestIQ is a verified competitive programming training platform. This repository implements Phase 1 only: the Training Intelligence ML/Core backend foundation.

The code takes a Codeforces handle and produces normalized history, user problem attempts, skill evidence, a safe weakness map, confidence levels, and a daily recommendation queue.

## What Phase 1 Does

- Fetches Codeforces submissions, rating history, and public problemset data.
- Normalizes problems and submissions into stable local models.
- Groups submissions into user problem attempts without claiming true solve start or exact solve time.
- Maps Codeforces tags into ContestIQ domain skills and technique overlays with reliability-weighted fractional credit.
- Computes explainable skill evidence, severity, confidence, and safe public buckets.
- Produces a staged recommendation queue with repair, maintenance, stretch, and exploration slots.

## What Phase 1 Does Not Do

Codeforces is outcome/history data, not process data. ContestIQ v1 does not infer exact conceptual mastery, exact solve time, independent solving, cheating detection, authenticity, implementation weakness from WA counts alone, badge readiness, guaranteed rating improvement, or an optimal plan.

SkillTrace verification, badges, organization dashboards, monetization, Judge0 integration, and process reports remain part of the long-term ContestIQ vision, but they are intentionally not implemented in this Phase 1 core.

Phase 1 is not SkillTrace and is not verification. It does not issue badges, prove authenticity, inspect code evolution, reconstruct debugging rhythm, or produce process reports.

## Severity vs Confidence

Severity and confidence are separate.

- `severity_score` estimates current friction evidence from success gap, attempts friction, repeated failure, verdict friction, ceiling gap, and recent decline.
- `confidence_score` estimates how much the system should trust that signal from effective sample size, distinct problem count, rating bucket coverage, tag reliability, recency, and evidence diversity.

A high severity score alone is not enough to create a public weakness claim. `Likely Needs Work` is suppressed unless:

- `confidence_score >= 0.55`
- `n_eff >= 6`
- `distinct_problem_count >= 4`
- the skill is not underexposed

If these thresholds are not met, the skill is placed in `Watchlist`, `Limited Evidence`, or `Hidden`.

## Limited Evidence

Low exposure is not treated as weakness. Underexposed skills are surfaced as `Limited Evidence` with cautious wording, for example: ContestIQ cannot make a reliable diagnosis yet.

This is especially important for sparse Codeforces histories, rare tags, noisy tags, and skills represented by only one or two problems.

## Recommendation Slots

- `repair`: eligible only for skills that pass public friction thresholds with moderate or high confidence.
- `focused_practice`: moderate-severity, high-confidence domain friction that is useful for training but not strong enough for a firm public weakness label.
- `maintenance`: uses stable or hidden skills to keep active coverage.
- `stretch`: slightly above estimated skill-specific ability, without heavily penalizing failed far-above-rating attempts.
- `exploration`: used for underexposed or low-evidence skills. Exploration does not imply weakness.

If a repair slot is not safe because evidence is sparse, the queue may fill with exploration or maintenance instead of overstating the diagnosis.

## Run

```bash
python -m pip install -r requirements.txt
python -m contestiq_core.pipeline.analyze_handle --handle tourist --out output.json
```

The Codeforces client caches raw API responses in `.cache/codeforces` to avoid repeated API calls.

## FastAPI Backend

Start the API wrapper:

```bash
pip install -r requirements.txt
uvicorn contestiq_api.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "contestiq-api",
  "model_version": "ml_core_v0.4"
}
```

Analyze a handle:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"handle\":\"tourist\",\"debug\":false,\"force_refresh\":false}"
```

Saved analyses are stored locally in `api_cache/analyses/`. The API returns a frontend-safe response by default and does not expose raw normalized history, full skill scores, repair blocking reasons, or internal diagnostics unless the development debug endpoint is used.

Configuration is read from environment variables:

- `APP_ENV`: defaults to `development`; use `production` for deployed environments.
- `ENABLE_DEBUG_ENDPOINT`: defaults to enabled in development and disabled in production.
- `CORS_ORIGINS`: comma-separated frontend origins; local dev origins are allowed by default.
- `RATE_LIMIT_ANALYZE_SECONDS`: simple in-memory cooldown for `POST /api/analyze`; defaults to `0` in development and `30` in production.
- `PORT`: optional hosting port.
- `DATABASE_PATH`: SQLite path shared by backend jobs, users/entitlements, and the Codeforces problem catalog/skill map. On Railway this MUST point at a mounted persistent volume (e.g. `/data/backend_jobs.db`) or the catalog/skill map are wiped on every redeploy — see "Persistent Storage on Railway" in `docs/deployment.md`.

See `.env.example`, `docs/deployment.md`, and `docs/model_limitations.md` for production-readiness and model-boundary notes.

Useful endpoints:

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/analysis/{handle}`
- `GET /api/analysis/{handle}/weakness-map`
- `GET /api/analysis/{handle}/daily-queue`
- `GET /api/analysis/{handle}/progress`
- `GET /api/analysis/{handle}/debug`
- `POST /api/feedback/problem`
- `POST /api/outcome/problem`
- `POST /api/feedback/queue`

The debug endpoint is for development only. Phase 1 API responses remain Codeforces outcome-history based and do not claim exact mastery, solving process, verification, authenticity, or expected improvement.

## Model v0.4 Feedback and Progress Foundation

Model v0.4 adds local data infrastructure for future recommendation quality work. It does not train a model automatically and does not change the current ML formulas or thresholds.

Feedback and outcome records are stored locally as JSONL:

- `api_cache/feedback/problem_feedback.jsonl`
- `api_cache/feedback/problem_outcomes.jsonl`
- `api_cache/feedback/queue_feedback.jsonl`

Problem feedback:

```bash
curl -X POST http://localhost:8000/api/feedback/problem \
  -H "Content-Type: application/json" \
  -d "{\"analysis_id\":\"...\",\"handle\":\"tourist\",\"problem_key\":\"1869B\",\"slot_type\":\"focused_practice\",\"anchor_skill\":\"graphs\",\"feedback\":\"good_fit\",\"comment\":\"This looked relevant\"}"
```

Problem outcome:

```bash
curl -X POST http://localhost:8000/api/outcome/problem \
  -H "Content-Type: application/json" \
  -d "{\"analysis_id\":\"...\",\"handle\":\"tourist\",\"problem_key\":\"1869B\",\"slot_type\":\"focused_practice\",\"anchor_skill\":\"graphs\",\"outcome\":\"attempted_but_failed\",\"comment\":\"Could not finish\"}"
```

Queue feedback:

```bash
curl -X POST http://localhost:8000/api/feedback/queue \
  -H "Content-Type: application/json" \
  -d "{\"analysis_id\":\"...\",\"handle\":\"tourist\",\"queue_rating\":\"good_fit\",\"comment\":\"The plan felt useful\"}"
```

Every successful `/api/analyze` call also saves a timestamped progress snapshot in `api_cache/snapshots/{handle}/{analysis_id}.json`.

Progress comparison:

```bash
curl http://localhost:8000/api/analysis/tourist/progress
```

The progress endpoint compares the latest two saved snapshots when available. It uses safe wording such as public friction signals changing over time; it does not claim improvement, mastery, verification, authenticity, or guaranteed future results.

This foundation is for future Recommendation Engine V2 calibration using real user feedback instead of guessing.

## Model v0.5 Feedback Analytics

Model v0.5 adds read-only analytics over the local feedback and outcome logs. It does not automatically train, tune, or update the recommendation model.

Feedback data is read from:

- `api_cache/feedback/problem_feedback.jsonl`
- `api_cache/feedback/problem_outcomes.jsonl`
- `api_cache/feedback/queue_feedback.jsonl`

JSON summary:

```bash
curl http://localhost:8000/api/feedback/summary
```

Markdown summary:

```bash
curl http://localhost:8000/api/feedback/summary.md
```

The summary includes global counts, feedback by slot type, feedback by anchor skill, outcomes by slot type, outcomes by anchor skill, and internal manual-review flags such as high too-hard or not-relevant rates. Groups with fewer than five records are marked as low sample size, so they should not be treated as strong evidence.

This is for manual calibration and future Recommendation Engine V2 work. It does not prove recommendation effectiveness and does not make public claims.

## Model v0.6 Weekly Progress Report

Model v0.6 adds analysis history and weekly progress reporting from saved snapshots. It does not change scoring, thresholds, recommendations, or the public meaning of weakness labels.

History endpoint:

```bash
curl http://localhost:8000/api/analysis/tourist/history
```

Weekly report endpoint:

```bash
curl http://localhost:8000/api/analysis/tourist/weekly-report
```

Markdown weekly report:

```bash
curl http://localhost:8000/api/analysis/tourist/weekly-report.md
```

The weekly report compares the latest saved snapshot against an earlier snapshot. When possible, it uses the earliest snapshot from the last seven days; otherwise it compares the latest two snapshots.

Reports include queue mode changes, public watchlist changes, limited-evidence changes, likely-needs-work changes, repeated focus skills, and the current training focus from the daily queue.

Safe interpretation rules:

- The report is based only on saved public-history snapshots.
- It does not verify skill or prove improvement.
- It does not infer true solve process, independent solving, authenticity, or badge readiness.
- Treat it as a training aid and manual review artifact, not a public proof.

## Product v0.7 Shareable Training Report

Product v0.7 adds a public, frontend-safe share report for an existing saved analysis. This is not SkillTrace, not a badge, not a verification result, and not proof of skill.

Create a share link:

```bash
curl -X POST http://localhost:8000/api/analysis/tourist/share
```

Public JSON report:

```bash
curl http://localhost:8000/api/share/{share_id}
```

Public Markdown report:

```bash
curl http://localhost:8000/api/share/{share_id}.md
```

The public report includes only:

- handle
- analysis id and date
- model version
- profile summary
- user-facing weakness map
- frontend-safe daily queue
- warnings
- safe interpretation
- caveats

The public report intentionally excludes debug data, skill scores, skill evidence, normalized history, raw submissions, feedback logs, problem results, blocking reasons, score components, candidate counts, and internal diagnostics.

Safe wording:

- "Shareable training report"
- "Based on public Codeforces history"
- "Not a verification result"
- "Training focus"
- "Current friction signals"

Do not present a share report as verification, authenticity evidence, a badge, or a proof of ability.

## Product v0.8 Lightweight Workspace

Product v0.8 adds a local saved-handle workspace so a frontend can show a small training dashboard. This is a local backend index only: there is no authentication, no database, and no verification layer.

Save a handle without running analysis:

```bash
curl -X POST http://localhost:8000/api/workspace/handles \
  -H "Content-Type: application/json" \
  -d '{"handle":"tourist","notes":"Strong baseline test"}'
```

List saved handles:

```bash
curl http://localhost:8000/api/workspace/handles
```

Delete a handle from the local workspace:

```bash
curl -X DELETE http://localhost:8000/api/workspace/handles/tourist
```

Open the training dashboard:

```bash
curl http://localhost:8000/api/workspace/dashboard
```

When `POST /api/analyze` completes, ContestIQ upserts the handle into `api_cache/workspace/saved_handles.json` with the latest analysis id, analysis date, queue mode, and model version. When `POST /api/analysis/{handle}/share` creates a public report, the workspace record is updated with `latest_share_id`.

Removing a handle from the workspace does not delete saved analyses, snapshots, feedback records, outcomes, or share reports. Workspace data is local and based on saved analyses; it is not verification, identity confirmation, or proof of skill.

For a deterministic offline sample:

```bash
python -m contestiq_core.pipeline.analyze_handle --handle sample_user --out sample_output.json --offline-sample
```

For debug diagnostics:

```bash
python -m contestiq_core.pipeline.analyze_handle --handle sample_user --offline-sample --debug --out sample_output_debug.json
```

## Real Handle Evaluation

Create a `handles.txt` file with one Codeforces handle per line:

```text
tourist
Petr
Benq
```

Run batch evaluation:

```bash
python -m contestiq_core.pipeline.batch_evaluate --handles handles.txt --out-dir eval_outputs --debug
```

For each handle, the evaluator writes:

- `{handle}_output.json`
- `{handle}_debug.json`

It also writes:

- `eval_outputs/eval_summary.json`
- `eval_outputs/eval_summary.md`

Open `eval_summary.md` for manual review. It includes data quality, public weakness bucket counts, queue mode, visible weakness map, daily queue, warnings, and a review checklist.

This toolkit is for local validation of the Phase 1 Training Intelligence core. It is not a public claim about mastery, verification, identity proof, contest integrity, or expected improvement.

Real-handle evaluation should be reviewed manually before any public claims.

## Calibration Scenario Suite

Synthetic scenarios are used to validate model behavior when the expected evidence pattern is known. They help separate routing or threshold bugs from normal conservative behavior on messy real Codeforces histories.

Run the suite:

```bash
python -m contestiq_core.pipeline.run_calibration_scenarios --out calibration_outputs --debug
```

The command writes:

- `calibration_outputs/calibration_summary.json`
- `calibration_outputs/calibration_summary.md`
- per-scenario output/debug JSON files

Use `calibration_summary.md` to compare expected behavior against actual severity, confidence, public buckets, repair eligibility, repair blocking reasons, and queue mode.

Failures should be interpreted as model-validation signals. Do not tune thresholds just to force more repair items; first check whether the failure is a scenario construction issue, a routing bug, or a real calibration concern.

This suite is for local model validation only. It is not a public claim about skill, verification, identity, or expected improvement.

## Test

```bash
pytest
```

## Output Shape

```json
{
  "profile_summary": {},
  "data_quality_summary": {},
  "normalized_history": {
    "submissions": [],
    "attempts": []
  },
  "skill_evidence": [],
  "weakness_map": {},
  "skill_scores": [],
  "daily_queue": {
    "items": []
  },
  "debug": {
    "skill_diagnostics": [],
    "recommendation_debug": []
  },
  "explanations": {},
  "warnings": []
}
```

## Product G1 Lightweight Gamification

Phase G1 adds retention gamification derived entirely from Phase 10's
`product_events` table — no new schema, no leaderboard, no duels, no
matchmaking, no public profile, no social comparison.

Only real learning actions are ever recorded as events, so gamification
structurally cannot reward page visits, refreshes, or just opening a page:
`first_analysis_completed`, `first_queue_generated`, `daily_queue_generated`,
`feedback_submitted`, `weekly_report_generated`, `verification_attempted`,
`premium_conversion`, `plan_started`.

Endpoints:

```bash
curl "http://localhost:8000/api/v1/gamification/me?handle=tourist"
curl "http://localhost:8000/api/v1/gamification/streak?handle=tourist"
curl "http://localhost:8000/api/v1/gamification/daily-goal?handle=tourist"
curl "http://localhost:8000/api/v1/gamification/badges?handle=tourist"
```

A bearer token also resolves a subject (merged with a linked handle's
events when the account has one), so premium/verification actions
(`user:<id>`) and handle-tracked actions (`handle:<handle>`) count toward the
same learner. Callers with neither a handle nor a token get a harmless empty
`"anonymous"` snapshot (200 OK) rather than an error.

`POST /api/v1/gamification/recompute` is admin-only (`X-Admin-Key` or an
admin user token) and simply replays a target subject's history on demand —
there is no cache to invalidate, since every value is derived live.

XP rules v1 (daily-capped per subject: 50 XP/day free, 150 XP/day premium,
200 XP/day team/event/admin; within a day, each action *type* contributes
its XP once no matter how many times it repeats):

| Action | XP |
| --- | --- |
| `first_analysis_completed` | 20 |
| `first_queue_generated` | 10 |
| `daily_queue_generated` | 5 |
| `feedback_submitted` | 5 |
| `weekly_report_generated` | 20 |
| `verification_attempted` | 25 |
| `premium_conversion` | 50 |
| `plan_started` | 15 |

Levels follow deterministic increasing thresholds (`contestiq_api/gamification.py`
documents and tests the formula): L1=0, L2=100, L3=250, L4=500, L5=900, and
beyond.

A streak day requires at least one meaningful event that UTC calendar day.
The daily goal completes once 2 distinct training categories are hit in a
day. Badges (`first_analysis`, `first_queue`, `feedback_loop`,
`three_day_streak`, `seven_day_streak`, `first_weekly_report`,
`first_verification_attempt`, `beta_premium`) are derived from the same
event history, so they are naturally earned exactly once and never
double-fire on recompute.

## Future Phases

- FastAPI endpoints
- Supabase persistence
- SkillTrace event logging
- Judge0 integration
- AI coach
- Verification badges
- Organization dashboards for clubs, hackathons, schools, and teams
