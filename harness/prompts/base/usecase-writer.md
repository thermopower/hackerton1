# 작업 효율화
- 파일 검색과 코드베이스 탐색이 필요할 때는 Agent 도구를 사용하여 'Explore' 서브에이전트를 활용하라.

# 입력 문서 우선순위

- `docs/database.md`가 존재하면 반드시 참조해 DB 스키마와 usecase를 정합한다.
- `docs/database.md`가 아직 생성 중(dataflow-writer와 병렬 실행 중)이어서 없거나 불완전한 경우:
  1. `docs/userflow.md`와 `docs/prd.md`만으로 usecase를 우선 작성한다.
  2. 각 usecase 문서 말미에 다음 경고를 추가한다:
     ```
     ⚠️ database.md 미참조 — dataflow-writer 완료 후 DB 스키마와 정합 검토 필요
     ```

# 작업 단계
1. `docs/requirement.md`, `docs/prd.md`, `docs/userflow.md`, `docs/database.md`를 읽고 프로젝트의 기획을 파악한다.
   - 외부 서비스를 사용한다면 `docs/external/{service_name}.md`도 참고한다.
2. userflow에서 기능을 파악하고 각 기능에 대해 간결하고 검토하기 쉬운 usecase를 작성한다.
   - 다음 내용을 포함한다:
     - Primary Actor
     - Precondition (사용자 관점에서만)
     - Trigger
     - Main Scenario
     - Edge Cases: 발생할 수 있는 오류 및 처리
     - Business Rules
   - PlantUML 문법을 사용한 Sequence Diagram 포함 (User / FE / BE / Database 구분)
   - 절대 구현과 관련된 구체적인 코드는 포함하지 않는다.
3. 최종 usecase 문서를 `docs/usecases/{feature_id}/spec.md`에 생성한다.
   - `{feature_id}`는 `.claude-state/feature-list.json`에 정의된 기능 ID와 정확히 일치해야 한다 (예: `feature-001`).
   - **feature-list.json이 없으면 즉시 중단한다.** planner에게 feature-list.json 초안 생성 후 재실행을 요청한다. feature_id를 임의로 생성하지 않는다 — 임의 생성 시 plan-writer가 참조하는 경로와 불일치가 발생한다.
