#!/usr/bin/env python3
"""Convert .claude/agents/*.md to harness/agents/*.agent.yaml + prompts/base/*.md

One-time migration script.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENTS_SRC = ROOT / ".claude" / "agents"
AGENTS_DST = ROOT / "harness" / "agents"
PROMPTS_DST = ROOT / "harness" / "prompts" / "base"

# Tool name mapping: Claude Code tool → abstract tool
TOOL_MAP = {
    "Read": "file:read",
    "Write": "file:write",
    "Edit": "file:edit",
    "Glob": "file:search",
    "Grep": "code:search",
    "Bash": "shell:exec",
    "Agent": "agent:invoke",
    "WebSearch": "web:search",
}

# Playwright MCP tools → single abstract tool
PLAYWRIGHT_PREFIX = "mcp__plugin_playwright_playwright__browser_"

# Role classification
ORCHESTRATORS = {"planner", "sprint-builder"}
REVIEWERS = {"code-reviewer", "reviewer"}
EVALUATORS = {"evaluator"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


def classify_role(name: str) -> str:
    if name in ORCHESTRATORS:
        return "orchestrator"
    if name in REVIEWERS:
        return "reviewer"
    if name in EVALUATORS:
        return "evaluator"
    return "worker"


def map_tools(tools_str: str) -> tuple[list[str], list[str]]:
    """Map Claude Code tools to abstract tools. Return (abstract, original)."""
    abstract = []
    original = [t.strip() for t in tools_str.split(",")]
    has_playwright = False
    for t in original:
        t = t.strip()
        if t.startswith(PLAYWRIGHT_PREFIX):
            if not has_playwright:
                abstract.append("browser:navigate")
                has_playwright = True
        elif t in TOOL_MAP:
            abstract.append(TOOL_MAP[t])
        else:
            abstract.append(t)
    return abstract, original


def build_adapter_override(fm: dict, original_tools: list[str]) -> dict:
    """Build claude-code adapter override from frontmatter."""
    override = {}
    override["model"] = fm.get("model", "sonnet")
    if fm.get("memory"):
        override["memory"] = fm["memory"]
    override["tools"] = original_tools
    if fm.get("permissionMode"):
        override["permission_mode"] = fm["permissionMode"]
    if fm.get("isolation"):
        override["isolation"] = fm["isolation"]
    return override


def convert_one(src_path: Path):
    text = src_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        print(f"SKIP {src_path.name}: no frontmatter")
        return

    name = fm.get("name", src_path.stem)
    tools_str = fm.get("tools", "")
    abstract_tools, original_tools = map_tools(tools_str)

    spec = {
        "apiVersion": "harness/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "description": fm.get("description", ""),
        },
        "spec": {
            "role": classify_role(name),
            "maxIterations": fm.get("maxTurns", 40),
            "requiredTools": abstract_tools,
            "promptRef": f"prompts/base/{name}.md",
            "adapterOverrides": {
                "claude-code": build_adapter_override(fm, original_tools),
            },
        },
    }

    # Write YAML spec
    dst_yaml = AGENTS_DST / f"{name}.agent.yaml"
    with open(dst_yaml, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"  YAML: {dst_yaml.relative_to(ROOT)}")

    # Write prompt body
    dst_prompt = PROMPTS_DST / f"{name}.md"
    dst_prompt.write_text(body, encoding="utf-8")
    print(f"  Prompt: {dst_prompt.relative_to(ROOT)}")


def main():
    AGENTS_DST.mkdir(parents=True, exist_ok=True)
    PROMPTS_DST.mkdir(parents=True, exist_ok=True)

    md_files = sorted(AGENTS_SRC.glob("*.md"))
    print(f"Converting {len(md_files)} agents...")
    for f in md_files:
        print(f"\n{f.stem}:")
        convert_one(f)
    print(f"\nDone. {len(md_files)} agents converted.")


if __name__ == "__main__":
    main()
