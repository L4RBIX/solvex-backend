"""Presentation identity derived from an authenticated SolveX account.

Authorization always uses the internal ``user_id``.  Public display labels
must not be caller-controlled either: a verified Codeforces handle is an
authoritative label, while an unverified account gets a stable pseudonymous
label that reveals no raw internal identifier.
"""

from __future__ import annotations

import hashlib
from typing import Any

from contestiq_api.cfdata import store


def account_display_name(caller: dict[str, Any]) -> str:
    verified_handle = caller.get("handle")
    if verified_handle:
        return store.canonical_handle(str(verified_handle))

    user_id = str(caller.get("user_id") or "")
    if not user_id:
        raise ValueError("authenticated user_id is required for an account display name")
    suffix = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:6].upper()
    return f"SolveX Player {suffix}"
