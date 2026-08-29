# 구현 로드맵

기준일: 2026-08-29 KST

## Phase 0: 기준 정리

- 기존 정적 목업 19개를 완료 기준으로 고정한다.
- React/Vite `apps/web`의 19개 화면 이전 완료 상태를 기준으로 고정한다.
- 화면별 필요한 데이터 필드는 기존 fixture와 `docs/fullstack/03-data-api-contract.md`를 기준으로 확인한다.
- API 미연결 원칙을 README와 앱 화면에 유지한다.

완료 기준:

- 풀스택 전환 계획 문서가 존재한다.
- 첫 구현 대상 API 후보가 `/api/health` 또는 대시보드 fixture API로 좁혀져 있다.
- React/Vite `apps/web` 프론트가 생성되어 정적 목업 19개에 대응하는 19개 화면을 포함한다.
- `FRONTEND-005` 승인 대기 행 접근성 정리가 완료됐다.
- `FRONTEND-FINAL-AUDIT-R1-V`에서 검증자 19세대가 최종 회귀 `통과`를 판정했다.

## Phase 1: 프로젝트 골격

- `apps/web` React + Vite 생성 완료
- `apps/api` FastAPI 생성은 아직 하지 않음
- 먼저 `/api/health`와 로컬 fixture 응답 원칙을 구현 범위로 확정
- 백엔드 생성 전까지는 프론트 로컬 fixture만 사용

완료 기준:

- 프론트 로컬 주소에서 백엔드 상태를 읽을 준비가 됐거나, 백엔드 생성 전 문서 단계에서는 `/api/health` 계약과 검증 기준이 확정되어 있다.
- 실제 외부 API 호출이 없다.

## Phase 2: 대시보드 수직 슬라이스

- 백엔드 `GET /api/dashboard`
- 기존 프론트 `DashboardPage`
- 기존 공통 `AppShell`
- 대시보드 차트, 보유 종목, 우측 인스펙터를 백엔드 fixture 응답과 연결

완료 기준:

- 정적 목업의 첫 화면과 같은 정보 구조가 컴포넌트로 동작한다.
- 데이터는 서버 fixture에서만 온다.

## Phase 3: 승인 흐름 수직 슬라이스

- 백엔드 `GET /api/approvals`
- 백엔드 `POST /api/approvals/{id}/approve`
- 백엔드 `POST /api/approvals/{id}/reject`
- 프론트 승인 대기 목록과 우측 상세 연결
- 승인·반려 후 감사 로그 상태 반영

완료 기준:

- 실제 주문 없이 화면 상태만 바뀐다.
- 새로고침 전까지 승인·반려 상태가 유지된다.
- 승인 응답은 실제 체결 없음이 명확하다.

## Phase 4: 근거 패킷과 변경 비교

- `GET /api/evidence-packets`
- `GET /api/portfolio-change-compare`
- 결정 선택, 필터, 인스펙터 동기화
- 관련 화면 간 링크 정리

완료 기준:

- 승인 전 근거 패킷과 변경 비교가 같은 결정 ID를 공유한다.
- 정책·비용·리스크·출처 경계가 화면에서 유지된다.

## Phase 5: 문서와 검증

- 실행 방법 정리
- API 응답 예시 문서화
- 프론트 단위 테스트
- 백엔드 단위 테스트
- Playwright 핵심 흐름 테스트

완료 기준:

- 대시보드 → 근거 패킷 → 변경 비교 → 승인 대기 → 결정 회고 흐름이 로컬에서 재현된다.
- 외부 API 호출 없음이 검색과 테스트로 확인된다.

## 첫 개발 티켓

바로 다음 개발은 아래 순서가 좋다.

1. 현재 `apps/web` 대시보드 fixture와 표시 필드 확인
2. `docs/backend/`의 `BACKEND-001` 범위와 안전 경계 재확인
3. 관리자가 첫 백엔드 범위를 `/api/health` 단독 또는 `/api/health`+`/api/dashboard`로 확정
4. 승인된 경우에만 `apps/api` FastAPI 폴더 생성
5. 승인된 엔드포인트의 로컬 fixture 응답 작성
6. 외부 API 호출 금지 테스트 추가
7. README에 풀스택 로컬 실행법 추가

## 결정이 필요한 것

개발 시작 전에 관리자가 확정하면 좋은 항목이다.

1. FastAPI 패키지 관리를 `uv`로 할지 `pip`/`venv`로 할지
2. DB 없이 메모리 fixture로만 갈지, SQLite를 쓸지
3. 첫 백엔드 연결 화면을 대시보드 하나로 할지, 대시보드+승인 대기까지 묶을지
4. 기존 정적 목업을 계속 유지할지, 새 앱 구현 뒤 일부를 보관 문서로 옮길지

현재 추천은 **기존 React + Vite 19개 화면 유지 + FastAPI 추가, 메모리 fixture, `/api/health` 또는 대시보드 API 1개 수직 슬라이스부터 시작**이다.
