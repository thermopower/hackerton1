#!/usr/bin/env bash
# SubagentStop hook — integration-fixer 완료 시 fix_attempt를 증가시킵니다.
# 훅은 메인 worktree에서 실행되므로 isolation: worktree인 integration-fixer 대신
# 이 훅이 카운터를 관리합니다.

CONTRACT=".claude-state/sprint-contract.md"

if [ ! -f "$CONTRACT" ]; then
  exit 0
fi

# 현재 fix_attempt 값 읽기
CURRENT=$(grep '^fix_attempt:' "$CONTRACT" 2>/dev/null | awk '{print $2}')
if [ -z "$CURRENT" ] || ! echo "$CURRENT" | grep -qE '^[0-9]+$'; then
  CURRENT=0
fi

NEXT=$((CURRENT + 1))

# sprint-contract.md에 fix_attempt 갱신
if grep -q '^fix_attempt:' "$CONTRACT"; then
  # 기존 필드 업데이트 (sed는 이식성 문제 있으므로 Python 사용)
  _PY=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python")
  "$_PY" -c "
import re, sys
next_val = int('$NEXT')
content = open('$CONTRACT').read()
content = re.sub(r'^fix_attempt:.*$', f'fix_attempt: {next_val}', content, flags=re.MULTILINE)
open('$CONTRACT', 'w').write(content)
" 2>/dev/null
else
  # 필드 없으면 파일 끝에 추가
  echo "fix_attempt: $NEXT" >> "$CONTRACT"
fi

echo "[track-fix-attempt] fix_attempt: $CURRENT → $NEXT"

# 메인 세션에 현재 카운트 알림
_try_python() { "$1" -c "import sys; sys.exit(0)" 2>/dev/null && echo "$1"; }
PYTHON="${PYTHON_CMD:-$(_try_python python || _try_python python3 || echo 'python')}"
"$PYTHON" -c "
import json
output = {
  'hookSpecificOutput': {
    'hookEventName': 'SubagentStop',
    'additionalContext': 'integration-fixer 완료. fix_attempt: $NEXT (2 이상이면 다음 실행 시 BLOCKER 처리)'
  }
}
print(json.dumps(output))
"

exit 0
