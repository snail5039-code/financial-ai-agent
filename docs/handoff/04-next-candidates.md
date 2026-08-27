# 다음 화면 후보

다음 작업 번호는 `MOCKUP-020`이다. `MOCKUP-015` 세금·수수료 영향 점검, `MOCKUP-016` 사용자 승인 이력·결정 회고, `MOCKUP-017` 에이전트별 역할 상태판, `MOCKUP-018` 포트폴리오 변경 전/후 비교, `MOCKUP-019` 승인 전 근거 패킷은 완료됐으므로, 아래 후보는 다음 기획자가 새로 정리할 후보 목록이다.

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

`MOCKUP-020` 후보는 아직 새로 확정하지 않았다. 다음 기획자는 완료 화면 19개와 현재 사용자 흐름을 보고 새 후보를 정리한다.
