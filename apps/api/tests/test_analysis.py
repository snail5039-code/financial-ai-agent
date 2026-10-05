"""분석 그래프(투자 AI ↔ 검증 AI) 테스트. Gemini는 가짜로 바꿔 끼운다 (비용 0)."""

from datetime import date, timedelta

import psycopg
import pytest

from app.agents import analysis, llm
from app.agents.schemas import ProposalDraft, VerificationDraft
from tests.conftest import LEVEL_4_QUIZ
from tests.test_chat import BALANCE, events_of, first, now_iso, resume

CODE, NAME = "777777", "테스트전자"
LAST_DAY = date(2026, 10, 2)
PRICE_ID = f"price:{CODE}:{LAST_DAY}"


@pytest.fixture(scope="module", autouse=True)
def market_data(migrated):
    """분석 대상 1종목: 종가 25일, 2025 사업보고서 재무, 공시 2건, 본문 조각 2개."""
    vector = str([0.1] * 768)
    with psycopg.connect(migrated) as conn:
        conn.execute("INSERT INTO stocks VALUES (%s, %s, 'KOSPI', true), ('888888', '대상아님', 'KOSPI', false)"
                     " ON CONFLICT DO NOTHING", (CODE, NAME))
        for days_ago in range(25):
            close = 10_000 + days_ago * 10
            conn.execute("INSERT INTO stock_prices VALUES (%s, %s, %s, %s, 1000) ON CONFLICT DO NOTHING",
                         (CODE, LAST_DAY - timedelta(days=days_ago), close, close * 1000))
        for account, amount, prev in [("매출액", 1200, 1000), ("영업이익", 300, 200), ("당기순이익(손실)", 100, 80),
                                      ("부채총계", 400, 380), ("자본총계", 1000, 900)]:
            conn.execute("INSERT INTO financials VALUES (%s, 2025, '11011', 'CFS', %s, %s, %s, 'T1')"
                         " ON CONFLICT DO NOTHING", (CODE, account, amount * 1_000_000, prev * 1_000_000))
        conn.execute("INSERT INTO disclosures VALUES ('T1', %s, '사업보고서 (2025.12)', 'https://dart/T1', '2026-03-10'),"
                     " ('T2', %s, '주요사항보고서', 'https://dart/T2', '2026-09-01') ON CONFLICT DO NOTHING", (CODE, CODE))
        for seq, text in enumerate(["메모리 수요가 늘어 매출이 증가했다.", "환율 변동은 위험 요인이다."]):
            conn.execute("INSERT INTO disclosure_chunks (rcept_no, seq, section, content, embedding)"
                         " VALUES ('T1', %s, 'II. 사업의 내용', %s, %s::vector) ON CONFLICT DO NOTHING", (seq, text, vector))


GOOD_CLAIMS = [
    {"text": "부채비율이 40%다", "type": "calc", "source_ids": ["fin:T1"], "metric_ids": ["debt_ratio"]},
    {"text": "메모리 수요가 늘었다", "type": "fact", "source_ids": ["dart:T1#0"]},
    {"text": "수요가 이어질 수 있다", "type": "inference", "source_ids": []},
]
BAD_CLAIMS = [{"text": "영업이익이 두 배다", "type": "fact", "source_ids": ["dart:FAKE"]}]


def proposal(action="buy", claims=GOOD_CLAIMS) -> ProposalDraft:
    return ProposalDraft(action=action, claims=claims, counter_arguments=["경기 둔화"], risks=["손실 가능"],
                         invalid_if=["영업이익 감소"])


def verdict(value="approve") -> VerificationDraft:
    return VerificationDraft(verdict=value, checks=[], risk_fit="ok", summary="출처와 수치가 맞아요",
                             disagreements=["수요 전망은 불확실"] if value != "approve" else [])


@pytest.fixture
def ai(monkeypatch):
    """invest/verify가 받은 글을 기록하고, 테스트가 정한 답을 차례로 돌려준다."""
    record = {"invest": [], "verify": [], "proposals": [proposal()], "verdicts": [verdict()]}

    def write(context):
        record["invest"].append(context)
        return record["proposals"][min(len(record["invest"]), len(record["proposals"])) - 1]

    def verify(context):
        record["verify"].append(context)
        return record["verdicts"][min(len(record["verify"]), len(record["verdicts"])) - 1]

    monkeypatch.setattr(llm, "understand", lambda q, h: llm.Understood(query=q, intent="analysis",
                                                                        stock_name=q.split(" 사도")[0]))
    monkeypatch.setattr(llm, "embed_query", lambda text: [0.1] * 768)
    monkeypatch.setattr(llm, "write_proposal", write)
    monkeypatch.setattr(llm, "verify_proposal", verify)
    return record


