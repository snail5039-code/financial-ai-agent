# 진행 상황 · 이어서 하기

마지막 갱신: 2026-10-06 · 다음 할 일: **7단계 증권사 연결 (KIS 모의)**

새 대화(세션)에서 이어서 작업할 때 이 문서부터 읽는다. 단계별 상세 기록은 [08-dev-order.md](08-dev-order.md)의 "완료 기록"에 있다.

## 1. 새 세션에서 처음 할 일

1. [AGENTS.md](../../AGENTS.md)(작업 규칙)와 이 문서를 읽는다
2. [08-dev-order.md](08-dev-order.md)의 **7단계** 할 일과 참고 문서를 읽는다
3. 계획을 사용자에게 보여주고 동의를 받은 뒤 구현한다 (AGENTS.md 2장)
4. 푸시·외부 전송·설치·약관 동의·비용 생기는 일은 **매번** 먼저 묻는다

## 2. 단계별 상태

| 단계 | 내용 | 상태 | 커밋 |
|---|---|---|---|
| 1 | 정리(archive) + 서버 뼈대(DB, 마이그레이션) | ✅ | `f627bd3`, `c8d86b4` |
| 2 | 로그인 · 성향 퀴즈(8문항) · 일반/맞춤 모드 · 투자 정책 API | ✅ | `5dd17cc`, `d24a5b8` |
| 3 | LangGraph 대화 그래프 · 조회(잔고·시세·주문내역) · SSE · 체크포인트 | ✅ | `66345dc`, `b67a0af`(속도 1.4~1.8초) |
| 4 | 투자 AI ↔ 검증 AI 분석 · 30종목 데이터 수집 · 지표 | ✅ | `6ef5516`, `c3a6640`, `29b817d`, `0461808`, `91a391c` |
| 5 | 주문 그래프: 처리안 → 승인 → 폰 실행(execute) → 기록, 승인·기록 API | ✅ | `70ed1e3` |
| — | 개발 환경: Flutter, Android SDK, 에뮬레이터 설치 | ✅ | `51832f9` |
| 6 | Flutter 앱 뼈대: 화면 8종, 대화·멈춤 처리, 가짜 증권사 | ✅ | `2623ba3` + 마무리 |
| 7 | **증권사 연결 (KIS 모의 주문, KB 조회)** | ⬜ 다음 | |
| 8 | 웹 · 기록 화면 · 마무리 · 평가 | ⬜ | |

서버 테스트 218개 통과, Flutter 테스트 9개(`apps/client`에서 `flutter test`) 통과 + 실제 Gemini 확인 11개(`-m gemini`).

## 3. 지금 서버가 할 수 있는 것 (`apps/api`)

| 기능 | API · 코드 |
|---|---|
| 가입·로그인(토큰 14일)·로그아웃·탈퇴(비밀번호 재확인) | `routers/auth.py` |
| 성향 퀴즈 8문항, 일반 모드(퀴즈 안 함: 정보만, 안정형 한도), 투자 정책·수수료율 | `routers/policy.py`, `functions/profile.py` ([09-investor-profile.md](09-investor-profile.md)) |
| 대화: `POST /api/chat`, `POST /api/chat/resume`(SSE), `GET /api/chat/pending` | `routers/chat.py`, `agents/graph.py` |
| 조회: 잔고·시세(앱은 fetch 멈춤, 웹은 스냅샷·최근 종가)·오늘 주문 내역 | `agents/query.py` |
| 분석: "삼성전자 사도 돼?" → 투자 AI 제안서(출처 ID) → 코드 검사 + 검증 AI(원문 다시 읽기) → 반박-수정 최대 2번 | `agents/analysis.py` |
| 주문: "SK하이닉스 4주 사줘" → 정책 검사(코드) → 처리안(approval) → execute(앱만) → 기록. 분석에서 "이대로 주문할까요?"로도 이어짐 | `agents/order.py`, `functions/orders.py` |
| 승인 대기·기록 | `GET /api/approvals?status=`, `/api/approvals/{id}`, `/api/history`, `/api/history/{id}` |
| 계좌 스냅샷(폰이 올림, 계좌번호 없음) | `routers/snapshot.py` |
| 데이터 수집: 코스피 시총 상위 30종목(우선주 제외) 종가·재무·공시 본문 임베딩, 서버가 매일 15시 자동 | `app/collect.py` |

앱(`apps/client`, Flutter): 로그인·퀴즈·홈·대화·처리안 상세·승인 대기·설정. 증권사는 아직 가짜(`broker/fake_broker.dart`) → 7단계에서 KIS 모의로 바꾼다.

API 형식: [06-api-spec.md](06-api-spec.md). 멈춤 4종류 `question` / `fetch` / `approval` / `execute`의 형식은 06 문서 3장과 `agents/interrupts.py`.

## 4. 실행 방법

```bash
docker start invest-db
```
(재부팅 후 Docker Desktop이 꺼져 있으면 먼저 켠다: `C:\Users\snail\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe`)

