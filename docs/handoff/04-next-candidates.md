# 다음 화면 후보

다음 화면 작업 번호는 `MOCKUP-020`이다. 다만 현재 판단은 새 화면 추가를 멈추고 `FINANCIAL_AI_FULLSTACK_PLAN.md`와 `docs/fullstack/00-readme.md` 기준으로 프론트엔드·백엔드 연결 앱 전환을 이어가는 것이다. `MOCKUP-015` 세금·수수료 영향 점검, `MOCKUP-016` 사용자 승인 이력·결정 회고, `MOCKUP-017` 에이전트별 역할 상태판, `MOCKUP-018` 포트폴리오 변경 전/후 비교, `MOCKUP-019` 승인 전 근거 패킷은 완료됐다. React/Vite `apps/web`에는 정적 목업 19개에 대응하는 19개 화면 이전이 완료됐고, `FRONTEND-FINAL-AUDIT-R1-V`에서 최종 회귀 `통과` 판정을 받았다.

## 완료: 세금·수수료 영향 점검

- 목적: 매수·매도 제안 전 수수료, 세금, 슬리피지, 예상 순손익이 어떻게 달라지는지 화면용으로 점검한다.
- 완료 파일: `tax-fee-impact.html`, `tax-fee-impact.css`, `tax-fee-impact.js`, `tax-fee-impact-1440x900.png`
- 검증: `MOCKUP-015-V` 대체 독립 검증 조건부 통과 후 README R1 재검증 `통과`
- 안전 경계:
  - 화면 검토용 가상 예시
  - 실제 세금 계산 아님
  - 실제 주문 아님
  - 실제 계좌·API·DB 미연결

## 완료: 사용자 승인 이력·결정 회고

- 목적: 사용자가 왜 승인·반려했는지, 이후 가상 결과가 어땠는지 돌아본다.
- 완료 파일: `decision-review.html`, `decision-review.css`, `decision-review.js`, `decision-review-1440x900.png`
- 검증: `MOCKUP-016-V` 대체 독립 검증 실패 후 R1 재검증 `통과`
- 안전 경계:
  - 실제 성과 회고 아님
  - 투자 판단 평가나 권유 아님
  - 화면용 가상 결과

## 완료: 에이전트별 역할 상태판

- 목적: 제안자, 검증자, 정책 감시자, 승인 관리자 등 역할이 현재 어떤 상태인지 보여준다.
- 완료 파일: `agent-role-status.html`, `agent-role-status.css`, `agent-role-status.js`, `agent-role-status-1440x900.png`
- 검증: `MOCKUP-017-V` 대체 독립 검증 `통과`
- 안전 경계:
  - 실제 AI 실행 상태 아님
  - 외부 에이전트·API 연결 없음
  - 사용자의 승인 없이 어떤 금융 행동도 하지 않음

## 완료: 포트폴리오 변경 전/후 비교

- 목적: 리밸런싱이나 승인 전후의 가상 포트폴리오 변화를 비교한다.
- 완료 파일: `portfolio-change-compare.html`, `portfolio-change-compare.css`, `portfolio-change-compare.js`, `portfolio-change-compare-1440x900.png`
- 검증: `MOCKUP-018-V` 대체 독립 검증 `통과`
- 안전 경계:
  - 변경 후 수치는 실제 체결 결과 아님
  - 실제 주문 생성 아님
  - 손실 회피나 수익 개선 보장 아님

## 완료: 승인 전 근거 패킷

- 목적: 승인 전 결정 후보의 계산 재현성, 정책 한도, 비용, 출처, 리스크, 역할 확인, 사용자 승인 경계를 한 묶음으로 점검한다.
- 구현 파일: `evidence-packet.html`, `evidence-packet.css`, `evidence-packet.js`, `evidence-packet-1440x900.png`
- 검증: `MOCKUP-019-V` 대체 독립 검증 `통과`
- 안전 경계:
  - 화면 검토용 가상 근거 패킷
  - 실제 투자 권유·주문·체결 아님
  - 실제 공시·시세·계좌 검증 아님
  - 사용자 승인 전 금융 행동 없음

## 추천

`MOCKUP-020` 후보는 아직 새로 확정하지 않았다. 화면 추가가 다시 필요해질 때만 완료 화면 19개와 현재 사용자 흐름을 보고 새 후보를 정리한다. 현재 우선순위는 새 화면이 아니라 `BACKEND-002`로 생성된 `apps/api` 최소 골격과 `GET /api/health`를 유지하면서 후속 백엔드 범위를 작게 분리하는 것이다. 실제 금융 데이터·API·계좌·주문·체결·운영 DB는 계속 연결하지 않는다.

## 다음 우선순위

`BACKEND-CORS-001`, `BACKEND-003`, `BACKEND-004`, `BACKEND-005`는 완료됐다. 대시보드·계좌·분석 에이전트·검증 에이전트·실행 에이전트·승인 대기 6개 화면이 백엔드에만 의존한다. React 화면은 23개다.

사이드바에 메뉴만 있고 화면이 없던 항목은 이제 없다.

`BACKEND-006`에서 결정(DEC) 데이터 통합 1차를 완료했다. DEC-1042는 대시보드·승인 대기·에이전트가 `app/fixtures/decisions.py`의 같은 정적 사실과 승인 스토어의 같은 실시간 상태를 공유한다. DEC-1043/DEC-1057 ID 충돌 버그도 이때 발견해 고쳤다.

## 다음 우선순위

1. 감사 로그, 결정 회고, 근거 패킷, 역할 상태 등 나머지 12개 화면을 백엔드로 옮기면서 결정 데이터를 `decisions.py`로 계속 통합한다. 옮기는 화면이 참조하는 결정 ID가 이미 등록된 것과 겹치면 재사용하고, 충돌하면 이번처럼 ID를 분리한다.
2. OpenAPI에서 TypeScript 타입 생성 도입.
3. Playwright 핵심 흐름 테스트. 프론트에 테스트가 0개다.
4. 사이드바 「승인 대기 4」 배지가 하드코딩이다. `GET /api/approvals`의 `pending` 개수로 바꾼다.

1. 승인 흐름 수직 슬라이스: `GET /api/approvals`, `POST /api/approvals/{id}/approve`, `POST /api/approvals/{id}/reject`, 프론트 승인 대기 화면 연결, `src/fixtures/approvals.ts` 제거.
   - 착수 전 결정: 상태 저장소(메모리 vs SQLite), `allow_methods`에 `POST` 추가 시점.
2. OpenAPI에서 TypeScript 타입 생성 도입. 화면이 19개라 Pydantic과 TS 타입을 수기로 맞추면 드리프트가 난다.
3. 남은 낮음 UI 이슈는 별도 후속 정리 후보로 분리하고, 백엔드 진행의 차단 조건으로 보지 않는다.
