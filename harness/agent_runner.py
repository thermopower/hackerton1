"""Agent execution engine — resolves adapters and orchestrates agent runs."""

from __future__ import annotations

import logging
from typing import Any

from harness.adapters.base import AgentContext, AgentResult, ModelAdapter
from harness.config import HarnessConfig
from harness.event_bus import EventBus

logger = logging.getLogger(__name__)

# Lazy import to avoid circular deps
_ADAPTER_REGISTRY: dict[str, type[ModelAdapter]] = {}


def _load_adapter_class(adapter_name: str) -> type[ModelAdapter]:
    """Lazily import and return the adapter class by name."""
    if adapter_name in _ADAPTER_REGISTRY:
        return _ADAPTER_REGISTRY[adapter_name]

    if adapter_name == "claude-code":
        from harness.adapters.claude_code import ClaudeCodeAdapter

        _ADAPTER_REGISTRY[adapter_name] = ClaudeCodeAdapter
        return ClaudeCodeAdapter
    elif adapter_name == "opencode":
        from harness.adapters.opencode import OpenCodeAdapter

        _ADAPTER_REGISTRY[adapter_name] = OpenCodeAdapter
        return OpenCodeAdapter
    elif adapter_name == "anthropic-api":
        from harness.adapters.anthropic_api import AnthropicApiAdapter

        _ADAPTER_REGISTRY[adapter_name] = AnthropicApiAdapter
        return AnthropicApiAdapter

    raise ValueError(f"Unknown adapter: {adapter_name}")


class AgentRunner:
    """Resolves the correct adapter per agent and executes it."""

    def __init__(
        self,
        config: HarnessConfig,
        event_bus: EventBus,
        project_dir: str = ".",
    ) -> None:
        self.config = config
        self.event_bus = event_bus
        self.project_dir = project_dir
        self._adapter_instances: dict[str, ModelAdapter] = {}

    def _get_adapter(self, agent_name: str) -> ModelAdapter:
        adapter_name = self.config.get_adapter_for_agent(agent_name)
        if adapter_name not in self._adapter_instances:
            cls = _load_adapter_class(adapter_name)
            self._adapter_instances[adapter_name] = cls()
        return self._adapter_instances[adapter_name]

    async def run(
        self,
        agent_name: str,
        message: str = "",
        extra: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Run an agent through the appropriate adapter."""
        adapter = self._get_adapter(agent_name)
        adapter_name = self.config.get_adapter_for_agent(agent_name)

        logger.info(
            "Running agent '%s' via adapter '%s'", agent_name, adapter_name
        )

        await self.event_bus.emit("agent:before-start", agent_name)

        context = AgentContext(
            agent_name=agent_name,
            message=message or f"Run {agent_name} agent.",
            state_dir=self.config.state_dir,
            project_dir=self.project_dir,
            extra=extra or {},
        )

        result = await adapter.run_agent(agent_name, context)

        hook_results = await self.event_bus.emit(
            "agent:after-stop", agent_name, {"result": result}
        )

        # Check if any hook blocked the agent (exit code 2)
        for hr in hook_results:
            if not hr.get("ok") and hr.get("exit_code") == 2:
                logger.warning(
                    "Hook blocked agent '%s': %s", agent_name, hr.get("handler")
                )
                result.success = False
                result.error = (
                    f"Blocked by hook: {hr.get('handler')}"
                )

        return result
