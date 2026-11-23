"""OIDC access-token verification (no web framework imports, so it is easy to test).

Locally the issuer is Keycloak (http://localhost:8080/realms/driplytics); in the cloud it is
WorkOS. Both publish signing keys at a JWKS URL; we verify signature, issuer, expiry and the
client the token was issued to (`azp`), plus the audience when one is configured.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import jwt

ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "PS256"]


class TokenError(Exception):
    """The token is missing, malformed, expired, or not for us. Always maps to HTTP 401."""


@dataclass(frozen=True)
class Claims:
    subject: str
    email: str | None
    email_verified: bool
    name: str | None
    client_id: str | None
    raw: dict[str, Any] = field(repr=False)


KeyResolver = Callable[[str], Any]  # token -> verification key


def jwks_key_resolver(jwks_url: str) -> KeyResolver:
    """Fetch (and cache) signing keys from the identity provider's JWKS endpoint."""
    client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=300, timeout=5)

    def resolve(token: str) -> Any:
        return client.get_signing_key_from_jwt(token).key

    return resolve


class TokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        key_resolver: KeyResolver,
        client_ids: list[str] | None = None,
        audience: str | None = None,
        leeway_s: int = 30,
    ) -> None:
        self.issuer = issuer
        self.key_resolver = key_resolver
        self.client_ids = set(client_ids or [])
        self.audience = audience
        self.leeway_s = leeway_s

    def verify(self, token: str) -> Claims:
        try:
            key = self.key_resolver(token)
            payload: dict[str, Any] = jwt.decode(
                token,
                key=key,
                algorithms=ALLOWED_ALGORITHMS,
                issuer=self.issuer,
                audience=self.audience,
                leeway=self.leeway_s,
                options={"require": ["exp", "iat", "iss", "sub"], "verify_aud": self.audience is not None},
            )
        except jwt.PyJWTError as exc:
            raise TokenError(f"invalid token: {exc}") from exc
        except Exception as exc:  # e.g. JWKS endpoint unreachable
            raise TokenError(f"could not verify token: {type(exc).__name__}") from exc

        client_id = payload.get("azp") or payload.get("client_id")
        if self.client_ids and client_id not in self.client_ids:
            raise TokenError(f"token was issued to client {client_id!r}, not to Driplytics")
        email = payload.get("email")
        return Claims(
            subject=str(payload["sub"]),
            email=email.strip().lower() if isinstance(email, str) else None,
            email_verified=bool(payload.get("email_verified", False)),
            name=payload.get("name") or payload.get("preferred_username"),
            client_id=client_id,
            raw=payload,
        )
