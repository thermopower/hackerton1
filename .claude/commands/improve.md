# /improve

누적된 learnings 기반으로 policy-updater를 실행해 에이전트·정책 개정안을 생성합니다.

## 실행 조건

`.claude-state/learnings.md`의 status가 `active`인 경우에만 실행합니다.
learnings가 없으면 "개선할 learnings가 없습니다." 메시지를 출력하고 종료합니다.

## 실행 절차

1. `.claude-state/learnings.md`를 읽어 status가 `active`인지 확인한다.
2. status가 `none`이거나 파일이 비어 있으면 중단하고 사용자에게 안내한다.
3. `policy-updater` 에이전트를 실행한다.
4. policy-updater가 생성한 개정안을 사용자에게 제시한다.
5. 사용자 승인 후 policy-updater가 파일을 적용한다.

## 주의사항

- 개정안은 사용자 승인 전까지 파일에 적용되지 않는다.
- policy-updater는 learnings 없이 추측으로 개정안을 생성하지 않는다.
- CLAUDE.md 수정은 diff 제안만 하며, 사용자가 직접 판단해 적용한다.
