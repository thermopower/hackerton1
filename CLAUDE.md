# 하네스 운영 규칙

이 저장소는 Claude Code 기반 앱 생성 하네스다.
기본 모드는 **일반 편집 모드**다. 하네스 루프(requirement-writer → planner → sprint-builder → ...)는 `/harness` 명령으로 명시적으로 시작한다.

---

## 0. Superpowers 스킬 — 모드별 사용 규칙

**일반 편집 모드에서는 Superpowers 스킬을 정상적으로 사용한다.**

**하네스 루프 모드(`/harness` 실행 후)에서는 Superpowers 스킬을 사용하지 않는다.**
하네스 에이전트가 각 스킬의 역할을 완전히 대체하기 때문이다:

| Superpowers 스킬 | 대체 에이전트 |
|---|---|
| `brainstorming` | `requirement-writer` |
| `writing-plans` | `planner`, `plan-writer` |
| `executing-plans` | `sprint-builder` |
| `systematic-debugging` | `integration-fixer` |
| `test-driven-development` | `implementer`, `common-module-writer` |

하네스 루프 모드에서는 Skill 도구를 호출하지 않는다.

---

## 1. 기본 모드: 일반 편집 모드

**세션 시작 시 기본값은 일반 편집 모드다.**

- 하네스 루프를 자동으로 시작하지 않는다.
- 단계 전환 규칙(섹션 2)을 적용하지 않는다.
- 사용자의 요청을 직접 수행한다.
- 세션 시작 시 `docs/harness-reference.md`를 먼저 읽어 현재 구조를 파악한다. 이후 작업은 이 문서를 기준점으로 삼는다.
- **하네스 구조에 영향을 주는 변경이 발생하면 `docs/harness-reference.md`와 `.claude-state/harness-version.md`를 자동으로 업데이트한다.**
  - 업데이트 대상: 에이전트 파일, 훅 스크립트, settings.json, 검증 스크립트, CLAUDE.md, .ruler/AGENTS.md, 커맨드 파일, 프로필 스크립트
  - 업데이트 안 하는 것: sprint 진행 중 생성되는 앱 코드, `.claude-state/` 상태 데이터

**하네스 루프 관련 명령어:**

| 명령어 | 동작 |
|---|---|
| `/harness` | 하네스 루프 모드로 전환. 상태 파일을 읽고 단계 전환 규칙을 적용한다. |
| `/harness start` | 요구사항 수집부터 새로 시작. 기존 상태 파일과 무관하게 requirement-writer를 실행한다. |
| `/edit-harness` | 하네스 루프 모드에서 일반 편집 모드로 복귀. |
| `/improve` | learnings 기반 policy-updater 실행 |

## 2. 하네스 모드: 단계 전환 규칙

`/harness` 명령 실행 후에만 아래 규칙을 적용한다.

세션 진입 시:
1. `.claude-state/claude-progress.txt`를 먼저 읽는다.
2. `.claude-state/sprint-contract.md`의 status를 확인한다.
3. 아래 규칙으로 현재 위치를 판단한다.

| 조건 | 다음 단계 |
|---|---|
| `docs/requirement.md` 내용 없음 | requirement-writer 실행 (사용자와 대화로 요구사항 수집) |
| `.claude-state/sprint-contract.md` status: none | planner 실행 |
| status: draft, **첫 번째 sprint** | 사용자에게 sprint-contract 내용 제시 후 승인 요청 |
| status: draft, **두 번째 이후 sprint** | 사용자 승인 없이 자동으로 status를 approved로 갱신 후 sprint-builder 실행 |
| status: approved | sprint-builder 실행 |
| status: implemented, `evaluation-report.md` status: none | evaluator 실행 |
| `evaluation-report.md` status: fail, 수정 시도 횟수 < 2 | integration-fixer 또는 수정 sprint 자동 실행 (사용자에게 묻지 않음) |
| `evaluation-report.md` status: fail, 수정 시도 횟수 ≥ 2 | **[BLOCKER]** 사용자에게 상황 보고 후 중단 |
| `evaluation-report.md` status: pass, `review-notes.md` 없음 | reviewer 실행 |
| `review-notes.md` status: reviewed, `learnings.md` status: none | retrospective 실행 |
| retrospective 완료, 미완료 sprint 남아있음 | 자동으로 다음 sprint planner 실행 |
| retrospective 완료, 모든 sprint 완료 (`feature-list.json` 전체 done), `improve_needed: true` | 사용자에게 완성품 제시 + `/improve` 실행 권장 |
| retrospective 완료, 모든 sprint 완료, `improve_needed: false` | 사용자에게 완성품 제시 후 종료 |
| `/improve` 명령 | policy-updater 실행 |

