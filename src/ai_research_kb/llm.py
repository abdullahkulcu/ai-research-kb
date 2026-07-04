"""Optional LLM provider abstraction.

Every LLM-backed feature (contradiction candidates, acceptance criteria, diff
summaries) must degrade gracefully: if no provider is configured, or the optional
dependency isn't installed, or the call fails, callers get an empty/None result and
the rest of the pipeline keeps working.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

from .config import load_config


class LLMProvider(Protocol):
    def find_contradictions(self, cluster: str, doc_paths: list[Path]) -> list[dict[str, Any]]: ...

    def generate_acceptance_criteria(self, excerpt: str) -> list[str]: ...

    def summarize_diff(self, before: str, after: str) -> str: ...


class AnthropicProvider:
    def __init__(self, model: str | None = None):
        import anthropic  # optional dependency, imported lazily

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY tanımlı değil")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model or "claude-sonnet-4-5"

    def _complete(self, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in resp.content if hasattr(block, "text"))

    def find_contradictions(self, cluster: str, doc_paths: list[Path]) -> list[dict[str, Any]]:
        texts = [f"### {p.name}\n{p.read_text(encoding='utf-8')}" for p in doc_paths]
        prompt = (
            "Aşağıdaki dokümanlar aynı research cluster'ına ait. Aralarında birbiriyle "
            "çelişen somut iddialar var mı? Sadece emin olduğun adayları "
            "'<dosya adı>: <iddia>' formatında, madde madde ve kısa listele. Emin "
            "değilsen o adayı yazma.\n\n" + "\n\n".join(texts)
        )
        try:
            raw = self._complete(prompt)
        except Exception:
            return []
        candidates = []
        for line in raw.splitlines():
            line = line.strip("-* \t")
            if line:
                candidates.append({"doc": cluster, "message": line})
        return candidates

    def generate_acceptance_criteria(self, excerpt: str) -> list[str]:
        prompt = (
            "Aşağıdaki research metnine dayanarak, kısa ve test edilebilir acceptance "
            "criteria maddeleri üret (madde madde, kısa):\n\n" + excerpt
        )
        try:
            raw = self._complete(prompt)
        except Exception:
            return []
        return [line.strip("-* \t") for line in raw.splitlines() if line.strip()]

    def summarize_diff(self, before: str, after: str) -> str:
        prompt = (
            "Aşağıdaki iki versiyon arasında bölüm bazlı ne değişti, kısaca özetle:\n\n"
            f"--- ESKİ ---\n{before}\n\n--- YENİ ---\n{after}"
        )
        try:
            return self._complete(prompt)
        except Exception:
            return ""


def get_llm_provider(root: Path | None = None) -> LLMProvider | None:
    cfg = load_config(root)
    provider_name = (cfg.get("llm") or {}).get("provider")
    if not provider_name:
        return None
    model = (cfg.get("llm") or {}).get("model")
    try:
        if provider_name == "anthropic":
            return AnthropicProvider(model=model)
    except Exception:
        return None
    return None
