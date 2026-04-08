#!/usr/bin/env bash
# SubagentStop hook (evaluator / reviewer / retrospective 전용)
# 산출물 파일이 갱신되었는지 확인합니다.
# 미갱신 시 exit 2로 완료를 차단합니다.

_try_python() { "$1" -c "import sys; sys.exit(0)" 2>/dev/null && echo "$1"; }
PYTHON="${PYTHON_CMD:-$(_try_python python || _try_python python3 || echo 'python')}"

INPUT=$(cat)

# SubagentStop JSON에서 에이전트 이름 추출
# Claude Code는 subagent_name, name, agent_name 등 여러 필드를 사용할 수 있으므로
# 알려진 모든 필드를 순서대로 시도하고, 모두 없으면 matcher를 통해 판별
AGENT_NAME=$(echo "$INPUT" | "$PYTHON" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # 알려진 필드명 우선순위 순으로 시도
    for key in ('subagent_name', 'agent_name', 'name', 'agent_type', 'description'):
        val = d.get(key, '')
        if val:
            print(val)
            sys.exit(0)
    print('')
except Exception:
    print('')
" 2>/dev/null || echo "")

EVAL_REPORT=".claude-state/evaluation-report.md"
REVIEW_NOTES=".claude-state/review-notes.md"
LEARNINGS=".claude-state/learnings.md"
METRICS=".claude-state/metrics.json"

check_file_updated() {
  local FILE="$1"
  local LABEL="$2"

  if [ ! -f "$FILE" ]; then
    echo "[$LABEL] $FILE 파일이 존재하지 않습니다." >&2
    exit 2
  fi

  # status: none 또는 빈 파일이면 미갱신으로 판단
  STATUS=$(grep '^status:' "$FILE" 2>/dev/null | awk '{print $2}')
  if [ -z "$STATUS" ] || [ "$STATUS" = "none" ]; then
    echo "[$LABEL] $FILE 가 갱신되지 않았습니다. (status: none)" >&2
    echo "[$LABEL] 판정 결과를 파일에 기록한 후 완료하세요." >&2
    exit 2
  fi

  echo "[$LABEL] $FILE 갱신 확인 (status: $STATUS)"
}

check_json_updated() {
  local FILE="$1"
  local LABEL="$2"

  if [ ! -f "$FILE" ]; then
    echo "[$LABEL] $FILE 파일이 존재하지 않습니다." >&2
    exit 2
  fi

  TOTAL=$("$PYTHON" -c "import json; d=json.load(open('${FILE}')); print(d.get('summary',{}).get('total_sprints',0))" 2>/dev/null || echo "0")
  if [ "$TOTAL" = "0" ]; then
    echo "[$LABEL] metrics.json에 기록된 sprint가 없습니다." >&2
    exit 2
  fi

  echo "[$LABEL] metrics.json 갱신 확인 (total_sprints: $TOTAL)"
}

# 에이전트 이름 기반으로 분기 (부분 일치)
case "$AGENT_NAME" in
  *evaluator*)
    check_file_updated "$EVAL_REPORT" "evaluator"
    ;;
  *reviewer*)
    check_file_updated "$REVIEW_NOTES" "reviewer"
    ;;
  *retrospective*)
    check_file_updated "$LEARNINGS" "retrospective"
    check_json_updated "$METRICS" "retrospective"
    ;;
  *)
    # 에이전트 이름 판별 불가 — 최근 5분 내 갱신된 산출물 파일을 기준으로 검사
    # 방금 실행된 에이전트가 담당 파일을 갱신했는지 mtime으로 판단한다.
    # 이 방식은 휴리스틱 상태 추론 없이도 "방금 쓰였는가"를 직접 확인한다.
    RECENT_SECS=300  # 5분
    NOW=$(date +%s)
    BLOCKED=0

    check_recent() {
      local FILE="$1"
      local LABEL="$2"
      if [ ! -f "$FILE" ]; then return; fi
      FILE_MTIME=$(date -r "$FILE" +%s 2>/dev/null || stat -c %Y "$FILE" 2>/dev/null || stat -f%m "$FILE" 2>/dev/null || echo "9999999999")
      AGE=$((NOW - FILE_MTIME))
      if [ "$AGE" -le "$RECENT_SECS" ]; then
        # 최근 수정된 파일이 있음 — status 확인
        STATUS=$(grep '^status:' "$FILE" 2>/dev/null | awk '{print $2}')
        if [ -z "$STATUS" ] || [ "$STATUS" = "none" ]; then
          echo "[$LABEL] $FILE 최근 수정됐으나 status가 갱신되지 않았습니다." >&2
          BLOCKED=1
        fi
      fi
    }

    check_recent "$EVAL_REPORT" "evaluator"
    check_recent "$REVIEW_NOTES" "reviewer"
    check_recent "$LEARNINGS" "retrospective"

    if [ "$BLOCKED" = "1" ]; then
      exit 2
    fi

    echo "[check-output] 에이전트 이름 판별 불가 (raw: '${AGENT_NAME}'). mtime 검사 완료."
    ;;
esac

exit 0
