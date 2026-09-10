"""Base agent interface.

Every agent receives and returns the shared InvestigationState. Agents
must not perform side effects outside of that state object (no direct
database writes, no direct API responses) so that the orchestrator
remains the single place that governs workflow progression.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from nexora.models.state import InvestigationState


class BaseAgent(ABC):
    name: str = "unnamed_agent"

    @abstractmethod
    def run(self, state: InvestigationState) -> InvestigationState:
        raise NotImplementedError
