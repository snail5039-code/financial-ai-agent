# 풀스택 전환 문서 읽기 안내

기준일: 2026-08-29 KST

## 목적

이 폴더는 정적 HTML 목업 19개와 React/Vite `apps/web`로 이전 완료된 19개 화면을 실제 금융 API 없이 프론트엔드·백엔드 연결 앱으로 발전시키기 위한 계획을 나눠 담는다.

루트의 `FINANCIAL_AI_FULLSTACK_PLAN.md`는 짧은 상위 요약이고, 실제 작업자는 이 폴더의 분할 문서를 필요한 범위만 읽는다.

## 현재 결론

- 정적 화면 추가는 일단 멈춘다.
- 풀스택 전환의 기본 스택은 **React + Vite + FastAPI**다.
- React/Vite `apps/web`는 이미 생성되어 정적 목업 19개에 대응하는 19개 화면 이전이 완료됐다.
- `FRONTEND-005`로 승인 대기 주문 행 접근성 구조 정리가 완료됐다.
- `FRONTEND-FINAL-AUDIT` 최초 검증은 16개 화면 1440×900 하단 잘림으로 실패했지만, `FRONTEND-FINAL-AUDIT-R1` CSS 수정 뒤 검증자 19세대가 `FRONTEND-FINAL-AUDIT-R1-V`에서 최종 회귀 `통과`를 판정했다.
- 백엔드는 아직 만들지 않았고, 만들 때도 실제 금융 API 대신 로컬 fixture 데이터를 제공한다.
- 다음 1차 구현 후보는 `/api/health` 또는 대시보드 fixture API처럼 좁은 FastAPI 로컬 수직 슬라이스다.
- 실제 금융 데이터, 계좌, 주문, 체결, 공시, 시세, 환율, AI 실행, 외부 API, 운영 DB는 연결하지 않는다.

## 읽는 순서

1. `01-overview.md`: 왜 풀스택 전환으로 넘어가는지 확인한다.
2. `02-stack-architecture.md`: 기술 스택과 폴더 구조를 확인한다.
3. `03-data-api-contract.md`: fixture 데이터와 로컬 API 계약을 확인한다.
4. `04-frontend-backend-scope.md`: 어떤 화면과 서버 기능부터 옮길지 확인한다.
5. `05-safety-validation.md`: 금지 연결과 검증 기준을 확인한다.
6. `06-implementation-roadmap.md`: 실제 구현 순서와 첫 티켓을 확인한다.

백엔드 1단계 구현 준비는 `docs/backend/00-readme.md`부터 별도로 참조한다.

## 역할별 최소 참조

- 관리자: `00-readme.md`, `01-overview.md`, `06-implementation-roadmap.md`
- 기획자: 전체 문서
- 구현자: `02-stack-architecture.md`, `03-data-api-contract.md`, `04-frontend-backend-scope.md`, `06-implementation-roadmap.md`
- 검증자: `03-data-api-contract.md`, `05-safety-validation.md`, `06-implementation-roadmap.md`

## 상위 규칙

모든 작업은 루트 `AGENTS.md`를 우선한다. 기획, 관리자 승인, 구현, 독립 검증, 재작업, 최종 인수 순서를 유지한다.
