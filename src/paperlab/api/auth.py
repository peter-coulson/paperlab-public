"""Supabase JWT authentication for PaperLab API.

Verifies Supabase-issued JWTs using JWKS (public key verification).
Maps Supabase user UUID to local student_id.
Auto-creates student record on first authenticated request (no registration step).

Development mode: Accepts "dev" token to bypass JWT verification for local testing.
"""

from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient  # type: ignore[attr-defined]

from paperlab.config import settings
from paperlab.config.constants import DatabaseSettings
from paperlab.data.database import connection
from paperlab.data.repositories.marking import students

http_bearer = HTTPBearer()

DEV_TOKEN = "dev"

# JWKS client singleton (caches public keys from Supabase)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Get JWKS client for Supabase public key verification."""
    global _jwks_client
    if _jwks_client is None:
        supabase_url = settings.supabase_url
        if not supabase_url:
            raise RuntimeError(
                "SUPABASE_URL not configured. Set PAPERLAB_SUPABASE_URL environment variable."
            )
        jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def _decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify Supabase JWT using JWKS public key.

    Args:
        token: JWT from Authorization header

    Returns:
        Decoded payload with 'sub' (Supabase user UUID)

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@lru_cache(maxsize=1000)
def _get_student_id_cached(supabase_uid: str) -> int:
    """Get or create student_id from Supabase UUID with caching.

    Cache is safe because supabase_uid → student_id mapping is immutable.
    First request per user hits DB, subsequent requests are O(1) dict lookup.
    """
    with connection(settings.db_path) as conn:
        student_id = students.get_or_create_by_supabase_uid(supabase_uid, conn)
        conn.commit()
    return student_id


def clear_student_cache(supabase_uid: str) -> None:
    """Clear cached student_id for a specific Supabase UID.

    Must be called when deleting a user account to prevent stale cache entries.
    """
    # lru_cache doesn't support removing individual entries, so we need to
    # access the cache internals or clear the whole cache
    _get_student_id_cached.cache_clear()


def get_current_student_id(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),  # noqa: B008
) -> int:
    """Extract student_id from Supabase JWT, auto-creating if needed.

    This is the ONLY function endpoints use. Maps Supabase UUID to local student_id.
    Auto-creates student record on first authenticated request (no registration step).

    Development mode: Accepts "dev" token to bypass JWT verification.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        Local student_id (integer)

    Raises:
        HTTPException: 401 if token invalid
    """
    # Dev mode bypass: accept "dev" token in development environment
    if settings.environment == "development" and credentials.credentials == DEV_TOKEN:
        return _get_student_id_cached(DatabaseSettings.TEST_STUDENT_SUPABASE_UID)

    # 1. Decode JWT and extract Supabase user UUID
    payload = _decode_supabase_jwt(credentials.credentials)
    supabase_uid = payload.get("sub")

    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Get or create local student_id (cached after first lookup)
    return _get_student_id_cached(supabase_uid)
