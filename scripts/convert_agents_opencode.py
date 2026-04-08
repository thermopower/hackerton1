#!/usr/bin/env python3
"""Convert .claude/agents/*.md to .opencode/agents/*.md format.

OpenCode agent frontmatter fields:
  description, mode (primary|subagent), model, temperature,
  tools (read, glob, grep, bash, write, edit, task, webfetch),
  permissions (edit, bash, task)
"""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_AGENTS = ROOT / ".claude" / "agents"
OPENCODE_AGENTS = ROOT / ".opencode" / "agents"

# Claude Code tool → OpenCode tool mapping
TOOL_MAP = {
    "Read": "read",
    "Write": "write",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "Bash": "bash",
    "Agent": "task",
    "WebSearch": "webfetch",
}

# Agents that are called by other agents (sub-agents)
SUBAGENTS = {
    "prd-writer", "userflow-writer", "dataflow-writer",
    "usecase-writer", "stack-selector", "common-module-writer",
    "plan-writer", "implementer", "code-reviewer", "policy-updater",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


def map_tools(tools_str: str) -> dict[str, bool]:
    """Map Claude tools to OpenCode tool permissions."""
    result = {
        "read": False,
        "glob": False,
        "grep": False,
        "bash": False,
        "write": False,
        "edit": False,
        "task": False,
        "webfetch": False,
    }
    for t in tools_str.split(","):
        t = t.strip()
        if t.startswith("mcp__"):
            continue  # Skip MCP tools (handled separately)
        oc_tool = TOOL_MAP.get(t)
        if oc_tool:
            result[oc_tool] = True
    return result


def convert_one(src_path: Path):
    text = src_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        print(f"  SKIP {src_path.name}: no frontmatter")
        return

    name = fm.get("name", src_path.stem)
    tools = map_tools(fm.get("tools", ""))
    mode = "subagent" if name in SUBAGENTS else "primary"

    # Build OpenCode frontmatter
    oc_fm = {
        "description": fm.get("description", ""),
        "mode": mode,
        "temperature": 0.1,
    }

    # Tools — explicitly set all
    oc_fm["tools"] = tools

    # Permissions
    perms = {}
    if tools.get("edit"):
        perms["edit"] = "allow"
    if tools.get("bash"):
        perms["bash"] = "allow"
    if tools.get("task"):
        perms["task"] = "allow"
    if perms:
        oc_fm["permissions"] = perms

    # Write OpenCode agent file
    dst = OPENCODE_AGENTS / f"{name}.md"
    fm_str = yaml.dump(oc_fm, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # Remove Claude Code-specific references from body
    # Replace "Agent 도구" / "Agent tool" references with "task 도구"
    body = body.replace("Agent 도구", "task 도구")
    body = body.replace("Agent tool", "task tool")

    dst.write_text(f"---\n{fm_str}---\n\n{body}", encoding="utf-8")
    print(f"  {name}.md (mode={mode}, tools={sum(tools.values())})")


def main():
    OPENCODE_AGENTS.mkdir(parents=True, exist_ok=True)
    md_files = sorted(CLAUDE_AGENTS.glob("*.md"))
    print(f"Converting {len(md_files)} agents to OpenCode format...\n")
    for f in md_files:
        convert_one(f)
    print(f"\nDone. {len(md_files)} agents written to .opencode/agents/")


if __name__ == "__main__":
    main()