```bash
uv --directory apps/api run python -m app.migrate
```

```bash
uv --directory apps/api run uvicorn app.main:app --port 8000
```

```bash
uv --directory apps/api run pytest
```

앱 (Android 에뮬레이터, 서버는 `10.0.2.2:8000`으로 접속):

```bash
cd apps/client && flutter run -d emulator-5554 --no-enable-impeller
```

웹 (`.claude/launch.json`의 `web`, http://localhost:5000): `.env`에 `CORS_ORIGINS=http://localhost:5000` 필요

- 비밀값은 `apps/api/.env`에만 있다 (git 제외): `DATABASE_URL`, `GEMINI_API_KEY`, `OPENDART_API_KEY`, `DATA_GO_KR_API_KEY`. 값을 출력하지 않는다
- Flutter: `C:\Users\snail\dev\flutter` (사용자 PATH 등록됨, 새 터미널부터 `flutter` 사용 가능)
- Android SDK: `C:\Users\snail\dev\android` (`ANDROID_HOME`), 가상 폰 `invest_phone`:

```bash
%ANDROID_HOME%\emulator\emulator.exe -avd invest_phone
```

## 5. 주요 결정 (이미 정함, 다시 묻지 않음)

- B 구조: 증권사 키·주문은 폰에만. 서버는 키를 받지 않는다. 기본 모의투자 (KIS 모의, `broker=kis_mock`, `mode=mock`)
- Gemini `gemini-3.6-flash`, 요청 이해는 한 번 호출(`understand`, `thinking_level=minimal`), 투자·검증 AI는 `low`
- 성향: 퀴즈 8문항, 일반 모드는 정보만·안정형 한도·올리기 불가, 퀴즈 하루 3회·유효 24개월, 19세 미만 거부
- 매수 제안 범위: 2등급(국내 주식)은 위험중립형(3단계)부터 (완화안). 변동성 규칙은 60일 변동성의 **분석 대상 안 순위** (위험중립형 하위 1/3, 적극투자형 상위 20% 제외, 공격투자형 제한 없음)
- 직접 지시한 주문은 검증 AI가 반려해도 막지 않고 "확인 필요"(`confirm_risk`)로 확인받는다. 정책 위반은 항상 막는다
- 주문: 분석 대상 30종목만, 지정가(없으면 현재가), 장 시간 평일 09:00~15:30, 승인 만료 10분, 가격 변동 1%, 매도 세금 0.20%
- 시세 출처: 금융위원회_주식시세정보 **V2 주소** (`GetStockSecuritiesInfoService_V2/getStockPriceInfo_V2`). 예전 주소는 새 키를 거부함

## 6. 알려진 한계 · 남은 일

- 공휴일 휴장 판별 없음 (주말만 거름)
- 투자주의·관리종목(1등급) 데이터 없음 → 모두 2등급
- 계좌 크기 비례 한도 (나중에)
- "아까 주문 체결됐어?"(결과 그래프) 미구현 → "준비 중" 안내
- 순이익은 비지배지분 포함, 시세는 하루 늦은 값
- 분석 대상 확장 계획: [10-coverage-expansion.md](10-coverage-expansion.md)
- 로그인 시도 횟수 제한 없음 (공개 배포 전에 추가)
- ERD·S-03 퀴즈 화면 그림이 옛날 기준 (원본 `.mmd`는 최신)
- 키 3개가 이전 대화 기록에 남음 → 공개 배포 전 재발급 권장

## 7. 작업할 때 주의 (겪은 것)

- 재부팅하면 Docker Desktop이 꺼져 있다 → DB 연결 실패·테스트 멈춤. 먼저 켠다
- Windows Git Bash의 `curl`은 한글 JSON 본문을 깨뜨린다 → API 수동 확인은 Python `httpx` 스크립트로
- Python heredoc으로 파일을 고칠 때 `"\n"`, `\U`가 실제 줄바꿈·이스케이프로 바뀌는 문제가 있었다 → 파일 수정은 Edit 도구 사용
- 주문 장 시간 검사는 실제 시계를 쓴다 → 장이 닫힌 시간에 실제 확인할 때는 테스트처럼 `app.clock.now`를 고정한다
- 에뮬레이터에서 Impeller(기본 그래픽)로 그리면 탭을 바꿔도 본문이 이전 화면으로 남는 현상이 있다 (앱 문제 아님). `--no-enable-impeller`로 실행하거나, 설치한 앱은 `adb shell am start -n com.investagent.invest_client/.MainActivity --ez enable-impeller false`
- 에뮬레이터 화면 조작은 `adb shell input tap/text` (한글 입력은 안 됨 → 추천 질문 칩을 누른다)
- 장이 닫힌 시간에 주문 흐름을 확인하려면 `.env`에 `MARKET_CLOCK=10:00` (운영에서는 비운다)
- 테스트는 `invest_test` DB를 새로 만들어 쓴다 (개발 DB `invest`는 안 건드림). Gemini는 가짜로 바꿔 끼워 비용 0
