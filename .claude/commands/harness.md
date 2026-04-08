# /harness

하네스 루프 모드로 전환합니다.

기본 모드는 일반 편집 모드입니다. 이 커맨드를 실행하면 하네스 루프(requirement-writer → planner → sprint-builder → evaluator → reviewer → retrospective)가 활성화됩니다.

## 사용법

- `/harness` — 상태 파일을 읽고 현재 위치에서 루프를 재개한다.
- `/harness start` — 요구사항 수집부터 새로 시작한다 (requirement-writer 실행).

## 실행 후 동작 규칙

이 커맨드가 실행되면 현재 세션에서 다음 규칙을 따른다:

1. **상태 파일 읽기**: `.claude-state/claude-progress.txt`와 `.claude-state/sprint-contract.md`를 읽어 현재 위치를 파악한다.
2. **단계 전환 규칙 적용**: CLAUDE.md 섹션 2의 단계 전환 규칙에 따라 다음 단계를 자동 실행한다.
3. **`/harness start`인 경우**: 상태와 무관하게 requirement-writer를 실행해 요구사항을 새로 수집한다.

## 종료

세션을 재시작하면 일반 편집 모드로 돌아온다.
