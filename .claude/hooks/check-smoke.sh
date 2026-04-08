#!/usr/bin/env bash
# SubagentStop hook (sprint-builder 전용)
# sprint-builder 종료 전 smoke test + stub 잔존 여부를 확인합니다.
# 실패 시 exit 2로 종료를 차단합니다.

BLOCKERS=()

# 1. smoke test 실행
echo "[check-smoke] smoke test 실행 중..."
if bash scripts/smoke 2>&1; then
  echo "[check-smoke] smoke PASS"
else
  BLOCKERS+=("smoke test 실패")
fi

# 2. stub/placeholder 잔존 검사
SEARCH_DIRS=""
[ -d "app" ] && SEARCH_DIRS="app"
[ -d "src" ] && SEARCH_DIRS="$SEARCH_DIRS src"

if [ -n "$SEARCH_DIRS" ]; then
  echo "[check-smoke] stub/placeholder 검사 중 (테스트 파일·주석 제외)..."
  # 테스트 파일(__tests__, *.test.*, *.spec.*, test_*.py)과 주석 전용 행 제외
  # 실제 구현 코드 경로에만 존재하는 stub/placeholder만 감지
  STUB_HITS=$(grep -rn \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    --include="*.py" --include="*.go" \
    --exclude-dir="__tests__" --exclude-dir="node_modules" --exclude-dir=".next" \
    --exclude-dir=".git" --exclude-dir="dist" --exclude-dir="build" \
    --exclude="*.test.ts" --exclude="*.test.tsx" --exclude="*.test.js" \
    --exclude="*.spec.ts" --exclude="*.spec.tsx" --exclude="*.spec.js" \
    --exclude="test_*.py" --exclude="*_test.go" \
    "TODO\|FIXME\|stub\|placeholder\|not implemented\|NotImplemented" \
    $SEARCH_DIRS 2>/dev/null \
    | grep -v "^[^:]*:[0-9]*:[[:space:]]*//" \
    | grep -v "^[^:]*:[0-9]*:[[:space:]]*#" \
    | grep -v "^[^:]*:[0-9]*:[[:space:]]*\*" \
    || true)
  if [ -n "$STUB_HITS" ]; then
    echo "[check-smoke] 핵심 경로에 stub/placeholder가 발견되었습니다:"
    echo "$STUB_HITS"
    BLOCKERS+=("stub/placeholder 잔존")
  else
    echo "[check-smoke] stub 검사 PASS"
  fi
fi

# 3. blocker 있으면 차단
if [ ${#BLOCKERS[@]} -gt 0 ]; then
  echo "" >&2
  echo "=== sprint-builder 종료 차단 ===" >&2
  for b in "${BLOCKERS[@]}"; do
    echo "  - $b" >&2
  done
  echo "위 항목을 해결한 후 다시 완료 처리하세요." >&2
  exit 2
fi

echo "[check-smoke] 모든 검사 통과. sprint-builder 종료 허용."
exit 0
