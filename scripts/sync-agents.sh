#!/usr/bin/env bash
# sync-agents.sh
# .claude/agents/ 본문을 .opencode/agents/에 동기화한다.
# 프론트매터는 각 플랫폼의 것을 유지하고, 본문(---)만 교체한다.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$REPO_ROOT/.claude/agents"
OPENCODE_DIR="$REPO_ROOT/.opencode/agents"

# 양쪽에 모두 존재하는 공유 에이전트
SHARED=(
  requirement-writer
  planner
  sprint-builder
  evaluator
  reviewer
  integration-fixer
  retrospective
  policy-updater
)

extract_body() {
  # 두 번째 '---' 이후의 내용을 출력한다.
  awk '/^---$/{n++; if(n==2){found=1; next}} found{print}' "$1"
}

extract_frontmatter() {
  # 첫 번째 '---'부터 두 번째 '---'까지 출력한다.
  awk '/^---$/{n++; print; if(n==2) exit; next} n>=1{print}' "$1"
}

synced=0
skipped=0

for agent in "${SHARED[@]}"; do
  src="$CLAUDE_DIR/$agent.md"
  dst="$OPENCODE_DIR/$agent.md"

  if [[ ! -f "$src" ]]; then
    echo "skip: $agent (source not found)"
    ((skipped++)) || true
    continue
  fi
  if [[ ! -f "$dst" ]]; then
    echo "skip: $agent (destination not found)"
    ((skipped++)) || true
    continue
  fi

  body=$(extract_body "$src")
  frontmatter=$(extract_frontmatter "$dst")

  new_content="${frontmatter}
${body}"

  current_content=$(cat "$dst")

  if [[ "$new_content" == "$current_content" ]]; then
    continue
  fi

  printf '%s\n' "$new_content" > "$dst"
  echo "synced: $agent"
  ((synced++)) || true
done

if [[ $synced -gt 0 ]]; then
  echo "--- $synced agent(s) synced to .opencode/agents/"
else
  echo "--- already in sync"
fi
