"""Codeforces handle ownership verification (security hotfix).

A Codeforces handle is PUBLIC data — anyone can see it, so it must never be
trusted as authentication. This module lets an authenticated SolveX user
(bearer token — see auth.require_user) PROVE they control a given CF handle
by placing a short-lived, single-use verification code in that handle's
public "Organization" profile field, then verifying it against a LIVE
(non-cached) fetch of the Codeforces profile.

Once verified, `handle_owners` is the single source of truth for "which
user_id, if any, owns this handle" — one verified owner per handle, enforced
by primary key. Authorization code (duels, leaderboards, gamification) must
key off `user:<id>` only; use `verified_handle_for_user` /
`owner_user_id_for_handle` when a verified CF handle is needed for display or
computation (e.g. duel problem-pick anchor rating), never for authorization.

`users.handle` (the older, free-text column) is updated on verification for
back-compat with existing admin tooling, but it is NOT authoritative — only
`handle_owners` is. An unverified/admin-set `users.handle` value grants no
handle-scoped privileges.
"""

from __future__ import annotations

import datetime as dt
import json
import secrets
import uuid
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle

CLAIM_TTL_MINUTES = 30
VERIFICATION_FIELD = "organization"  # public, user-editable CF profile field returned by user.info
CODE_PREFIX = "solvex-verify-"

STATUS_PENDING = "pending"
STATUS_VERIFIED = "verified"
STATUS_EXPIRED = "expired"
STATUS_SUPERSEDED = "superseded"

BOUND_SELF = "self_verification"
BOUND_ADMIN = "admin_reconciliation"

# The PostgreSQL migration and SQLite mirror deliberately keep
# verification_code NOT NULL.  Terminal claims therefore erase the secret
# with an empty string instead of NULL.
_CLEARED_CODE = ""


def _now_dt() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _generate_code() -> str:
    return CODE_PREFIX + secrets.token_hex(4)


def owner_user_id_for_handle(handle: str) -> str | None:
    canonical = store.canonical_handle(handle)
    with store.connect() as conn:
        row = conn.execute("SELECT user_id FROM handle_owners WHERE handle = ?", (canonical,)).fetchone()
    return row["user_id"] if row else None


def verified_handle_for_user(user_id: str) -> str | None:
    binding = verified_binding_for_user(user_id)
    return binding["handle"] if binding else None


def verified_binding_for_user(user_id: str) -> dict[str, Any] | None:
    """Return the caller's latest verified binding, including its cutoff.

    ``verified_at`` bounds legacy handle telemetry: events authored under a
    public ``handle:`` alias after ownership was established are not trusted
    as account activity, because any visitor can still inspect that handle.
    """
    with store.connect() as conn:
        row = conn.execute(
            "SELECT handle, user_id, bound_by, verified_at FROM handle_owners"
            " WHERE user_id = ? ORDER BY verified_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def get_claim(claim_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        conn.execute(
            "UPDATE handle_claims SET status = ?, verification_code = ?"
            " WHERE claim_id = ? AND status = ? AND expires_at <= ?",
            (STATUS_EXPIRED, _CLEARED_CODE, claim_id, STATUS_PENDING, _now_dt().isoformat()),
        )
        row = conn.execute("SELECT * FROM handle_claims WHERE claim_id = ?", (claim_id,)).fetchone()
    return dict(row) if row else None