def analyze(client, user, client_kind="app", holdings=None, name=NAME):
    events = events_of(client.post("/api/chat", headers=user["headers"],
                                   json={"text": f"{name} 사도 돼?", "client": client_kind}))
    if first(events, "interrupt") is None:
        return events, None
    fetch = first(events, "interrupt")
    payload = {"balance": {**BALANCE, "holdings": holdings or [], "fetched_at": now_iso()},
               "prices": [{"stock_code": CODE, "price": 10_100, "as_of": now_iso()}]}
    return events, events_of(resume(client, user, events, payload)), fetch


def take_quiz(client, user, **changes):
    assert client.put("/api/profile", headers=user["headers"], json={**LEVEL_4_QUIZ, **changes}).status_code == 200


def saved(migrated, user):
    with psycopg.connect(migrated) as conn:
        rows = conn.execute("SELECT p.action, v.round, v.verdict FROM proposals p JOIN verifications v ON v.proposal_id = p.id"
                            " WHERE p.user_id = %s ORDER BY v.round", (user["id"],)).fetchall()
    return rows


# ---------- 전체 흐름 ----------

def test_analysis_flow_with_sources_and_independent_verification(client, user, ai, migrated) -> None:
    take_quiz(client, user)  # 4단계 적극투자형

    _, answer, fetch = analyze(client, user)

    assert fetch["needs"] == [{"type": "balance"}, {"type": "price", "stock_code": CODE}]
    text = first(answer, "message")["text"]
    assert "검증: 승인" in text and "제안: 매수 검토" in text
    assert "OpenDART 주요 재무 (2025년 사업보고서, 연결)" in text
    assert "부채비율: 40.00%" in text and "PER:" in text
    assert "주문으로 이어가는 기능은 다음 단계" in text and "투자 판단과 책임은 본인에게" in text
    sources_part = text.split("출처 (근거와 지표에 쓴 것)")[1]
    assert sources_part.count("사업보고서 (2025.12) · II. 사업의 내용") == 1  # 인용한 조각
    assert "주요사항보고서" not in sources_part  # 인용하지 않은 공시는 빼고 보여준다
    assert saved(migrated, user) == [("buy", 0, "approve")]

    invest, verify = ai["invest"][0], ai["verify"][0]
    assert "[허용 행동] watch, buy" in invest
    assert PRICE_ID in invest and "dart:T1#0" in invest and "quote:777777" in invest
    # 검증 AI는 투자 AI의 입력(허용 행동, 자료 목록)을 받지 않고, 인용된 출처의 원문만 다시 읽는다
    assert "[허용 행동]" not in verify and "[자료]" not in verify
    assert "자본총계: 이번 기간 1,000,000,000원" in verify
    assert "dart:T1#1" not in verify  # 인용하지 않은 조각은 주지 않는다
    assert "[다시 계산한 지표]" in verify and "[코드 검사]" in verify


def test_progress_shows_both_agents(client, user, ai) -> None:
    _, answer, _ = analyze(client, user)
    steps = [data["step"] for event, data in answer if event == "progress"]
    assert steps.index("invest_agent") < steps.index("verify_agent") < steps.index("record")


# ---------- 성향 규칙 ----------

def test_general_mode_gives_information_only(client, user, ai, migrated) -> None:
    _, answer, _ = analyze(client, user)  # 퀴즈 안 함

    assert "[허용 행동] watch" in ai["invest"][0]
    text = first(answer, "message")["text"]
    assert "일반 모드라 사라·말라 판단은 하지 않고" in text
    assert "주문으로 이어가는" not in text
    assert saved(migrated, user)[0][0] == "watch"  # AI가 buy를 냈어도 코드가 관찰로 바꿨다


def test_level_2_cannot_get_buy_proposal(client, user, ai, migrated) -> None:
    take_quiz(client, user, drop_reaction="sell_some", portfolio_choice="B")  # 4점 → 2단계

    _, answer, _ = analyze(client, user)

    assert "buy" not in ai["invest"][0].split("[허용 행동]")[1].split("\n")[0]
    assert saved(migrated, user)[0][0] == "watch"
    assert "성향 규칙에 따라 '매수 검토' 대신 '관찰'로 바꿨어요" in first(answer, "message")["text"]


def test_borrowed_money_flag_reaches_invest_ai(client, user, ai, migrated) -> None:
    take_quiz(client, user, money_use="borrowed")
    analyze(client, user)
    assert "매수를 제안하지 않는다" in ai["invest"][0]
    assert saved(migrated, user)[0][0] == "watch"


def test_holding_allows_sell(client, user, ai, migrated) -> None:
    take_quiz(client, user)
    ai["proposals"] = [proposal(action="sell")]
    analyze(client, user, holdings=[{"stock_code": CODE, "stock_name": NAME, "qty": 3, "avg_price": 9000}])
    assert "sell" in ai["invest"][0].split("[허용 행동]")[1].split("\n")[0]
    assert saved(migrated, user)[0][0] == "sell"


# ---------- 검증과 반박-수정 ----------

