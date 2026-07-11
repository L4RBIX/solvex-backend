from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from contestiq_api import auth, entitlements, handles, supabase_auth
from contestiq_api.cfdata import store

ISSUER = "https://example.supabase.co/auth/v1"
AUDIENCE = "authenticated"
JWKS_URL = "https://example.supabase.co/auth/v1/.well-known/jwks.json"
ADMIN_KEY = "supabase-auth-test-admin-key"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    monkeypatch.setenv("SUPABASE_JWT_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("SUPABASE_JWKS_URL", JWKS_URL)
    getattr(supabase_auth._jwks_client, "cache_clear", lambda: None)()
    yield
    getattr(supabase_auth._jwks_client, "cache_clear", lambda: None)()


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


@pytest.fixture
def signing(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class SigningKey:
        key = private_key.public_key()

    class JwksClient:
        def get_signing_key_from_jwt(self, _token: str):
            return SigningKey()

    monkeypatch.setattr(supabase_auth, "_jwks_client", lambda _url: JwksClient())
    return private_key


def token_for(
    private_key,
    subject: str = "supabase-user-a",
    *,
    email: str = "learner@example.com",
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expires_delta: dt.timedelta = dt.timedelta(minutes=10),
) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {
            "sub": subject,
            "email": email,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + expires_delta,
            "role": "authenticated",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_valid_jwt_creates_and_reuses_stable_internal_user(client, signing):
    token = token_for(signing)
    first = client.get("/api/v1/auth/me", headers=bearer(token))
    second = client.get("/api/v1/auth/me", headers=bearer(token))
    assert first.status_code == second.status_code == 200
    assert first.json()["user_id"] == second.json()["user_id"]
    assert first.json()["email"] == "learner@example.com"
    assert first.json()["auth_provider"] == "supabase"

    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        identity = conn.execute("SELECT * FROM auth_identities").fetchone()
    assert identity["provider"] == "supabase"
    assert identity["provider_subject"] == "supabase-user-a"


@pytest.mark.parametrize(
    ("factory", "expected_status"),
    [
        (lambda key: token_for(rsa.generate_private_key(public_exponent=65537, key_size=2048)), 401),
        (lambda key: token_for(key, expires_delta=dt.timedelta(minutes=-1)), 401),
        (lambda key: token_for(key, issuer="https://wrong.example/auth/v1"), 401),
        (lambda key: token_for(key, audience="wrong-audience"), 401),
    ],
)
def test_invalid_signature_expiry_issuer_and_audience_are_rejected(client, signing, factory, expected_status):
    response = client.get("/api/v1/auth/me", headers=bearer(factory(signing)))
    assert response.status_code == expected_status
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_missing_auth_configuration_fails_closed(client, signing, monkeypatch):
    monkeypatch.delenv("SUPABASE_JWKS_URL")
    response = client.get("/api/v1/auth/me", headers=bearer(token_for(signing)))
    assert response.status_code == 503
    assert response.json()["error_code"] == "AUTH_NOT_CONFIGURED"


def test_jwt_shaped_token_never_falls_back_to_legacy_hash(client, signing):
    forged = token_for(rsa.generate_private_key(public_exponent=65537, key_size=2048))
    legacy = auth.create_user()
    with store.connect() as conn:
        conn.execute(
            "UPDATE users SET token_hash = ? WHERE user_id = ?",
            (hashlib.sha256(forged.encode()).hexdigest(), legacy["user_id"]),
        )
    assert client.get("/api/v1/auth/me", headers=bearer(forged)).status_code == 401


def test_client_identity_fields_cannot_override_jwt_user(client, signing):
    token = token_for(signing, subject="real-subject")
    response = client.get(
        "/api/v1/gamification/me?user_id=victim&handle=famous-handle&subject=user:victim",
        headers=bearer(token),
    )
    assert response.status_code == 200
    me = client.get("/api/v1/auth/me", headers=bearer(token)).json()
    assert response.json()["subject"] == f"user:{me['user_id']}"


def test_concurrent_first_login_creates_exactly_one_user(signing):
    claims = supabase_auth.verify_access_token(token_for(signing, subject="concurrent-subject"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        user_ids = list(pool.map(lambda _: supabase_auth.resolve_internal_user(claims)["user_id"], range(16)))
    assert len(set(user_ids)) == 1
    with store.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM auth_identities WHERE provider = 'supabase' AND provider_subject = ?",
            ("concurrent-subject",),
        ).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


def test_provider_subject_uniqueness_is_enforced(signing):
    claims = supabase_auth.verify_access_token(token_for(signing, subject="unique-subject"))
    user = supabase_auth.resolve_internal_user(claims)
    now = store._now()
    with store.connect() as conn, pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO auth_identities"
            " (identity_id, user_id, provider, provider_subject, email, created_at, updated_at)"
            " VALUES ('duplicate', ?, 'supabase', 'unique-subject', NULL, ?, ?)",
            (user["user_id"], now, now),
        )


def test_handle_ownership_and_entitlement_remain_bound_to_internal_user(client, signing):
    token_a = token_for(signing, subject="owner-a", email="a@example.com")
    token_b = token_for(signing, subject="owner-b", email="b@example.com")
    user_a = client.get("/api/v1/auth/me", headers=bearer(token_a)).json()
    user_b = client.get("/api/v1/auth/me", headers=bearer(token_b)).json()
    handles.admin_bind(user_a["user_id"], "stable-owned-handle")
    entitlements.grant_entitlement(
        user_a["user_id"], "premium_student", source="test", granted_by="test-suite"
    )

    again = client.get("/api/v1/auth/me", headers=bearer(token_a)).json()
    assert again["user_id"] == user_a["user_id"]
    assert again["handle"] == "stable-owned-handle"
    assert handles.owner_user_id_for_handle("stable-owned-handle") == user_a["user_id"]
    assert client.get("/api/v1/me/entitlements", headers=bearer(token_a)).json()["plan"] == "premium_student"
    assert client.get("/api/v1/me/entitlements", headers=bearer(token_b)).json()["plan"] == "free"
    assert user_a["user_id"] != user_b["user_id"]


def test_auth_me_has_only_safe_fields(client, signing):
    response = client.get("/api/v1/auth/me", headers=bearer(token_for(signing)))
    payload = response.json()
    assert set(payload) == {"user_id", "role", "email", "auth_provider", "handle", "handle_verified"}
    raw = json.dumps(payload).lower()
    for forbidden in ("provider_subject", "token_hash", "access_token", "refresh_token", "api_token"):
        assert forbidden not in raw


def test_legacy_register_is_retired_in_production(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    response = client.post("/api/v1/auth/register")
    assert response.status_code == 410
    assert response.json()["error_code"] == "ENDPOINT_RETIRED"
