"""Supabase Auth JWT verification and stable internal-user mapping.

Only a signed JWT from the configured Supabase issuer may reach the mapping
layer. The untrusted token payload is never used before PyJWT has verified the
signature, issuer, audience, and expiration against the project's public JWKS.
"""

from __future__ import annotations

import sqlite3
import uuid
from functools import lru_cache
from typing import Any

import jwt

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

AUTH_PROVIDER = "supabase"
ALLOWED_ALGORITHMS = ["RS256", "ES256"]


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url, cache_keys=True)


def verify_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if not (
        settings.supabase_jwt_issuer
        and settings.supabase_jwt_audience
        and settings.supabase_jwks_url
    ):
        raise APIError(
            "AUTH_NOT_CONFIGURED",
            "Supabase authentication is not configured on this server.",
            503,
        )
    try:
        signing_key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            issuer=settings.supabase_jwt_issuer,
            audience=settings.supabase_jwt_audience,
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise APIError("INVALID_TOKEN", "The provided access token is not valid.", 401) from exc
    except Exception as exc:  # JWKS transport/parse failure: never fall back to unverified claims.
        raise APIError(
            "AUTH_VERIFICATION_UNAVAILABLE",
            "Authentication verification is temporarily unavailable.",
            503,
        ) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
        raise APIError("INVALID_TOKEN", "The provided access token is not valid.", 401)
    return claims


def _safe_email(claims: dict[str, Any]) -> str | None:
    email = claims.get("email")
    if not isinstance(email, str):
        return None
    cleaned = email.strip().lower()
    return cleaned[:320] if cleaned else None


def resolve_internal_user(claims: dict[str, Any]) -> dict[str, Any]:
    """Atomically resolve/create one internal user for a verified Supabase sub."""
    provider_subject = str(claims["sub"]).strip()
    email = _safe_email(claims)
    now = store._now()

    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        identity = conn.execute(
            "SELECT user_id FROM auth_identities WHERE provider = ? AND provider_subject = ?",
            (AUTH_PROVIDER, provider_subject),
        ).fetchone()
        if identity is None:
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (user_id, handle, email, role, token_hash, created_at)"
                " VALUES (?, NULL, ?, 'user', NULL, ?)",
                (user_id, email, now),
            )
            try:
                conn.execute(
                    "INSERT INTO auth_identities"
                    " (identity_id, user_id, provider, provider_subject, email, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), user_id, AUTH_PROVIDER, provider_subject, email, now, now),
                )
            except sqlite3.IntegrityError:
                # Defensive for databases whose transaction semantics differ:
                # discard the unused user and resolve the unique winner.
                conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                identity = conn.execute(
                    "SELECT user_id FROM auth_identities WHERE provider = ? AND provider_subject = ?",
                    (AUTH_PROVIDER, provider_subject),
                ).fetchone()
                if identity is None:
                    raise
                user_id = identity["user_id"]
        else:
            user_id = identity["user_id"]

        conn.execute(
            "UPDATE auth_identities SET email = ?, updated_at = ?"
            " WHERE provider = ? AND provider_subject = ?",
            (email, now, AUTH_PROVIDER, provider_subject),
        )
        if email:
            conn.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    if user is None:
        raise APIError("AUTH_IDENTITY_ERROR", "Could not resolve the authenticated account.", 500)
    return {**dict(user), "auth_provider": AUTH_PROVIDER}


def authenticate(token: str) -> dict[str, Any]:
    return resolve_internal_user(verify_access_token(token))
