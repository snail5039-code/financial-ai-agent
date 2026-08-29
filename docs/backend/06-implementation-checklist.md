# BACKEND-001 구현 체크리스트

기준일: 2026-08-29 KST

## 다음 구현자 체크리스트

- 작업 시작 전 `AGENTS.md`와 `docs/backend/00-readme.md`를 읽는다.
- 현재 Git 상태와 최신 커밋을 확인한다.
- `apps/api` 생성 전 관리자 승인 범위가 `BACKEND-001`인지 확인한다.
- FastAPI 패키지 관리 도구 결정을 확인한다.
- `/api/health`부터 만든다.
- 공통 응답 래퍼에 `isMock`, `paperOnly`, `executed`, `disclaimer`를 포함한다.
- 외부 API, 실제 금융 데이터, 계좌, 주문, 체결, 운영 DB 연결 코드를 만들지 않는다.
- React 코드는 승인된 연결 범위가 없으면 수정하지 않는다.
- 커밋/푸시는 별도 지시가 있을 때만 수행한다.

## 이번 문서 작업 자체 점검

- `docs/backend/00-readme.md`부터 `06-implementation-checklist.md`까지 7개 문서가 존재한다.
- 문서가 인덱스, 범위, fixture 계약, FastAPI 골격, health API, 안전 경계, 체크리스트로 나뉘어 있다.
- `docs/fullstack/*`의 장기 API 전체 목록을 복사하지 않고 참조만 둔다.
- FastAPI 코드, `apps/api`, 패키지, React 파일을 만들지 않는다.
- `docs/fullstack/00-readme.md`가 백엔드 1단계 문서 위치를 안내한다.
- `docs/handoff/01-current-state.md`와 `docs/handoff/02-active-roles.md`가 현재 문서 단계와 공식 역할 최신 세대를 반영한다.

## 다음 검증자 체크리스트

- 문서 작업 검증 시 `docs/backend/` 7개 문서 존재와 분할 구조를 먼저 확인한다.
- 문서 작업 검증 시 FastAPI 코드, `apps/api`, 패키지, React 변경이 없는지 확인한다.
- `apps/api` 외의 불필요한 코드 변경이 없는지 확인한다.
- `/api/health`가 HTTP 200과 JSON으로 응답하는지 확인한다.
- `isMock: true`, `paperOnly: true`, `executed: false`가 응답에 있는지 확인한다.
- 금지 문자열과 외부 URL 호출 코드가 없는지 검색한다.
- 실제 주문·체결·계좌·공시·시세·환율·운영 DB 연결이 없음을 확인한다.
- 테스트가 통과하는지 확인하고, 실행하지 못한 항목은 이유를 남긴다.

## 보고 형식

구현자는 완료 보고에 다음을 포함한다.

- 생성/수정 파일
- 구현한 엔드포인트와 응답 예시
- 사용한 fixture와 기준 시각
- 테스트 결과
- 금지 연결 문자열 점검 결과
- 남은 위험과 관리자 결정 필요 항목
