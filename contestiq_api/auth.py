"""Minimal user/token auth for the paid beta (Phase 06).

Users are created by an admin and authenticate with a bearer token
(`Authorization: Bearer <token>`). Only the sha256 of the token is stored.
Admin access is either a user with role=admin or the ADMIN_API_KEY bootstrap
header (`X-Admin-Key`) so the very first admin operations are possible before
any user exists. Anonymous requests are valid and resolve to the free plan.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from typing import Any

from fastapi import Request

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(handle: str | None = None, email: str | None = None, role: str = "user") -> dict[str, Any]:
    """Create a user and return it WITH the raw token (shown exactly once)."""
    if role not in ("user", "admin"):
        raise APIError("INVALID_ROLE", "role must be 'user' or 'admin'.", 422)
    token = secrets.token_hex(20)
    user_id = str(uuid.uuid4())
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO users (user_id, handle, email, role, token_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, store.canonical_handle(handle) if handle else None, email, role, _hash_token(token), store._now()),
        )
    return {"user_id": user_id, "handle": handle, "email": email, "role": role, "api_token": token}


def get_user_by_token(token: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE token_hash = ?", (_hash_token(token),)).fetchone()
    return dict(row) if row else None


def get_user(user_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_handle(handle: str) -> dict[str, Any] | None:
    """Best-effort lookup used by gamification to merge a CF handle's public
    events with any linked authenticated user's events (premium_conversion,
    verification_attempted). Returns the most recently created match."""
    with store.connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(COALESCE(handle,'')) = ? ORDER BY created_at DESC LIMIT 1",
            (store.canonical_handle(handle),),
        ).fetchone()
    return dict(row) if row else None


def search_users(query: str, limit: int = 20) -> list[dict[str, Any]]:
    like = f"%{query.strip().lower()}%"
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT user_id, handle, email, role, created_at FROM users"
            " WHERE LOWER(COALESCE(handle,'')) LIKE ? OR LOWER(COALESCE(email,'')) LIKE ? OR user_id = ?"
            " ORDER BY created_at DESC LIMIT ?",
            (like, like, query.strip(), limit),
        ).fetchall()
    return [dict(row) for row in rows]


def current_user(request: Request) -> dict[str, Any] | None:
    """Resolve the optional bearer token; None = anonymous (free plan)."""
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    user = get_user_by_token(header[7:].strip())
    if user is None:
        raise APIError("INVALID_TOKEN", "The provided API token is not valid.", 401)
    return user


def require_admin(request: Request) -> dict[str, Any]:
    """Admin = role-admin user token, or the ADMIN_API_KEY bootstrap header."""
    settings = get_settings()
    admin_key = request.headers.get("X-Admin-Key")
    if admin_key and settings.admin_api_key and secrets.compare_digest(admin_key, settings.admin_api_key):
        return {"user_id": None, "role": "admin", "actor": "admin_api_key"}
    user = current_user(request)
    if user is not None and user["role"] == "admin":
        return {**user, "actor": f"user:{user['user_id']}"}
    raise APIError("ADMIN_REQUIRED", "This endpoint requires admin access.", 403)


def audit(actor: str, action: str, target: str | None, details: dict[str, Any] | None = None) -> None:
    import json

    with store.connect() as conn:
        conn.execute(
            "INSERT INTO admin_audit_logs (audit_id, actor, action, target, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), actor, action, target, json.dumps(details or {}, ensure_ascii=False), store._now()),
        )
