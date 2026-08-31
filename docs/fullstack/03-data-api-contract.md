# 데이터 원칙과 API 계약

기준일: 2026-08-29 KST

## 데이터 원칙

1차 백엔드는 `BACKEND-002`에서 `apps/api` 최소 골격과 `GET /api/health` 단독 엔드포인트까지 생성했다. 화면별 API를 만들 때도 실제 DB 없이 시작한다. 현재 `apps/web` 프론트는 로컬 fixture 모듈로 정적 목업 19개에 대응하는 화면 데이터를 표시한다.

- Python 코드 또는 JSON fixture로 고정 데이터를 제공한다.
- 서버 재시작 시 상태가 초기화되어도 된다.
- 승인·반려 같은 변경은 메모리 저장소에만 반영한다.
- 모든 fixture에는 `asOf`, `sourceLabel`, `isMock`, `disclaimer`를 포함한다.
- 금액, 수익률, 비중은 **원본 숫자만** 내려주고 화면 문자열은 프론트가 만든다. `BACKEND-003`에서 확정했다.
  - 금액은 응답의 `currency` 기준 정수다. `128450000`
  - 비율은 퍼센트 단위 실수다. `6.65`는 6.65%다.
  - 해당 없는 값은 `"-"`나 `""`가 아니라 `null`이다.
  - 시각은 KST 오프셋을 포함한 ISO 8601 문자열이다.
- 이 규칙은 이후 비용·비중·위험 계산을 서버로 옮길 때 계약을 다시 뜯지 않기 위한 것이다. 자세한 예시는 `docs/backend/07-dashboard-api.md`를 본다.

## 공통 응답 예시

```json
{
  "generatedAt": "2026-08-27T16:30:00+09:00",
  "dataAsOf": "2026-08-27T15:20:00+09:00",
  "isMock": true,
  "disclaimer": "화면 검토용 가상 예시이며 실제 계좌·주문·API와 연결되지 않습니다.",
  "data": {}
}
```

## API 범위

실제 외부 API가 아니라 프론트엔드가 호출하는 **내부 로컬 API**만 만든다.

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/health` | 백엔드 상태 확인, `BACKEND-002` 완료 |
| `GET` | `/api/dashboard` | 대시보드 총자산, 차트, 보유 종목, 결정 후보. `BACKEND-003` 완료 |
| `GET` | `/api/companies/{code}` | 기업 상세 가상 근거 |
| `GET` | `/api/approvals` | 승인 대기 목록 |
| `POST` | `/api/approvals/{id}/approve` | 로컬 상태에서 모의승인 처리 |
| `POST` | `/api/approvals/{id}/reject` | 로컬 상태에서 반려 처리 |
| `GET` | `/api/audit-events` | 감사 로그 |
| `GET` | `/api/policies` | 투자 정책 설정값 |
| `PUT` | `/api/policies` | 로컬 정책 설정 저장 |
| `GET` | `/api/risk-alerts` | 리스크 알림 |
| `GET` | `/api/rebalance-plan` | 전략 조정 데이터 |
| `GET` | `/api/evidence-packets` | 승인 전 근거 패킷 |

모든 `POST`, `PUT`은 실제 금융 행동이 아니라 로컬 데모 상태만 바꾼다.
