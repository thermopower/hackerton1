"""Abstract tool interface for the harness tool abstraction layer.

Each tool provides a uniform interface that adapters can use when the
underlying AI tool doesn't have native support for the capability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Base class for all harness tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name matching the abstract tool registry (e.g. 'file:read')."""
        ...

    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        ...

    def to_api_schema(self) -> dict[str, Any]:
        """Return an Anthropic-compatible tool schema for API adapters."""
        return {
            "name": self.name.replace(":", "_"),
            "description": f"Tool: {self.name}",
            "input_schema": {"type": "object", "properties": {}},
        }
