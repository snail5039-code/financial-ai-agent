"""대화 그래프와 대화 API 테스트. Gemini는 부르지 않고 규칙으로 답하는 가짜로 바꿔 끼운다 (비용 0)."""

import json
from datetime import datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.agents import llm
from app.agents.graph import NOT_READY_MESSAGE
from app.agents.query import SYNC_MESSAGE, WEB_PRICE_MESSAGE
from app.clock import KST
from app.main import create_app


# ---------- 가짜 LLM ----------

def fake_classify(query: str) -> str:
    if "사도 돼" in query:
        return "analysis"
    if "사줘" in query or "팔아" in query:
        return "order"
    if "체결" in query:
        return "result"
    if any(word in query for word in ("잔고", "얼마", "내역", "시세")):
        return "query"
    return "other"


def fake_extract(query: str) -> llm.QueryTarget:
    if "잔고" in query:
        return llm.QueryTarget(kind="balance")
    if "내역" in query:
        return llm.QueryTarget(kind="orders")
    name = query.split(" 얼마")[0].strip() if " 얼마" in query else None
    return llm.QueryTarget(kind="price", stock_name=name)


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    calls = {"rewrite": []}

    def fake_rewrite(query: str, history: list) -> str:
        calls["rewrite"].append(history)
        return query

    monkeypatch.setattr(llm, "classify_intent", fake_classify)
    monkeypatch.setattr(llm, "extract_query", fake_extract)
    monkeypatch.setattr(llm, "rewrite_query", fake_rewrite)
    return calls


@pytest.fixture(scope="module", autouse=True)
def stocks(migrated):
    # 테스트용 종목 (실제 종목 목록은 4단계에서 채운다)
    with psycopg.connect(migrated) as conn:
        conn.execute(
            "INSERT INTO stocks (code, name, market) VALUES"
            " ('005930', '삼성전자', 'KOSPI'), ('005935', '삼성전자우', 'KOSPI'), ('000660', 'SK하이닉스', 'KOSPI')"
            " ON CONFLICT DO NOTHING"
        )


# ---------- 도우미 ----------

def now_iso(minutes_ago: int = 0) -> str:
    return (datetime.now(KST) - timedelta(minutes=minutes_ago)).isoformat()


BALANCE = {
    "cash_krw": 1_500_000,
    "holdings": [{"stock_code": "005930", "stock_name": "삼성전자", "qty": 20, "avg_price": 68_000}],
}


def events_of(response) -> list[tuple[str, dict]]:
    assert response.status_code == 200, response.text
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def first(events, name: str) -> dict | None:
    return next((data for event, data in events if event == name), None)


def chat(client, user, text, client_kind="app", thread_id=None):
    body = {"text": text, "client": client_kind, **({"thread_id": thread_id} if thread_id else {})}
    return events_of(client.post("/api/chat", headers=user["headers"], json=body))


def resume(client, user, events, payload):
    return client.post("/api/chat/resume", headers=user["headers"], json={
        "thread_id": first(events, "done")["thread_id"],
        "interrupt_id": first(events, "interrupt")["interrupt_id"],
        "payload": payload,
    })


# ---------- 잔고: fetch 멈춤 → 이어서 답 (3단계 완료 조건) ----------

def test_balance_pauses_for_phone_then_answers(client, user, migrated) -> None:
    events = chat(client, user, "잔고 보여줘")

    assert [e for e, _ in events][-2:] == ["interrupt", "done"]
    assert [e for e, _ in events].count("interrupt") == 1
    assert first(events, "progress") is not None
    fetch = first(events, "interrupt")
    assert fetch["kind"] == "fetch"
    assert fetch["needs"] == [{"type": "balance"}]

    answer = events_of(resume(client, user, events, {"balance": {**BALANCE, "fetched_at": now_iso()}}))

    text = first(answer, "message")["text"]
    assert "현금 1,500,000원" in text
    assert "삼성전자(005930) 20주, 평균 매입가 68,000원" in text
    assert "앱 실시간 조회" in text and "기준" in text
    with psycopg.connect(migrated) as conn:
        roles = conn.execute(
            "SELECT role FROM messages WHERE thread_id = %s ORDER BY created_at", (first(events, "done")["thread_id"],)
        ).fetchall()
    assert [r[0] for r in roles] == ["user", "assistant"]


