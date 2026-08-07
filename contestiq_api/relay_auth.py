"""Statement-fetch relay auth and helpers.

The relay authenticates with STATEMENT_RELAY_TOKEN via:
  Authorization: Bearer <token>
"""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import Request

from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings


def require_relay(request: Request) -> dict[str, Any]:
    """Authorize the persistent statement-fetch relay."""
    settings = get_settings()
    expected = (settings.statement_relay_token or "").strip()
    if not expected or len(expected) < 24:
        raise APIError(
            "RELAY_NOT_CONFIGURED",
            "Statement relay token is not configured on this server.",
            503,
        )

    auth = (request.headers.get("Authorization") or "").strip()
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        token = (request.headers.get("X-Relay-Token") or "").strip()

    if not token or not secrets.compare_digest(token, expected):
        raise APIError("RELAY_UNAUTHORIZED", "Valid statement relay token required.", 401)

    relay_id = (request.headers.get("X-Relay-Id") or "relay").strip()[:64] or "relay"
    return {"actor": f"relay:{relay_id}", "relay_id": relay_id, "role": "relay"}
