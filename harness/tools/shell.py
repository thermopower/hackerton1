"""Shell execution tool — runs bash commands as subprocesses."""

from __future__ import annotations

import asyncio
from typing import Any

from harness.tools.base import Tool, ToolResult


class ShellTool(Tool):
    """Executes a bash command and returns stdout/stderr."""

    def __init__(self, cwd: str = ".", timeout: int = 120) -> None:
        self._cwd = cwd
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "shell:exec"

    async def execute(self, **params: Any) -> ToolResult:
        command = params.get("command", "")
        if not command:
            return ToolResult(success=False, error="command is required")

        timeout = params.get("timeout", self._timeout)

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout}s: {command[:100]}",
            )

        exit_code = proc.returncode or 0
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        return ToolResult(
            success=exit_code == 0,
            output=stdout_str,
            error=stderr_str if exit_code != 0 else None,
            data={"exit_code": exit_code},
        )

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "shell_exec",
            "description": "Execute a bash command and return the output.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Bash command to execute.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds.",
                        "default": 120,
                    },
                },
                "required": ["command"],
            },
        }
