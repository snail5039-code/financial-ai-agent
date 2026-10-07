"""주문 그래프 테스트: 처리안 → 승인 → 폰 실행 → 기록. Gemini·시계·폰은 가짜로 바꿔 끼운다."""

from datetime import date, datetime, timedelta

import psycopg
import pytest

from app import clock
from app.agents import llm
from app.agents.schemas import ProposalDraft, VerificationDraft
from app.clock import KST
from tests.conftest import LEVEL_4_QUIZ
from tests.test_chat import events_of, first, now_iso

CODE, NAME, PRICE = "555555", "주문전자", 100_000
OPEN = datetime(2026, 10, 6, 10, 0, tzinfo=KST)  # 화요일 10시 (장중)


@pytest.fixture(scope="module", autouse=True)
def order_stock(migrated):
    with psycopg.connect(migrated) as conn:
        conn.execute("INSERT INTO stocks VALUES (%s, %s, 'KOSPI', true) ON CONFLICT DO NOTHING", (CODE, NAME))
        for days_ago in range(10):
            conn.execute("INSERT INTO stock_prices VALUES (%s, %s, %s, %s, 1000) ON CONFLICT DO NOTHING",
                         (CODE, date(2026, 10, 1) - timedelta(days=days_ago), PRICE, PRICE * 1000))


@pytest.fixture
def now(monkeypatch):
    """가짜 시계. 테스트에서 now["value"]를 바꾸면 시간이 흐른 것처럼 된다."""
    holder = {"value": OPEN}
    monkeypatch.setattr(clock, "now", lambda: holder["value"])
    return holder


def understand(query: str, history: list) -> llm.Understood:
    if "체결" in query:
        return llm.Understood(query=query, intent="result", stock_name=NAME if NAME in query else None)
    if "사도 돼" in query:
        return llm.Understood(query=query, intent="analysis", stock_name=NAME)
    side = "sell" if "팔" in query else "buy"
    qty = int(query.split("주 ")[0].split()[-1]) if "주 " in query else None
    return llm.Understood(query=query, intent="order", stock_name=NAME, side=side, qty=qty)


@pytest.fixture
def ai(monkeypatch, now):
    record = {"invest": [], "verify": [], "verdict": "approve", "action": None, "edit": llm.OrderEdit()}

    def write(context):
        record["invest"].append(context)
        action = record["action"] or ("sell" if "매도" in context.split("[사용자 지시 주문]")[-1] else "buy")
        return ProposalDraft(action=action, claims=[{"text": "실적이 좋아 보인다", "type": "opinion"}],
                             counter_arguments=["경기 둔화"], risks=["손실 가능"], invalid_if=["실적 감소"])

    def verify(context):
        record["verify"].append(context)
        return VerificationDraft(verdict=record["verdict"], checks=[], risk_fit="ok", summary="검증 요약")

    monkeypatch.setattr(llm, "understand", understand)
    monkeypatch.setattr(llm, "embed_query", lambda text: [0.1] * 768)
    monkeypatch.setattr(llm, "write_proposal", write)
    monkeypatch.setattr(llm, "verify_proposal", verify)
    monkeypatch.setattr(llm, "parse_order_edit", lambda text, order: record["edit"])
    return record


# ---------- 도우미 ----------

def balance(cash=10_000_000, holdings=None):
    return {"balance": {"cash_krw": cash, "holdings": holdings or [], "fetched_at": now_iso()},
            "prices": [{"stock_code": CODE, "price": PRICE, "as_of": now_iso()}]}


def chat(client, user, text, client_kind="app", thread_id=None):
    body = {"text": text, "client": client_kind, **({"thread_id": thread_id} if thread_id else {})}
    return events_of(client.post("/api/chat", headers=user["headers"], json=body))


def answer(client, user, events, payload, client_kind=None):
    body = {"thread_id": first(events, "done")["thread_id"], "interrupt_id": first(events, "interrupt")["interrupt_id"],
            "payload": payload, **({"client": client_kind} if client_kind else {})}
    return client.post("/api/chat/resume", headers=user["headers"], json=body)


