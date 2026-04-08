## Layered Architecture
항상 레이어드 아키텍처를 따른다.

### Layer Definitions
- Presentation: UI, controller, route, handler, request/response, DTO, input validation
- Application: use case, orchestration, transaction boundary, workflow coordination
- Domain: business rules, entity, value object, domain service, policy, domain interface/port
- Infrastructure: DB, ORM, external API, file storage, cache, messaging, repository implementation, adapters

### Allowed Dependencies
- Presentation -> Application
- Application -> Domain
- Infrastructure -> Domain/Application contracts
- Domain -> no outer-layer dependency

### Forbidden
- Presentation에서 repository, DB, SQL, ORM, external API 직접 호출 금지
- Controller/route/UI에 비즈니스 로직 구현 금지
- Domain에서 framework, HTTP, DB, ORM, file I/O, external SDK import 금지
- Application에서 concrete infrastructure 직접 의존 금지
- Repository/API client에 비즈니스 정책 구현 금지
- DTO를 Domain model처럼 사용 금지
- Persistence model을 Domain entity처럼 사용 금지
- request/domain/persistence model 혼용 금지
- 레이어 역방향 의존성 금지
- 레이어 건너뛰기 금지

### Folder Structure
모든 앱 코드는 `src/` 아래에 위치한다. 레이어 폴더명은 스택 관행을 따르되, 각 폴더가 어느 레이어에 해당하는지 명확해야 한다.

| 스택 | Presentation | Application | Domain | Infrastructure |
|------|-------------|-------------|--------|----------------|
| Next.js | `src/app/`, `src/components/` | `src/lib/` | `src/domain/` | `src/server/`, `src/lib/db/` |
| React + Vite | `src/pages/`, `src/components/` | `src/hooks/`, `src/services/` | `src/domain/` | `src/api/`, `src/lib/` |
| FastAPI | `src/routers/`, `src/schemas/` | `src/services/` | `src/domain/` | `src/repositories/`, `src/db/` |

### Implementation Rules
- 새 기능은 먼저 어느 레이어에 속하는지 판단한다.
- 비즈니스 규칙은 Domain 또는 Application에만 둔다.
- 외부 시스템 접근이 필요하면 inner layer에 interface/port를 정의하고 Infrastructure에서 구현한다.
- DTO, Domain, Persistence 모델 간 매핑은 명시적으로 처리한다.
