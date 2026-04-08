"""Abstract base class for model adapters.

Each adapter wraps a specific AI coding tool (Claude Code, OpenCodeInterpreter,
Anthropic API, etc.) and provides a uniform interface for the orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterCapabilities:
    supports_sub_agents: bool = False
    supports_parallel: bool = False
    supports_mcp: bool = False
    supports_memory: bool = False
    supports_isolation: bool = False
    max_context_window: int = 200_000
    supported_tools: list[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """Context passed to an adapter when running an agent."""

    agent_name: str
    message: str = ""
    state_dir: str = ".claude-state"
    project_dir: str = "."
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result returned by an adapter after running an agent."""

    success: bool
    output: str = ""
    exit_code: int = 0
    error: str | None = None
    files_changed: list[str] = field(default_factory=list)


class ModelAdapter(ABC):
    """Interface that every adapter must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter name (e.g. 'claude-code', 'opencode')."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        ...

    @abstractmethod
    async def run_agent(
        self, agent_name: str, context: AgentContext
    ) -> AgentResult:
        """Execute an agent with the given context."""
        ...

    async def check_available(self) -> bool:
        """Return True if the adapter's underlying tool is installed."""
        return True
