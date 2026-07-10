"""v1 billing and entitlement endpoints (Phase 06)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from contestiq_api import billing as billing_mod
from contestiq_api import entitlements
from contestiq_api import auth
from contestiq_api.auth import current_user
from contestiq_api.errors import APIError

router = APIRouter(prefix="/api/v1")


class CheckoutRequest(BaseModel):
    plan: str = Field(pattern="^(premium_student|team|event)$")
    provider: str | None = None


@router.get("/me/entitlements")
def my_entitlements(ctx: dict[str, Any] = Depends(entitlements.plan_context)):
    user = ctx["user"]
    return {
        "user": {"user_id": user["user_id"], "handle": user.get("handle"), "role": user.get("role")} if user else None,
        "plan": ctx["plan"],
        "features": ctx["features"],
        "grants": entitlements.active_grants(user["user_id"]) if user and user.get("user_id") else [],
        "usage": entitlements.usage_summary(ctx["subject"]),
    }


@router.post("/billing/checkout")
def create_checkout(payload: CheckoutRequest, request: Request):
    user = current_user(request)
    if user is None:
        raise APIError("AUTH_REQUIRED", "Checkout requires an API token (Authorization: Bearer …).", 401)
    return billing_mod.checkout(user, payload.plan, payload.provider)


@router.post("/billing/webhook/{provider}")
async def billing_webhook(provider: str, request: Request):
    from contestiq_api import metrics
    from contestiq_api.throttle import throttle

    throttle(request, "billing_webhook")
    if provider not in billing_mod.PROVIDERS:
        raise APIError("UNKNOWN_PROVIDER", f"Unknown billing provider: {provider}", 422)
    if provider in {"manual", "local"}:
        # These providers have no third-party signature. They are operational
        # confirmation endpoints, so only a SolveX admin may invoke them.
        auth.require_admin(request)
    else:
        # Do not accept an external payment assertion until that provider's
        # signature verification is implemented. A configured secret alone
        # is not verification.
        raise APIError(
            "WEBHOOK_VERIFICATION_UNAVAILABLE",
            f"Signed {provider} webhooks are not implemented.",
            501,
        )
    payload = await request.json()
    if not isinstance(payload, dict):
        raise APIError("INVALID_WEBHOOK", "Webhook payload must be a JSON object.", 422)
    result = billing_mod.process_webhook(provider, payload)
    metrics.inc("payment_webhooks_total")
    if str(result.get("result", "")).startswith("granted:"):
        metrics.inc("payment_success_total")
    return result
