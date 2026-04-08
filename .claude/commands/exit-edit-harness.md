# /exit-edit-harness

> **참고**: `/harness` 명령이 같은 역할을 합니다. 이 커맨드 대신 `/harness`를 사용하세요.

하네스 루프 모드로 전환합니다. `/harness`와 동일하게 동작합니다.

## 실행 후 동작 규칙

1. **하네스 루프 재활성화**: CLAUDE.md 섹션 2의 단계 전환 규칙을 적용한다.
2. **상태 재확인**: `.claude-state/claude-progress.txt`와 `.claude-state/sprint-contract.md`를 읽고 현재 단계를 판단한다.
3. 판단 결과에 따라 다음 단계를 사용자에게 안내한다.