def test_fake_source_is_rejected_even_if_ai_approves_then_user_judgement(client, user, ai, migrated) -> None:
    take_quiz(client, user)
    ai["proposals"] = [proposal(claims=BAD_CLAIMS)]  # 계속 없는 출처를 낸다
    ai["verdicts"] = [verdict("approve")]           # 검증 AI는 속아서 승인한다

    _, answer, _ = analyze(client, user)

    assert len(ai["invest"]) == 3  # 처음 + 수정 2번
    assert "없는 출처 ID: dart:FAKE" in ai["invest"][1]  # 코드 검사의 반박이 투자 AI에게 간다
    assert [row[1:] for row in saved(migrated, user)] == [(0, "reject"), (1, "reject"), (2, "user_judgement")]
    assert "검증: 사용자 판단 필요" in first(answer, "message")["text"]


def test_revision_fixes_and_passes(client, user, ai, migrated) -> None:
    take_quiz(client, user)
    ai["proposals"] = [proposal(claims=BAD_CLAIMS), proposal()]
    ai["verdicts"] = [verdict("approve")]

    analyze(client, user)

    assert [row[1:] for row in saved(migrated, user)] == [(0, "reject"), (1, "approve")]


def test_conditional_verdict_shows_conditions_and_disagreements(client, user, ai) -> None:
    take_quiz(client, user)
    ai["verdicts"] = [VerificationDraft(verdict="conditional", checks=[], risk_fit="warn", summary="조건부",
                                        conditions=["비중 10% 이하로"], disagreements=["수요 전망은 불확실"])]
    text = first(analyze(client, user)[1], "message")["text"]
    assert "검증: 조건부 승인" in text and "조건: 비중 10% 이하로" in text and "의견 차이: 수요 전망은 불확실" in text


# ---------- 그 밖의 경우 ----------

def test_not_target_stock(client, user, ai) -> None:
    events, _ = analyze(client, user, name="대상아님")
    assert "아직 분석 대상이 아니에요" in first(events, "message")["text"]
    assert ai["invest"] == []


def test_daily_limit(client, user, ai, migrated) -> None:
    with psycopg.connect(migrated) as conn:
        thread = conn.execute("INSERT INTO threads (user_id) VALUES (%s) RETURNING id", (user["id"],)).fetchone()[0]
        for _ in range(analysis.MAX_ANALYSES_PER_DAY):
            conn.execute("INSERT INTO proposals (user_id, thread_id, stock_code, action) VALUES (%s, %s, %s, 'watch')",
                         (user["id"], thread, CODE))
    events, _ = analyze(client, user)
    assert "오늘 분석은 20번까지" in first(events, "message")["text"]
    assert ai["invest"] == []


def test_web_analysis_uses_server_data_without_phone(client, user, ai) -> None:
    events, _ = analyze(client, user, client_kind="web")
    assert first(events, "interrupt") is None
    assert "검증: 승인" in first(events, "message")["text"]
    assert "quote:" not in ai["invest"][0] and PRICE_ID in ai["invest"][0]  # 실시간 현재가 없이 전일 종가


def test_phone_error_stops_without_saving(client, user, ai, migrated) -> None:
    events = events_of(client.post("/api/chat", headers=user["headers"], json={"text": f"{NAME} 사도 돼?", "client": "app"}))
    answer = events_of(resume(client, user, events, {"error": "KB 연결 실패"}))
    assert "조회에 실패했어요" in first(answer, "message")["text"]
    assert saved(migrated, user) == [] and ai["invest"] == []


# ---------- 코드 검사 ----------

def test_code_checks_catch_missing_sources_metrics_and_risks() -> None:
    draft = proposal(claims=[
        {"text": "a", "type": "fact"},                                           # 사실인데 출처 없음
        {"text": "b", "type": "calc", "source_ids": ["fin:T1"]},                  # 계산인데 지표 없음
        {"text": "c", "type": "calc", "source_ids": ["fin:T1"], "metric_ids": ["per"]},  # 계산 불가 지표
    ]).model_dump()
    draft["risks"] = []
    metrics_now = [{"metric_id": "per", "value": None}, {"metric_id": "debt_ratio", "value": "40.00"}]
    checks = {c["target"]: c for c in analysis.code_checks(draft, {"fin:T1": {}}, metrics_now, metrics_now)}

    assert checks["claim:0"]["result"] == checks["claim:1"]["result"] == checks["claim:2"]["result"] == "fail"
    assert checks["risks"]["result"] == "fail" and checks["counter_arguments"]["result"] == "pass"
    assert checks["metrics"]["result"] == "pass"


def test_code_checks_catch_changed_metric_values() -> None:
    draft = proposal().model_dump()
    gathered = [{"metric_id": "debt_ratio", "value": "40.00"}]
    recomputed = [{"metric_id": "debt_ratio", "value": "41.00"}]
    checks = {c["target"]: c for c in analysis.code_checks(draft, {"fin:T1": {}, "dart:T1#0": {}}, gathered, recomputed)}
    assert checks["metrics"]["result"] == "fail"
