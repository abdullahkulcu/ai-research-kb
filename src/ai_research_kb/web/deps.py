"""FastAPI dependencies: auth, RBAC, repo root."""

from __future__ import annotations

from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import load_config
from ..repo import find_repo_root
from .auth import TokenPayload, decode_access_token
from .roles import Role, at_least

_bearer = HTTPBearer(auto_error=False)


def get_app_root() -> Path:
    """Actual repo root — where config.yaml/users.yaml live."""
    return find_repo_root()


def get_docs_root(root: Path = Depends(get_app_root)) -> Path:
    """Directory the web panel scans for docs (config: web.docs_root, default "research")."""
    docs_root = load_config(root)["web"]["docs_root"]
    return root / docs_root


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Yetkilendirme gerekli")
    try:
        return decode_access_token(credentials.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Geçersiz token: {e}") from e


def require_role(minimum: Role):
    def _check(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if not at_least(user.role, minimum):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Bu işlem en az '{minimum.value}' rolü gerektirir",
            )
        return user

    return _check
