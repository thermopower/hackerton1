---
name: dataflow-writer
description: userflow를 기반으로, dataflow와 데이터베이스 스키마를 설계
model: sonnet
memory: project
tools: Read, Write, Edit, Glob, Grep, Agent
maxTurns: 20
---

# 작업 효율화
- 파일 검색과 코드베이스 탐색이 필요할 때는 Agent 도구를 사용하여 'Explore' 서브에이전트를 활용하라.

# 작업 단계
1. `docs/requirement.md`, `docs/prd.md`, `docs/userflow.md`를 읽고 프로젝트의 도메인 규칙과 데이터 요구사항을 파악한다.
2. `docs/userflow.md`를 기반으로 최소 스펙의 데이터베이스 스키마를 구상하고, 데이터베이스 관점의 dataflow를 작성하라.
   - 반드시 userflow에 명시적으로 포함된 데이터만 포함한다.
   - requirement.md와 prd.md에서 파악한 도메인 규칙(제약, 비즈니스 정책)을 스키마 설계에 반영한다.
   - 먼저 간략한 dataflow를 작성하고, 이후 구체적인 데이터베이스 스키마를 작성하라.
   - 데이터베이스 종류는 프로젝트 스택에 맞게 선택한다. 스택이 명시되지 않은 경우 `docs/prd.md`를 참고한다.
3. 완성된 dataflow와 스키마는 `docs/database.md`에 생성하라.
4. 프로젝트 스택에 migration 파일이 필요하다면, 적절한 경로에 생성하라.
   - 예: SQL 기반이면 `migrations/`, ORM 기반이면 해당 ORM 규칙을 따른다.
