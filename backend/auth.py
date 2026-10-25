
import hmac
import os
from functools import lru_cache
from urllib.parse import urlparse

import jwt
from jwt import PyJWKClient, PyJWKClientConnectionError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


DEMO_TOKEN_PATHS = {
    "/api/v1/institutions",
}


def error_response(status_code: int, detail: str) -> JSONResponse:
    headers = {}
    if status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers,
    )


@lru_cache(maxsize=1)
def get_jwks_client():
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    parsed = urlparse(supabase_url)

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("SUPABASE_URL is missing or invalid")

    return PyJWKClient(
        f"{supabase_url}/auth/v1/.well-known/jwks.json",
        cache_jwk_set=True,
        lifespan=600,
        timeout=5,
    )


def verify_supabase_jwt(token: str) -> dict:
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured")

    signing_key = get_jwks_client().get_signing_key_from_jwt(token)

    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        issuer=f"{supabase_url}/auth/v1",
        audience="authenticated",
        leeway=10,
        options={"require": ["exp", "iss", "aud", "sub"]},
    )

    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise jwt.InvalidTokenError("Invalid subject")

    return claims


async def authenticate_request(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    path = request.url.path

    if not path.startswith("/api/v1/"):
        return await call_next(request)

    # Preserve the existing disabled-endpoint behavior.
    if (
        path == "/api/v1/overlaps/semantic-check"
        and os.getenv("SETU_ENABLE_SEMANTIC_CHECK", "").lower() != "true"
    ):
        return await call_next(request)

    # The shared demo token only grants access to selected read-only routes.
    supplied_token = request.headers.get("X-SETU-API-TOKEN", "")
    configured_token = os.getenv("SETU_API_TOKEN", "")

    if supplied_token and configured_token and hmac.compare_digest(
        supplied_token, configured_token
    ):
        if path not in DEMO_TOKEN_PATHS:
            return error_response(
                403,
                "Demo token is not authorized for this endpoint",
            )

        request.state.auth_type = "demo_token"
        return await call_next(request)

    # All remaining versioned API requests require a Supabase JWT.
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not separator or not token.strip():
        return error_response(
            401,
            "A valid demo token or Supabase bearer token is required",
        )

    try:
        claims = await run_in_threadpool(
            verify_supabase_jwt,
            token.strip(),
        )
    except PyJWKClientConnectionError:
        return error_response(
            503,
            "Supabase signing keys are temporarily unavailable",
        )
    except (jwt.InvalidTokenError, jwt.PyJWKClientError, ValueError):
        return error_response(
            401,
            "Invalid or expired Supabase access token",
        )
    except RuntimeError:
        return error_response(
            503,
            "Supabase authentication is not configured correctly",
        )

    request.state.auth_type = "supabase_jwt"
    request.state.user_id = claims["sub"]
    request.state.jwt_claims = claims

    return await call_next(request)