def to_approval(client, user, text="주문전자 4주 사줘", cash=10_000_000, holdings=None):
    events = chat(client, user, text)
    assert first(events, "interrupt")["kind"] == "fetch"
    return events_of(answer(client, user, events, balance(cash, holdings)))


def filled(execute, qty=4, price=PRICE):
    return {"result": {"idempotency_key": execute["request"]["idempotency_key"], "status": "filled",
                       "broker_order_no": "0000123", "filled_qty": qty, "filled_price": price}}


def db(migrated, sql, *params):
    with psycopg.connect(migrated) as conn:
        return conn.execute(sql, params).fetchall()


@pytest.fixture
def custom_user(client, user):
    assert client.put("/api/profile", headers=user["headers"], json=LEVEL_4_QUIZ).status_code == 200
    return user


# ---------- 전체 흐름 (5단계 완료 조건) ----------

def test_order_flow_to_execution_and_record(client, custom_user, ai, migrated) -> None:
    user = custom_user
    approval_events = to_approval(client, user)

    approval = first(approval_events, "interrupt")
    assert approval["kind"] == "approval"
    card = approval["card"]
    assert (card["qty"], card["limit_price"], card["amount"], card["fee"]) == (4, PRICE, 400_000, None)
    assert card["weight_after"] == "4.00" and card["worst_case_loss"] == 40_000
    assert card["confirm_required"] == [] and all(rule["ok"] for rule in card["policy"])
    assert "수수료율 미입력" in approval["text"] and "모의투자" in approval["text"]
    assert "[사용자 지시 주문] 주문전자 4주 100,000원 매수" in ai["invest"][0]

    execute_events = events_of(answer(client, user, approval_events, {"decision": "approve"}))
    execute = first(execute_events, "interrupt")
    assert execute["kind"] == "execute"
    assert execute["request"] == {"approval_id": approval["approval_id"], "stock_code": CODE, "side": "buy", "qty": 4,
                                  "limit_price": PRICE, "approved_price": PRICE, "max_price_drift_pct": 1,
                                  "idempotency_key": approval["approval_id"]}

    done = events_of(answer(client, user, execute_events, filled(execute)))
    assert "주문이 체결됐어요 (모의투자)" in first(done, "message")["text"]
    assert "주문번호 0000123" in first(done, "message")["text"]

    [(status, channel)] = db(migrated, "SELECT status, decided_channel FROM approvals WHERE id = %s", approval["approval_id"])
    assert (status, channel) == ("approved", "app")
    [(order_status, broker, mode, qty)] = db(migrated, "SELECT status, broker, mode, qty FROM orders WHERE approval_id = %s",
                                             approval["approval_id"])
    assert (order_status, broker, mode, qty) == ("filled", "kis_mock", "mock", 4)
    [(directed, saved_qty)] = db(migrated, "SELECT p.user_directed, p.qty FROM proposals p JOIN approvals a"
                                           " ON a.proposal_id = p.id WHERE a.id = %s", approval["approval_id"])
    assert (directed, saved_qty) == (True, 4)
    events = [r[0] for r in db(migrated, "SELECT event FROM audit_logs WHERE user_id = %s ORDER BY id", user["id"])]
    assert events[-3:] == ["approval_requested", "approval_approved", "order_result"]


def test_asks_quantity_when_missing(client, custom_user, ai) -> None:
    events = chat(client, custom_user, "주문전자 사줘")
    question = first(events, "interrupt")
    assert (question["kind"], question["text"]) == ("question", "몇 주 살까요?")
    after = events_of(answer(client, custom_user, events, {"text": "3주"}))
    assert first(after, "interrupt")["kind"] == "fetch"


# ---------- 정책 검사 (처리안 전에 막음) ----------

