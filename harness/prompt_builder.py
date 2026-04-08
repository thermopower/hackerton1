"""Prompt builder — assembles prompts from base + partials + overrides.

Template syntax: {{include:partial_name}} is replaced with the content
of prompts/partials/{partial_name}.md.
"""

from __future__ import annotations

import re
from pathlib import Path

_INCLUDE_PATTERN = re.compile(r"\{\{include:([a-zA-Z0-9_-]+)\}\}")


class PromptBuilder:
    """Builds agent prompts by combining base, partials, and overrides."""

    def __init__(self, prompts_dir: str | Path) -> None:
        self.prompts_dir = Path(prompts_dir)
        self.base_dir = self.prompts_dir / "base"
        self.partials_dir = self.prompts_dir / "partials"
        self.overrides_dir = self.prompts_dir / "overrides"
        self._partials_cache: dict[str, str] = {}

    def _load_partial(self, name: str) -> str:
        if name not in self._partials_cache:
            path = self.partials_dir / f"{name}.md"
            if path.is_file():
                self._partials_cache[name] = path.read_text(encoding="utf-8")
            else:
                self._partials_cache[name] = ""
        return self._partials_cache[name]

    def _resolve_includes(self, text: str) -> str:
        """Replace {{include:name}} with partial content."""

        def replacer(match: re.Match) -> str:
            return self._load_partial(match.group(1))

        return _INCLUDE_PATTERN.sub(replacer, text)

    def build(self, agent_name: str, adapter_name: str | None = None) -> str:
        """Build the full prompt for an agent.

        1. Load base prompt (prompts/base/{agent_name}.md)
        2. Resolve {{include:...}} directives
        3. Append adapter-specific override if it exists
        """
        base_path = self.base_dir / f"{agent_name}.md"
        if not base_path.is_file():
            return ""

        prompt = base_path.read_text(encoding="utf-8")
        prompt = self._resolve_includes(prompt)

        # Append adapter override if present
        if adapter_name:
            override_path = (
                self.overrides_dir / adapter_name / f"{agent_name}.suffix.md"
            )
            if override_path.is_file():
                suffix = override_path.read_text(encoding="utf-8")
                prompt = prompt.rstrip() + "\n\n" + suffix

        return prompt

    def list_agents(self) -> list[str]:
        """Return names of agents that have base prompts."""
        return sorted(
            p.stem for p in self.base_dir.glob("*.md") if p.is_file()
        )