## 3. 사용자 승인이 필요한 시점

**기본 원칙: 요구사항을 한 번 승인하면 완성품이 나올 때까지 자동으로 진행한다.**

**반드시 멈추고 사용자 확인을 받는다 (3가지):**
- **첫 번째 sprint-contract**: planner 완료 후 범위를 제시하고 승인을 받는다. 이후 sprint는 자동 진행한다.
- **수정 sprint 2회 초과 블로커**: evaluation fail 후 수정 시도가 2회를 초과하면 사용자에게 보고하고 중단한다.
- **policy-updater 완료 후**: 에이전트/정책 개정안을 diff 형태로 제시하고 승인을 받는다. 승인 없이 파일을 수정하지 않는다.

**자동으로 진행하는 것 (사용자에게 묻지 않음):**
- 두 번째 이후 sprint-contract 승인
- evaluation fail 후 수정 sprint (2회 이내)
- sprint 완료 후 다음 sprint 전환
- reviewer → retrospective → 다음 sprint planner 전환

## 4. 역할 구분

- **requirement-writer**: 사용자와 대화해 요구사항 수집 → docs/requirement.md 작성. 설계·구현하지 않는다.
- **planner**: 요구사항 → 설계 문서 + sprint-contract 초안. 구현하지 않는다.
- **sprint-builder**: 승인된 sprint-contract 범위만 구현. 범위를 넘지 않는다.
- **evaluator**: pass/fail 판정만 한다. 개선 제안을 하지 않는다.
- **reviewer**: 품질 비평과 개선 제안만 한다. pass/fail 판정을 하지 않는다.
- **integration-fixer**: 환경/의존성 복구만 한다. 기능을 추가하지 않는다.
- **retrospective**: sprint 지표 수집 및 learnings 누적. 파일 수정은 learnings.md/metrics.json만 허용.
- **policy-updater**: learnings 기반 개정안 생성. 업데이트 우선, 신규 최소. 승인 후 적용.

evaluator와 reviewer는 다른 역할이다. 절대 혼용하지 않는다.

## 5. Context Window 절약 원칙

- 코드 탐색은 Explore subagent에 위임한다. main context에서 직접 파일을 통째로 읽지 않는다.
- 이전에 파악한 파일 구조와 의존 관계는 subagent memory에 기록해 재탐색을 방지한다.
- `feature-list.json`의 `verification linkage`로 탐색 범위를 파일 단위로 좁힌다.

## 6. 품질 기준

- stub, placeholder, TODO가 핵심 경로에 남아 있으면 완료가 아니다.
- smoke test를 통과하지 않으면 sprint-builder를 완료로 처리하지 않는다.
- QA 없이 done 선언하지 않는다.
- **테스트 통과는 완료의 필요조건이지 충분조건이 아니다.** 다음 중 하나라도 해당하면 완료가 아니다:
  - AC 문구에 명시된 조건이 코드에 구현되지 않은 경우 (AC 미구현)
  - 선언만 되고 값이 채워지지 않는 dead code (Set, Map, 배열 등)
  - 빈 catch 또는 에러를 삼키는 패턴 (catch 무시)
  - 오류 발생 시 성공 경로가 계속 실행되는 경우 (제어 흐름 오류)

## 7. 상태 파일 원칙

- 상태는 대화가 아니라 `.claude-state/` 파일에 남긴다.
- 세션이 끊겨도 상태 파일을 기반으로 재개한다.
- `claude-progress.txt`에는 항상 현재 상태, blocker, 다음 액션을 기록한다.

## 8. 자기개선 명령

- `/improve`: 누적된 learnings 기반으로 policy-updater를 실행해 에이전트·정책 개정안을 생성한다.
  - 개정안은 diff 형태로 제시되며 사용자 승인 후 적용된다.
  - learnings가 없으면 실행하지 않는다.

## 9. 코딩 원칙

> 에이전트 포함 모든 코드 작업에 적용된다.

@.ruler/AGENTS.md