@pytest.mark.parametrize(
    "text, kwargs, rule_label",
    [
        ("주문전자 30주 사줘", {}, "1회 주문 한도"),                  # 300만 > 적극투자형 1회 200만
        ("주문전자 4주 사줘", {"cash": 100_000}, "현금"),
        ("주문전자 4주 팔아줘", {}, "보유 수량"),                     # 보유 없음
    ],
)
def test_policy_violation_blocks_without_approval(client, custom_user, ai, migrated, text, kwargs, rule_label) -> None:
    events = to_approval(client, custom_user, text, **kwargs)
    message = first(events, "message")["text"]
    assert message.startswith("주문할 수 없어요") and rule_label in message
    assert first(events, "interrupt") is None
    assert db(migrated, "SELECT count(*) FROM approvals a JOIN proposals p ON p.id = a.proposal_id WHERE p.user_id = %s",
              custom_user["id"])[0][0] == 0
    assert db(migrated, "SELECT bool_and(NOT ok) FROM policy_checks c JOIN proposals p ON p.id = c.proposal_id"
                        " WHERE p.user_id = %s", custom_user["id"])[0][0] is True


def test_market_closed_blocks(client, custom_user, ai, now) -> None:
    now["value"] = datetime(2026, 10, 10, 10, 0, tzinfo=KST)  # 토요일
    assert "장 운영 시간" in first(to_approval(client, custom_user), "message")["text"]


# ---------- 승인 · 거절 · 만료 · 수정 ----------

def test_reject_records_and_does_not_order(client, custom_user, ai, migrated) -> None:
    events = to_approval(client, custom_user)
    approval_id = first(events, "interrupt")["approval_id"]
    done = events_of(answer(client, custom_user, events, {"decision": "reject"}))
    assert "주문하지 않았어요" in first(done, "message")["text"]
    assert db(migrated, "SELECT status FROM approvals WHERE id = %s", approval_id)[0][0] == "rejected"
    assert db(migrated, "SELECT count(*) FROM orders WHERE approval_id = %s", approval_id)[0][0] == 0


def test_late_approval_expires(client, custom_user, ai, now, migrated) -> None:
    events = to_approval(client, custom_user)
    approval_id = first(events, "interrupt")["approval_id"]
    now["value"] = OPEN + timedelta(minutes=10, seconds=1)
    done = events_of(answer(client, custom_user, events, {"decision": "approve"}))
    assert "만료" in first(done, "message")["text"]
    assert db(migrated, "SELECT status FROM approvals WHERE id = %s", approval_id)[0][0] == "expired"


def test_edit_quantity_makes_new_card_on_same_approval(client, custom_user, ai, migrated) -> None:
    events = to_approval(client, custom_user)
    approval_id = first(events, "interrupt")["approval_id"]

    edited = events_of(answer(client, custom_user, events, {"decision": "edit", "text": "2주만"}))

    card = first(edited, "interrupt")["card"]
    assert (card["qty"], card["amount"], card["approval_id"]) == (2, 200_000, approval_id)
    assert db(migrated, "SELECT p.qty FROM proposals p JOIN approvals a ON a.proposal_id = p.id WHERE a.id = %s",
              approval_id)[0][0] == 2
    assert len(ai["invest"]) == 1  # 수량만 바꾸면 AI를 다시 부르지 않고 정책만 다시 검사한다


def test_unclear_edit_asks_again_without_executing(client, custom_user, ai) -> None:
    events = to_approval(client, custom_user)
    again = events_of(answer(client, custom_user, events, {"decision": "edit", "text": "음 좀 바꿔줘"}))
    assert first(again, "interrupt")["kind"] == "approval"


def test_price_change_requires_new_approval(client, custom_user, ai, migrated) -> None:
    events = to_approval(client, custom_user)
    execute_events = events_of(answer(client, custom_user, events, {"decision": "approve"}))
    execute = first(execute_events, "interrupt")
    changed = {"result": {"idempotency_key": execute["request"]["idempotency_key"], "status": "price_changed",
                          "current_price": 102_000}}

    reapproval = events_of(answer(client, custom_user, execute_events, changed))

    approval = first(reapproval, "interrupt")
    assert approval["kind"] == "approval" and approval["card"]["limit_price"] == 102_000
    assert db(migrated, "SELECT status FROM approvals WHERE id = %s", approval["approval_id"])[0][0] == "pending"
    execute2 = events_of(answer(client, custom_user, reapproval, {"decision": "approve"}))
    done = events_of(answer(client, custom_user, execute2, filled(first(execute2, "interrupt"), price=102_000)))
    assert "체결" in first(done, "message")["text"]


