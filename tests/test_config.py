"""Tests for config — harness.config.yaml loader."""

import tempfile
from pathlib import Path

import pytest

from harness.config import HarnessConfig, load_config


@pytest.fixture
def config_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, config_dir: Path):
        config = load_config(config_dir / "nonexistent.yaml")
        assert config.default_adapter == "claude-code"
        assert config.agent_adapters == {}
        assert config.state_dir == ".claude-state"

    def test_parses_full_config(self, config_dir: Path):
        cfg_path = config_dir / "harness.config.yaml"
        cfg_path.write_text(
            """
apiVersion: harness/v1
defaultAdapter: anthropic-api
agentAdapters:
  implementer: opencode
  evaluator: claude-code
events:
  - event: "agent:after-stop"
    matcher: "sprint-builder"
    handler: ".claude/hooks/check-smoke.sh"
    timeout: 120
stateDir: .state
scripts:
  smoke: scripts/smoke
  evaluationGate: scripts/eval
"""
        )
        config = load_config(cfg_path)
        assert config.default_adapter == "anthropic-api"
        assert config.agent_adapters["implementer"] == "opencode"
        assert config.agent_adapters["evaluator"] == "claude-code"
        assert len(config.events) == 1
        assert config.events[0].matcher == "sprint-builder"
        assert config.events[0].timeout == 120
        assert config.state_dir == ".state"
        assert config.scripts.evaluation_gate == "scripts/eval"

    def test_get_adapter_for_agent_with_override(self):
        config = HarnessConfig(
            default_adapter="claude-code",
            agent_adapters={"implementer": "opencode"},
        )
        assert config.get_adapter_for_agent("implementer") == "opencode"
        assert config.get_adapter_for_agent("planner") == "claude-code"
