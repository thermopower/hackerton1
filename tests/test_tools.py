"""Tests for tool abstraction layer."""

import tempfile
from pathlib import Path

import pytest

from harness.tools.file_ops import (
    CodeSearchTool,
    FileReadTool,
    FileSearchTool,
    FileWriteTool,
)
from harness.tools.shell import ShellTool
from harness.tools.registry import create_tool_registry


@pytest.fixture
def work_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestFileReadTool:
    @pytest.mark.asyncio
    async def test_reads_existing_file(self, work_dir: Path):
        (work_dir / "test.txt").write_text("hello")
        tool = FileReadTool()
        result = await tool.execute(path=str(work_dir / "test.txt"))
        assert result.success
        assert result.output == "hello"

    @pytest.mark.asyncio
    async def test_fails_on_missing_file(self):
        tool = FileReadTool()
        result = await tool.execute(path="/nonexistent/path.txt")
        assert not result.success

    @pytest.mark.asyncio
    async def test_fails_without_path(self):
        tool = FileReadTool()
        result = await tool.execute()
        assert not result.success


class TestFileWriteTool:
    @pytest.mark.asyncio
    async def test_writes_file(self, work_dir: Path):
        tool = FileWriteTool()
        result = await tool.execute(
            path=str(work_dir / "output.txt"), content="world"
        )
        assert result.success
        assert (work_dir / "output.txt").read_text() == "world"

    @pytest.mark.asyncio
    async def test_creates_parent_dirs(self, work_dir: Path):
        tool = FileWriteTool()
        result = await tool.execute(
            path=str(work_dir / "a" / "b" / "c.txt"), content="deep"
        )
        assert result.success
        assert (work_dir / "a" / "b" / "c.txt").read_text() == "deep"


class TestFileSearchTool:
    @pytest.mark.asyncio
    async def test_finds_files(self, work_dir: Path):
        (work_dir / "a.py").write_text("pass")
        (work_dir / "b.txt").write_text("text")
        tool = FileSearchTool()
        result = await tool.execute(pattern="*.py", directory=str(work_dir))
        assert result.success
        assert "a.py" in result.output
        assert "b.txt" not in result.output


class TestCodeSearchTool:
    @pytest.mark.asyncio
    async def test_finds_pattern(self, work_dir: Path):
        (work_dir / "test.py").write_text("def hello():\n    return 42\n")
        tool = CodeSearchTool()
        result = await tool.execute(
            pattern="return 42", directory=str(work_dir)
        )
        assert result.success
        assert "return 42" in result.output


class TestShellTool:
    @pytest.mark.asyncio
    async def test_runs_command(self, work_dir: Path):
        tool = ShellTool(cwd=str(work_dir))
        result = await tool.execute(command="echo hello")
        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_returns_failure_on_bad_command(self, work_dir: Path):
        tool = ShellTool(cwd=str(work_dir))
        result = await tool.execute(command="false")
        assert not result.success


class TestToolRegistry:
    def test_creates_all_tools(self):
        registry = create_tool_registry()
        assert "file:read" in registry
        assert "file:write" in registry
        assert "file:search" in registry
        assert "code:search" in registry
        assert "shell:exec" in registry

    def test_tools_have_api_schemas(self):
        registry = create_tool_registry()
        for tool in registry.values():
            schema = tool.to_api_schema()
            assert "name" in schema
            assert "input_schema" in schema
