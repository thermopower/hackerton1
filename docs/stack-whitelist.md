# 기술 스택 화이트리스트

> requirement-writer(섹션 3 스택 질문)와 planner(스택 결정)가 이 파일을 참조한다.
> 목록에 없는 라이브러리를 사용하려면 사용자에게 이유를 설명하고 명시적 승인을 받는다.

---

## 1. 프론트엔드 프레임워크

| 라이브러리 | 버전 기준 | 용도 | 비고 |
|---|---|---|---|
| **Next.js** | 14+ (App Router) | 풀스택 React 프레임워크 | 기본 권장 |
| **React** | 18+ | UI 라이브러리 | Next.js 없이 단독 사용 시 |
| **Vite** | 5+ | React 단독 프로젝트 빌드 도구 | React+Vite 조합 |

---

## 2. 스타일링

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **Tailwind CSS** | 유틸리티 CSS | 기본 권장 |
| **shadcn/ui** | Tailwind 기반 컴포넌트 라이브러리 | Radix UI 기반, 코드 소유권 유지 |
| **Radix UI** | 헤드리스 접근성 컴포넌트 | shadcn 대신 직접 사용 시 |
| **CSS Modules** | 컴포넌트 스코프 CSS | Tailwind 없이 순수 CSS 원할 때 |

---

## 3. 백엔드 / 데이터베이스

### 3-1. BaaS (Backend as a Service)

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Supabase** | PostgreSQL DB + Auth + Storage + Realtime | 기본 권장 (오픈소스, self-host 가능) |
| **Firebase** | Firestore/Realtime DB + Auth + Storage | Google 생태계 선호 시 |
| **PlanetScale** | 서버리스 MySQL | 대용량 확장 필요 시 |
| **Neon** | 서버리스 PostgreSQL | Vercel 통합 용이, Next.js 권장 조합 |

### 3-2. ORM / 쿼리 빌더

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **Supabase JS SDK** | Supabase 전용 쿼리 | Supabase 사용 시 기본 권장 |

### 3-3. 자체 API 서버 (Python)

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **FastAPI** | Python REST API | 기본 권장 |
| **SQLAlchemy** | Python ORM | FastAPI + PostgreSQL 조합 |
| **Alembic** | Python DB 마이그레이션 | SQLAlchemy와 함께 사용 |
| **Pydantic v2** | 데이터 검증 및 직렬화 | FastAPI 내장 |

### 3-4. 경량 / 로컬 DB

| 라이브러리/서비스 | 용도 | 비고 |
|---|---|---|
| **SQLite** | 파일 기반 경량 DB | 로컬 앱, 프로토타입, 단일 서버 |
| **better-sqlite3** | Node.js SQLite 드라이버 (동기) | Next.js API Route / Electron |
| **Turso (libSQL)** | SQLite 호환 엣지 DB | 서버리스 + SQLite 원할 때 |

---

## 4. 인증 (Authentication)

| 서비스/라이브러리 | 용도 | 비고 |
|---|---|---|
| **Clerk** | 풀 관리형 인증 UI+API | 빠른 구현, Social/MFA 포함 |
| **Supabase Auth** | Supabase 내장 인증 | Supabase 사용 시 기본 권장 |
| **NextAuth.js (Auth.js v5)** | Next.js 자체 인증 | 서버 제어 원할 때 |
| **Firebase Auth** | Firebase 내장 인증 | Firebase 사용 시 |

---

## 5. 상태 관리

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **TanStack Query (React Query)** | 서버 상태 캐싱/동기화 | API 호출이 많은 앱 기본 권장 |
| **Zustand** | 클라이언트 전역 상태 | 간단한 전역 상태 |
| **Jotai** | 원자 단위 상태 | 세분화된 상태 관리 필요 시 |
| **React Context + useReducer** | 소규모 전역 상태 | 외부 의존성 없이 처리 가능한 규모 |

---

## 6. 폼 처리 및 유효성 검사

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **React Hook Form** | 폼 상태 관리 | 기본 권장 |
| **Zod** | 스키마 기반 유효성 검사 | TypeScript 타입 자동 생성, 기본 권장 |
| **Yup** | 스키마 유효성 검사 | Zod 대안 |

---

## 7. 결제

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Stripe** | 국제 결제 | 기본 권장 |
| **Toss Payments** | 국내 결제 | 한국 서비스 대상 |
| **카카오페이 / 네이버페이** | 국내 간편결제 | 한국 사용자 비율 높을 때 |

---

## 8. AI / ML

