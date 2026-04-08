# Claude Code 앱 생성 하네스

Claude Code 기반 앱 개발을 위한 구조화된 하네스 템플릿입니다.  
요구사항 수집부터 구현, 평가, 회고까지 전체 개발 루프를 에이전트로 자동화합니다.

> **버전**: 1.0 (2026-04-04)

---

## 시작하기

```bash
# 1. 이 저장소를 클론하거나 템플릿으로 사용
# 2. Claude Code에서 프로젝트 열기
# 3. 하네스 루프 시작
/harness start
```

> Windows에서는 **Git Bash** 또는 **WSL**이 필요합니다.

---

## 커맨드

| 커맨드 | 설명 |
|---|---|
| `/harness` | 현재 상태에서 하네스 루프 재개 |
| `/harness start` | 요구사항 수집부터 새로 시작 |
| `/edit-harness` | 하네스 루프 종료 → 일반 편집 모드로 복귀 |
| `/improve` | 누적된 learnings 기반으로 에이전트/정책 개선안 생성 |

---

## 개발 루프

```
requirement-writer  →  사용자 인터뷰 → docs/requirement.md
        ↓
    planner         →  설계 문서 + sprint-contract (draft) → [사용자 승인]
        ↓
  sprint-builder    →  구현 → status: implemented
        ↓ (hook: check-smoke.sh)
    evaluator       →  pass/fail 판정 (Playwright MCP 브라우저 검증 포함)
        ↓ fail → integration-fixer
    reviewer        →  품질 비평 · 개선 제안
        ↓ (hook: trigger-retrospective.sh)
  retrospective     →  지표 수집 · learnings 누적
        ↓ improve_needed: true
  policy-updater    →  에이전트/정책 개정안 → [사용자 승인 후 적용]
```

---

## 에이전트

| 에이전트 | 모델 | 역할 |
|---|---|---|
| `requirement-writer` | sonnet | 사용자 인터뷰 → 요구사항 문서 작성 |
| `planner` | sonnet | 설계 문서 + sprint-contract 초안 작성 |
| `sprint-builder` | sonnet | 승인된 범위만 구현 (`permissionMode: acceptEdits`) |
| `evaluator` | haiku | pass/fail 판정 (Playwright MCP 브라우저 검증 포함) |
| `reviewer` | opus | 품질 비평 · 개선 제안 |
| `integration-fixer` | sonnet | 환경/의존성 복구 (`isolation: worktree`, Playwright MCP) |
| `retrospective` | haiku | 지표 수집 · learnings 누적 |
| `policy-updater` | sonnet | learnings 기반 정책 개정안 생성 |

### 서브 에이전트 (planner/sprint-builder가 내부 호출)

`prd-writer` · `userflow-writer` · `dataflow-writer` · `usecase-writer` · `plan-writer` · `common-module-writer` · `implementer`

---

## 파일 구조

```
.claude/
  agents/          # 에이전트 정의 (16개, 서브에이전트 포함)
  hooks/           # SessionStart · SubagentStop 훅 스크립트
  commands/        # 커스텀 커맨드
  settings.json    # 훅 연결 설정
.claude-state/     # sprint 상태 · 진행상황 · learnings · metrics
scripts/           # smoke(lint+타입+빌드) · unit · e2e · evaluation-gate(+npm audit) · collect-metrics · check-thresholds
profiles/          # 스택별 검증 스크립트 (planner가 sprint 시작 시 생성)
docs/              # 설계 문서 · harness-reference.md
src/               # 앱 코드 (planner가 스택 확정 후 생성)
CLAUDE.md          # 하네스 운영 규칙
.ruler/AGENTS.md   # 코딩 원칙 (레이어드 아키텍처, TDD 등)
```

---

## 지원 스택

| 스택 | profile 이름 |
|---|---|
| Next.js + Supabase | `nextjs-supabase` |
| Next.js | `nextjs` |
| React + Vite | `react-vite` |
| Python FastAPI | `fastapi` |
| 기타 | `generic` |

---

## 참고 문서

- **[docs/harness-reference.md](docs/harness-reference.md)** — 전체 구조 빠른 참조
- **[.claude-state/harness-version.md](.claude-state/harness-version.md)** — 버전 및 변경 이력
- **[CLAUDE.md](CLAUDE.md)** — 하네스 운영 규칙 전문
