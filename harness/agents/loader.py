"""Loads agent specs from harness/agents/*.agent.yaml files."""

from __future__ import annotations

from pathlib import Path

import yaml

from harness.agents.schema import AgentSpec, AdapterOverride


def load_agent_spec(
    agent_name: str, agents_dir: str | Path | None = None
) -> AgentSpec | None:
    """Load a single agent spec by name.

    Returns None if the spec file doesn't exist.
    """
    if agents_dir is None:
        agents_dir = Path(__file__).parent
    else:
        agents_dir = Path(agents_dir)

    spec_path = agents_dir / f"{agent_name}.agent.yaml"
    if not spec_path.is_file():
        return None

    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None

    metadata = raw.get("metadata", {})
    spec = raw.get("spec", {})

    adapter_overrides = {}
    for adapter_name, override_raw in spec.get("adapterOverrides", {}).items():
        adapter_overrides[adapter_name] = AdapterOverride(
            model=override_raw.get("model"),
            memory=override_raw.get("memory"),
            tools=override_raw.get("tools"),
            max_tokens=override_raw.get("max_tokens"),
            permission_mode=override_raw.get("permission_mode"),
            isolation=override_raw.get("isolation"),
        )

    return AgentSpec(
        name=metadata.get("name", agent_name),
        description=metadata.get("description", ""),
        role=spec.get("role", "worker"),
        max_iterations=spec.get("maxIterations", 40),
        inputs=spec.get("inputs", []),
        outputs=spec.get("outputs", []),
        required_tools=spec.get("requiredTools", []),
        prompt_ref=spec.get("promptRef", ""),
        adapter_overrides=adapter_overrides,
    )


def list_agent_specs(agents_dir: str | Path | None = None) -> list[str]:
    """Return names of all available agent specs."""
    if agents_dir is None:
        agents_dir = Path(__file__).parent
    else:
        agents_dir = Path(agents_dir)

    return sorted(
        p.stem.replace(".agent", "")
        for p in agents_dir.glob("*.agent.yaml")
    )
