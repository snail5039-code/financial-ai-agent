# 개발 순서

작성일: 2026-10-04 · 기준 문서: [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md) 5장 MVP

MVP를 8단계로 나눠 만든다. 증권사 키 없이 할 수 있는 것부터 하고, 키는 7단계에서야 필요하다.

## 진행 방법

1. 단계를 시작하기 전에 그 단계의 **참고 문서**를 읽는다.
2. 할 일을 계획해서 사용자에게 보여주고 동의를 받는다 ([AGENTS.md](../../AGENTS.md) 2장).
3. 구현한다.
4. **완료 조건**을 확인한다 (테스트, 화면은 직접 띄워서).
5. 진행 상황 표의 ⬜를 ✅로 바꾸고, 그 단계의 "완료 기록"에 날짜와 커밋을 적은 뒤 커밋한다.
6. 다음 단계로 넘어간다.

## 진행 상황

| 단계 | 내용 | 필요한 키 | 상태 |
|---|---|---|---|
| 1 | 정리 + 서버 뼈대 | 없음 | ✅ |
| 2 | 로그인 · 성향 설문 · 투자 정책 API | 없음 | ⬜ |
| 3 | LangGraph 뼈대 · 조회 | Gemini | ⬜ |
| 4 | 투자 AI + 검증 AI | Gemini, OpenDART | ⬜ |
| 5 | 주문 그래프 | Gemini | ⬜ |
| 6 | Flutter 앱 뼈대 | 없음 | ⬜ |
| 7 | 증권사 연결 | KIS 모의, KB | ⬜ |
| 8 | 웹 · 기록 · 마무리 | 없음 | ⬜ |

---

## 1. 정리 + 서버 뼈대

**할 일**
- 기존 목업·fixture 코드와 이전 단계 문서를 `archive/`로 옮긴다 (삭제 아님)
- `README.md`를 새 방향으로 다시 쓴다
- `apps/api`에 PostgreSQL 연결 (`psycopg`)
- `migrations/*.sql` 파일과 순서대로 적용하는 실행기로 테이블 15개 생성
- `/api/health`가 DB 연결 상태도 알려준다
- 테스트는 별도 DB `invest_test`에서

**완료 조건**: 서버가 DB에 연결돼 뜨고, 테이블 15개가 생기고, 테스트 통과

**참고 문서**
- [02-architecture.md](02-architecture.md): 3장 서버 구조, 7장 개발 환경·저장소
- [07-database.md](07-database.md): ERD, 테이블, 제약조건
- [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md): 10장 아직 정할 것 6번 (기존 화면 정리)
- 개발 환경: PostgreSQL은 Docker 컨테이너 `invest-db` (`pgvector/pgvector:pg18`), 접속 정보는 `apps/api/.env`

**완료 기록**: 2026-10-04 · 커밋 `f627bd3`(archive 이동), 그다음 커밋(서버 뼈대)
- 옮긴 곳: `archive/mockup`, `archive/web`, `archive/api-fixture`, `archive/docs`, `archive/ideas`
- DB 접근은 psycopg, 마이그레이션은 SQL 파일 + `app/migrate.py` ([07-database.md](07-database.md) 5장)
- 테이블은 ERD대로 15개 (처음 적은 14개는 잘못 센 것)
- 서버의 `.env.example`에서 KIS 키 항목을 지웠다 (서버는 증권사 키를 받지 않음)
- 임베딩 크기와 벡터 인덱스는 4단계에서 정한다

---

## 2. 로그인 · 성향 설문 · 투자 정책 API

**할 일**
- 회원가입·로그인 (비밀번호 해시, 토큰), 내 정보, 탈퇴 (데이터 삭제)
- 성향 설문 제출 → 성향 단계(1~5) → 정책 기본 한도
- 투자 정책 조회·수정 (성향보다 높으면 경고), 수수료율 입력

**완료 조건**: API 테스트 통과 (잘못된 입력, 한도 범위, 탈퇴 시 삭제 포함)

**참고 문서**
- [01-requirements.md](01-requirements.md): FR-01 ~ FR-04, FR-07 ~ FR-07b, NFR-03
- [06-api-spec.md](06-api-spec.md): 1장 목록 (계정, 성향·정책), 5장 예시
- [07-database.md](07-database.md): `users`, `investor_profiles`, `policies`
- [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md): 6장 사용자 성향 분석
- 정해야 할 것: 로그인 방식 (기획서 10장 7번), 설문 문항

