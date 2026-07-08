from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import load_config
from ..auth import create_access_token
from ..deps import get_app_root, get_current_user
from ..schemas import LoginRequest, MeResponse, TokenResponse
from ..users import get_user, verify_password

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, root=Depends(get_app_root)):
    user = get_user(payload.username, root)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kullanıcı adı veya şifre hatalı")

    cfg = load_config(root)
    expire_minutes = cfg["web"]["access_token_expire_minutes"]
    token = create_access_token(user.username, user.role, expire_minutes)
    return TokenResponse(access_token=token, username=user.username, role=user.role)


@router.get("/auth/me", response_model=MeResponse)
def me(user=Depends(get_current_user)):
    return MeResponse(username=user.username, role=user.role)
