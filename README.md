# 자연어 투자 에이전트

말로 "SK하이닉스 4주 사줘", "삼성전자 사도 돼?"라고 하면 투자 AI가 제안하고, 검증 AI가 따로 확인하고, 사용자가 승인한 주문만 **사용자 폰에서** 증권사로 나가는 앱이다.

- 증권사 키와 계좌번호는 사용자 폰에만 저장한다. 서버는 키를 받지 않는다.
- 기본은 모의투자다. 모든 주문은 투자 AI → 검증 AI → 사용자 승인을 거친다.
- 자세한 내용: [INVEST_AGENT_PLAN.md](INVEST_AGENT_PLAN.md) (기획서), [AGENTS.md](AGENTS.md) (작업 규칙)

## 진행 상황

[docs/plan/08-dev-order.md](docs/plan/08-dev-order.md)에 8단계와 진행 체크가 있다. 지금은 4단계(투자 AI + 검증 AI) 진행 중이다. 분석 그래프는 동작하고, 30종목 시세 수집이 남았다.

## 폴더

```
apps/api/        서버 (Python, FastAPI, uv)
  app/           코드
  migrations/    DB 테이블 SQL (번호 순서대로 적용)
  tests/         테스트 (DB invest_test 사용)
apps/client/     앱 + 웹 (Flutter) — 6단계에서 만든다
docs/plan/       기획 문서 (요구사항, 아키텍처, 화면, 그래프, DB 등)
archive/         이전 단계 목업·fixture 코드와 문서 (참고용)
```

## 실행

준비물: Docker Desktop(켜져 있어야 함), [uv](https://docs.astral.sh/uv/)

```bash
docker start invest-db
```

처음이라면 컨테이너를 만든다 (`<비밀번호>`는 직접 정한다).

```bash
docker run -d --name invest-db -e POSTGRES_PASSWORD=<비밀번호> -e POSTGRES_DB=invest -p 5432:5432 -v invest-pgdata:/var/lib/postgresql pgvector/pgvector:pg18
```

`apps/api/.env.example`을 `apps/api/.env`로 복사하고 `DATABASE_URL`을 채운 뒤:

```bash
uv --directory apps/api run python -m app.migrate
```

```bash
uv --directory apps/api run uvicorn app.main:app --port 8000
```

분석용 데이터(시세·재무·공시) 수집 (`.env`에 `OPENDART_API_KEY`, `DATA_GO_KR_API_KEY`, `GEMINI_API_KEY` 필요):

```bash
uv --directory apps/api run python -m app.collect
```

http://localhost:8000/api/health 가 `{"status":"ok","db":"ok"}`면 정상이다. DB에 연결되지 않으면 503과 `"db":"error"`를 돌려준다.

## 테스트

```bash
uv --directory apps/api run pytest
```

테스트는 같은 PostgreSQL 서버에 `invest_test` DB를 새로 만들어 쓴다. 개발 DB `invest`는 건드리지 않는다. 기본 테스트는 Gemini를 부르지 않는다(가짜로 바꿔 끼움).

실제 Gemini로 분류가 맞는지 보려면 (`.env`에 `GEMINI_API_KEY` 필요, 비용 발생):

```bash
uv --directory apps/api run pytest -m gemini
```
