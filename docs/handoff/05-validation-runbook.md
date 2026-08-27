# 검증 체크리스트

새 화면을 구현하거나 수정한 뒤에는 아래 항목을 확인한다.

## 정적 검사

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

## 로컬 렌더 검증

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
