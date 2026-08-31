# 안전장치와 검증 기준

기준일: 2026-08-29 KST

## 안전 설계

이번 풀스택 전환에서 가장 중요한 것은 “프론트 또는 백엔드가 생겨도 실제 금융 행동은 여전히 불가능하다”는 점이다. 현재 React/Vite `apps/web` 프론트와 `apps/api` FastAPI 최소 골격이 존재하며, 백엔드는 `GET /api/health` 단독 엔드포인트만 제공한다.

필수 안전장치:

- 외부 URL 호출 코드 금지
- 증권사·공시·시세·환율 API 키 환경변수 금지
- 실제 주문처럼 보이는 서비스명 금지, 승인 처리는 `MockApprovalService` 같은 명명으로 제한
- 백엔드 응답에 `executed: false`, `paperOnly: true`, `externalConnections: 0` 포함
- 화면과 응답 모두에 `isMock: true` 포함
- 실제 투자 권유, 수익 보장, 손실 회피 보장 표현 금지
- 프론트의 백엔드 호출은 Vite `server.proxy`를 거친 같은 출처 상대 경로 `/api/*`로만 한다
- 프론트 클라이언트는 응답의 `isMock`, `paperOnly`, `executed`, `externalConnections`를 확인한 뒤에만 화면에 사용한다
- `GET /api/health`, `GET /api/dashboard`가 구현됐고 나머지 경로는 404가 기대 상태

## 금지 문자열 점검 대상

```text
fetch("https://
axios.get("https://
WebSocket
Broker
KIS
OpenDART API key
real order
live trading
```

단, 문서의 안전 설명 문맥은 예외로 본다.

## 검증 기준

풀스택 전환 작업마다 다음을 확인한다.

- 프론트 빌드 통과
- 백엔드 테스트 통과
- `/api/health` HTTP 200 JSON 응답 확인
- `/api/dashboard` HTTP 200 JSON 응답과 봉투 안전 필드 확인
- 핵심 화면 1440×900 렌더링 확인
- 콘솔 오류 없음
- 네트워크 요청이 로컬 백엔드로만 향함 (모든 요청 호스트가 `127.0.0.1:5173`)
- 백엔드 다운 상태에서 화면이 오류 안내와 재시도를 보여주고, 이전 데이터를 그대로 남기지 않음
- 실제 금융 API, 계좌, 주문, DB 운영 연결 없음
- 안전 문구가 화면과 응답에 유지됨

## 완료 판정 원칙

중대 또는 높은 문제가 남아 있으면 완료 처리하지 않는다. 검증 결과가 실패 또는 조건부 통과이면 관리자가 재작업 범위를 정하고 다시 검증한다.