# ---------- 확인 필요한 위험 ----------

def test_general_mode_order_needs_risk_confirmation(client, user, ai) -> None:
    events = to_approval(client, user, "주문전자 2주 사줘")  # 퀴즈 안 함 → 안정형 한도 (1회 30만)
    assert any("일반 모드" in c for c in first(events, "interrupt")["confirm_required"])

    assert answer(client, user, events, {"decision": "approve"}).status_code == 422
    confirmed = events_of(answer(client, user, events, {"decision": "approve", "confirm_risk": True}))
    assert first(confirmed, "interrupt")["kind"] == "execute"


def test_verifier_rejection_does_not_block_directed_order_but_needs_confirm(client, custom_user, ai) -> None:
    ai["verdict"] = "reject"  # 계속 반려 → 2번 수정 후 사용자 판단 필요
    events = to_approval(client, custom_user)
    approval = first(events, "interrupt")
    assert approval["kind"] == "approval"
    assert len(ai["invest"]) == 3
    assert any("검증 AI 판정이 '사용자 판단 필요'" in c for c in approval["confirm_required"])


# ---------- 웹 승인 → 폰 실행, 중복 방지 ----------

def test_web_approval_waits_for_phone(client, custom_user, ai) -> None:
    user = custom_user
    client.post("/api/snapshot", headers=user["headers"], json=balance()["balance"])
    events = chat(client, user, "주문전자 4주 사줘", "web")
    assert first(events, "interrupt")["kind"] == "approval"  # 웹은 fetch 없이 스냅샷·최근 종가로

    execute_events = events_of(answer(client, user, events, {"decision": "approve"}, "web"))
    execute = first(execute_events, "interrupt")
    assert execute["kind"] == "execute"
    assert answer(client, user, execute_events, filled(execute), "web").status_code == 403  # 웹은 주문 못 함

    pending = client.get("/api/chat/pending", headers=user["headers"]).json()
    assert [p["kind"] for p in pending] == ["execute"]
    done = events_of(answer(client, user, execute_events, filled(execute), "app"))
    assert "체결" in first(done, "message")["text"]


def test_execute_result_for_other_order_is_rejected(client, custom_user, ai) -> None:
    events = to_approval(client, custom_user)
    execute_events = events_of(answer(client, custom_user, events, {"decision": "approve"}))
    wrong = {"result": {"idempotency_key": "other", "status": "failed", "message": "x"}}
    assert answer(client, custom_user, execute_events, wrong).status_code == 422


def test_duplicate_result_is_recorded_once(client, custom_user, ai, migrated) -> None:
    events = to_approval(client, custom_user)
    execute_events = events_of(answer(client, custom_user, events, {"decision": "approve"}))
    execute = first(execute_events, "interrupt")
    key = execute["request"]["idempotency_key"]
    with psycopg.connect(migrated) as conn:  # 같은 주문 결과가 이미 기록돼 있다고 가정
        conn.execute("INSERT INTO orders (approval_id, idempotency_key, broker, mode, side, qty, price, status)"
                     " VALUES (%s, %s, 'kis_mock', 'mock', 'buy', 4, %s, 'accepted')", (key, key, PRICE))

    events_of(answer(client, custom_user, execute_events, filled(execute)))

    assert db(migrated, "SELECT count(*), min(status) FROM orders WHERE idempotency_key = %s", key) == [(1, "accepted")]


# ---------- 분석에서 이어서 주문 ----------

