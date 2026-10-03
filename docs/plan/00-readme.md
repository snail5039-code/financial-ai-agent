# 기획 문서 목록

자연어 투자 에이전트의 설계 문서다. 큰 방향은 루트의 [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md), 작업 규칙은 [AGENTS.md](../../AGENTS.md)를 본다.

| 문서 | 내용 |
|---|---|
| [01-requirements.md](01-requirements.md) | 요구사항 정의 (기능 FR, 비기능 NFR, 미확정 값) |
| [02-architecture.md](02-architecture.md) | 전체 구조, 서버가 지휘하고 폰이 증권사 일을 하는 방식, 폴더 구조 |
| [03-screens.md](03-screens.md) | 화면 목록, 화면 흐름, 화면별 정의 |
| [04-graph-design.md](04-graph-design.md) | LangGraph 그래프, 멈춤 4종류, State, 분기 조건 |
| [05-schemas.md](05-schemas.md) | 투자 AI 제안서, 검증 AI 판정, 처리안, 주문 요청·결과 형식 |
| [06-api-spec.md](06-api-spec.md) | 서버 API, 대화 이벤트 스트림, 멈춤 메시지 형식 |
| [07-database.md](07-database.md) | PostgreSQL ERD, 테이블, 제약조건, 자주 쓰는 SQL |

화면 그림(와이어프레임)은 `wireframes/`에 있다. 고칠 때는 `wireframes/make_wireframes.py`를 수정하고 다시 실행한다 (HTML로 그린 뒤 Chrome으로 캡처).

```bash
python docs/plan/wireframes/make_wireframes.py docs/plan/wireframes
```

나머지 그림은 `diagrams/`의 PNG 이미지다. 원본은 같은 이름의 `.mmd`(머메이드) 파일이고, 그림을 고칠 때는 `.mmd`를 수정한 뒤 PNG를 다시 만든다.

```bash
npx -p @mermaid-js/mermaid-cli mmdc -i docs/plan/diagrams/erd.mmd -o docs/plan/diagrams/erd.png -s 2 -b white
```

## 다음에 만들 문서

- 테스트·평가 계획 (데모 시나리오, Golden Set, 검증 AI 오류 주입 세트)
- 일정 (주 단위)
- 보안 위협 정리 (프롬프트 인젝션 등), 예외 상황 정의, 데이터 출처 확정, 성향 설문 문항, 개발 환경 설치 안내
