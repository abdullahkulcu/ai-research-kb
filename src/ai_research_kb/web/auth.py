"""JWT issuance/verification.

The signing secret is read from the WEB_JWT_SECRET env var on every call (not
cached at import time) so tests can set it per-run. Unlike the LLM provider,
this is not optional: auth is security-critical, so a missing secret is a hard
error rather than a silent skip.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from pydantic import BaseModel

from .roles import Role

ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    username: str
    role: Role


def _secret() -> str:
    secret = os.environ.get("WEB_JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "WEB_JWT_SECRET tanımlı değil. .env dosyasında bir değer ayarlayın "
            "(ör. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
        )
    return secret


def create_access_token(username: str, role: Role, expire_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role.value,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    return TokenPayload(username=payload["sub"], role=payload["role"])
