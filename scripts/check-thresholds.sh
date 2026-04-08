#!/usr/bin/env bash
# metrics.json을 읽어 임계점 도달 여부를 판단합니다.
# --summary 옵션: 한 줄 요약 출력
# exit 0: 정상, exit 1: 임계점 도달

METRICS=".claude-state/metrics.json"
SUMMARY_MODE=false
[ "$1" = "--summary" ] && SUMMARY_MODE=true

if [ ! -f "$METRICS" ]; then
  $SUMMARY_MODE && echo "지표 없음 (metrics.json 미존재)"
  exit 0
fi

_try_python() { "$1" -c "import sys; sys.exit(0)" 2>/dev/null && echo "$1"; }
PYTHON="${PYTHON_CMD:-$(_try_python python || _try_python python3 || echo 'python')}"
"$PYTHON" - "$METRICS" "$@" <<'PYEOF'
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

metrics_path = sys.argv[1]
args = sys.argv[2:]
with open(metrics_path, "r") as f:
    data = json.load(f)

summary = data.get("summary", {})
sprints = data.get("sprints", [])
summary_mode = "--summary" in args

triggered = []

# 임계점 1: 3회 연속 fail
if len(sprints) >= 3:
    last3 = [s["eval_result"] for s in sprints[-3:]]
    if all(r == "fail" for r in last3):
        triggered.append("3회 연속 eval fail")

# 임계점 2: 전체 pass율 < 50% (최소 4회 이상)
total = summary.get("total_sprints", 0)
pass_rate = summary.get("pass_rate")
if total >= 4 and pass_rate is not None and pass_rate < 0.5:
    triggered.append(f"전체 pass율 {int(pass_rate*100)}% (< 50%)")

# 임계점 3: 동일 blocker 유형 3회 이상
repeated = {k: v for k, v in summary.get("repeated_blocker_types", {}).items() if v >= 3}
for bt, cnt in repeated.items():
    triggered.append(f"blocker '{bt}' {cnt}회 반복")

# 임계점 4: 평균 턴 수 60 초과 3회 연속
if len(sprints) >= 3:
    last3_turns = [s["total_turns"] for s in sprints[-3:]]
    if all(t > 60 for t in last3_turns):
        triggered.append("3회 연속 턴 수 초과 (60턴 기준)")

if summary_mode:
    if triggered:
        print("[WARNING] 임계점 도달: " + " / ".join(triggered))
    else:
        pr = f"{int(pass_rate*100)}%" if pass_rate is not None else "N/A"
        print(f"정상 (총 {total}회, pass율 {pr})")
    sys.exit(0)

if triggered:
    for t in triggered:
        print(f"[threshold] {t}", flush=True)
    sys.exit(1)
else:
    sys.exit(0)
PYEOF
