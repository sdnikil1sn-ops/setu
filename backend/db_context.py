"""Request-scoped PostgreSQL RLS context.

Context is set only by the verified authentication middleware. Database settings
are transaction-local, so pooled/reused connections cannot retain another
request's identity.
"""
from contextvars import ContextVar

_auth_user_id = ContextVar("setu_auth_user_id", default="")
_demo_mode = ContextVar("setu_demo_mode", default=False)


def set_request_db_context(auth_user_id=None, demo_mode=False):
    auth_token = _auth_user_id.set(str(auth_user_id or ""))
    demo_token = _demo_mode.set(bool(demo_mode))
    return auth_token, demo_token


def reset_request_db_context(tokens):
    auth_token, demo_token = tokens
    _auth_user_id.reset(auth_token)
    _demo_mode.reset(demo_token)


def apply_connection_context(conn):
    """Set transaction-local identity before application queries execute."""
    auth_user_id = _auth_user_id.get()
    demo_mode = _demo_mode.get()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                set_config('setu.auth_user_id', %s, true),
                set_config('setu.demo_mode', %s, true)
            """,
            (auth_user_id, "true" if demo_mode else "false"),
        )
    return conn
