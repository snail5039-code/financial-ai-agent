# AI 판단·검증 수정 기록

모의 자동매매에서 드러난 문제와 AI 판단·검증 로직을 어떻게 고쳤는지 모은다.
나중에 고칠 때 **어디를 보면 되는지(파일·함수)**와 **어떤 값으로 조절하는지(상수·설정)**를 함께 적는다.
최신이 위. 성과 숫자는 [README](../README.md) 1장과 `docs/reports/live-*.md`.

## 조절 값 한눈에

| 값 | 지금 | 위치 | 뜻 |
|---|---|---|---|
| `autoReviewGap` | 30분 | `apps/client/lib/features/auto/auto_trader.dart` | 보유 종목 매도 판단 주기 |
| `autoBuyRetryGap` | 30분 | 같은 파일 | "관찰"·오류로 안 산 종목을 다시 묻는 주기 |
| `autoRescanSlots` | 10·11·12·13·14시, 14:35 | 같은 파일 | 매수 후보 다시 찾기 (서버 `REFRESH_GAP_MINUTES` 60분) |
| `autoDropPct` / `autoRisePct` | −3% / +3% | 같은 파일 | 매입가 대비 이만큼 움직이면 30분 안 기다리고 바로 AI에게 |
| `autoMarketDropPct` | −1.5% | 같은 파일 | 코스피가 이만큼 빠지면 보유 종목 전부 바로 AI에게 |
| `autoStopLossPct` | −7% | 같은 파일 | 손절선. 바로 AI에게 묻는다 (AI 없이 팔지 않음) |
| `autoMaxStockPct` | 35% | 같은 파일 | 한 종목에 쓰는 살 총액 최대 몫 (서버 비중 40% 아래) |
| `autoMaxReviews` | 20 | 같은 파일 | 종목당 하루 매도 판단 횟수 |
| 매수 시간 | 09:05~15:20 | `tick()` | 매도 판단은 15:28까지 |
| `autoApproves()` | 매수=승인만, 매도=조건부까지 | 같은 파일 | 자동으로 승인할 검증 판정 |
| `MAX_ANALYSES_PER_DAY` | 100 | `apps/api/app/agents/analysis.py` | 하루 AI 분석 한도 (Gemini 비용) |
| `MOCK_ORDER_LIMITS` | 끔 | `apps/api/app/config.py` (.env) | 모의에도 금액 한도 적용할지 |
| `AUTO_COLLECT_HOUR` / `MORNING_BRIEF_TIME` | 7 / 08:20 | `apps/api/app/config.py` (.env) | 공시·시세 수집, 아침 브리핑 자동 시각 |

## 10/13 (3일차)