def test_analysis_offers_order_and_continues(client, custom_user, ai) -> None:
    user = custom_user
    events = chat(client, user, "주문전자 사도 돼?")
    analysis_answer = events_of(answer(client, user, events, balance()))
    offer = first(analysis_answer, "interrupt")
    assert offer["kind"] == "question" and offer["text"].endswith("이대로 주문할까요?")

    qty_question = events_of(answer(client, user, analysis_answer, {"choice_id": "yes"}))
    assert first(qty_question, "interrupt")["text"] == "몇 주 살까요?"
    approval = events_of(answer(client, user, qty_question, {"text": "3주"}))

    card = first(approval, "interrupt")["card"]
    assert (card["qty"], card["user_directed"]) == (3, False)
    assert len(ai["invest"]) == 1  # 분석 때 한 번만. 주문으로 이어갈 때 AI를 다시 부르지 않는다
    # 기록에도 주문 수량·가격이 남는다 (분석 때 제안서에는 수량이 없었다)
    latest = client.get("/api/history", headers=user["headers"]).json()[0]
    assert (latest["qty"], latest["limit_price"]) == (3, PRICE)
    assert "3주 매수" in result_text(client, user)


def test_analysis_offer_declined(client, custom_user, ai) -> None:
    events = chat(client, custom_user, "주문전자 사도 돼?")
    offer = events_of(answer(client, custom_user, events, balance()))
    done = events_of(answer(client, custom_user, offer, {"choice_id": "no"}))
    assert first(done, "interrupt") is None and "분석" in first(done, "message")["text"]


# ---------- 행동 코치 · 하루 한도 (실제 주문 기록으로) ----------

def place_filled_order(client, user, text="주문전자 4주 사줘"):
    events = to_approval(client, user, text)
    execute_events = events_of(answer(client, user, events, {"decision": "approve"}))
    events_of(answer(client, user, execute_events, filled(first(execute_events, "interrupt"))))


def test_frequent_trading_warning_and_daily_total(client, custom_user, ai) -> None:
    place_filled_order(client, custom_user)
    place_filled_order(client, custom_user)

    card = first(to_approval(client, custom_user), "interrupt")["card"]
    assert any("최근 7일 동안 이 종목을 2번 거래" in w for w in card["warnings"])
    daily = next(rule for rule in card["policy"] if rule["rule"] == "max_daily")
    assert daily["actual"] == 3 * 400_000  # 오늘 체결 2건 + 이번 주문


def test_daily_limit_blocks_after_orders(client, custom_user, ai, migrated) -> None:
    with psycopg.connect(migrated) as conn:  # 1회 40만, 1일 60만으로 낮춘다 (1일 ≥ 1회)
        conn.execute("UPDATE policies SET max_order_krw = 400000, max_daily_krw = 600000 WHERE user_id = %s",
                     (custom_user["id"],))
    place_filled_order(client, custom_user)                      # 40만
    message = first(to_approval(client, custom_user), "message")["text"]  # 40만 + 40만 > 60만
    assert "1일 주문 한도" in message


# ---------- 승인 대기 · 기록 API ----------

def test_approval_lists_and_history_timeline(client, custom_user, ai) -> None:
    user, headers = custom_user, custom_user["headers"]
    events = to_approval(client, user)
    approval_id = first(events, "interrupt")["approval_id"]
    with psycopg.connect(client.app.state.database_url) as conn:  # 목록은 DB 시계로 만료를 본다 (테스트 시계는 10시 고정)
        conn.execute("UPDATE approvals SET expires_at = now() + interval '10 minutes' WHERE id = %s", (approval_id,))

    waiting = client.get("/api/approvals?status=needs_approval", headers=headers).json()
    assert [a["approval_id"] for a in waiting] == [approval_id]
    assert waiting[0]["card"]["qty"] == 4 and waiting[0]["thread_id"] == first(events, "done")["thread_id"]

    execute_events = events_of(answer(client, user, events, {"decision": "approve"}))
    assert [a["approval_id"] for a in client.get("/api/approvals?status=needs_execution", headers=headers).json()] == [approval_id]

    events_of(answer(client, user, execute_events, filled(first(execute_events, "interrupt"))))
    closed = client.get(f"/api/approvals/{approval_id}", headers=headers).json()
    assert (closed["state"], closed["order_result"]["status"]) == ("closed", "filled")

    [item] = client.get("/api/history", headers=headers).json()
    assert (item["stock_name"], item["verdict"], item["approval_status"], item["order_status"]) == (NAME, "approve", "approved", "filled")
    assert item["policy_ok"] is True
    [proposal] = client.get("/api/agents/proposals", headers=headers).json()
    assert (proposal["proposal_id"], proposal["action"], proposal["verdict"]) == (item["proposal_id"], "buy", "approve")
    assert proposal["claims"][0]["text"] == "실적이 좋아 보인다"
    [verification] = client.get("/api/agents/verifications", headers=headers).json()
    assert (verification["stock_name"], verification["round"], verification["failed_checks"]) == (NAME, 0, 0)
    steps = [step["step"] for step in client.get(f"/api/history/{item['proposal_id']}", headers=headers).json()["timeline"]]
    assert steps[0] == "proposal" and steps[-1] == "order_result"
    assert {"verification", "policy_check", "approval_requested", "approval_approved"} <= set(steps)


