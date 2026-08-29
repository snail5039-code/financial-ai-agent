# Health API

기준일: 2026-08-29 KST

## 목적

`GET /api/health`는 백엔드가 로컬에서 실행 중이고 실제 금융 연결 없이 fixture 모드로 동작한다는 점을 확인하는 최소 엔드포인트다.

이 엔드포인트는 사용자 계좌, 실제 주문, 시세, 공시, 환율, AI 실행 상태를 확인하지 않는다. 서버 프로세스가 살아 있고 안전 플래그가 유지되는지만 확인한다.

## 응답 예시

```json
{
  "generatedAt": "2026-08-28T10:00:00+09:00",
  "dataAsOf": "2026-08-28T10:00:00+09:00",
  "sourceLabel": "로컬 FastAPI health",
  "isMock": true,
  "paperOnly": true,
  "executed": false,
  "disclaimer": "로컬 개발용 상태 확인이며 실제 금융 데이터·계좌·주문·API와 연결되지 않습니다.",
  "data": {
    "status": "ok",
    "service": "financial-ai-agent-api",
    "mode": "local-fixture",
    "externalConnections": 0
  }
}
```

## 필드 기준

- `status`: 정상일 때 `ok`
- `service`: 로컬 백엔드 식별자
- `mode`: `local-fixture`
- `externalConnections`: 항상 `0`
- 공통 안전 필드: `isMock: true`, `paperOnly: true`, `executed: false`

## 검증 포인트

- HTTP 200으로 응답한다.
- 응답이 JSON이다.
- `isMock`, `paperOnly`, `executed`, `disclaimer`가 누락되지 않는다.
- `mode`는 `local-fixture`이고 `externalConnections`는 `0`이다.
- 외부 API, 실제 계좌, 실제 주문, 운영 DB 연결을 시도하지 않는다.
- 로그나 환경변수에 비밀키 또는 실제 금융 연결 정보가 필요하지 않다.