**완료 기록**: 

---

## 3. LangGraph 뼈대 · 조회

**할 일**
- 공유 State, supervisor(요청 분류), 조회 그래프
- 멈춤(interrupt) 4종류 처리 틀: `question` / `fetch` / `approval` / `execute`
- 대화 API: `POST /api/chat`, `POST /api/chat/resume` (이벤트 스트림), `GET /api/chat/pending`
- 체크포인트 `PostgresSaver`
- 웹 요청이면 `fetch` 대신 계좌 스냅샷 사용 (`POST/GET /api/snapshot`)

**완료 조건**: "잔고 보여줘" → `fetch` 멈춤 → 가짜 잔고로 이어서 답. 서버를 재시작해도 멈춘 업무가 남아 있음

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 1장 전체 그래프, 2장 멈춤 4종류, 3장 조회 그래프, 7장 State, 9장 노드 목록
- [06-api-spec.md](06-api-spec.md): 2장 대화와 멈춤 흐름(SSE), 3장 멈춤 형식
- [02-architecture.md](02-architecture.md): 2장 서버가 지휘하고 폰이 증권사 일을 한다, 웹에서 대화할 때
- [01-requirements.md](01-requirements.md): FR-08 ~ FR-13, NFR-06 ~ NFR-08
- 참고 코드: `virtual_bank_agent`의 `src/agents/supervisor`, `src/state.py`, `web/bank/main.py` (thread_id, Command resume)

**완료 기록**: 

---

## 4. 투자 AI + 검증 AI

**할 일**
- 분석 대상 종목 목록 (`stocks`, 시총 상위 30개)
- OpenDART 공시 수집 → 조각 나누기 → pgvector 저장 → 검색 (기존 `integrations/opendart.py` 재사용)
- 지표 계산 함수 (`functions/`): PER, 부채비율, 증감률, 변동성, 주문 후 비중
- 투자 AI 제안서, 검증 AI 판정 (structured output), 반박-수정 루프 최대 2번
- 검증 AI 독립성: 제안·근거·출처 ID만 전달, 원문 다시 불러오기, 다른 프롬프트

**완료 조건**: "삼성전자 사도 돼?" → 출처 달린 제안서 → 독립 검증 판정. 지표 계산 테스트 통과

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 4장 분석 그래프, 검증 AI의 독립성
- [05-schemas.md](05-schemas.md): 전체 (Source, Metric, Proposal, Claim, Verification, Check)
- [07-database.md](07-database.md): `stocks`, `proposals`, `verifications`, `disclosures`, `disclosure_chunks`, 공시 검색 SQL
- [01-requirements.md](01-requirements.md): FR-14 ~ FR-21, NFR-09, NFR-10
- [AGENTS.md](../../AGENTS.md): 5장 금융 정보 규칙
- 참고 코드: `aim-ai-agent`의 RAG(06~10), reflection(17), 평가(10-rag-evaluation)
- 정해야 할 것: 공개 시세 데이터 출처 (서버용)

**완료 기록**: 

---

## 5. 주문 그래프

**할 일**
- 주문 값 뽑기·검사 (빠진 값 질문, 후보 고르기, 불가능 안내)
- 정책 검사 (코드): 1회·1일 한도, 종목 비중, 현금, 장 운영 시간
- 처리안 카드, 승인·거절·수정·만료(10분), `execute` 멈춤, 가격 재확인 결과 처리
- 기록 저장 (`record` 노드 한 곳에서만), 중복 주문 방지 (`idempotency_key`)
- 승인 대기 API, 기록 API