def test_expired_approval_shows_as_closed(client, custom_user, ai, now) -> None:
    events = to_approval(client, custom_user)
    approval_id = first(events, "interrupt")["approval_id"]
    with psycopg.connect(client.app.state.database_url) as conn:  # 만료 시각이 지난 것처럼
        conn.execute("UPDATE approvals SET expires_at = now() - interval '1 second' WHERE id = %s", (approval_id,))
    detail = client.get(f"/api/approvals/{approval_id}", headers=custom_user["headers"]).json()
    assert (detail["state"], detail["status"]) == ("closed", "expired")


def test_other_users_cannot_see_approvals_or_history(client, custom_user, ai) -> None:
    events = to_approval(client, custom_user)
    approval_id = first(events, "interrupt")["approval_id"]
    proposal_id = client.get("/api/history", headers=custom_user["headers"]).json()[0]["proposal_id"]
    email = "other-" + custom_user["email"]
    client.post("/api/auth/signup", json={"email": email, "password": "pw-other-1", "agreed_terms": True})
    other = {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": email, "password": "pw-other-1"}).json()["token"]}
    assert client.get(f"/api/approvals/{approval_id}", headers=other).status_code == 404
    assert client.get(f"/api/history/{proposal_id}", headers=other).status_code == 404
    assert client.get("/api/approvals", headers=other).json() == []
    assert client.get("/api/history", headers=other).json() == []
    assert client.get("/api/agents/proposals", headers=other).json() == []
    assert client.get("/api/agents/verifications", headers=other).json() == []


# ---------- 결과 확인 ("아까 주문 체결됐어?") ----------

def result_text(client, user, text="아까 주문 체결됐어?"):
    return first(chat(client, user, text), "message")["text"]


def test_result_after_fill(client, custom_user, ai) -> None:
    place_filled_order(client, custom_user)
    text = result_text(client, custom_user, "주문전자 체결됐어?")
    assert "주문전자(555555) 4주 매수" in text and "체결됐어요" in text
    assert "체결 4주 × 100,000원" in text and "주문번호 0000123" in text and "기준" in text


def test_result_while_waiting_and_after_web_approval(client, custom_user, ai) -> None:
    events = to_approval(client, custom_user)
    assert "승인을 기다리고 있어요" in result_text(client, custom_user)
    # 새 메시지를 보내면 멈춘 업무는 버려지므로 다른 대화에서 웹 승인 흐름을 만든다
    events = to_approval(client, custom_user)
    events_of(answer(client, custom_user, events, {"decision": "approve"}, client_kind="web"))
    assert "웹에서 승인했지만 아직 폰에서 실행하지 않았어요" in result_text(client, custom_user)


def test_result_for_blocked_and_rejected(client, custom_user, ai) -> None:
    to_approval(client, custom_user, "주문전자 4주 사줘", cash=100)  # 현금 부족
    assert "정책 검사에 걸려 주문하지 않았어요" in result_text(client, custom_user)
    events = to_approval(client, custom_user)
    events_of(answer(client, custom_user, events, {"decision": "reject"}))
    assert "거절했어요" in result_text(client, custom_user)


def test_result_is_only_mine(client, custom_user, ai) -> None:
    place_filled_order(client, custom_user)
    email = "other-" + custom_user["email"]
    client.post("/api/auth/signup", json={"email": email, "password": "pw-other-1", "agreed_terms": True})
    token = client.post("/api/auth/login", json={"email": email, "password": "pw-other-1"}).json()["token"]
    assert result_text(client, {"headers": {"Authorization": f"Bearer {token}"}}) == "주문 기록이 없어요."


# ---------- 체결 갱신 (접수 → 체결) ----------

def place_accepted_order(client, user):
    events = to_approval(client, user)
    execute_events = events_of(answer(client, user, events, {"decision": "approve"}))
    key = first(execute_events, "interrupt")["request"]["idempotency_key"]
    accepted = {"result": {"idempotency_key": key, "status": "accepted", "broker_order_no": "0000777", "filled_qty": 0}}
    events_of(answer(client, user, execute_events, accepted))
    return key


def test_fill_sync_updates_accepted_order(client, custom_user, ai) -> None:
    headers = custom_user["headers"]
    key = place_accepted_order(client, custom_user)
    assert "접수됐어요. 아직 체결되지 않았어요" in result_text(client, custom_user)

    [open_order] = client.get("/api/orders/open", headers=headers).json()
    assert open_order == {"idempotency_key": key, "stock_code": CODE, "broker_order_no": "0000777", "side": "buy",
                          "qty": 4, "filled_qty": 0}

    def post(qty, price=99_500):
        fill = {"idempotency_key": key, "filled_qty": qty, **({"filled_price": price} if price else {})}
        return client.post("/api/orders/fills", headers=headers, json={"fills": [fill]})

    assert post(1, None).status_code == 422                       # 체결 수량이 있으면 가격도
    assert post(1).json()["updated"][0]["status"] == "partially_filled"
    assert post(0, None).json()["updated"] == []                   # 체결 수량은 줄어들 수 없다
    assert post(5).json()["updated"] == []                         # 주문 수량을 넘을 수 없다
    assert post(4).json()["updated"][0]["status"] == "filled"
    assert client.get("/api/orders/open", headers=headers).json() == []
    assert post(4).json()["updated"] == []                         # 끝난 주문은 다시 바꾸지 않는다

    text = result_text(client, custom_user)
    assert "체결됐어요" in text and "체결 4주 × 99,500원" in text and "증권사에서 확인한 기록" in text


def test_fill_sync_ignores_other_users_orders(client, custom_user, ai) -> None:
    key = place_accepted_order(client, custom_user)
    email = "fill-" + custom_user["email"]
    client.post("/api/auth/signup", json={"email": email, "password": "pw-other-1", "agreed_terms": True})
    other = {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": email, "password": "pw-other-1"}).json()["token"]}
    assert client.get("/api/orders/open", headers=other).json() == []
    fill = {"idempotency_key": key, "filled_qty": 4, "filled_price": PRICE}
    assert client.post("/api/orders/fills", headers=other, json={"fills": [fill]}).json()["updated"] == []


def test_today_rings(client, custom_user, ai, migrated) -> None:
    headers = custom_user["headers"]
    place_filled_order(client, custom_user)
    today = client.get("/api/orders/today", headers=headers).json()
    [(limit,)] = db(migrated, "SELECT max_daily_krw FROM policies WHERE user_id = %s", custom_user["id"])
    assert today == {"daily_used_krw": 400_000, "daily_limit_krw": limit, "clean_days": 0}  # 오늘 가입
    with psycopg.connect(migrated) as conn:  # 사흘 전에 가입했고 그 뒤로 규칙에 걸린 적 없음
        conn.execute("UPDATE users SET created_at = now() - interval '3 days' WHERE id = %s", (custom_user["id"],))
    assert client.get("/api/orders/today", headers=headers).json()["clean_days"] == 3
    with psycopg.connect(migrated) as conn:  # 1회 한도를 낮춰서 오늘 규칙에 걸리게
        conn.execute("UPDATE policies SET max_order_krw = 100000 WHERE user_id = %s", (custom_user["id"],))
    to_approval(client, custom_user)
    assert client.get("/api/orders/today", headers=headers).json()["clean_days"] == 0
