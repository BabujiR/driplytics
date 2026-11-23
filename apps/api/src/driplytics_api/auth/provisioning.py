"""Map a verified identity (OIDC 'sub' + email) to our app_user row.

1. Known subject             -> that user (refresh email, name, last login).
2. Unclaimed user, same verified email (invited / seeded) -> link the subject to it.
3. Otherwise                 -> create a new user with no memberships (sees nothing until invited).
A verified email that already belongs to a DIFFERENT subject is refused (account takeover guard).
"""

from uuid import UUID

from driplytics_api.db.connection import Conn

from .oidc import Claims


class ProvisioningError(Exception):
    """Maps to HTTP 403."""


def provision_user(conn: Conn, claims: Claims) -> UUID:
    row = conn.execute(
        "UPDATE app_user SET last_login_at = now(), display_name = coalesce(%s, display_name) "
        "WHERE idp_subject = %s RETURNING id",
        (claims.name, claims.subject),
    ).fetchone()
    if row:
        return UUID(str(row["id"]))

    if not claims.email:
        raise ProvisioningError("the identity provider did not send an email address")
    if not claims.email_verified:
        raise ProvisioningError("email address is not verified with the identity provider")

    row = conn.execute(
        "UPDATE app_user SET idp_subject = %s, last_login_at = now(), "
        "display_name = coalesce(display_name, %s) WHERE email = %s AND idp_subject IS NULL RETURNING id",
        (claims.subject, claims.name, claims.email),
    ).fetchone()
    if row:
        return UUID(str(row["id"]))

    row = conn.execute(
        "INSERT INTO app_user (email, idp_subject, display_name, last_login_at) VALUES (%s, %s, %s, now()) "
        "ON CONFLICT (email) DO NOTHING RETURNING id",
        (claims.email, claims.subject, claims.name),
    ).fetchone()
    if row:
        return UUID(str(row["id"]))
    raise ProvisioningError("this email address is already linked to a different sign-in")