def test_pending_survives_server_restart(client, user, migrated) -> None:
    events = chat(client, user, "잔고 보여줘")

    # 서버를 새로 띄운다 (그래프·연결을 새로 만들고, 상태는 DB 체크포인트에서 읽음)
    with TestClient(create_app(migrated)) as restarted:
        pending = restarted.get("/api/chat/pending", headers=user["headers"]).json()
        assert [p["interrupt_id"] for p in pending] == [first(events, "interrupt")["interrupt_id"]]
        assert pending[0]["kind"] == "fetch"

        answer = events_of(resume(restarted, user, events, {"balance": {**BALANCE, "fetched_at": now_iso()}}))
        assert "현금 1,500,000원" in first(answer, "message")["text"]
        assert restarted.get("/api/chat/pending", headers=user["headers"]).json() == []


# ---------- 멈춤 답 검사 ----------

def test_resume_with_wrong_or_used_interrupt_id_is_409(client, user) -> None:
    events = chat(client, user, "잔고 보여줘")
    body = {"thread_id": first(events, "done")["thread_id"], "interrupt_id": "nope",
            "payload": {"balance": {**BALANCE, "fetched_at": now_iso()}}}
    assert client.post("/api/chat/resume", headers=user["headers"], json=body).status_code == 409

    payload = {"balance": {**BALANCE, "fetched_at": now_iso()}}
    assert resume(client, user, events, payload).status_code == 200
    assert resume(client, user, events, payload).status_code == 409  # 이미 처리된 멈춤


@pytest.mark.parametrize(
    "payload",
    [
        {"balance": {**BALANCE, "account_no": "12345678-01"}},  # 계좌번호 칸은 받지 않는다 (NFR-01)
        {"balance": {**BALANCE, "holdings": [{**BALANCE["holdings"][0], "account_no": "1"}]}},
        {"balance": {**BALANCE, "cash_krw": -1}},
        {"balance": {**BALANCE, "fetched_at": "2099-01-01T00:00:00+09:00"}},  # 미래 시각
        {"balance": {**BALANCE, "fetched_at": "2026-10-05T10:00:00"}},       # 시간대 없음
        {},                                                                  # 결과도 실패 사유도 없음
        {"balance": BALANCE, "error": "x"},                                  # 둘 다
    ],
)
def test_bad_fetch_answer_is_rejected_and_stays_paused(client, user, payload: dict) -> None:
    if "balance" in payload and "fetched_at" not in payload["balance"]:
        payload = {**payload, "balance": {**payload["balance"], "fetched_at": now_iso()}}
    events = chat(client, user, "잔고 보여줘")

    assert resume(client, user, events, payload).status_code == 422

    pending = client.get("/api/chat/pending", headers=user["headers"]).json()
    assert first(events, "interrupt")["interrupt_id"] in [p["interrupt_id"] for p in pending]


def test_phone_error_is_reported_honestly(client, user) -> None:
    events = chat(client, user, "잔고 보여줘")
    answer = events_of(resume(client, user, events, {"error": "KB 연결 실패"}))
    text = first(answer, "message")["text"]
    assert "조회에 실패했어요" in text and "KB 연결 실패" in text
    assert "원" not in text  # 가짜 숫자를 만들지 않는다


def test_other_users_thread_is_404(client, user) -> None:
    events = chat(client, user, "잔고 보여줘")
    thread_id = first(events, "done")["thread_id"]
    email = "other-" + user["email"]
    client.post("/api/auth/signup", json={"email": email, "password": "pw-other-1", "agreed_terms": True})
    token = client.post("/api/auth/login", json={"email": email, "password": "pw-other-1"}).json()["token"]
    other = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/chat", headers=other, json={"text": "잔고", "client": "app", "thread_id": thread_id}).status_code == 404
    body = {"thread_id": thread_id, "interrupt_id": first(events, "interrupt")["interrupt_id"], "payload": {"error": "x"}}
    assert client.post("/api/chat/resume", headers=other, json=body).status_code == 404
    assert client.get("/api/chat/pending", headers=other).json() == []


def test_chat_needs_login(client) -> None:
    assert client.post("/api/chat", json={"text": "잔고", "client": "app"}).status_code == 401


# ---------- 웹: fetch 대신 스냅샷 ----------

def test_web_balance_uses_recent_snapshot(client, user) -> None:
    assert first(chat(client, user, "잔고 보여줘", "web"), "message")["text"] == SYNC_MESSAGE  # 스냅샷 없음

    snapshot = {**BALANCE, "fetched_at": now_iso(minutes_ago=5)}
    assert client.post("/api/snapshot", headers=user["headers"], json=snapshot).status_code == 204

    events = chat(client, user, "잔고 보여줘", "web")
    assert first(events, "interrupt") is None  # 웹은 폰에 부탁하지 않는다
    text = first(events, "message")["text"]
    assert "현금 1,500,000원" in text and "폰 동기화" in text