def list_claims_for_user(user_id: str) -> list[dict[str, Any]]:
    with store.connect() as conn:
        # Expiry is a data-state transition, not just a UI timer. Clear stale
        # one-time codes as soon as the account reads its claim history so an
        # abandoned claim cannot remain "pending" indefinitely at rest.
        conn.execute(
            "UPDATE handle_claims SET status = ?, verification_code = ?"
            " WHERE user_id = ? AND status = ? AND expires_at <= ?",
            (STATUS_EXPIRED, _CLEARED_CODE, user_id, STATUS_PENDING, _now_dt().isoformat()),
        )
        rows = conn.execute(
            "SELECT * FROM handle_claims WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def start_claim(user_id: str, handle: str) -> dict[str, Any]:
    """Begin ownership verification for `handle`. Returns a fresh code every
    call (superseding any still-pending claim for the same user+handle) so a
    stale/leaked code from an earlier attempt can't be replayed."""
    cleaned = validate_handle(handle)
    canonical = store.canonical_handle(cleaned)

    existing_owner = owner_user_id_for_handle(canonical)
    if existing_owner is not None:
        if existing_owner == user_id:
            return {"already_verified": True, "handle": canonical}
        raise APIError(
            "HANDLE_ALREADY_CLAIMED",
            "This Codeforces handle is already verified by another SolveX account.",
            409,
        )

    code = _generate_code()
    claim_id = str(uuid.uuid4())
    now = _now_dt()
    expires = now + dt.timedelta(minutes=CLAIM_TTL_MINUTES)
    with store.connect() as conn:
        conn.execute(
            "UPDATE handle_claims SET status = ?, verification_code = ?"
            " WHERE user_id = ? AND handle = ? AND status = ?",
            (STATUS_SUPERSEDED, _CLEARED_CODE, user_id, canonical, STATUS_PENDING),
        )
        conn.execute(
            "INSERT INTO handle_claims (claim_id, user_id, handle, verification_code, status, created_at, expires_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (claim_id, user_id, canonical, code, STATUS_PENDING, now.isoformat(), expires.isoformat()),
        )
    return {
        "already_verified": False,
        "claim_id": claim_id,
        "handle": canonical,
        "verification_code": code,
        "verification_field": VERIFICATION_FIELD,
        "expires_at": expires.isoformat(),
        "instructions": (
            f"On Codeforces, go to Settings and set your 'Organization' field to exactly '{code}', "
            "save, then call verify before this code expires. You can change it back afterwards."
        ),
    }


def verify_claim(user_id: str, claim_id: str) -> dict[str, Any]:
    """Fetch the CF profile live (never cached) and check the verification
    code against the agreed public field. Only on a match does the handle
    bind to user_id in handle_owners."""
    claim = get_claim(claim_id)
    if claim is None or claim["user_id"] != user_id:
        raise APIError("CLAIM_NOT_FOUND", "Verification claim not found.", 404)
    if claim["status"] == STATUS_VERIFIED:
        raise APIError(
            "CLAIM_ALREADY_USED",
            "This verification claim has already been consumed.",
            409,
        )
    if claim["status"] == STATUS_EXPIRED:
        raise APIError("CLAIM_EXPIRED", "This verification code has expired — start a new claim.", 410)
    if claim["status"] != STATUS_PENDING:
        raise APIError(
            "CLAIM_NOT_PENDING",
            "This verification claim is no longer pending (expired or superseded) — start a new claim.",
            409,
        )

    expires = dt.datetime.fromisoformat(claim["expires_at"])
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=dt.timezone.utc)
    if _now_dt() > expires:
        with store.connect() as conn:
            conn.execute(
                "UPDATE handle_claims SET status = ?, verification_code = ? WHERE claim_id = ? AND status = ?",
                (STATUS_EXPIRED, _CLEARED_CODE, claim_id, STATUS_PENDING),
            )
        raise APIError("CLAIM_EXPIRED", "This verification code has expired — start a new claim.", 410)

    existing_owner = owner_user_id_for_handle(claim["handle"])
    if existing_owner is not None:
        with store.connect() as conn:
            conn.execute(
                "UPDATE handle_claims SET status = ?, verification_code = ? WHERE claim_id = ? AND status = ?",
                (STATUS_SUPERSEDED, _CLEARED_CODE, claim_id, STATUS_PENDING),
            )
        if existing_owner == user_id:
            raise APIError(
                "CLAIM_NOT_PENDING",
                "This handle is already bound to your account; the pending claim was superseded.",
                409,
            )
        raise APIError(
            "HANDLE_ALREADY_CLAIMED",
            "This Codeforces handle is already verified by another SolveX account.",
            409,
        )

    from contestiq_core.codeforces.client import CodeforcesAPIError, fetch_user_info

    try:
        profile = fetch_user_info(claim["handle"], use_cache=False)
    except CodeforcesAPIError as exc:
        raise APIError("CF_PROFILE_FETCH_FAILED", f"Could not fetch the Codeforces profile: {exc}", 502) from exc

    field_value = (profile.get(VERIFICATION_FIELD) or "").strip()
    if field_value != claim["verification_code"]:
        raise APIError(
            "VERIFICATION_CODE_MISMATCH",
            f"Your Codeforces '{VERIFICATION_FIELD}' field does not match the verification code yet.",
            422,
        )

    now_dt = _now_dt()
    now = now_dt.isoformat()
    terminal_error: APIError | None = None
    with store.connect() as conn:
        # Serialize the final status/owner transition.  Re-reading after the
        # write lock makes simultaneous verify calls single-use and prevents
        # an admin/self-service race from reporting a false success.
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute(
            "SELECT * FROM handle_claims WHERE claim_id = ? AND user_id = ?",
            (claim_id, user_id),
        ).fetchone()
        if current is None:
            terminal_error = APIError("CLAIM_NOT_FOUND", "Verification claim not found.", 404)
        elif current["status"] == STATUS_VERIFIED:
            terminal_error = APIError(
                "CLAIM_ALREADY_USED",
                "This verification claim has already been consumed.",
                409,
            )
        elif current["status"] != STATUS_PENDING:
            terminal_error = APIError(
                "CLAIM_NOT_PENDING",
                "This verification claim is no longer pending (expired or superseded) — start a new claim.",
                409,
            )
        else:
            current_expires = dt.datetime.fromisoformat(current["expires_at"])
            if current_expires.tzinfo is None:
                current_expires = current_expires.replace(tzinfo=dt.timezone.utc)
            if now_dt > current_expires:
                conn.execute(
                    "UPDATE handle_claims SET status = ?, verification_code = ? WHERE claim_id = ?",
                    (STATUS_EXPIRED, _CLEARED_CODE, claim_id),
                )
                terminal_error = APIError(
                    "CLAIM_EXPIRED",
                    "This verification code has expired — start a new claim.",
                    410,
                )
            elif current["verification_code"] != claim["verification_code"]:
                # A concurrent replacement/terminal transition invalidated
                # the code that was checked against the live profile.
                terminal_error = APIError(
                    "CLAIM_NOT_PENDING",
                    "This verification claim changed while it was being checked — start a new claim.",
                    409,
                )
            else:
                owner = conn.execute(
                    "SELECT user_id FROM handle_owners WHERE handle = ?",
                    (claim["handle"],),
                ).fetchone()
                if owner is not None:
                    conn.execute(
                        "UPDATE handle_claims SET status = ?, verification_code = ? WHERE claim_id = ?",
                        (STATUS_SUPERSEDED, _CLEARED_CODE, claim_id),
                    )
                    if owner["user_id"] == user_id:
                        terminal_error = APIError(
                            "CLAIM_NOT_PENDING",
                            "This handle is already bound to your account; the pending claim was superseded.",
                            409,
                        )
                    else:
                        terminal_error = APIError(
                            "HANDLE_ALREADY_CLAIMED",
                            "This Codeforces handle is already verified by another SolveX account.",
                            409,
                        )
                else:
                    conn.execute(
                        "INSERT INTO handle_owners (handle, user_id, claim_id, bound_by, verified_at)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (claim["handle"], user_id, claim_id, BOUND_SELF, now),
                    )
                    conn.execute(
                        "UPDATE handle_claims SET status = ?, verification_code = ?, verified_at = ?"
                        " WHERE claim_id = ?",
                        (STATUS_VERIFIED, _CLEARED_CODE, now, claim_id),
                    )
                    conn.execute("UPDATE users SET handle = ? WHERE user_id = ?", (claim["handle"], user_id))

    if terminal_error is not None:
        raise terminal_error
    return {"handle": claim["handle"], "verified": True, "already_verified": False}


