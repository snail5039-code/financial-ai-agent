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
| 2 | 로그인 · 성향 설문 · 투자 정책 API | 없음 | ✅ |
| 3 | LangGraph 뼈대 · 조회 | Gemini | ✅ |
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

**완료 기록**: 2026-10-04 · 2단계 커밋
- 로그인: 이메일·비밀번호 (소셜 로그인은 6단계 공개 배포 때 다시 정함). 비밀번호는 `hashlib.scrypt`, 토큰은 무작위 값의 sha256만 `sessions`에 저장, 14일 유효, 로그아웃 시 폐기
- 탈퇴는 비밀번호를 다시 확인한다
- 설문 5문항(1~5점) → 합계로 5단계, 손실 문항 점수 + 1 단계를 넘지 않음. 문항과 단계별 기본 한도는 `apps/api/app/functions/profile.py` (2~5단계 한도는 임시값)
- 한도가 성향 기본값보다 높으면 저장하고 경고. 설문을 다시 하면 한도는 내려가기만 한다
- 수수료율 `fee_rate_pct` 추가, 비어 있으면 미입력
- 미룸: 로그인 시도 횟수 제한(6단계 전), 비밀번호 찾기·변경, 이메일 인증
- **2026-10-04 보완**: 조사(증권사 준칙, 연구) 후 5문항 설문을 **퀴즈 8문항**으로 바꾸고 **일반 모드**(퀴즈 안 함: 정보만, 안정형 한도, 올리기 불가)를 추가. 19세 미만 거부, 65세 이상 표시, 유효기간 24개월, 하루 3회, 모순 답 안내. `003_quiz_modes.sql`, `DELETE /api/profile`. 정책은 가입할 때 만들어진다(설문 전 409 없음). 규칙과 근거: [09-investor-profile.md](09-investor-profile.md)

---

## 3. LangGraph 뼈대 · 조회

**할 일**
- 공유 State, supervisor(요청 분류), 조회 그래프
- 멈춤(interrupt) 4종류 처리 틀: `question` / `fetch` / `approval` / `execute`
- 대화 API: `POST /api/chat`, `POST /api/chat/resume` (이벤트 스트림), `GET /api/chat/pending`
- 체크포인트 `PostgresSaver`
- 웹 요청이면 `fetch` 대신 계좌 스냅샷 사용 (`POST/GET /api/snapshot`)
- State에 성향 정보 `mode`(general/custom), `risk_level`, `flags`를 넣는다 ([09-investor-profile.md](09-investor-profile.md) 5장)

**완료 조건**: "잔고 보여줘" → `fetch` 멈춤 → 가짜 잔고로 이어서 답. 서버를 재시작해도 멈춘 업무가 남아 있음

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 1장 전체 그래프, 2장 멈춤 4종류, 3장 조회 그래프, 7장 State, 9장 노드 목록
- [06-api-spec.md](06-api-spec.md): 2장 대화와 멈춤 흐름(SSE), 3장 멈춤 형식
- [02-architecture.md](02-architecture.md): 2장 서버가 지휘하고 폰이 증권사 일을 한다, 웹에서 대화할 때
- [01-requirements.md](01-requirements.md): FR-08 ~ FR-13, NFR-06 ~ NFR-08
- [09-investor-profile.md](09-investor-profile.md): 2장 일반·맞춤 모드, 5장 3단계
- 참고 코드: `virtual_bank_agent`의 `src/agents/supervisor`, `src/state.py`, `web/bank/main.py` (thread_id, Command resume)

**완료 기록**: 2026-10-05 · 3단계 커밋
- 그래프: rewrite → classify → 조회 그래프(extract_query → find_stock → get_market(fetch 또는 스냅샷) → make_answer / read_orders). 분석·주문·결과는 "준비 중" 안내
- LLM(Gemini `gemini-3.6-flash`)은 rewrite·classify·extract_query만. 답 문장·금액·기준 시각은 코드가 만든다
- 멈춤 답은 그래프에 넣기 전에 검사: 지금 멈춘 `interrupt_id`만(409), 형식 엄격·계좌번호 칸 거부(422), fetch는 앱만(403). 폰 조회 실패는 가짜 값 없이 실패 안내
- 체크포인트 `PostgresSaver` (테이블은 LangGraph가 `checkpoint*`로 직접 만듦). DB 주소는 State가 아닌 실행 Context로 넘겨 체크포인트에 남지 않게 함
- 같은 대화에 새 메시지가 오면 멈춘 업무는 버리고 새로 시작한다
- 테스트 110개 (가짜 LLM, 비용 0) + 실제 Gemini 확인 14개 (`uv run pytest -m gemini`, 기본 제외). 실제 서버를 껐다 켜도 멈춘 업무가 남고 이어서 진행되는 것 확인
- **미충족**: 단순 조회 3초(NFR-12). 실제 측정 잔고 6.8초(LLM 2번), "그거" 풀기 포함 9.7초(3번), 한 번에 약 2~3초. 개선 후보: classify와 extract_query를 한 번의 호출로 합치기, rewrite는 가리키는 말("그거" 등)이 있을 때만 부르기, 분류에 더 가벼운 모델(flash-lite)
- 종목 목록(`stocks`)은 4단계에서 채우므로, 지금 실제 서버의 "삼성전자 얼마야?"는 "종목을 찾지 못했어요"로 답한다 (테스트는 테스트용 종목으로 확인)

---

## 4. 투자 AI + 검증 AI

