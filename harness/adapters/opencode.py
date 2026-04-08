"""OpenCode adapter — wraps the `opencode` CLI (opencode.ai).

OpenCode is a Go-based terminal AI coding agent that supports 75+ LLM
providers. It has its own agent system (.opencode/agents/), MCP support,
and non-interactive mode.

CLI flags (global):
  -p, --prompt    Run single prompt non-interactively
  -f, --output-format  Output format (text, json)
  -q, --quiet     Hide spinner in non-interactive mode
  -c, --cwd       Set working directory

Two execution modes:
1. CLI mode: `opencode -p "prompt" -f json -q` (non-interactive)
2. Headless mode: `opencode serve` → `opencode attach --port <port>`
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from typing import Any

from harness.adapters.base import (
    AdapterCapabilities,
    AgentContext,
    AgentResult,
    ModelAdapter,
)
from harness.agents.loader import load_agent_spec
from harness.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Default headless server port
DEFAULT_SERVE_URL = "http://localhost:4096"


class OpenCodeAdapter(ModelAdapter):
    """Adapter for OpenCode (opencode.ai).

    OpenCode is a terminal AI coding agent similar to Claude Code.
    Key differences:
    - Supports 75+ LLM providers (GPT, Gemini, local models)
    - Has its own .opencode/agents/ system (markdown-based)
    - Supports MCP servers
    - Non-interactive mode: `opencode run -p "prompt" -f json`

    Best for all agent types since OpenCode has full file editing,
    shell access, and agent capabilities — unlike OpenCodeInterpreter
    which is limited to code generation.
    """

    def __init__(
        self,
        prompts_dir: str = "harness/prompts",
        serve_url: str | None = None,
    ) -> None:
        self._prompts_dir = prompts_dir
        self._serve_url = serve_url or os.environ.get(
            "OPENCODE_SERVE_URL", DEFAULT_SERVE_URL
        )

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_sub_agents=True,   # .opencode/agents/ 지원
            supports_parallel=False,    # 오케스트레이터에서 병렬 관리
            supports_mcp=True,          # MCP 서버 지원
            supports_memory=False,      # 세션 간 메모리 없음
            supports_isolation=False,   # worktree 격리 미지원
            max_context_window=200_000, # 프로바이더에 따라 다름
            supported_tools=[
                "file:read",
                "file:write",
                "file:edit",
                "file:search",
                "code:search",
                "shell:exec",
                "agent:invoke",
            ],
        )

    async def check_available(self) -> bool:
        """Check if `opencode` CLI is installed."""
        return shutil.which("opencode") is not None

    async def run_agent(
        self, agent_name: str, context: AgentContext
    ) -> AgentResult:
        opencode_bin = shutil.which("opencode")
        if opencode_bin is None:
            return AgentResult(
                success=False,
                error="'opencode' CLI not found in PATH. Install from https://opencode.ai/",
            )

        # Build the prompt
        prompt = self._build_prompt(agent_name, context)

        # Try headless (attach) mode first, fall back to direct run
        if await self._headless_available():
            return await self._run_attach(opencode_bin, prompt, context)
        return await self._run_direct(opencode_bin, prompt, context)

    def _build_prompt(self, agent_name: str, context: AgentContext) -> str:
        """Build full prompt from prompt_builder + context message."""
        spec = load_agent_spec(agent_name)
        prompt_builder = PromptBuilder(self._prompts_dir)
        system_prompt = prompt_builder.build(agent_name, adapter_name="opencode")

        if not system_prompt and spec:
            system_prompt = spec.description

        parts = []
        if system_prompt:
            parts.append(system_prompt)
        if context.message:
            parts.append(context.message)

        return "\n\n---\n\n".join(parts) if parts else f"Run {agent_name} agent."

    async def _headless_available(self) -> bool:
        """Check if an OpenCode headless server is running."""
        try:
            import urllib.request

            req = urllib.request.Request(
                f"{self._serve_url}/health", method="GET"
            )
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            return False

    async def _run_attach(
        self, opencode_bin: str, prompt: str, context: AgentContext
    ) -> AgentResult:
        """Run via headless server: `opencode attach` + prompt."""
        # Parse port from serve URL
        port = self._serve_url.rsplit(":", 1)[-1] if ":" in self._serve_url else "4096"
        cmd = [
            opencode_bin,
            "attach",
            "--port",
            port,
            "-p",
            prompt,
            "-f",
            "json",
            "-q",
        ]

        return await self._execute_cmd(cmd, context)

    async def _run_direct(
        self, opencode_bin: str, prompt: str, context: AgentContext
    ) -> AgentResult:
        """Run directly: `opencode -p "prompt" -f json -q`.

        -p is a global flag, not a subcommand flag.
        """
        cmd = [
            opencode_bin,
            "-p",
            prompt,
            "-f",
            "json",
            "-q",  # quiet mode (no spinner, for scripts)
            "-c",
            context.project_dir,  # set working directory
        ]

        return await self._execute_cmd(cmd, context)

    async def _execute_cmd(
        self, cmd: list[str], context: AgentContext
    ) -> AgentResult:
        """Execute an opencode CLI command and parse results."""
        logger.info("Running: %s", " ".join(cmd[:5]) + " ...")

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
                "opencode exited with code %d: %s", exit_code, stderr[:500]
            )

        # Try to parse JSON output (from -f json flag)
        output_text = stdout
        files_changed: list[str] = []

        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                output_text = parsed.get("output", parsed.get("text", stdout))
                files_changed = parsed.get("files_changed", [])
        except (json.JSONDecodeError, TypeError):
            pass

        return AgentResult(
            success=success,
            output=output_text,
            exit_code=exit_code,
            error=stderr if not success else None,
            files_changed=files_changed,
        )
