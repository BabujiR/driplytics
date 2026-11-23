"""Token verification with real RSA-signed JWTs (no network, no identity provider needed)."""

import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from driplytics_api.auth.oidc import TokenError, TokenVerifier
from driplytics_api.auth.roles import Role, has_at_least

ISSUER = "http://localhost:8080/realms/driplytics"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(key: Any = KEY, **overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": "kc-alice",
        "azp": "driplytics-web",
        "iat": now,
        "exp": now + 300,
        "email": "Alice@Riverbend.test",
        "email_verified": True,
        "name": "Alice Riverbend",
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test"})


def verifier(**kw: Any) -> TokenVerifier:
    return TokenVerifier(
        issuer=ISSUER, key_resolver=lambda _t: KEY.public_key(), client_ids=["driplytics-web"], **kw
    )


def test_valid_token() -> None:
    c = verifier().verify(make_token())
    assert c.subject == "kc-alice" and c.email == "alice@riverbend.test"  # normalized to lower case
    assert c.email_verified and c.client_id == "driplytics-web" and c.name == "Alice Riverbend"


@pytest.mark.parametrize(
    ("overrides", "key", "fragment"),
    [
        ({"exp": int(time.time()) - 120}, KEY, "expired"),
        ({"iss": "https://evil.example/realms/driplytics"}, KEY, "issuer"),
        ({}, OTHER_KEY, "Signature"),
        ({"azp": "some-other-app"}, KEY, "client"),
        ({"sub": None}, KEY, "sub"),
    ],
    ids=["expired", "wrong-issuer", "wrong-signing-key", "wrong-client", "missing-sub"],
)
def test_rejected_tokens(overrides: dict[str, Any], key: Any, fragment: str) -> None:
    with pytest.raises(TokenError, match=fragment):
        verifier().verify(make_token(key, **overrides))


def test_unsigned_alg_none_is_rejected() -> None:
    token = jwt.encode({"iss": ISSUER, "sub": "x", "iat": 1, "exp": 9999999999}, None, algorithm="none")
    with pytest.raises(TokenError):
        verifier().verify(token)


def test_garbage_is_rejected() -> None:
    with pytest.raises(TokenError):
        verifier().verify("not-a-jwt")


def test_jwks_failure_becomes_token_error() -> None:
    def broken(_t: str) -> Any:
        raise ConnectionError("keycloak down")

    v = TokenVerifier(issuer=ISSUER, key_resolver=broken)
    with pytest.raises(TokenError, match="could not verify"):
        v.verify(make_token())


def test_audience_checked_when_configured() -> None:
    v = verifier(audience="driplytics-api")
    with pytest.raises(TokenError):
        v.verify(make_token(aud="account"))
    assert v.verify(make_token(aud="driplytics-api")).subject == "kc-alice"


def test_clock_skew_leeway() -> None:
    assert verifier(leeway_s=30).verify(make_token(exp=int(time.time()) - 10)).subject == "kc-alice"


@pytest.mark.parametrize(
    ("role", "minimum", "ok"),
    [
        (Role.OWNER, Role.ADMIN, True),
        (Role.ENGINEER, Role.ENGINEER, True),
        (Role.VIEWER, Role.ENGINEER, False),
        (Role.TECHNICIAN, Role.VIEWER, True),
        (Role.TECHNICIAN, Role.ENGINEER, False),
        (Role.PARTNER, Role.VIEWER, True),
    ],
)
def test_role_ranking(role: Role, minimum: Role, ok: bool) -> None:
    assert has_at_least(role, minimum) is ok
