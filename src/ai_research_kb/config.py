"""Loads config.yaml (falling back to config.example.yaml, then built-in defaults).

Nothing in here is org-specific: canonical terms, expected sections, blocklist and
time-sensitive patterns all live in the YAML file so the tool stays generic OSS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .repo import find_repo_root

DEFAULT_CONFIG: dict[str, Any] = {
    "canonical_terms": [],
    "expected_sections": {
        "analysis": [],
        "design": [],
        "change-plan": [],
        "notes": [],
        "other": [],
    },
    "time_sensitive_patterns": [
        r"\bbeta\b",
        r"\bGA\b",
        r"\bTBD\b",
        r"\bTODO\b",
    ],
    "blocklist": [],
    "llm": {"provider": None, "model": None},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(root: Path | None = None) -> dict[str, Any]:
    root = root or find_repo_root()
    for name in ("config.yaml", "config.example.yaml"):
        cfg_path = root / name
        if cfg_path.exists():
            user_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            return _deep_merge(DEFAULT_CONFIG, user_cfg)
    return dict(DEFAULT_CONFIG)
