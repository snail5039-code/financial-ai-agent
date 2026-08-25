# 금융 AI 에이전트 목업

검증과 사용자 승인을 중심으로 설계한 금융 AI 투자 운영 대시보드 목업과 관련 기획 문서를 모아 둔 저장소입니다. 투자 판단을 만드는 역할, 근거를 독립적으로 검증하는 역할, 사용자가 최종 통제하는 승인 흐름을 분리해 표현합니다.

## 주요 화면

- 투자 운영 대시보드: 총자산, 기간별 자산 변화, 보유 종목, AI 분석·검증·승인 대기 흐름
- 삼성전자 기업 상세: 화면용 가격·보유 정보, 재무 지표, 긍정·반대 근거, 예시 공시 검증 인스펙터
- 접근성 지원: 키보드 이동, 포커스 표시, 차트 대체 설명, 선택 상태 및 라이브 영역

화면 캡처는 다음 파일에서 확인할 수 있습니다.

- `mockup/financial-dashboard/financial-dashboard-1440x900.png`
- `mockup/financial-dashboard/company-detail-1440x900.png`

## 로컬 실행

별도 패키지 설치 없이 Python 표준 라이브러리로 실행할 수 있습니다.

```powershell
python -m http.server 4173
```

실행 후 브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:4173/mockup/financial-dashboard/
```

## 안전 고지

- 이 저장소의 가격, 공시, 재무 수치와 투자 근거는 화면 검토용 가상 예시입니다.
- 실제 시세, OpenDART, 증권사 API, 계좌 또는 주문 시스템과 연결되지 않습니다.
- 실제 공시 검증을 수행하지 않았으며 확인되지 않은 정보는 투자 판단에 사용할 수 없습니다.
- 이 프로젝트는 투자 권유가 아니며 수익이나 손실 회피를 보장하지 않습니다.
- 모의승인 동작은 브라우저 화면 상태만 변경하며 실제 주문을 생성하지 않습니다.

## 문서 구조

- `AGENTS.md`: 금융 AI 에이전트 역할·승인·검증 운영 규칙
- `FINANCIAL_AI_AGENT_IDEA.md`: 프로젝트 개념과 에이전트 구조
- `FINANCIAL_AI_AGENT_IMPLEMENTATION.md`: 구현 방향과 기술 검토
- `FINANCIAL_AI_SITE_MOCKUP_PLAN.md`: 최초 대시보드 목업 기획
- `mockup/financial-dashboard/`: 실행 가능한 정적 HTML/CSS/JavaScript와 화면 캡처
- 그 밖의 루트 Markdown 파일: 작업공간에서 검토한 서비스 및 제품 아이디어 문서

세부 실행법과 상호작용 목록은 `mockup/financial-dashboard/README.md`를 참고하세요.
