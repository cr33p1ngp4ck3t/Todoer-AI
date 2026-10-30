import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlmodel import select
from src.api.auth import (
    SECRET_KEY,
    create_access_token,
    hash_token,
    needs_rehash,
    pwd_context,
    verify_password,
)
from src.models.refresh_token import RefreshToken
from src.models.user import User


@pytest.fixture
def account(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "test-password-123",
    }
    response = client.post("/users/register", json=payload)
    assert response.status_code == 201
    return payload | {"id": response.json()["id"]}


def test_legacy_bcrypt_passwords_still_verify():
    legacy_hash = pwd_context.hash("legacy-password", scheme="bcrypt")
    assert verify_password("legacy-password", legacy_hash)
    assert needs_rehash(legacy_hash)


@pytest.fixture
def tokens(client, account):
    response = client.post(
        "/users/login",
        json={"email": account["email"], "password": account["password"]},
    )
    assert response.status_code == 200
    return response.json()


def test_registration_stores_hash_and_rejects_duplicates(client, account, db_session):
    user = db_session.get(User, UUID(account["id"]))
    assert user.hashed_password != account["password"]
    assert verify_password(account["password"], user.hashed_password)
    assert client.post("/users/register", json=account).status_code == 409
    assert (
        client.post(
            "/users/register", json=account | {"email": "other@example.com"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/users/login", json={"email": account["email"], "password": "wrong"}
        ).status_code
        == 401
    )


def test_access_token_authenticates_profile(client, account, tokens):
    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == account["id"]
    assert "hashed_password" not in response.json()


@pytest.mark.parametrize("path", ["/users/me", "/tasks", "/api/conversations"])
def test_protected_endpoints_require_authentication(client, path, db_session):
    assert client.get(path).status_code == 401
    assert db_session.exec(select(User)).all() == []


@pytest.mark.parametrize("subject", ["not-a-uuid", "", None])
def test_invalid_token_subject_is_unauthorized(client, subject):
    token = create_access_token({"sub": subject})
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_tampered_and_expired_access_tokens_are_unauthorized(client, account):
    valid = create_access_token({"sub": account["id"]})
    assert (
        client.get(
            "/users/me", headers={"Authorization": f"Bearer {valid[:-1]}x"}
        ).status_code
        == 401
    )


def test_standard_hs256_tokens_remain_compatible(client, account):
    def encode(value):
        return base64.urlsafe_b64encode(value).rstrip(b"=")

    header = encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = encode(
        json.dumps(
            {
                "sub": account["id"],
                "exp": int(
                    (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()
                ),
            }
        ).encode()
    )
    content = header + b"." + claims
    signature = encode(hmac.new(SECRET_KEY.encode(), content, hashlib.sha256).digest())
    token = (content + b"." + signature).decode()

    assert (
        client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )
    expired = create_access_token(
        {"sub": account["id"]}, expires_delta=timedelta(seconds=-1)
    )
    assert (
        client.get(
            "/users/me", headers={"Authorization": f"Bearer {expired}"}
        ).status_code
        == 401
    )


def test_refresh_rotates_and_logout_revokes(client, tokens, db_session):
    original = tokens["refresh_token"]
    stored = db_session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(original))
    ).one()
    assert stored.token_hash != original
    response = client.post("/auth/refresh", json={"refresh_token": original})
    assert response.status_code == 200
    replacement = response.json()["refresh_token"]
    assert replacement != original
    assert (
        client.post("/auth/refresh", json={"refresh_token": original}).status_code
        == 401
    )
    assert (
        client.post("/auth/logout", json={"refresh_token": replacement}).status_code
        == 200
    )
    assert (
        client.post("/auth/refresh", json={"refresh_token": replacement}).status_code
        == 401
    )


def test_expired_refresh_token_is_rejected(client, tokens, db_session):
    stored = db_session.exec(select(RefreshToken)).one()
    stored.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.add(stored)
    db_session.commit()
    assert (
        client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )


def test_logout_all_revokes_each_session(client, account, tokens):
    second = client.post("/users/login", json=account).json()
    response = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    for token in (tokens, second):
        assert (
            client.post(
                "/auth/refresh", json={"refresh_token": token["refresh_token"]}
            ).status_code
            == 401
        )
