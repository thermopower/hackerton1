"""File operation tools — read, write, edit, search (glob), code search (grep)."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from harness.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    @property
    def name(self) -> str:
        return "file:read"

    async def execute(self, **params: Any) -> ToolResult:
        path = params.get("path", "")
        if not path:
            return ToolResult(success=False, error="path is required")
        p = Path(path)
        if not p.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")
        try:
            content = p.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "file_read",
            "description": "Read the contents of a file at the given path.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path to read.",
                    }
                },
                "required": ["path"],
            },
        }


class FileWriteTool(Tool):
    @property
    def name(self) -> str:
        return "file:write"

    async def execute(self, **params: Any) -> ToolResult:
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return ToolResult(success=False, error="path is required")
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"Written {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "file_write",
            "description": "Write content to a file, creating directories as needed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write."},
                    "content": {"type": "string", "description": "Content to write."},
                },
                "required": ["path", "content"],
            },
        }


class FileSearchTool(Tool):
    """Glob-based file search."""

    @property
    def name(self) -> str:
        return "file:search"

    async def execute(self, **params: Any) -> ToolResult:
        pattern = params.get("pattern", "")
        directory = params.get("directory", ".")
        if not pattern:
            return ToolResult(success=False, error="pattern is required")
        try:
            matches = sorted(str(p) for p in Path(directory).rglob(pattern))
            return ToolResult(
                success=True,
                output="\n".join(matches[:200]),
                data={"count": len(matches), "files": matches[:200]},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "file_search",
            "description": "Search for files matching a glob pattern.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. '*.py')."},
                    "directory": {"type": "string", "description": "Directory to search in.", "default": "."},
                },
                "required": ["pattern"],
            },
        }


class CodeSearchTool(Tool):
    """Grep-like content search."""

    @property
    def name(self) -> str:
        return "code:search"

    async def execute(self, **params: Any) -> ToolResult:
        pattern = params.get("pattern", "")
        directory = params.get("directory", ".")
        glob_filter = params.get("glob", "*")
        if not pattern:
            return ToolResult(success=False, error="pattern is required")

        import re

        try:
            regex = re.compile(pattern)
        except re.error as e:
            return ToolResult(success=False, error=f"Invalid regex: {e}")

        matches = []
        for root, _, files in os.walk(directory):
            for f in files:
                if not fnmatch.fnmatch(f, glob_filter):
                    continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, encoding="utf-8", errors="ignore") as fh:
                        for i, line in enumerate(fh, 1):
                            if regex.search(line):
                                matches.append(f"{fpath}:{i}: {line.rstrip()}")
                                if len(matches) >= 200:
                                    break
                except (OSError, UnicodeDecodeError):
                    continue
            if len(matches) >= 200:
                break

        return ToolResult(
            success=True,
            output="\n".join(matches),
            data={"count": len(matches)},
        )

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "code_search",
            "description": "Search file contents using a regex pattern.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for."},
                    "directory": {"type": "string", "description": "Directory to search.", "default": "."},
                    "glob": {"type": "string", "description": "File glob filter.", "default": "*"},
                },
                "required": ["pattern"],
            },
        }