def test_web_old_snapshot_asks_to_sync(client, user) -> None:
    client.post("/api/snapshot", headers=user["headers"], json={**BALANCE, "fetched_at": now_iso(minutes_ago=31)})
    assert first(chat(client, user, "잔고 보여줘", "web"), "message")["text"] == SYNC_MESSAGE


def test_web_price_is_not_available(client, user) -> None:
    assert first(chat(client, user, "삼성전자 얼마야?", "web"), "message")["text"] == WEB_PRICE_MESSAGE


# ---------- 시세: 종목 찾기 → fetch ----------

def test_price_for_exact_stock(client, user) -> None:
    events = chat(client, user, "삼성전자 얼마야?")
    assert first(events, "interrupt")["needs"] == [{"type": "price", "stock_code": "005930"}]

    answer = events_of(resume(client, user, events, {"prices": [{"stock_code": "005930", "price": 71_200, "as_of": now_iso()}]}))
    assert "삼성전자(005930) 현재가 71,200원" in first(answer, "message")["text"]


def test_price_asks_to_pick_among_candidates(client, user) -> None:
    events = chat(client, user, "삼성 얼마야?")
    question = first(events, "interrupt")
    assert question["kind"] == "question"
    assert {c["id"] for c in question["choices"]} == {"005930", "005935"}

    events2 = events_of(resume(client, user, events, {"choice_id": "005935"}))
    fetch = first(events2, "interrupt")
    assert fetch["needs"] == [{"type": "price", "stock_code": "005935"}]


def test_price_for_unknown_stock(client, user) -> None:
    text = first(chat(client, user, "없는회사 얼마야?"), "message")["text"]
    assert "찾지 못했어요" in text


def test_price_missing_in_phone_answer(client, user) -> None:
    events = chat(client, user, "삼성전자 얼마야?")
    answer = events_of(resume(client, user, events, {"prices": [{"stock_code": "000660", "price": 1, "as_of": now_iso()}]}))
    assert "시세가 없어요" in first(answer, "message")["text"]


# ---------- 그 밖의 요청 ----------

def test_orders_today_empty(client, user) -> None:
    assert first(chat(client, user, "오늘 주문 내역 보여줘"), "message")["text"] == "오늘 주문 내역이 없어요."


@pytest.mark.parametrize("text", ["SK하이닉스 4주 사줘", "삼성전자 사도 돼?", "아까 주문 체결됐어?"])
def test_not_ready_intents(client, user, text: str) -> None:
    assert first(chat(client, user, text), "message")["text"] == NOT_READY_MESSAGE


def test_new_message_replaces_pending_task(client, user) -> None:
    events = chat(client, user, "잔고 보여줘")
    thread_id = first(events, "done")["thread_id"]

    second = chat(client, user, "오늘 주문 내역 보여줘", thread_id=thread_id)

    assert first(second, "message")["text"] == "오늘 주문 내역이 없어요."
    assert resume(client, user, events, {"error": "x"}).status_code == 409  # 버려진 멈춤


def test_history_is_passed_to_rewrite(client, user, fake_llm) -> None:
    events = chat(client, user, "오늘 주문 내역 보여줘")
    chat(client, user, "그거 다시", thread_id=first(events, "done")["thread_id"])
    assert fake_llm["rewrite"][-1] == [{"request": "오늘 주문 내역 보여줘", "answer": "오늘 주문 내역이 없어요."}]


def test_llm_failure_is_reported(client, user, monkeypatch) -> None:
    def broken(query):
        raise llm.LLMUnavailable("quota")

    monkeypatch.setattr(llm, "classify_intent", broken)
    events = chat(client, user, "잔고 보여줘")
    assert "AI 응답을 받지 못했어요" in first(events, "error")["detail"]
    assert [e for e, _ in events][-1] == "done"


# ---------- 스냅샷 API ----------

def test_snapshot_api(client, user) -> None:
    assert client.get("/api/snapshot", headers=user["headers"]).status_code == 404
    snapshot = {**BALANCE, "fetched_at": now_iso()}
    assert client.post("/api/snapshot", headers=user["headers"], json=snapshot).status_code == 204
    assert client.get("/api/snapshot", headers=user["headers"]).json()["cash_krw"] == 1_500_000

    with_account = {**snapshot, "account_no": "12345678-01"}
    assert client.post("/api/snapshot", headers=user["headers"], json=with_account).status_code == 422
