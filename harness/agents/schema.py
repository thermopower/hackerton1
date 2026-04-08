"""Agent spec schema — Pydantic models for *.agent.yaml files."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OrchestrationStep(BaseModel):
    """A step in the orchestration flow for orchestrator agents."""

    agents: list[str]
    parallel: bool = False


class AdapterOverride(BaseModel):
    """Per-adapter settings that override the base spec."""

    model: str | None = None
    memory: str | None = None
    tools: list[str] | None = None
    max_tokens: int | None = None
    permission_mode: str | None = None
    isolation: str | None = None


class AgentSpec(BaseModel):
    """Universal agent specification, decoupled from Claude Code frontmatter."""

    # Metadata
    name: str
    description: str = ""

    # Execution
    role: str = "worker"  # orchestrator | worker | reviewer | evaluator
    max_iterations: int = 40

    # I/O contract
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)

    # Tools (abstract names: file:read, file:write, shell:exec, etc.)
    required_tools: list[str] = Field(default_factory=list)

    # Sub-agents (for orchestrator role)
    orchestration_steps: list[OrchestrationStep] = Field(default_factory=list)

    # Prompt
    prompt_ref: str = ""  # path relative to prompts/base/

    # Adapter-specific overrides
    adapter_overrides: dict[str, AdapterOverride] = Field(default_factory=dict)

    def get_claude_code_override(self) -> AdapterOverride:
        return self.adapter_overrides.get("claude-code", AdapterOverride())
