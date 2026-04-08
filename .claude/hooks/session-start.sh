#!/usr/bin/env bash
# SessionStart hook
# 세션 시작 시 상태 파일을 스캔하고 다음 단계를 Claude에게 주입합니다.

PROGRESS=".claude-state/claude-progress.txt"
CONTRACT=".claude-state/sprint-contract.md"
EVAL_REPORT=".claude-state/evaluation-report.md"
REVIEW_NOTES=".claude-state/review-notes.md"

CONTEXT=""

# 1. progress 요약
if [ -f "$PROGRESS" ]; then
  RECENT=$(tail -20 "$PROGRESS")
  CONTEXT="${CONTEXT}\n## 최근 진행 상황\n${RECENT}\n"
else
  CONTEXT="${CONTEXT}\n## 상태\n초기 상태입니다. docs/requirement.md에 요구사항을 작성하고 planner를 실행하세요.\n"
fi

# 2. sprint-contract 상태 판별
NEXT_STEP=""

# requirement.md 내용 확인 (없거나 비어있으면 requirement-writer 실행)
REQ_FILE="docs/requirement.md"
REQ_EMPTY=false
if [ ! -f "$REQ_FILE" ] || [ ! -s "$REQ_FILE" ]; then
  REQ_EMPTY=true
else
  # 주석(#)과 공백만 있는 경우도 비어있다고 판단
  CONTENT=$(grep -v '^\s*$' "$REQ_FILE" 2>/dev/null | grep -v '^\s*#' || true)
  [ -z "$CONTENT" ] && REQ_EMPTY=true
fi

if $REQ_EMPTY; then
  NEXT_STEP="docs/requirement.md가 비어있습니다. requirement-writer를 실행해 사용자와 대화로 요구사항을 수집하세요."
elif [ ! -f "$CONTRACT" ]; then
  NEXT_STEP="planner를 실행하세요."
else
  STATUS=$(grep '^status:' "$CONTRACT" 2>/dev/null | awk '{print $2}')
  case "$STATUS" in
    none)
      NEXT_STEP="planner를 실행하세요."
      ;;
    draft)
      SPRINT_NUM=$(grep '^sprint_number:' "$CONTRACT" 2>/dev/null | awk '{print $2}')
      if [ -z "$SPRINT_NUM" ] || [ "$SPRINT_NUM" = "1" ]; then
        NEXT_STEP="sprint-contract.md가 draft 상태입니다 (sprint 1). 사용자에게 내용을 제시하고 승인을 요청하세요."
      else
        NEXT_STEP="sprint-contract.md가 draft 상태입니다 (sprint ${SPRINT_NUM}). 두 번째 이후 sprint이므로 사용자 승인 없이 status를 approved로 갱신하고 sprint-builder를 실행하세요."
      fi
      ;;
    approved)
      NEXT_STEP="sprint-contract가 승인되었습니다. sprint-builder를 실행하세요."
      ;;
    implemented)
      # evaluation-report 확인
      EVAL_STATUS=$(grep '^status:' "$EVAL_REPORT" 2>/dev/null | awk '{print $2}')
      if [ -z "$EVAL_STATUS" ] || [ "$EVAL_STATUS" = "none" ]; then
        NEXT_STEP="sprint-builder가 완료되었습니다. evaluator를 실행하세요."
      elif [ "$EVAL_STATUS" = "fail" ]; then
        NEXT_STEP="evaluation이 fail입니다. blocker를 확인하고 integration-fixer 또는 수정 sprint를 진행하세요."
      elif [ "$EVAL_STATUS" = "pass" ]; then
        # review-notes 확인: status: reviewed 이면 완료로 판단
        REVIEW_STATUS=$(grep '^status:' "$REVIEW_NOTES" 2>/dev/null | awk '{print $2}')
        if [ -z "$REVIEW_STATUS" ] || [ "$REVIEW_STATUS" = "none" ]; then
          NEXT_STEP="evaluation이 pass입니다. reviewer를 실행하세요."
        else
          # retrospective 완료 여부 확인 (learnings.md status)
          LEARNINGS=".claude-state/learnings.md"
          LEARN_STATUS=$(grep '^status:' "$LEARNINGS" 2>/dev/null | awk '{print $2}')
          if [ -z "$LEARN_STATUS" ] || [ "$LEARN_STATUS" = "none" ]; then
            NEXT_STEP="review가 완료되었습니다. retrospective 에이전트를 실행하세요."
          else
            # remaining_sprints 및 improve_needed 확인
            REMAINING=$(grep '^remaining_sprints:' ".claude-state/claude-progress.txt" 2>/dev/null | awk '{print $2}')
            IMPROVE_NEEDED=$(grep '^improve_needed:' "$LEARNINGS" 2>/dev/null | awk '{print $2}')
            if [ "$REMAINING" = "true" ]; then
              NEXT_STEP="retrospective가 완료되었습니다. 미완료 sprint가 남아있습니다. 다음 sprint planner를 자동으로 실행하세요."
            elif [ "$IMPROVE_NEEDED" = "true" ]; then
              NEXT_STEP="모든 sprint가 완료되었습니다. 개선 임계점에 도달했습니다. 사용자에게 완성품을 제시하고 /improve 실행을 권장하세요."
            else
              NEXT_STEP="모든 sprint가 완료되었습니다. 사용자에게 완성품을 제시하고 종료하세요."
            fi
          fi
        fi
      fi
      ;;
    *)
      NEXT_STEP="sprint-contract status를 확인하세요: $STATUS"
      ;;
  esac
fi

# 3. learnings 최근 내용 주입
if [ -f ".claude-state/learnings.md" ]; then
  LEARN_STATUS=$(grep '^status:' ".claude-state/learnings.md" 2>/dev/null | awk '{print $2}')
  if [ "$LEARN_STATUS" = "active" ] || [ "$LEARN_STATUS" = "reviewed" ]; then
    RECENT_LEARNINGS=$(tail -20 ".claude-state/learnings.md")
    CONTEXT="${CONTEXT}\n## 최근 학습 내용\n${RECENT_LEARNINGS}\n"
  fi
fi

# 4. 지표 요약 주입
if [ -f "scripts/check-thresholds.sh" ]; then
  THRESHOLD_SUMMARY=$(bash scripts/check-thresholds.sh --summary 2>/dev/null || echo "지표 확인 불가")
  CONTEXT="${CONTEXT}\n## 지표 요약\n${THRESHOLD_SUMMARY}\n"
fi

CONTEXT="${CONTEXT}\n## 다음 단계\n${NEXT_STEP}\n"

# JSON output for additionalContext
_try_python() { "$1" -c "import sys; sys.exit(0)" 2>/dev/null && echo "$1"; }
PYTHON="${PYTHON_CMD:-$(_try_python python || _try_python python3 || echo 'python')}"
"$PYTHON" -c "
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
context = sys.argv[1]
# 리터럴 \n 을 실제 줄바꿈으로 통일
context = context.replace('\\\\n', '\n')
output = {
  'hookSpecificOutput': {
    'hookEventName': 'SessionStart',
    'additionalContext': context
  }
}
print(json.dumps(output))
" "$CONTEXT" 2>/dev/null || echo "{}"

exit 0