**할 일**
- 분석 대상 종목 목록 (`stocks`, 시총 상위 30개)
- OpenDART 공시 수집 → 조각 나누기 → pgvector 저장 → 검색 (기존 `integrations/opendart.py` 재사용)
- 지표 계산 함수 (`functions/`): PER, 부채비율, 증감률, 변동성, 주문 후 비중
- 투자 AI 제안서, 검증 AI 판정 (structured output), 반박-수정 루프 최대 2번
- 검증 AI 독립성: 제안·근거·출처 ID만 전달, 원문 다시 불러오기, 다른 프롬프트
- **일반 모드 답변 규칙**: 판단("사세요/마세요") 없이 정보·분석만. 프롬프트와 검증 AI 검사 둘 다에
- 표시 값 처리: `no_buy_proposals`면 매수 제안 금지, `vulnerable`이면 불리한 점 먼저, `high_interest_debt`면 빚 먼저 안내, `quiz_missed`면 개념 설명
- 종목 위험등급(국내 주식 2등급, 투자주의·관리종목·해외·레버리지 ETF 1등급)과 성향 비교를 검증 AI `risk_fit`에

**완료 조건**: "삼성전자 사도 돼?" → 출처 달린 제안서 → 독립 검증 판정. 지표 계산 테스트 통과

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 4장 분석 그래프, 검증 AI의 독립성
- [05-schemas.md](05-schemas.md): 전체 (Source, Metric, Proposal, Claim, Verification, Check)
- [07-database.md](07-database.md): `stocks`, `proposals`, `verifications`, `disclosures`, `disclosure_chunks`, 공시 검색 SQL
- [01-requirements.md](01-requirements.md): FR-14 ~ FR-21, NFR-09, NFR-10
- [AGENTS.md](../../AGENTS.md): 5장 금융 정보 규칙
- [09-investor-profile.md](09-investor-profile.md): 4장 표시 값, 5장 4단계
- 참고 코드: `aim-ai-agent`의 RAG(06~10), reflection(17), 평가(10-rag-evaluation)
- 정해야 할 것: 공개 시세 데이터 출처 (서버용), 종목 위험등급 적용 강도 (09 문서 5장)

**완료 기록**: 

---

## 5. 주문 그래프

**할 일**
- 주문 값 뽑기·검사 (빠진 값 질문, 후보 고르기, 불가능 안내)
- 정책 검사 (코드): 1회·1일 한도, 종목 비중, 현금, 장 운영 시간
- 처리안 카드, 승인·거절·수정·만료(10분), `execute` 멈춤, 가격 재확인 결과 처리
- 기록 저장 (`record` 노드 한 곳에서만), 중복 주문 방지 (`idempotency_key`)
- 승인 대기 API, 기록 API
- **행동 코치 규칙** (`functions/`, AI 없이 계산): 잦은 매매(7일 안 3번째), 급등 추격(`chases_hot_stocks`면 한 번 더 확인), 비중 80% 넘으면 분산 안내, 처분효과 안내
- **성향보다 위험한 주문 확인 절차**: 일반 모드이거나 성향보다 위험한 종목을 직접 지시하면 위험을 보여주고 확인을 받은 뒤 진행, `audit_logs`에 기록

**완료 조건**: "SK하이닉스 4주 사줘" → 처리안 → 승인 → `execute` 멈춤 → 가짜 체결 결과로 기록까지. 정책 위반·중복 주문 테스트 통과

**참고 문서**
- [04-graph-design.md](04-graph-design.md): 5장 주문 그래프, 승인·주문 상태 변화, 8장 분기 조건
- [05-schemas.md](05-schemas.md): 6장 PolicyResult, 7장 ApprovalCard, 8장 ExecuteRequest·ExecutionResult
- [06-api-spec.md](06-api-spec.md): 3장 `approval`·`execute` 형식, 4장 폰 주문 실행 과정
- [07-database.md](07-database.md): `policy_checks`, `approvals`, `orders`, `audit_logs`, 오늘 주문 금액 SQL
- [01-requirements.md](01-requirements.md): FR-22 ~ FR-30, FR-35, FR-36
- [09-investor-profile.md](09-investor-profile.md): 5장 5단계 (행동 코치, 확인 절차)
- 참고 코드: `virtual_bank_agent`의 이체 그래프 (값 뽑기 → 검사 → 처리안 → 승인 → 실행 직전 재검사)
- 정해야 할 것: 직접 지시한 주문을 검증 AI가 반려하면 막을지, 경고 후 진행할지

**완료 기록**: 

---

## 6. Flutter 앱 뼈대

**할 일**
- Flutter 설치, `apps/client` 생성
- 로그인·회원가입·성향 퀴즈(가입 후 "퀴즈 / 나중에"), 홈, 대화(이벤트 스트림, 멈춤 처리), 처리안 상세, 승인 대기
- 설정: 모드(일반/맞춤), 퀴즈 다시 하기, 일반 모드로 돌아가기
- 공통: 모의투자 배지, 일반 모드 배지, 금액 표시, 상승 빨강·하락 파랑, 출처·기준 시각 표시

**완료 조건**: 앱에서 3·5단계 흐름을 가짜 증권사 데이터로 끝까지 진행

**참고 문서**
- [03-screens.md](03-screens.md): 화면 목록, 흐름, S-01 ~ S-08 와이어프레임, 공통 규칙
- [09-investor-profile.md](09-investor-profile.md): 3장 퀴즈 문항·보기 키, 5장 6단계
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