**완료 조건**: "SK하이닉스 4주 사줘" → 처리안 → 승인 → `execute` 멈춤 → 가짜 체결 결과로 기록까지. 정책 위반·중복 주문 테스트 통과

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 5장 주문 그래프, 승인·주문 상태 변화, 8장 분기 조건
- [05-schemas.md](05-schemas.md): 6장 PolicyResult, 7장 ApprovalCard, 8장 ExecuteRequest·ExecutionResult
- [06-api-spec.md](06-api-spec.md): 3장 `approval`·`execute` 형식, 4장 폰 주문 실행 과정
- [07-database.md](07-database.md): `policy_checks`, `approvals`, `orders`, `audit_logs`, 오늘 주문 금액 SQL
- [01-requirements.md](01-requirements.md): FR-22 ~ FR-30, FR-35, FR-36
- 참고 코드: `virtual_bank_agent`의 이체 그래프 (값 뽑기 → 검사 → 처리안 → 승인 → 실행 직전 재검사)
- 정해야 할 것: 직접 지시한 주문을 검증 AI가 반려하면 막을지, 경고 후 진행할지

**완료 기록**: 

---

## 6. Flutter 앱 뼈대

**할 일**
- Flutter 설치, `apps/client` 생성
- 로그인·회원가입·성향 설문, 홈, 대화(이벤트 스트림, 멈춤 처리), 처리안 상세, 승인 대기
- 공통: 모의투자 배지, 금액 표시, 상승 빨강·하락 파랑, 출처·기준 시각 표시

**완료 조건**: 앱에서 3·5단계 흐름을 가짜 증권사 데이터로 끝까지 진행

**참고 문서**
- [03-screens.md](03-screens.md): 화면 목록, 흐름, S-01 ~ S-08 와이어프레임, 공통 규칙
- [02-architecture.md](02-architecture.md): 4장 클라이언트 구조
- [06-api-spec.md](06-api-spec.md): 2장 이벤트 스트림, 3장 멈춤 형식
- 개발 환경: 이 PC에 Flutter SDK·Android SDK 아직 없음

**완료 기록**: 

---

## 7. 증권사 연결

**할 일**
- `BrokerAdapter`: KIS 모의 어댑터(주문 검증), KB 어댑터(조회)
- 키 보안 저장소 (`flutter_secure_storage`), 증권사 연결 화면
- `fetch` 처리 (잔고·현재가), `execute` 처리 (가격 재확인 → 생체인증 → 주문 → 시간 초과 시 주문내역 조회)
- 계좌 스냅샷 서버 전송 (계좌번호 제외)

**완료 조건**: **KIS 모의계좌로 실제 주문이 접수·체결**되고 기록됨. KB 잔고·시세 조회 성공

**참고 문서**
- [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md): 9장 증권사 API 사용 방식, KB 약관 반영
- [06-api-spec.md](06-api-spec.md): 3장 `fetch`·`execute`, 4장 폰 주문 실행 과정
- [03-screens.md](03-screens.md): S-04 증권사 연결, S-07 처리안 상세, S-09 주문 결과
- [01-requirements.md](01-requirements.md): FR-05 ~ FR-06c, FR-26 ~ FR-29, NFR-01, NFR-02, NFR-04, NFR-05a
- [AGENTS.md](../../AGENTS.md): 4장 실전투자 관련 규칙 (KB 키로 주문 API 호출 금지)
- 참고 코드: `archive/api-fixture/integrations/kis.py` (KIS 모의 토큰·주문 형식), [KIS open-trading-api](https://github.com/koreainvestment/open-trading-api)
- 필요한 것: KIS 모의투자 키, KB Open API 키 (사용자 발급)

**완료 기록**: 

---

## 8. 웹 · 기록 · 마무리

**할 일**
- Flutter Web 빌드: 주문 버튼 없음, 웹 승인은 폰의 "실행 필요"로
- 기록 화면, 기록 상세 (타임라인), 주문 결과, 설정
- 데모 시나리오 3개, Golden Set 정확도, 검증 AI 오류 주입 20개 탐지율

**완료 조건**: [INVEST_AGENT_PLAN.md](../../INVEST_AGENT_PLAN.md) 5장 "완료 기준" 3가지 충족

**참고 문서**
- [03-screens.md](03-screens.md): 웹 레이아웃, S-08 ~ S-12
- [02-architecture.md](02-architecture.md): 웹에서 대화할 때
- [01-requirements.md](01-requirements.md): FR-30, FR-35, FR-36, NFR-15 ~ NFR-17
- 참고 코드: `virtual_bank_agent`의 `evaluation/` (Golden Set, LangSmith)

**완료 기록**: 
