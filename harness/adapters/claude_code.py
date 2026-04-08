"""Claude Code adapter — wraps the `claude` CLI as a subprocess.

Preserves 100% compatibility with existing .claude/agents/*.md,
.claude/settings.json, and MCP integrations.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil

from harness.adapters.base import (
    AdapterCapabilities,
    AgentContext,
    AgentResult,
    ModelAdapter,
)

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(ModelAdapter):
    """Runs agents via the `claude` CLI subprocess."""

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_sub_agents=True,
            supports_parallel=True,
            supports_mcp=True,
            supports_memory=True,
            supports_isolation=True,
            max_context_window=1_000_000,
            supported_tools=[
                "file:read",
                "file:write",
                "file:edit",
                "file:search",
                "code:search",
                "shell:exec",
                "agent:invoke",
                "browser:navigate",
                "web:search",
            ],
        )

    async def check_available(self) -> bool:
        return shutil.which("claude") is not None

    async def run_agent(
        self, agent_name: str, context: AgentContext
    ) -> AgentResult:
        claude_bin = shutil.which("claude")
        if claude_bin is None:
            return AgentResult(
                success=False,
                error="'claude' CLI not found in PATH",
            )

        cmd = [
            claude_bin,
            "--print",
            "--output-format",
            "json",
            "--agent",
            agent_name,
            "--message",
            context.message or f"Run {agent_name} agent.",
        ]

        logger.info("Running: %s", " ".join(cmd[:6]) + " ...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=context.project_dir,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        exit_code = proc.returncode or 0
        success = exit_code == 0

        if not success:
            logger.warning(
                "claude --agent %s exited with code %d: %s",
                agent_name,
                exit_code,
                stderr[:500],
            )

        return AgentResult(
            success=success,
            output=stdout,
            exit_code=exit_code,
            error=stderr if not success else None,
        )
