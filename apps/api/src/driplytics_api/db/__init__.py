"""Database access: psycopg connections with per-transaction tenant context (ADR 0003)."""

from .connection import request_tx

__all__ = ["request_tx"]
