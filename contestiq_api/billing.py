"""Billing provider abstraction and webhook processing (Phase 06).

Providers are pluggable because the payment rails vary by country/legal
entity. Three ship today:
- manual: the paid-beta path — checkout returns payment instructions and an
  admin confirms the payment (or grants the entitlement directly);
- local: dev/test provider — checkout returns a fake checkout id whose
  completion is driven through the same webhook path as real providers;
- stripe: placeholder that fails loudly until BILLING_API_KEY is configured.

Webhook idempotency: (provider, event_id) is the payment_webhook_events
primary key. A replayed event returns the recorded result and side effects
run exactly once.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from contestiq_api import entitlements
from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

PLAN_PRICES_CENTS = {"premium_student": 500, "team": 5000, "event": 20000}
DEFAULT_GRANT_DAYS = {"premium_student": 31, "team": 31, "event": 45}


class BillingProvider(Protocol):
    name: str

    def create_checkout(self, user: dict[str, Any], plan: str) -> dict[str, Any]: ...


class ManualProvider:
    name = "manual"

    def create_checkout(self, user: dict[str, Any], plan: str) -> dict[str, Any]:
        payment_id = _create_payment(user["user_id"], self.name, plan, "pending")
        return {
            "provider": self.name,
            "payment_id": payment_id,
            "status": "pending_manual_payment",
            "instructions": (
                "Manual beta checkout: pay via the agreed channel and share the payment id "
                "with the SolveX team. An admin will confirm and activate the plan."
            ),
        }


class LocalProvider:
    name = "local"

    def create_checkout(self, user: dict[str, Any], plan: str) -> dict[str, Any]:
        payment_id = _create_payment(user["user_id"], self.name, plan, "pending")
        return {
            "provider": self.name,
            "payment_id": payment_id,
            "status": "pending",
            "checkout_url": f"local://checkout/{payment_id}",
            "note": "Dev provider: complete by POSTing a payment.completed webhook with this payment_id.",
        }


class StripeProvider:
    name = "stripe"

    def create_checkout(self, user: dict[str, Any], plan: str) -> dict[str, Any]:
        if not get_settings().billing_api_key:
            raise APIError(
                "PROVIDER_NOT_CONFIGURED",
                "Stripe provider requires BILLING_API_KEY. Use the 'manual' provider for the beta.",
                501,
            )
        # Real Stripe session creation lands when keys exist; the abstraction
        # boundary (create_checkout + webhook) is what later code relies on.
        raise APIError("PROVIDER_NOT_IMPLEMENTED", "Stripe checkout is not implemented yet.", 501)


PROVIDERS: dict[str, BillingProvider] = {
    "manual": ManualProvider(),
    "local": LocalProvider(),
    "stripe": StripeProvider(),
}


def get_provider(name: str | None = None) -> BillingProvider:
    resolved = (name or get_settings().billing_provider or "manual").lower()
    provider = PROVIDERS.get(resolved)
    if provider is None:
        raise APIError("UNKNOWN_PROVIDER", f"Unknown billing provider: {resolved}", 422)
    return provider


def _create_payment(user_id: str, provider: str, plan: str, status: str) -> str:
    if plan not in PLAN_PRICES_CENTS:
        raise APIError("INVALID_PLAN", f"plan must be one of: {', '.join(PLAN_PRICES_CENTS)}", 422)
    payment_id = str(uuid.uuid4())
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO payments (payment_id, user_id, provider, plan, amount_cents, currency, payment_status, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, 'USD', ?, ?, ?)",
            (payment_id, user_id, provider, plan, PLAN_PRICES_CENTS[plan], status, now, now),
        )
        existing = conn.execute(
            "SELECT customer_id FROM billing_customers WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO billing_customers (customer_id, user_id, provider, created_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, provider, now),
            )
    return payment_id


def checkout(user: dict[str, Any], plan: str, provider_name: str | None = None) -> dict[str, Any]:
    return get_provider(provider_name).create_checkout(user, plan)


# ─── Webhook processing ──────────────────────────────────────────────────────


def process_webhook(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Idempotent webhook processing keyed by (provider, event_id)."""
    if provider not in PROVIDERS:
        raise APIError("UNKNOWN_PROVIDER", f"Unknown billing provider: {provider}", 422)
    event_id = str(payload.get("event_id") or "").strip()
    if not event_id:
        raise APIError("INVALID_WEBHOOK", "Webhook payload must include event_id.", 422)
    event_type = str(payload.get("type") or "unknown")

    with store.connect() as conn:
        try:
            conn.execute(
                "INSERT INTO payment_webhook_events (event_id, provider, event_type, payload, processed_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (event_id, provider, event_type, json.dumps(payload, ensure_ascii=False), store._now()),
            )
        except sqlite3.IntegrityError:
            row = conn.execute(
                "SELECT result FROM payment_webhook_events WHERE provider = ? AND event_id = ?",
                (provider, event_id),
            ).fetchone()
            return {"status": "already_processed", "event_id": event_id, "result": row["result"]}

    result = _apply_webhook_event(provider, event_type, payload)
    with store.connect() as conn:
        conn.execute(
            "UPDATE payment_webhook_events SET result = ? WHERE provider = ? AND event_id = ?",
            (result, provider, event_id),
        )
    return {"status": "processed", "event_id": event_id, "result": result}


def _apply_webhook_event(provider: str, event_type: str, payload: dict[str, Any]) -> str:
    if event_type != "payment.completed":
        return f"ignored_event_type:{event_type}"

    user_id = payload.get("user_id")
    payment_id = payload.get("payment_id")
    plan = payload.get("plan")
    now = store._now()

    with store.connect() as conn:
        if payment_id:
            row = conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone()
            if row is not None:
                user_id = user_id or row["user_id"]
                plan = plan or row["plan"]
                conn.execute(
                    "UPDATE payments SET payment_status = 'completed', external_payment_id = ?, updated_at = ?"
                    " WHERE payment_id = ?",
                    (payload.get("external_payment_id"), now, payment_id),
                )
    if not user_id or not plan:
        return "error:missing_user_or_plan"

    expires = payload.get("expires_at")
    if not expires:
        days = DEFAULT_GRANT_DAYS.get(plan, 31)
        expires = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    entitlements.grant_entitlement(
        user_id, plan, source="webhook", granted_by=f"webhook:{provider}",
        reference=payload.get("external_payment_id") or payment_id, expires_at=expires,
    )
    return f"granted:{plan}"


def billing_summary(user_id: str) -> dict[str, Any]:
    with store.connect() as conn:
        payments = [dict(r) for r in conn.execute(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,)).fetchall()]
        customers = [dict(r) for r in conn.execute(
            "SELECT * FROM billing_customers WHERE user_id = ?", (user_id,)).fetchall()]
        subscriptions = [dict(r) for r in conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)).fetchall()]
    return {
        "user_id": user_id,
        "payments": payments,
        "customers": customers,
        "subscriptions": subscriptions,
        "grants": entitlements.active_grants(user_id),
        "effective_plan": entitlements.effective_plan({"user_id": user_id, "role": "user"}),
    }
