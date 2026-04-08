"""Event bus that replaces Claude Code's Hook system.

Supports both Python callables and bash script handlers (for reusing
existing .claude/hooks/*.sh scripts).
"""

from __future__ import annotations

import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class EventHandler:
    event: str
    handler: str | Callable[..., Awaitable[None]]
    matcher: str | None = None
    timeout: int = 30


class EventBus:
    """Simple event bus with regex-based agent name matching."""

    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def register(
        self,
        event: str,
        handler: str | Callable[..., Awaitable[None]],
        matcher: str | None = None,
        timeout: int = 30,
    ) -> None:
        self._handlers.append(
            EventHandler(event=event, handler=handler, matcher=matcher, timeout=timeout)
        )

    async def emit(
        self,
        event: str,
        agent_name: str = "",
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Emit an event and run all matching handlers.

        Returns a list of handler results. Bash scripts return their
        exit code; async callables return whatever they return.
        """
        results: list[dict[str, Any]] = []

        for h in self._handlers:
            if h.event != event:
                continue
            if h.matcher and not re.search(h.matcher, agent_name):
                continue

            try:
                if isinstance(h.handler, str):
                    result = await self._run_script(h.handler, h.timeout, context)
                else:
                    result = await asyncio.wait_for(
                        h.handler(agent_name, context), timeout=h.timeout
                    )
                results.append({"handler": str(h.handler), "result": result, "ok": True})
            except subprocess.CalledProcessError as e:
                results.append({
                    "handler": str(h.handler),
                    "exit_code": e.returncode,
                    "ok": False,
                })
                if e.returncode == 2:
                    logger.warning(
                        "Handler %s blocked agent %s (exit 2)",
                        h.handler,
                        agent_name,
                    )
            except asyncio.TimeoutError:
                logger.warning(
                    "Handler %s timed out after %ds", h.handler, h.timeout
                )
                results.append({"handler": str(h.handler), "ok": False, "timeout": True})

        return results

    async def _run_script(
        self, script_path: str, timeout: int, context: dict[str, Any] | None
    ) -> int:
        proc = await asyncio.create_subprocess_exec(
            "bash",
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode or 1,
                f"bash {script_path}",
                output=stdout,
                stderr=stderr,
            )
        return proc.returncode or 0
