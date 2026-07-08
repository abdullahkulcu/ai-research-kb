"""Role hierarchy: viewer < editor < admin."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    viewer = "viewer"
    editor = "editor"
    admin = "admin"


_RANK = {Role.viewer: 0, Role.editor: 1, Role.admin: 2}


def at_least(role: Role, minimum: Role) -> bool:
    return _RANK[role] >= _RANK[minimum]
