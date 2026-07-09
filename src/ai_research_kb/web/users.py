"""users.yaml: flat-file user store for the web panel (credentials, not committed).

`users.example.yaml` at the repo root is the tracked template; the real
`users.yaml` is gitignored, same pattern as `.env` vs `.env.example`.
"""

from __future__ import annotations

from pathlib import Path

import bcrypt
import yaml
from pydantic import BaseModel

from ..repo import find_repo_root
from .roles import Role


class UserRecord(BaseModel):
    username: str
    role: Role
    password_hash: str


def users_path(root: Path | None = None) -> Path:
    return (root or find_repo_root()) / "users.yaml"


def load_users(root: Path | None = None) -> list[UserRecord]:
    path = users_path(root)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [UserRecord.model_validate(u) for u in data.get("users", [])]


def save_users(users: list[UserRecord], root: Path | None = None) -> None:
    path = users_path(root)
    data = {"users": [u.model_dump(mode="json") for u in users]}
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def get_user(username: str, root: Path | None = None) -> UserRecord | None:
    for u in load_users(root):
        if u.username == username:
            return u
    return None


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def upsert_user(username: str, password: str, role: Role, root: Path | None = None) -> UserRecord:
    """Create or update a user (idempotent by username)."""
    users = load_users(root)
    record = UserRecord(username=username, role=role, password_hash=hash_password(password))
    for i, u in enumerate(users):
        if u.username == username:
            users[i] = record
            break
    else:
        users.append(record)
    save_users(users, root)
    return record
