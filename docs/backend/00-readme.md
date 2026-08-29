# BACKEND-001 문서 읽기 안내

기준일: 2026-08-29 KST

## 목적

이 폴더는 실제 FastAPI 백엔드 구현 전에 `BACKEND-001` 1단계 범위와 안전 경계를 작은 문서로 나눠 확인하기 위한 준비 문서다. React/Vite `apps/web` 19개 화면 이전과 `FRONTEND-FINAL-AUDIT-R1-V` 통과 이후에도 상위 방향과 장기 로드맵은 `FINANCIAL_AI_FULLSTACK_PLAN.md`와 `docs/fullstack/`를 따른다.

## 읽는 순서

1. `01-backend-001-scope.md`: 이번 백엔드 1단계의 구현 범위와 비범위를 확인한다.
2. `02-local-fixture-contract.md`: 로컬 fixture 응답의 공통 원칙을 확인한다.
3. `03-fastapi-skeleton.md`: 다음 구현에서 만들 예상 폴더 구조를 확인한다.
4. `04-health-api.md`: `/api/health` 응답 필드와 검증 포인트를 확인한다.
5. `05-safety-boundary.md`: 실제 금융 연결 금지 기준과 금지 문자열을 확인한다.
6. `06-implementation-checklist.md`: 다음 구현자와 검증자의 체크리스트를 확인한다.

## 상위 참조

- `AGENTS.md`: 역할 분리, 승인, 검증, 금융 안전 규칙
- `docs/handoff/00-readme.md`: 인수 문서 읽기 순서
- `docs/handoff/01-current-state.md`: 현재 커밋과 제품 상태
- `docs/fullstack/03-data-api-contract.md`: 장기 API 후보 목록과 공통 데이터 원칙
- `docs/fullstack/05-safety-validation.md`: 풀스택 전환 전체 안전 기준

## 원칙

- 실제 금융 데이터, 계좌, 주문, 체결, 공시, 시세, 환율, AI 실행, 외부 API, 운영 DB는 연결하지 않는다.
- `BACKEND-001`은 문서와 다음 구현 준비 단계다. 이 문서 작업에서는 FastAPI 코드, `apps/api`, 패키지 설치를 만들지 않는다. 다음 구현은 관리자 승인 후 `/api/health` 또는 대시보드 fixture API처럼 좁은 로컬 수직 슬라이스로 시작한다.
- 장기 API 전체 목록은 이 폴더에 복사하지 않고 `docs/fullstack/03-data-api-contract.md`를 참조한다.
