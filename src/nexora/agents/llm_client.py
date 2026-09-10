"""LLM access layer.

Reasoning agents (classifier, planner, evidence reviewer, root cause
analyzer) go through this client rather than calling a model SDK
directly. This keeps the orchestration and prompt-construction logic
independent of which provider is configured.

Two providers are supported:

- "heuristic": no external calls are made. Agents fall back to explicit,
  auditable rule-based reasoning implemented in each agent module. This
  is the default so that the project runs out of the box without an API
  key, and so that its behavior is fully reproducible.
- "gemini": routes through Google's Gemini models. This requires
    GOOGLE_API_KEY to be set and the `adk` optional dependency to be
    installed. The optional Gemini reasoning stage receives serialized
    deterministic evidence and returns a validated structured conclusion.

Nexora never claims a Gemini-backed response when the heuristic provider
is active. Every LLM-derived summary is only produced when `is_available()`
returns True.
"""

from __future__ import annotations

import logging

from nexora.config.settings import get_settings

logger = logging.getLogger("nexora.agents.llm_client")


class LLMUnavailableError(Exception):
    """Raised when a caller requests a live LLM call but none is configured."""


class LLMClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def provider(self) -> str:
        return self._settings.llm_provider

    def is_available(self) -> bool:
        return self.provider == "gemini" and bool(self._settings.google_api_key)
