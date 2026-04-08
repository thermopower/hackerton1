# 작업 효율화
- 파일 검색과 코드베이스 탐색이 필요할 때는 Agent 도구를 사용하여 'Explore' 서브에이전트를 활용하라.

# 핵심 원칙 (test-driven-development 흡수)

**공통 모듈 구현 코드를 먼저 작성하지 않는다. 반드시 실패하는 테스트를 먼저 작성한다.**

이것은 선택이 아니다. 테스트 없이 작성된 구현 코드는 즉시 삭제하고 TDD 사이클로 돌아간다.

# 작업 개요
기능 단위 개발을 시작하기 전에 많이 사용될 공통 로직이나 라이브러리 관련 세팅을 위해 문서를 작성하고 구현한다.

# 작업 단계
1. `docs/requirement.md`, `docs/prd.md`, `docs/userflow.md`, `docs/database.md`를 읽고 프로젝트의 기획을 파악한다.
   - 외부 서비스를 사용한다면 `docs/external/{service_name}.md`도 참고한다.
2. `.ruler/AGENTS.md`의 Testing 섹션(TDD 사이클, FIRST, AAA)을 준수한다.
3. 코드베이스 현 상태를 Explore 서브에이전트로 파악한다.
4. 최소한의 설계로 오버엔지니어링을 피한다. 설계된 모든 모듈은 반드시 문서에 근거해야 한다.
5. **여러 기능에 걸쳐 반복될 패턴을 미리 식별한다.**
   - `docs/usecases/` 아래 모든 usecase 문서를 읽고, 2개 이상의 기능(feature)에서 반복되는 로직(인증 처리, 에러 핸들링, 데이터 변환, API 호출 패턴 등)을 목록화한다.
   - 이 단계 없이 공통 모듈을 정하면 병렬 implementer들이 같은 로직을 각자 다르게 구현해 코드가 분기된다.
6. 완성된 공통 모듈 계획을 `docs/common-modules.md`에 생성한다.
   - 이후 기능 단위 개발은 병렬로 진행할 수 있도록, 코드 conflict가 생길 수 있는 공통 모듈은 모두 이 문서에 포함되어야 한다.
7. **TDD 사이클(Red-Green-Refactor)을 준수하여 공통 모듈을 구현한다.**

---

## TDD 원칙 (필수 준수)

### TDD 기반 구현 계획 작성

공통 모듈 계획 문서에 다음 내용을 반드시 포함한다:

#### 1. 테스트 우선 작성 명시

각 공통 모듈에 대해 다음을 명시:

```markdown
## {모듈명} 구현 계획

### TDD 프로세스
1. **RED Phase**: 테스트 파일 먼저 작성
   - 테스트 파일 위치 (프로젝트 스택 규칙을 따른다)
   - 테스트 시나리오:
     - 정상 케이스
     - 경계 케이스
     - 에러 케이스

2. **GREEN Phase**: 최소 구현
   - 구현 파일 위치 (프로젝트 구조에 따라 조정)
   - YAGNI 원칙 준수

3. **REFACTOR Phase**: 코드 개선
   - DRY 원칙 적용
   - 네이밍 개선
```

#### 2. 테스트 시나리오 작성

각 공통 모듈의 주요 기능에 대해 테스트 시나리오를 먼저 작성:

```markdown
### 테스트 시나리오

#### 1. {기능명} 테스트
- **정상 케이스**: {설명}
  - Given: {전제조건}
  - When: {실행}
  - Then: {예상결과}

- **경계 케이스**: {설명}
  - Given: {전제조건}
  - When: {실행}
  - Then: {예상결과}

- **에러 케이스**: {설명}
  - Given: {전제조건}
  - When: {실행}
  - Then: {예상 예외/에러}
```

#### 3. 구현 순서 명시

TDD 사이클을 따르는 구현 순서를 명시:

```markdown
### 구현 순서 (TDD 사이클)

**Phase 1: {기능1}**
1. RED: 테스트 파일 작성 → 테스트 실행 (FAILED 확인)
2. GREEN: 최소 구현 → 테스트 실행 (PASSED 확인)
3. REFACTOR: 코드 개선 → 테스트 실행 (PASSED 유지)
```

#### 4. 검증 체크리스트

```markdown
### 검증 체크리스트

- [ ] 모든 기능에 대한 테스트 시나리오 작성 완료
- [ ] RED Phase: 테스트 실패 확인 (FAILED)
- [ ] GREEN Phase: 테스트 통과 확인 (PASSED)
- [ ] REFACTOR Phase: 리팩토링 후 테스트 통과 유지
- [ ] 에러 케이스 테스트 포함
- [ ] 문서화 완료
```

---

## 문서 작성 원칙

- 구현 계획보다 **테스트 시나리오를 먼저** 작성
- 각 공통 모듈의 구현 순서를 **TDD 사이클**로 명시
- FIRST 원칙 준수: Fast, Independent, Repeatable, Self-validating, Timely
- AAA 패턴 사용: Arrange, Act, Assert

---

## 완료 / 실패 반환 규약

작업 완료 또는 실패 시 `.claude-state/claude-progress.txt`에 다음 필드를 기록한다.

**성공**: `docs/common-modules.md`에 모든 포트·인터페이스가 기술되고 구현 코드와 테스트가 모두 통과한 경우.
```
common_module_status: done
```

**실패**: 요구사항 불명확, 의존성 설치 불가, 테스트 반복 실패 등으로 완료 불가 시.
```
common_module_status: failed
common_module_error: <실패 사유를 구체적으로 기술>
```

실패 시 즉시 작업을 중단하고 메인 세션(sprint-builder)에 실패 사실과 사유를 보고한다.
