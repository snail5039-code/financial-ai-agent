# 안전장치와 검증 기준

기준일: 2026-08-29 KST

## 안전 설계

이번 풀스택 전환에서 가장 중요한 것은 “프론트 또는 백엔드가 생겨도 실제 금융 행동은 여전히 불가능하다”는 점이다. 현재 React/Vite `apps/web` 프론트와 `apps/api` FastAPI 최소 골격이 존재하며, 백엔드는 `GET /api/health` 단독 엔드포인트만 제공한다.

필수 안전장치:

- 외부 URL 호출 코드 금지 — **단, `app/integrations/opendart.py`는 예외다.** 2026-09-01 사용자 승인으로, 금융감독원 OpenDART 공시 API(읽기 전용, 계좌·금액 무관)에 한해 서버 사이드 호출을 허용한다. 다른 파일에서 외부 URL을 호출하는 코드는 여전히 금지다.
- 증권사·시세·환율 API 키 환경변수 금지. **OpenDART API 키(`OPENDART_API_KEY`, `apps/api/.env`, git 미포함)는 예외다** — 공시 조회 전용이고 계좌·주문과 무관하다.
- 실제 주문처럼 보이는 서비스명 금지, 승인 처리는 `MockApprovalService` 같은 명명으로 제한
- 백엔드 응답에 `executed: false`, `paperOnly: true` 포함. `externalConnections`는 기본 `0`이고, 기업 상세 화면이 OpenDART 공시를 실제로 받아온 요청에 한해서만 `1`을 허용한다(다른 모든 화면은 여전히 `0` 고정).
- 화면과 응답 모두에 `isMock: true` 포함
- 실제 투자 권유, 수익 보장, 손실 회피 보장 표현 금지
- 프론트의 백엔드 호출은 Vite `server.proxy`를 거친 같은 출처 상대 경로 `/api/*`로만 한다
- 프론트 클라이언트는 응답의 `isMock`, `paperOnly`, `executed`, `externalConnections`(허용 목록 기준, 기본 `[0]`)를 확인한 뒤에만 화면에 사용한다
- 23개 화면 전부와 `GET /api/health`가 구현됐다(현재 상태는 `docs/handoff/01-current-state.md` 기준)

## 금지 문자열 점검 대상

```text
fetch("https://
axios.get("https://
WebSocket
Broker
KIS
real order
live trading
```

단, 문서의 안전 설명 문맥과 `app/integrations/opendart.py`(및 이를 부르는 `app/routers/company_detail.py`, `app/config.py`)의 `https://opendart.fss.or.kr` 호출은 예외로 본다. 그 외 파일에서 이 문자열들이 나오면 실패로 본다.

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
- 증권사 API, 실제 계좌, 주문, DB 운영 연결 없음. OpenDART 공시 조회(기업 상세 화면)만 예외적으로 실제 외부 연결이며, 이 경우 응답이 `filingsConnected: true`·`externalConnections: 1`로 정직하게 표시하는지 확인한다
- 안전 문구가 화면과 응답에 유지됨

## 완료 판정 원칙

중대 또는 높은 문제가 남아 있으면 완료 처리하지 않는다. 검증 결과가 실패 또는 조건부 통과이면 관리자가 재작업 범위를 정하고 다시 검증한다.