| 드러난 문제 (근거) | 고친 것 | 위치 | 테스트 |
|---|---|---|---|
| 셀트리온 매수 3건이 "숫자를 고쳐라" 같은 **조건부 승인**인데 자동매매가 샀다 | 자동 매수는 "승인"만, 매도는 조건부까지. 검증 AI: 고쳐야 하면 조건부가 아니라 반려 | `auto_trader.dart` `autoApproves`, `llm.py` `VERIFY_PROMPT` | `client_test` 자동 승인 |
| 제안 36건 중 21건이 **뉴스만 출처인 사실 근거** | 코드가 반려 (투자 AI가 고쳐 다시 냄) | `analysis.py` `claim_check` | `test_news_only_fact_claim_fails` |
| 3거래일 묵은 종가로 분석해도 통과 (신선도 경고 0건) | 오늘 시세 없이 평일 2일 넘게 묵으면 warn | `analysis.py` `freshness_checks` | `test_freshness_and_today_data_checks` |
| 보유 판단이 오늘 가격·시장을 안 봄 | 보유 종목 보유·매도 판단에 오늘 자료(quote·intraday·market) 미인용이면 fail | 같은 함수 | 같은 테스트 |
| 반대 근거에 "하락 중"을 적고도 매수 (10/8) | 검증 항목 9 "결론 일관성" | `llm.py` `VERIFY_PROMPT` | (프롬프트, 실제 분석으로 확인) |
| 보유 종목에 "관찰" (모호) | 보유 종목은 보유·매도만 | `suitability.py` `allowed_actions` | `test_sell_and_hold_only_when_holding` |
| −7% 손절만 AI 없이 팔았다 | 손절선도 AI 판단 + 검증 후에만 판다 | `auto_trader.dart` `sellReason`·`_review` | `client_test` 매도 판단 |
| 오를 때 이익을 지킬 기회가 30분 주기뿐 | +3% 급등이면 바로 AI에게 | `sellReason` 'rise', `sellQuestion` | 같은 테스트 |
| 아침 브리핑·공시 수집을 사람이 돌림 | 서버가 매일 07:00 수집, 08:20 브리핑 | `config.py` | 10/13 08:20 자동 동작 확인 |
| 모의에도 1일 한도 → 판 돈으로 못 갈아탐 | 모의는 금액 한도 없음, 살 총액 "주문 가능 금액 전부" (`autoAllCash`) | `orders.py` `policy_check(mock=)`, `auto_trader.dart` | `test_mock_has_no_amount_limits` |
| "관찰"이 한 번 나오면 그날 끝, 후보 다시 찾기 2번뿐 | 사는 판단 30분 주기, 다시 찾기 매시 | `_buy` `settled()`, `autoRescanSlots` | (장중 확인 예정) |
| Gemini 429 오류가 재시도 횟수를 다 씀 | 오류도 30분 뒤 다시 | `_buy` | 14:28 재시도 확인 |
| 후보가 공시 종목 몇 개뿐 | 폰이 KIS 거래대금·상승률 상위를 받아 후보로 | `kis_mock_broker.dart` `movers`, `briefing.py` `pick_candidates(movers)` | `test_refresh_rebuilds...` |
| 하루 새 종목 3개 제한, 매수 15:00 정지 | 개수 제한 없음(종목당 35%), 매수 15:20까지 | `buyRoom`, `tick()` | `client_test` 매수 금액 |
| **남은 과제**: 시초가 급락 때 판 3종목 모두 종가가 더 높았다 (약 7.9만 원) | 장 초반 급락 직후 매도 판단에 반등 근거를 함께 보게 | 미정 | — |

## 10/12 (2일차)

| 드러난 문제 | 고친 것 | 위치 |
|---|---|---|
| AI가 시장 전체를 못 봄 (10/8 −2.62%, 10/12 −3.65% 날 손실) | 폰이 KIS 지수(현재·일별)를 보내고, 서버가 1·5·20거래일 흐름·연속 하락을 계산해 출처 `market:KOSPI`로 | `kis_mock_broker.dart` `market`, `analysis.py` `market_source`, `interrupts.py` `MarketIndex` |
| 시장 급락에도 30분 기다림 | 코스피 −1.5%면 보유 전부 즉시 재판단 | `marketDropped`, `sellReason(marketDrop:)` |
| 매도는 전부 아니면 0 | 투자 AI가 `sell_portion` (전부/절반) | `schemas.py` `ProposalDraft`, `sellQty` |
| 하루 분석 한도 20이 10:44에 차서 3시간 판단 정지, 실패를 "보유"로 기록 | 한도 100, 한도 실패는 따로 기록하고 횟수에서 뺌 | `analysis.py`, `_review` |
| −3% 아래 종목을 11분마다 다시 물음 | 지난번보다 1%p 더 빠졌을 때만 | `sellReason` |
| 팔 종목을 사람이 고름, 정해진 시각에만 | 30분마다 AI가 "곧 떨어질 것 같으면 미리 판다" | `sellQuestion`, `autoReviewGap` |

## 10/8 (1일차)

자세한 원인 분석은 README 1장. 장중 하락 중 매수 → 자동 주문은 투자 AI가 "관찰"로 거절할 수 있게, 뉴스 출처 추가, 매도 나눠 팔기.
