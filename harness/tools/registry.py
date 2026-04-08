"""Tool registry — maps abstract tool names to implementations."""

from __future__ import annotations

from harness.tools.base import Tool
from harness.tools.file_ops import (
    CodeSearchTool,
    FileReadTool,
    FileSearchTool,
    FileWriteTool,
)
from harness.tools.shell import ShellTool


def create_tool_registry(cwd: str = ".") -> dict[str, Tool]:
    """Create a registry of all available tools."""
    tools: list[Tool] = [
        FileReadTool(),
        FileWriteTool(),
        FileSearchTool(),
        CodeSearchTool(),
        ShellTool(cwd=cwd),
    ]

    # Browser tool is optional
    try:
        from harness.tools.browser import BrowserNavigateTool

        tools.append(BrowserNavigateTool())
    except Exception:
        pass

    return {t.name: t for t in tools}