| 서비스/라이브러리 | 용도 | 비고 |
|---|---|---|
| **Anthropic SDK** (`@anthropic-ai/sdk`) | Claude API | 기본 권장 |
| **OpenAI SDK** (`openai`) | GPT API | OpenAI 필요 시 |
| **Vercel AI SDK** (`ai`) | 스트리밍 AI 응답 + 멀티모델 | Next.js 스트리밍 UI에 적합 |
| **LangChain.js** | LLM 체인/에이전트 | 복잡한 LLM 파이프라인 필요 시 |

---

## 9. 파일 스토리지

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Supabase Storage** | 파일 업로드/다운로드 | Supabase 사용 시 기본 |
| **AWS S3** | 대용량 파일 스토리지 | 자체 AWS 인프라 시 |
| **Cloudflare R2** | S3 호환, 무료 티어 큰 스토리지 | 비용 최적화 시 |
| **Uploadthing** | Next.js 파일 업로드 | 간단한 구현 원할 때 |

---

## 10. 알림 / 메시지

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Resend** | 트랜잭션 이메일 | 기본 권장 (React Email 통합) |
| **React Email** | 이메일 템플릿 | Resend와 함께 사용 |
| **Twilio** | SMS / 전화 인증 | 전화번호 인증 필요 시 |
| **OneSignal** | Push 알림 | 웹/앱 푸시 |

---

## 11. 지도 / 위치

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Kakao Map SDK** | 국내 지도 | 한국 서비스 기본 권장 |
| **Naver Map SDK** | 국내 지도 대안 | |
| **Google Maps JavaScript API** | 글로벌 지도 | 해외 서비스 또는 정확도 중요 시 |
| **Mapbox GL JS** | 커스텀 스타일 지도 | 지도 디자인 자유도 필요 시 |

---

## 12. 모니터링 / 에러 추적

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Sentry** | 에러 추적 + 성능 모니터링 | 기본 권장 |
| **Vercel Analytics** | 웹 성능/방문자 분석 | Vercel 배포 시 |
| **PostHog** | 프로덕트 분석 + 피처 플래그 | 오픈소스, self-host 가능 |

---

## 13. 배포 / 인프라

| 서비스 | 용도 | 비고 |
|---|---|---|
| **Vercel** | Next.js / React 배포 | 기본 권장 |
| **Railway** | Node.js / Python 서버 배포 | 간단한 서버 배포 |
| **Fly.io** | 컨테이너 배포 | 지역 엣지 배포 필요 시 |
| **AWS Amplify** | AWS 기반 풀스택 배포 | AWS 생태계 내 시 |

---

## 14. 테스트

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **Vitest** | 단위/통합 테스트 (JS/TS) | Next.js, React+Vite 기본 권장 |
| **Playwright** | E2E 브라우저 테스트 | 기본 권장 |
| **Testing Library** (`@testing-library/react`) | 컴포넌트 테스트 | Vitest와 함께 사용 |
| **pytest** | Python 단위/통합 테스트 | FastAPI 기본 권장 |
| **httpx** | Python HTTP 테스트 클라이언트 | FastAPI E2E |
| **MSW (Mock Service Worker)** | API 모킹 | 프론트엔드 테스트 격리 |

---

## 15. 유틸리티

| 라이브러리 | 용도 | 비고 |
|---|---|---|
| **date-fns** | 날짜 처리 | 기본 권장 (트리쉐이킹 우수) |
| **dayjs** | 날짜 처리 경량 대안 | 번들 크기 중요 시 |
| **clsx / cn** | 조건부 클래스네임 | shadcn/ui에 포함 |
| **axios** | HTTP 클라이언트 | fetch 대신 인터셉터 필요 시 |
| **ky** | 경량 fetch 래퍼 | axios 대안 |
| **uuid** | UUID 생성 | |
| **lodash-es** | 유틸리티 함수 모음 | 트리쉐이킹 가능 버전 |

---

## 사용 규칙

1. **whitelist 우선**: 목록에 있는 라이브러리를 먼저 고려한다.
2. **목록 외 사용 시**: requirement-writer는 사용자에게, planner는 sprint-contract에 사유를 명시하고 사용자 승인을 받는다.
3. **버전 고정**: `package.json`에 `^` 없이 정확한 버전을 명시한다 (보안/재현성).
4. **중복 방지**: 같은 역할의 라이브러리를 두 개 이상 도입하지 않는다. 예: `axios`와 `ky` 동시 사용 금지.
5. **목록 갱신**: policy-updater가 learnings 기반으로 이 파일을 업데이트할 수 있다.
