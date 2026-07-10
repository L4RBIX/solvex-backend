"""Per-IP daily throttles for cheap-to-abuse endpoints (Phase 09).

Complements the plan-based usage limits in entitlements.py: these protect
endpoints that are public or anonymous (code execution, badge views, webhooks,
Judge0 callbacks) against unrestricted resource consumption. Backed by the
same usage_limits table so limits survive restarts.
"""

from __future__ import annotations

import datetime as dt

from fastapi import Request

from contestiq_api import metrics
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError

# Requests per IP per UTC day. Test hook: monkeypatch this dict.
DAILY_LIMITS: dict[str, int] = {
    "execute": 500,
    "badge_view": 2000,
    "billing_webhook": 5000,
    "judge0_callback": 20000,
    "report_export": 200,
    "recommendation_feedback": 300,
    "auth_register": 100,
    "handle_claim": 30,
    "handle_verify": 100,
}


def throttle(request: Request, bucket: str) -> None:
    limit = DAILY_LIMITS.get(bucket)
    if limit is None:
        return
    ip = request.client.host if request.client else "unknown"
    subject = f"throttle:{ip}"
    window = dt.date.today().isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO usage_limits (subject, feature, window_start, used) VALUES (?, ?, ?, 0)"
            " ON CONFLICT(subject, feature, window_start) DO NOTHING",
            (subject, bucket, window),
        )
        row = conn.execute(
            "SELECT used FROM usage_limits WHERE subject = ? AND feature = ? AND window_start = ?",
            (subject, bucket, window),
        ).fetchone()
        if row["used"] >= limit:
            metrics.inc(f"throttle_429_total_{bucket}")
            raise APIError(
                "RATE_LIMITED",
                f"Daily request limit for this endpoint was reached ({limit}/day). Try again tomorrow.",
                429,
            )
        conn.execute(
            "UPDATE usage_limits SET used = used + 1 WHERE subject = ? AND feature = ? AND window_start = ?",
            (subject, bucket, window),
        )