def admin_bind(user_id: str, handle: str, *, audit_actor: str | None = None) -> dict[str, Any]:
    """Audited admin/reconciliation operation: bind a handle to a user_id
    without the self-service verification flow (support cases, or explicitly
    reattributing pre-fix historical data after manual investigation). Never
    called automatically — see routes/admin.py for the audit-logged endpoint.

    When ``audit_actor`` is supplied (as it always is at the admin endpoint),
    the ownership mutation and audit row commit atomically.
    """
    canonical = store.canonical_handle(validate_handle(handle))
    now = _now_dt().isoformat()
    result: dict[str, Any]
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
            raise APIError("USER_NOT_FOUND", f"No user found with id {user_id}.", 404)

        existing = conn.execute(
            "SELECT user_id, bound_by, verified_at FROM handle_owners WHERE handle = ?",
            (canonical,),
        ).fetchone()
        if existing is not None and existing["user_id"] != user_id:
            raise APIError(
                "HANDLE_ALREADY_CLAIMED",
                "This Codeforces handle is already verified by another SolveX account.",
                409,
            )
        if existing is None:
            conn.execute(
                "INSERT INTO handle_owners (handle, user_id, claim_id, bound_by, verified_at)"
                " VALUES (?, ?, NULL, ?, ?)",
                (canonical, user_id, BOUND_ADMIN, now),
            )
            result = {
                "handle": canonical,
                "user_id": user_id,
                "bound_by": BOUND_ADMIN,
                "verified_at": now,
            }
        else:
            result = {
                "handle": canonical,
                "user_id": user_id,
                "bound_by": existing["bound_by"],
                "verified_at": existing["verified_at"],
            }
        conn.execute("UPDATE users SET handle = ? WHERE user_id = ?", (canonical, user_id))
        if audit_actor is not None:
            conn.execute(
                "INSERT INTO admin_audit_logs (audit_id, actor, action, target, details, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    audit_actor,
                    "handle_bind",
                    user_id,
                    json.dumps({"handle": canonical}, ensure_ascii=False),
                    store._now(),
                ),
            )
    return result
