# Harness Version

version: 1.0
updated: 2026-04-05

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.1 | 2026-04-08 | 멀티모델 하네스 지원: Python 오케스트레이터(`harness/` 패키지) + 어댑터 패턴(claude-code / opencode / anthropic-api) 추가. OpenCode 실행 환경(opencode.json, .opencode/agents/ 17개, .opencode/rules/, .opencode/plugins/harness-hooks.js) 추가. harness.config.yaml, pyproject.toml, 범용 에이전트 스펙(harness/agents/*.agent.yaml), 프롬프트 관리(harness/prompts/), 도구 추상화(harness/tools/) 포함. `python -m harness run/start/status/agent` CLI 진입점 제공 |
| 1.0 | 2026-04-07 | planner step 10: 첫 sprint 승인 시 전체 스프린트 로드맵 요약 테이블을 먼저 출력하도록 변경. 사용자가 모든 요구사항이 여러 sprint에 걸쳐 구현됨을 한눈에 파악할 수 있게 함 |
| 1.0 | 2026-04-05 | 기술 스택 화이트리스트 도입: docs/stack-whitelist.md 신규 생성(15개 카테고리, 검증된 라이브러리 목록). requirement-writer 섹션 3에 화이트리스트 안내 원칙 추가. planner 9단계에 whitelist 참조 및 non_whitelist_libs 필드 기록 규칙 추가. harness-reference.md에 스택 화이트리스트 섹션 추가 |
| 1.0 | 2026-04-05 | 설계 결함 13건 수정: [#1] 병렬 implementer feature 단위 커밋 규칙 추가, [#2] code_review_attempt 필드로 루프 카운터 추적, [#3] common-module-writer 성공/실패 반환 규약·sprint-builder 실패 감지 분기·implementer 블로커 절차 추가, [#4] session-start.sh remaining_sprints를 feature-list.json 기반으로 수정, [#5] check-output.sh fallback 단순화(오차단 방지), [#6] reviewer에 retrospective 직접 호출 금지 명시, [#7] check-smoke.sh stub 검사 테스트 파일·주석 제외 필터 추가, [#8] integration-fixer fix_attempt 증가 규칙·sprint-contract.md 기록 통일, [#9] planner feature-list.json 초안 선행 생성 순서 명시·usecase-writer 임의 ID 부여 금지, [#10] retrospective improve_needed:true 시 policy-updater 자동 실행, [#11] planner 스크립트 복사 정책을 초기 생성 시만으로 제한, [#12] planner 사전 준비 섹션에 .claude-state/ 초기화 명시, [#13] usecase-writer database.md 미참조 시 경고 표시 추가 |
| 1.0 | 2026-04-05 | 기능중심 설계 전환 후 정합성 수정: prd-writer 페이지→기능 중심 언어 통일, usecase-writer 산출물 경로 `{N}` → `{feature_id}` 통일, plan-writer usecase 탐색 경로 동기화, dataflow-writer 입력 문서에 requirement+prd 추가, sub-agents 전체 tools 선언 추가(plan-writer/implementer/common-module-writer/prd-writer/userflow-writer/dataflow-writer/usecase-writer), evaluator tools에 Edit 추가, session-start.sh remaining_sprints 분기 추가, reviewer 이중 트리거 제거, planner에 scripts/ 루트 복사 규칙 명시 |
| 1.0 | 2026-04-05 | state-writer 제거. plan-writer를 페이지 단위 → feature 단위로 재설계. 상태 설계(source of truth, 전역/로컬 구분, cross-feature 공유 상태 레이어) plan.md 안에 통합. 산출물 경로 `docs/pages/{page}/` → `docs/features/{feature_id}/` |
| 1.0 | 2026-04-05 | planner: AC를 정상/경계/에러 케이스로 분리 작성 강제. 요구사항에 없는 케이스도 planner가 직접 채우도록 명시 |
| 1.0 | 2026-04-05 | common-module-writer: docs/usecases/ 전체 읽고 반복 패턴 미리 추출하는 단계 추가. plan-writer: 필요한 공통 모듈 누락 시 중단 후 보완 요청 경로 추가 |
| 1.0 | 2026-04-05 | planner: 범주형·파생 필드 AC 명시 규칙 추가 (저장→변환→레이어). reviewer: 1-A 요구사항↔구현 직접 비교 단계 추가 (AC 완결성 검증) |
| 1.0 | 2026-04-04 | smoke에 lint 추가, evaluation-gate에 npm audit(high 이상) 추가, planner smoke 템플릿 업데이트 |
| 1.0 | 2026-04-01 | Playwright MCP 브라우저 검증 통합, session-start.sh \n 정규화 버그 수정, 설계문서 실구현 동기화 완료 |
| 1.0 | 2026-04-01 | profiles/nextjs-supabase 예시 제거 (planner가 sprint마다 생성), collect-metrics.sh BLOCKER_COUNT 버그 수정 |

## 구성 요소

| 파일/폴더 | 역할 |
|-----------|------|
| `CLAUDE.md` | 하네스 운영 규칙 |
| `.ruler/AGENTS.md` | 코딩 원칙 |
| `.claude/agents/` | AI 에이전트 정의 (16개) |
| `.claude/hooks/` | SessionStart·SubagentStop 훅 스크립트 |
| `.claude/commands/` | 커스텀 커맨드 (/harness, /improve, /edit-harness, /exit-edit-harness) |
| `.claude/settings.json` | 훅 연결 설정 |
| `.claude-state/` | sprint 상태, 진행상황, 학습 누적 |
| `scripts/` | smoke·unit·e2e·evaluation-gate·collect-metrics·check-thresholds |
| `profiles/<stack>/scripts/` | 스택별 smoke·unit·e2e 스크립트 |
| `docs/stack-whitelist.md` | 기술 스택 화이트리스트 (15개 카테고리, requirement-writer·planner 참조) |
| `docs/` | 설계 문서 (planner가 생성, harness-reference.md 포함) |
| `harness/` | Python 오케스트레이터 패키지 (멀티모델 지원) |
| `harness/adapters/` | claude-code / opencode / anthropic-api 어댑터 |
| `harness/agents/` | 범용 AgentSpec YAML (17개) |
| `harness/prompts/` | 에이전트별 프롬프트 (base / partials / overrides) |
| `harness/tools/` | 도구 추상화 (file_ops / shell / browser) |
| `harness.config.yaml` | 어댑터 선택·이벤트 핸들러·스크립트 경로 설정 |
| `opencode.json` | OpenCode 프로젝트 설정 |
| `.opencode/agents/` | OpenCode frontmatter 형식 에이전트 (17개) |
| `.opencode/rules/AGENTS.md` | OpenCode용 코딩 원칙 |
| `.opencode/plugins/harness-hooks.js` | OpenCode session.idle → bash 훅 브릿지 |
| `scripts/convert_agents_opencode.py` | .claude/agents/ → .opencode/agents/ 변환 |
