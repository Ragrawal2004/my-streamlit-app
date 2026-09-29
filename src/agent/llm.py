"""Provider-agnostic LLM client (plain HTTP, no vendor SDK lock-in).

Env vars:
  LLM_PROVIDER = anthropic | openai | none   (openai also covers any OpenAI-compatible
                                              endpoint: Groq, OpenRouter, Ollama, ... via LLM_BASE_URL)
  LLM_MODEL, LLM_API_KEY, LLM_BASE_URL (optional)
If unset or 'none', the agent uses its deterministic template explanation.
"""
from __future__ import annotations

import os
from typing import Callable, Optional

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def get_llm() -> Optional[Callable[[str, str], str]]:
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
    key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if provider in ("", "none") or not key or not model:
        return None
    timeout = float(os.getenv("LLM_TIMEOUT", "60"))

    if provider == "anthropic":
        base = os.getenv("LLM_BASE_URL", "https://api.anthropic.com")

        def call(system: str, user: str) -> str:
            r = httpx.post(f"{base}/v1/messages", timeout=timeout,
                           headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                    "content-type": "application/json"},
                           json={"model": model, "max_tokens": 900, "temperature": 0,
                                 "system": system, "messages": [{"role": "user", "content": user}]})
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
        return call

    if provider == "openai":
        base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

        def call(system: str, user: str) -> str:
            r = httpx.post(f"{base}/chat/completions", timeout=timeout,
                           headers={"Authorization": f"Bearer {key}"},
                           json={"model": model, "temperature": 0,
                                 "messages": [{"role": "system", "content": system},
                                              {"role": "user", "content": user}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        return call

    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'")
