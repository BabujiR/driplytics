"""Roles live in OUR database (membership.role), not in the identity provider (ADR 0004)."""

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    ENGINEER = "engineer"
    TECHNICIAN = "technician"
    VIEWER = "viewer"
    PARTNER = "partner"


# Higher rank can do everything a lower rank can. Technicians can do field verification on top of
# viewing; engineers can also change mappings and settings; admins manage users; owners manage billing.
_RANK = {
    Role.OWNER: 50,
    Role.ADMIN: 40,
    Role.ENGINEER: 30,
    Role.TECHNICIAN: 20,
    Role.VIEWER: 10,
    Role.PARTNER: 10,  # read access to client tenants; partner_access grants arrive in Phase 3
}


def has_at_least(role: Role | str, minimum: Role | str) -> bool:
    return _RANK[Role(role)] >= _RANK[Role(minimum)]
