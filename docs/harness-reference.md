# Harness 참조 문서

> 매 세션 전체를 읽지 말고 이 문서만 참조하세요.  
> 상세 내용이 필요할 때만 해당 파일을 직접 읽으세요.

**이 하네스는 Dify 워크플로우 YAML 파일 생성 전용이다.**

---

## 전체 흐름

```
requirement.md 비어있음
        ↓
requirement-writer (사용자 인터뷰 → docs/requirement.md 작성)
        ↓
    planner ──→ docs/workflow-design.md (노드 설계)
             ──→ sprint-contract (draft) ──→ [사용자 승인]
        ↓
  sprint-builder:
    - docs/workflow-design.md + docs/node-reference.md 참조
    - output/<이름>.yml 작성
    - 자체 검증 체크리스트 통과
    - status: implemented
        ↓ (hook: check-smoke.sh → YAML 파일 존재 여부 확인)
    evaluator ──→ evaluation-report (pass/fail)
        ↓ fail → integration-fixer 자동 실행 (최대 2회 / 초과 시 사용자 보고)
    reviewer ──→ review-notes.md (워크플로우 품질 비평)
        ↓ (hook: trigger-retrospective.sh)
  retrospective ──→ learnings.md + metrics.json
        ↓ 완료 → 완성된 YAML 파일 제시
  /improve → policy-updater ──→ 에이전트/정책 개정안 [사용자 승인 후 적용]
```

---

## 단계 전환 조건 (빠른 판단)

| requirement.md | sprint-contract status | evaluation-report | review-notes | → 다음 액션 |
|---|---|---|---|---|
| 비어있음 | - | - | - | requirement-writer 실행 |
| 있음 | none | - | - | planner 실행 |
| 있음 | draft | - | - | 사용자에게 승인 요청 |
| 있음 | approved | - | - | sprint-builder 실행 |
| 있음 | implemented | none/없음 | - | evaluator 실행 |
| 있음 | implemented | fail | - | fix_attempt < 2: integration-fixer 자동 실행 |
| 있음 | implemented | fail | - | fix_attempt ≥ 2: [BLOCKER] 사용자 보고 후 중단 |
| 있음 | implemented | pass | 없음 | reviewer 실행 |
| 있음 | implemented | pass | reviewed | retrospective 실행 |
| 있음 | implemented | pass | reviewed (완료) | 완성된 YAML 파일 제시 후 종료 |

---

## 에이전트 역할 요약

| 에이전트 | 모델 | maxTurns | 역할 | 금지 |
|---|---|---|---|---|
| **requirement-writer** | sonnet | 20 | 사용자 인터뷰 → docs/requirement.md 작성. 섹션: 워크플로우 목적 → 처리 단계 → 세부 규칙. 승인 게이트 포함 | 노드 설계, YAML 작성, 섹션 건너뜀 |
| **planner** | sonnet | 30 | 요구사항 → 노드 설계(docs/workflow-design.md) → sprint-contract 초안. 사용자 승인 후 approved로 갱신 | YAML 파일 직접 작성, 구현 코드, 승인 없이 sprint-builder 실행 |
| **sprint-builder** | sonnet | 40 | 설계 문서 기반으로 output/*.yml 작성. 자체 검증 체크리스트 통과 후 implemented 선언 | 범위 초과, 설계 없는 노드 추가, 검증 없이 done 선언 |
| **evaluator** | sonnet | 30 | YAML 구조 검증 (V-1~V-10). pass/fail 판정. evaluation-report.md 작성 | 개선 제안, reviewer 역할, sprint-contract 수정 |
| **reviewer** | opus | 30 | YAML 품질 비평: 요구사항 정렬성, 프롬프트 품질, 노드 설계 효율성. review-notes.md 작성 | pass/fail 판정, evaluator 역할, retrospective 직접 호출 |
| **integration-fixer** | sonnet | 50 | evaluation fail 시 YAML 구조 오류 복구. fix_attempt 증가는 훅이 담당 | 기능 추가, 범위 확장 |
| **retrospective** | haiku | 20 | 지표 수집, learnings 누적 | learnings.md·metrics.json 외 파일 수정 |
| **policy-updater** | sonnet | 30 | learnings 기반 에이전트/정책 개정안 생성 | 승인 없이 파일 수정 |

---

## 산출물 파일

| 파일 | 작성자 | 설명 |
|---|---|---|
| `docs/requirement.md` | requirement-writer | 워크플로우 목적, 처리 단계, 세부 규칙 |
| `docs/workflow-design.md` | planner | 노드 목록, 입출력 변수, 엣지 연결 설계 |
| `docs/node-reference.md` | 수동 (하네스 초기화) | 노드 타입 스키마 레퍼런스 |
| `output/*.yml` | sprint-builder | **최종 산출물**: 완성된 Dify YAML 파일 |

---

## 상태 파일 (`/.claude-state/`)

| 파일 | 작성자 | 핵심 필드 |
|---|---|---|
| `claude-progress.txt` | 모든 에이전트 | 현재 상태, blocker, 다음 액션 |
| `sprint-contract.md` | planner | `status: none/draft/approved/implemented`, `fix_attempt` |
| `evaluation-report.md` | evaluator | `status: pass/fail`, blocker 목록 |
| `review-notes.md` | reviewer | `status: reviewed`, Critical/Major/Minor 항목 |
| `learnings.md` | retrospective | `status: active`, `improve_needed: true/false` |
| `metrics.json` | retrospective | sprint 지표 |
| `harness-version.md` | 자동 | 하네스 버전, 변경 이력 |

---

## Hooks (`/.claude/settings.json`)

| 이벤트 | 조건 | 스크립트 | 역할 |
|---|---|---|---|
| SessionStart | 항상 | `session-start.sh` | 상태 스캔 → additionalContext 주입 |
| SubagentStop | sprint-builder | `check-smoke.sh` | output/*.yml 존재 여부 확인 |
| SubagentStop | reviewer | `trigger-retrospective.sh` | retrospective 트리거 |
| SubagentStop | integration-fixer | `track-fix-attempt.sh` | sprint-contract.md의 fix_attempt 증가 |
| SubagentStop | evaluator·reviewer·retrospective | `check-output.sh` | 출력 결과 검증 |

---

## 사용자 승인 필수 시점

1. **sprint-contract**: 노드 설계 요약 제시 → 승인 후에만 sprint-builder 시작
2. **수정 2회 초과**: fix_attempt ≥ 2이면 [BLOCKER] 보고 후 중단
3. **policy-updater 완료 후**: 개정안 diff 제시 → 승인 후에만 파일 적용

---

## 노드 타입 목록 (빠른 참조)

상세 스키마는 `docs/node-reference.md` 참조.

| 타입 | 용도 |
|---|---|
| `start` | 워크플로우 진입점, 사용자 입력 변수 정의 |
| `end` | 워크플로우 종료, 출력 변수 반환 |
| `llm` | LLM(Claude 등) 호출, 텍스트 생성/분석 |
| `code` | Python3 코드 실행, 데이터 가공/계산 |
| `if-else` | 조건에 따른 분기 처리 |
| `template-transform` | Jinja2 템플릿으로 텍스트 포맷팅 |
| `parameter-extractor` | LLM으로 비정형 텍스트에서 구조화 데이터 추출 |
| `knowledge-retrieval` | Knowledge Base 문서 검색 |
| `tool` | 내장 도구 호출 (차트, HTTP 요청 등) |
