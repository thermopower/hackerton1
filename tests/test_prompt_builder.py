"""Tests for prompt_builder and agent loader."""

import tempfile
from pathlib import Path

import pytest

from harness.prompt_builder import PromptBuilder
from harness.agents.loader import load_agent_spec, list_agent_specs


@pytest.fixture
def prompts_dir():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "base").mkdir()
        (p / "partials").mkdir()
        (p / "overrides" / "opencode").mkdir(parents=True)
        yield p


class TestPromptBuilder:
    def test_loads_base_prompt(self, prompts_dir: Path):
        (prompts_dir / "base" / "planner.md").write_text("You are a planner.\n")
        builder = PromptBuilder(prompts_dir)
        result = builder.build("planner")
        assert "You are a planner." in result

    def test_resolves_include(self, prompts_dir: Path):
        (prompts_dir / "base" / "impl.md").write_text(
            "Implement.\n\n{{include:tdd-rules}}\n"
        )
        (prompts_dir / "partials" / "tdd-rules.md").write_text("RED GREEN REFACTOR\n")
        builder = PromptBuilder(prompts_dir)
        result = builder.build("impl")
        assert "RED GREEN REFACTOR" in result
        assert "{{include:" not in result

    def test_missing_partial_replaced_with_empty(self, prompts_dir: Path):
        (prompts_dir / "base" / "x.md").write_text("Hello {{include:missing}}\n")
        builder = PromptBuilder(prompts_dir)
        result = builder.build("x")
        assert result == "Hello \n"

    def test_appends_adapter_override(self, prompts_dir: Path):
        (prompts_dir / "base" / "impl.md").write_text("Base prompt.\n")
        (prompts_dir / "overrides" / "opencode" / "impl.suffix.md").write_text(
            "Use OCI tools.\n"
        )
        builder = PromptBuilder(prompts_dir)
        result = builder.build("impl", adapter_name="opencode")
        assert "Base prompt." in result
        assert "Use OCI tools." in result

    def test_no_override_when_adapter_missing(self, prompts_dir: Path):
        (prompts_dir / "base" / "impl.md").write_text("Base prompt.\n")
        builder = PromptBuilder(prompts_dir)
        result = builder.build("impl", adapter_name="nonexistent")
        assert result == "Base prompt.\n"

    def test_returns_empty_when_no_base(self, prompts_dir: Path):
        builder = PromptBuilder(prompts_dir)
        assert builder.build("nonexistent") == ""

    def test_list_agents(self, prompts_dir: Path):
        (prompts_dir / "base" / "a.md").write_text("a")
        (prompts_dir / "base" / "b.md").write_text("b")
        builder = PromptBuilder(prompts_dir)
        assert builder.list_agents() == ["a", "b"]


class TestAgentLoader:
    def test_loads_real_agent_specs(self):
        agents = list_agent_specs()
        assert "planner" in agents
        assert "evaluator" in agents
        assert len(agents) == 17

    def test_loads_planner_spec(self):
        spec = load_agent_spec("planner")
        assert spec is not None
        assert spec.name == "planner"
        assert spec.role == "orchestrator"
        assert spec.max_iterations == 40
        assert "file:read" in spec.required_tools
        cc = spec.get_claude_code_override()
        assert cc.model == "sonnet"
        assert cc.memory == "project"

    def test_loads_reviewer_with_opus(self):
        spec = load_agent_spec("reviewer")
        assert spec is not None
        cc = spec.get_claude_code_override()
        assert cc.model == "opus"

    def test_loads_sprint_builder_with_permission(self):
        spec = load_agent_spec("sprint-builder")
        assert spec is not None
        cc = spec.get_claude_code_override()
        assert cc.permission_mode == "acceptEdits"

    def test_returns_none_for_missing(self):
        assert load_agent_spec("nonexistent") is None
