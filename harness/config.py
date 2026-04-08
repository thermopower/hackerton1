"""Loads and validates harness.config.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class EventConfig:
    event: str
    handler: str
    matcher: str | None = None
    timeout: int = 30


@dataclass
class ScriptsConfig:
    smoke: str = "scripts/smoke"
    unit: str = "scripts/unit"
    e2e: str = "scripts/e2e"
    evaluation_gate: str = "scripts/evaluation-gate"


@dataclass
class HarnessConfig:
    default_adapter: str = "claude-code"
    agent_adapters: dict[str, str] = field(default_factory=dict)
    events: list[EventConfig] = field(default_factory=list)
    state_dir: str = ".claude-state"
    scripts: ScriptsConfig = field(default_factory=ScriptsConfig)

    def get_adapter_for_agent(self, agent_name: str) -> str:
        """Return the adapter name for a given agent, falling back to default."""
        return self.agent_adapters.get(agent_name, self.default_adapter)


def load_config(config_path: str | Path | None = None) -> HarnessConfig:
    """Load harness config from YAML file.

    Falls back to defaults if file doesn't exist.
    """
    if config_path is None:
        config_path = Path("harness.config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.is_file():
        return HarnessConfig()

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HarnessConfig()

    events = []
    for ev in raw.get("events", []):
        events.append(
            EventConfig(
                event=ev["event"],
                handler=ev["handler"],
                matcher=ev.get("matcher"),
                timeout=ev.get("timeout", 30),
            )
        )

    scripts_raw = raw.get("scripts", {})
    scripts = ScriptsConfig(
        smoke=scripts_raw.get("smoke", "scripts/smoke"),
        unit=scripts_raw.get("unit", "scripts/unit"),
        e2e=scripts_raw.get("e2e", "scripts/e2e"),
        evaluation_gate=scripts_raw.get("evaluationGate", "scripts/evaluation-gate"),
    )

    return HarnessConfig(
        default_adapter=raw.get("defaultAdapter", "claude-code"),
        agent_adapters=raw.get("agentAdapters", {}),
        events=events,
        state_dir=raw.get("stateDir", ".claude-state"),
        scripts=scripts,
    )
