# 검증 체크리스트

새 화면을 구현하거나 수정한 뒤에는 아래 항목을 확인한다. 정적 목업과 React/Vite 앱은 검증 대상에 맞는 절을 선택하되, 금융 안전 검증은 항상 포함한다.

## 정적 목업 검사

- 새 JavaScript 파일에 대해 `node --check <file>.js`를 실행한다.
- 다음 금지 패턴이 없는지 확인한다.
  - `fetch`
  - `XMLHttpRequest`
  - `WebSocket`
  - `EventSource`
  - `sendBeacon`
  - `localStorage`
  - `sessionStorage`
  - `indexedDB`
  - `document.cookie`
- 외부 URL

## 정적 목업 로컬 렌더 검증

- 로컬 서버:

```powershell
cd "C:\Users\snail\OneDrive\바탕 화면\new_idea\mockup\financial-dashboard"
python -m http.server 4173 --bind 127.0.0.1
```

- 기준 화면: 1440×900
- 앱 창: 1392×852
- 내부 열: 223px / 815px / 352px
- 가로 오버플로 없음
- 콘솔 오류 없음
- 새 캡처는 실제 PNG 헤더와 1440×900 크기를 확인한다.

## React/Vite 최종 감사 기준

- 로컬 정적 검사:
  - `cd apps/web`
  - `npm run typecheck`
  - `npm run build`
- 19개 화면 라우팅:
  - 포트폴리오
  - 기업 상세
  - 거래 내역
  - 세금·수수료
  - 리스크 알림
  - 백테스트
  - 전략 조정
  - 변경 비교
  - 근거 패킷
  - 스트레스 테스트
  - 포트폴리오 건강
  - 승인 대기
  - 역할 상태
  - 투자 리포트
  - 감사 로그
  - 결정 회고
  - 투자 정책
  - 알림 설정
  - 데이터 연결
- 1440×900 기준:
  - `.app-shell` 앱 창이 1392×852 기준으로 들어오는지 확인한다.
  - main 영역과 우측 인스펙터의 `getBoundingClientRect().bottom`이 `.app-shell` 하단 밖으로 나가지 않는지 확인한다.
  - 사이드바 하단 안전 고지가 앱 하단 안에 남는지 확인한다.
  - `documentElement.scrollWidth/clientWidth`, `scrollHeight/clientHeight`로 문서 전체 가로·세로 오버플로가 없는지 확인한다.
- 회귀 상호작용:
  - 사이드바 그룹, 문구, 순서, 활성 상태가 유지되는지 확인한다.
  - 필터 변경 시 목록, 개수, 선택, 인스펙터, 관련 링크, ARIA 상태가 함께 갱신되는지 확인한다.
  - 빈 결과에서는 이전 상세나 이전 링크가 남지 않는지 확인한다.
  - 콘솔 오류가 없는지 확인한다.
- 안전 문구와 금지 연결:
  - `모의투자`, `화면 검토용 가상 예시`, `실제 주문 아님`, `실제 계좌·API·DB 미연결` 등 화면별 필수 안전 문구가 유지되는지 확인한다.
  - `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `sendBeacon`, `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, 외부 URL, 실제 금융 연결을 암시하는 문자열을 확인한다.
  - 백엔드가 아직 없는 상태에서는 외부 네트워크 또는 운영 DB 연결이 없어야 한다.

## 상호작용 검증

- 필터 선택 시 목록과 요약이 함께 갱신되는지 확인한다.
- 행 또는 카드 선택 시 우측 인스펙터가 갱신되는지 확인한다.
- 필터 변경 뒤 숨겨진 선택 항목이 우측에 남지 않는지 확인한다.
- 빈 결과 상태가 있으면 기본 링크나 이전 선택이 남지 않는지 확인한다.
- 관련 기존 화면 링크가 로컬에서 200 응답하는지 확인한다.

## 금융 안전 검증

- 화면에 `모의투자`, `화면 검토용 가상 예시`, `실제 주문 아님`, `실제 계좌·API·DB 미연결` 중 해당 화면에 필요한 문구가 보이는지 확인한다.
- 수익률, 손실, 세금, 비용, 위험, 건강 점수 등은 보장이나 실제 판단처럼 표현하지 않는다.
- 실제 주문, 실제 계좌, 실제 API, 실제 DB 연결을 암시하지 않는다.
