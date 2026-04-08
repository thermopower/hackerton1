"""Anthropic API adapter — runs agents via the Anthropic SDK's tool_use loop.

Suitable for non-coding agents (planner, reviewer, evaluator) that need
file read/write and shell access but not a full coding IDE.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from harness.adapters.base import (
    AdapterCapabilities,
    AgentContext,
    AgentResult,
    ModelAdapter,
)
from harness.agents.loader import load_agent_spec
from harness.prompt_builder import PromptBuilder
from harness.tools.base import Tool, ToolResult
from harness.tools.registry import create_tool_registry

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicApiAdapter(ModelAdapter):
    """Runs agents via Anthropic SDK messages.create() with tool_use."""

    def __init__(self, prompts_dir: str = "harness/prompts") -> None:
        self._prompts_dir = prompts_dir

    @property
    def name(self) -> str:
        return "anthropic-api"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_sub_agents=False,
            supports_parallel=True,
            supports_mcp=False,
            supports_memory=False,
            supports_isolation=False,
            max_context_window=200_000,
            supported_tools=[
                "file:read",
                "file:write",
                "file:search",
                "code:search",
                "shell:exec",
                "browser:navigate",
            ],
        )

    async def check_available(self) -> bool:
        try:
            import anthropic  # noqa: F401

            return bool(os.environ.get("ANTHROPIC_API_KEY"))
        except ImportError:
            return False

    async def run_agent(
        self, agent_name: str, context: AgentContext
    ) -> AgentResult:
        try:
            import anthropic
        except ImportError:
            return AgentResult(
                success=False,
                error="anthropic package not installed. Install with: pip install 'harness[anthropic]'",
            )

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return AgentResult(
                success=False,
                error="ANTHROPIC_API_KEY environment variable not set.",
            )

        # Load agent spec and build prompt
        spec = load_agent_spec(agent_name)
        prompt_builder = PromptBuilder(self._prompts_dir)
        system_prompt = prompt_builder.build(agent_name, adapter_name="anthropic-api")

        if not system_prompt and spec:
            system_prompt = spec.description

        # Determine model
        model = DEFAULT_MODEL
        if spec:
            override = spec.adapter_overrides.get("anthropic-api")
            if override and override.model:
                model = override.model

        # Build tool schemas
        tool_registry = create_tool_registry(cwd=context.project_dir)
        tool_schemas = [t.to_api_schema() for t in tool_registry.values()]

        max_iterations = spec.max_iterations if spec else 40

        # Create client and run tool_use loop
        client = anthropic.AsyncAnthropic(api_key=api_key)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": context.message},
        ]

        full_output: list[str] = []
        iterations = 0

        try:
            while iterations < max_iterations:
                iterations += 1

                response = await client.messages.create(
                    model=model,
                    max_tokens=8192,
                    system=system_prompt,
                    tools=tool_schemas,
                    messages=messages,
                )

                # Process response content
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})

                # Check if there are tool uses to process
                tool_uses = [
                    block
                    for block in assistant_content
                    if block.type == "tool_use"
                ]

                if not tool_uses:
                    # No more tool calls — extract final text
                    for block in assistant_content:
                        if hasattr(block, "text"):
                            full_output.append(block.text)
                    break

                # Execute tool calls
                tool_results = []
                for tool_use in tool_uses:
                    result = await self._execute_tool(
                        tool_use.name, tool_use.input, tool_registry
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result.output if result.success else (result.error or "Error"),
                        "is_error": not result.success,
                    })

                messages.append({"role": "user", "content": tool_results})

                # Also collect text output from this iteration
                for block in assistant_content:
                    if hasattr(block, "text"):
                        full_output.append(block.text)

            return AgentResult(
                success=True,
                output="\n".join(full_output),
                exit_code=0,
            )

        except Exception as e:
            logger.exception("Anthropic API error for agent '%s'", agent_name)
            return AgentResult(
                success=False,
                error=str(e),
            )

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        registry: dict[str, Tool],
    ) -> ToolResult:
        """Execute a tool call from the API response."""
        # Map API tool names back to registry names
        name_map = {
            "file_read": "file:read",
            "file_write": "file:write",
            "file_search": "file:search",
            "code_search": "code:search",
            "shell_exec": "shell:exec",
            "browser_navigate": "browser:navigate",
        }
        registry_name = name_map.get(tool_name, tool_name)

        tool = registry.get(registry_name)
        if tool is None:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        return await tool.execute(**tool_input)
