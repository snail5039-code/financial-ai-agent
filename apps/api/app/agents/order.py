"""주문 그래프 (docs/plan/04-graph-design.md 5장).

    find_stock → check_target → order_values → get_account → set_price
      → gather → invest_agent ⇄ verify_agent (가벼운 분석: 경고 위주)
      → policy ─┬─ 위반 → blocked (기록하고 막음)
                └─ 통과 → prepare_approval → approval ─┬─ 승인 → execute ─┬─ 결과 → 기록
                                                       ├─ 수정 → policy  └─ 가격 1% 넘게 변동 → policy (다시 승인)
                                                       └─ 거절·만료 → 기록
    분석에서 "이대로 주문할까요?"로 왔으면(from_analysis): order_values → set_price → policy (분석·계좌 조회는 이미 함)

- 정책 검사·금액·행동 코치는 코드(functions/orders.py)가 한다
- 사용자가 직접 지시한 주문은 검증 AI가 반려해도 막지 않고, 처리안에 "확인 필요"로 올려 확인을 받는다 (2026-10-06 결정).
  정책 위반(한도·현금·장 시간)은 확인과 상관없이 막는다
- 주문은 서버가 내지 않는다. execute 멈춤으로 폰에 부탁하고, 폰이 증권사에 주문한 결과를 받아 기록한다
"""

import json
import re
from datetime import datetime, timedelta
from decimal import Decimal

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app import clock
from app.agents import llm
from app.agents.analysis import (
    VERDICT_LABELS, check_target_node, gather_node, get_account_node, invest_agent_node, save_proposal,
    verify_agent_node,
)
from app.agents.interrupts import pause
from app.agents.query import end_if_answered, find_stock_node, won
from app.agents.state import Context, InvestState
from app.db import audit, connect
from app.functions import orders

SIDE_LABELS = {"buy": "매수", "sell": "매도"}
RESULT_LABELS = {
    "accepted": "주문이 접수됐어요", "filled": "주문이 체결됐어요", "partially_filled": "주문이 일부 체결됐어요",
    "failed": "주문이 실패했어요", "unknown_checked": "응답이 불확실해 주문 내역을 확인했어요",
}
BROKER, MODE = "kis_mock", "mock"  # MVP는 KIS 모의투자만 (실전은 로드맵 4단계에서)


def parse_qty(text: str) -> int | None:
    match = re.search(r"\d[\d,]*", text or "")
    return int(match.group().replace(",", "")) if match else None


# ---------- 값 모으기 ----------

def order_values_node(state: InvestState) -> dict:
    """매수·매도와 수량이 없으면 묻는다 (FR-11). 0주 이하나 너무 큰 수량은 막는다."""
    side = state.get("side")
    if side is None:
        reply = pause("question", text=f"{state['stock_name']}을(를) 살까요, 팔까요?",
                      choices=[{"id": "buy", "label": "매수"}, {"id": "sell", "label": "매도"}])
        answer = reply.get("choice_id") or reply.get("text") or ""
        side = "buy" if answer == "buy" or "사" in answer else "sell" if answer == "sell" or "팔" in answer else None
        if side is None:
            return {"answer": "매수인지 매도인지 알아듣지 못했어요. 다시 말해 주세요."}
    qty = state.get("qty")
    if qty is None:
        verb = "살까요" if side == "buy" else "팔까요"
        qty = parse_qty(pause("question", text=f"몇 주 {verb}?", choices=None).get("text"))
        if qty is None:
            return {"answer": "수량을 알아듣지 못했어요. '4주'처럼 다시 말해 주세요."}
    if not 1 <= qty <= orders.MAX_QTY:
        return {"answer": f"수량은 1주부터 {orders.MAX_QTY:,}주까지 주문할 수 있어요."}
    return {"side": side, "qty": qty}


def set_price_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    """지정가: 사용자가 말한 가격, 없으면 폰이 받은 현재가, 웹이면 최근 종가. 시장가는 MVP에서 지원하지 않는다."""
    if state.get("limit_price"):
        return {}
    if state.get("prices"):
        return {"limit_price": state["prices"][0]["price"]}
    with connect(runtime.context.database_url, row_factory=dict_row) as conn:
        last = conn.execute("SELECT close FROM stock_prices WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 1",
                            (state["stock_code"],)).fetchone()
    if last is None:
        return {"answer": "주문 가격을 정할 수 없어요. '7만원에'처럼 가격을 말해 주세요."}
    return {"limit_price": last["close"]}


# ---------- 정책 검사와 처리안 ----------

def closes_of(conn, codes: list[str]) -> dict[str, int]:
    rows = conn.execute(
        "SELECT DISTINCT ON (stock_code) stock_code, close FROM stock_prices WHERE stock_code = ANY(%s)"
        " ORDER BY stock_code, trade_date DESC", (codes,),
    ).fetchall()
    return {row["stock_code"]: row["close"] for row in rows}


def five_day_rank(conn, code: str) -> tuple[float | None, Decimal | None]:
    """최근 5거래일 상승률과, 분석 대상 안에서 그 순위 (0~1, 1이면 가장 많이 오름)."""
    returns = {}
    for row in conn.execute("SELECT code FROM stocks WHERE is_target").fetchall():
        closes = [r["close"] for r in conn.execute(
            "SELECT close FROM stock_prices WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 6", (row["code"],))]
        if len(closes) == 6:
            returns[row["code"]] = (Decimal(closes[0]) / closes[5] - 1) * 100
    if code not in returns:
        return None, None
    rank = sum(1 for value in returns.values() if value <= returns[code]) / len(returns)
    return rank, returns[code].quantize(Decimal("0.1"))


def policy_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    side, qty, price, code = state["side"], state["qty"], state["limit_price"], state["stock_code"]
    snapshot = state.get("snapshot")
    holdings = snapshot["holdings"] if snapshot else []
    with connect(runtime.context.database_url, row_factory=dict_row) as conn:
        policy = conn.execute("SELECT * FROM policies WHERE user_id = %s", (state["user_id"],)).fetchone()
        today_ordered = int(conn.execute(orders.TODAY_ORDERED_SQL, (state["user_id"],)).fetchone()["total"])
        recent_trades = conn.execute(
            "SELECT count(*) AS n FROM orders o JOIN approvals a ON a.id = o.approval_id"
            " JOIN proposals p ON p.id = a.proposal_id WHERE p.user_id = %s AND p.stock_code = %s"
            " AND o.status IN ('accepted', 'filled', 'partially_filled') AND o.created_at >= now() - %s::interval",
            (state["user_id"], code, f"{orders.FREQUENT_TRADE_DAYS} days"),
        ).fetchone()["n"]
        market = conn.execute("SELECT market FROM stocks WHERE code = %s", (code,)).fetchone()["market"]
        closes = closes_of(conn, [h["stock_code"] for h in holdings])
        hot_rank, five_day_return = five_day_rank(conn, code)

    result = orders.policy_check(side, qty, price, policy, today_ordered, snapshot, closes, code, clock.market_now(),
                                 ["snapshot"] if snapshot else [])
    amount = orders.order_amount(qty, price)
    fee = orders.fee_estimate(amount, policy["fee_rate_pct"])
    tax = orders.sell_tax(amount, market) if side == "sell" else 0
    held = next((h for h in holdings if h["stock_code"] == code), None)
    gain_pct = (Decimal(price - held["avg_price"]) / held["avg_price"] * 100).quantize(Decimal("0.1")) \
        if side == "sell" and held and held["avg_price"] else None
    losers = [h["stock_name"] for h in holdings
              if h["stock_code"] != code and closes.get(h["stock_code"], h["avg_price"]) < h["avg_price"]]
    warnings = orders.coach_warnings(side, recent_trades, hot_rank, five_day_return, "chases_hot_stocks" in state["flags"],
                                     result["weight_after"], policy["max_weight_pct"], gain_pct, losers,
                                     (fee or 0) + tax)

    confirm = []
    if state["mode"] != "custom":
        confirm.append("성향 퀴즈를 하지 않은 일반 모드라 내 성향에 맞는지 확인하지 않은 주문이에요.")
    elif side == "buy" and state.get("buy_block_reason"):
        confirm.append(f"성향보다 위험한 주문이에요: {state['buy_block_reason']}.")
    verification = state["verifications"][-1]
    if verification["verdict"] in ("reject", "user_judgement"):
        confirm.append(f"검증 AI 판정이 '{VERDICT_LABELS[verification['verdict']]}'이에요: {verification['summary']}")
    if orders.needs_hot_confirm(warnings, "chases_hot_stocks" in state["flags"]):
        confirm.append("급등 직후 매수예요. 한 번 더 생각해 보셨나요?")

    card = {
        "stock_code": code, "stock_name": state["stock_name"], "side": side, "qty": qty, "limit_price": price,
        "amount": amount, "fee": fee, "tax": tax,
        "weight_after": None if result["weight_after"] is None else str(result["weight_after"]),
        "worst_case_loss": amount * orders.WORST_CASE_DROP_PCT // 100 if side == "buy" else None,
        "verdict": verification["verdict"], "summary": verification["summary"],
        "conditions": verification["conditions"], "disagreements": verification["disagreements"],
        "claims": [{"text": c["text"], "type": c["type"]} for c in state["proposal"]["claims"]],
        "counter_arguments": state["proposal"]["counter_arguments"], "risks": state["proposal"]["risks"],
        "policy": result["rules"], "warnings": warnings, "confirm_required": confirm,
        "broker": BROKER, "mode": MODE, "user_directed": state["user_directed"],
    }
    return {"policy_result": {**result, "weight_after": card["weight_after"]}, "coach_warnings": warnings,
            "confirm_required": confirm, "card": card}


def route_after_policy(state: InvestState) -> str:
    return "prepare_approval" if state["policy_result"]["ok"] else "blocked"


def save_policy_check(conn, proposal_id: str, result: dict) -> None:
    conn.execute(
        "INSERT INTO policy_checks (proposal_id, ok, rules) VALUES (%s, %s, %s)"
        " ON CONFLICT (proposal_id) DO UPDATE SET ok = EXCLUDED.ok, rules = EXCLUDED.rules, created_at = now()",
        (proposal_id, result["ok"], Jsonb(result["rules"], dumps=json_dumps)),
    )


def json_dumps(value) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


def blocked_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    """정책 위반: 처리안을 만들지 않고 이유를 알려준다 (FR-22). 제안·검증·정책 검사 결과는 기록한다.
    수정·가격 변동 뒤 다시 검사해서 걸린 것이면 기존 처리안을 취소한다."""
    with connect(runtime.context.database_url) as conn:
        if state.get("approval_id"):
            proposal_id = conn.execute("SELECT proposal_id FROM approvals WHERE id = %s",
                                       (state["approval_id"],)).fetchone()[0]
            conn.execute("UPDATE approvals SET status = 'rejected', decided_at = now() WHERE id = %s",
                         (state["approval_id"],))
        else:
            proposal_id = save_proposal(conn, state)
        save_policy_check(conn, proposal_id, state["policy_result"])
        audit(conn, state["user_id"], "order_blocked", {"proposal_id": str(proposal_id), "approval_id": state.get("approval_id")})
    reasons = [f"- {r['label']}: 한도 {format_value(r['limit'])}, 이번 {format_value(r['actual'])}"
               for r in state["policy_result"]["rules"] if not r["ok"]]
    return {"answer": "주문할 수 없어요. 아래 규칙에 걸렸어요.\n" + "\n".join(reasons)}


def format_value(value) -> str:
    return f"{value:,}원" if isinstance(value, int) else str(value)


def prepare_approval_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    """처리안을 저장하고 승인 대기로 둔다. 수정·가격 변동으로 다시 온 것이면 같은 처리안을 고쳐 다시 승인 대기로."""
    expires_at = clock.now() + timedelta(minutes=orders.APPROVAL_MINUTES)
    with connect(runtime.context.database_url) as conn:
        if state.get("approval_id"):
            approval_id = state["approval_id"]
            proposal_id = conn.execute("SELECT proposal_id FROM approvals WHERE id = %s", (approval_id,)).fetchone()[0]
            conn.execute("UPDATE proposals SET qty = %s, limit_price = %s WHERE id = %s",
                         (state["qty"], state["limit_price"], proposal_id))
            conn.execute("UPDATE approvals SET status = 'pending', card = %s, expires_at = %s, decided_at = NULL,"
                         " decided_channel = NULL WHERE id = %s",
                         (Jsonb(state["card"], dumps=json_dumps), expires_at, approval_id))
            event = "approval_renewed"
        else:
            proposal_id = save_proposal(conn, state)
            approval_id = str(conn.execute(
                "INSERT INTO approvals (proposal_id, expires_at, card) VALUES (%s, %s, %s) RETURNING id",
                (proposal_id, expires_at, Jsonb(state["card"], dumps=json_dumps)),
            ).fetchone()[0])
            event = "approval_requested"
        save_policy_check(conn, proposal_id, state["policy_result"])
        audit(conn, state["user_id"], event, {"approval_id": approval_id, "qty": state["qty"], "price": state["limit_price"]})
    return {"approval_id": approval_id, "expires_at": expires_at.isoformat(),
            "card": {**state["card"], "approval_id": approval_id, "expires_at": expires_at.isoformat()}}


def format_card(card: dict) -> str:
    """처리안을 글로 (앱·웹 화면은 card 값을 직접 그린다)."""
    side = SIDE_LABELS[card["side"]]
    fee = f"{card['fee']:,}원" if card["fee"] is not None else "수수료율 미입력"
    lines = [
        f"[처리안 · 모의투자] {card['stock_name']}({card['stock_code']}) {card['qty']:,}주 {side} · 지정가 {won(card['limit_price'])}",
        f"예상 금액 {won(card['amount'])} · 수수료 추정 {fee}" + (f" · 세금 {won(card['tax'])}" if card["side"] == "sell" else ""),
    ]
    if card["weight_after"] is not None:
        lines.append(f"주문 후 이 종목 비중 {card['weight_after']}%")
    if card["worst_case_loss"]:
        lines.append(f"최악의 경우: {orders.WORST_CASE_DROP_PCT}% 하락하면 −{won(card['worst_case_loss'])}")
    lines.append(f"검증 AI: {VERDICT_LABELS[card['verdict']]} — {card['summary']}")
    lines += [f"- 조건: {c}" for c in card["conditions"]] + [f"- 의견 차이: {d}" for d in card["disagreements"]]
    lines += [f"주의: {w}" for w in card["warnings"]]
    lines += [f"확인 필요: {c}" for c in card["confirm_required"]]
    lines.append(f"{datetime.fromisoformat(card['expires_at']):%H:%M}까지 승인하지 않으면 만료돼요.")
    return "\n".join(lines)


# ---------- 승인과 실행 ----------

def approval_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    reply = pause("approval", approval_id=state["approval_id"], card=state["card"], text=format_card(state["card"]),
                  expires_at=state["expires_at"], confirm_required=state["confirm_required"])
    approval_id, decision = state["approval_id"], reply["decision"]
    with connect(runtime.context.database_url) as conn:
        if clock.now() > datetime.fromisoformat(state["expires_at"]):
            # 답이 늦으면 승인으로 보지 않는다 (FR-25)
            conn.execute("UPDATE approvals SET status = 'expired' WHERE id = %s", (approval_id,))
            audit(conn, state["user_id"], "approval_expired", {"approval_id": approval_id})
            return {"answer": "승인 시간이 지나 처리안이 만료됐어요. 주문하지 않았어요."}
        if decision == "reject":
            conn.execute("UPDATE approvals SET status = 'rejected', decided_at = now(), decided_channel = %s WHERE id = %s",
                         (reply["client"], approval_id))
            audit(conn, state["user_id"], "approval_rejected", {"approval_id": approval_id})
            return {"answer": "처리안을 거절했어요. 주문하지 않았어요."}
        if decision == "edit":
            edit = edited_values(reply["text"], state)
            audit(conn, state["user_id"], "approval_edit", {"approval_id": approval_id, "text": reply["text"], **edit})
            return {**edit, "decision": "edit"}
        conn.execute("UPDATE approvals SET status = 'approved', decided_at = now(), decided_channel = %s WHERE id = %s",
                     (reply["client"], approval_id))
        audit(conn, state["user_id"], "approval_approved", {"approval_id": approval_id, "confirm_risk": reply.get("confirm_risk")})
    return {"decision": "approve"}


def edited_values(text: str, state: InvestState) -> dict:
    """"5주만" 같은 수정. "N주"는 코드로 읽고, 그 밖의 말(가격 등)은 LLM으로 뽑는다."""
    match = re.search(r"(\d[\d,]*)\s*주", text)
    if match:
        return {"qty": int(match.group(1).replace(",", ""))}
    edit = llm.parse_order_edit(text, f"{state['stock_name']} {state['qty']}주 {won(state['limit_price'])}")
    return {key: value for key, value in (("qty", edit.qty), ("limit_price", edit.limit_price)) if value}


def route_after_approval(state: InvestState) -> str:
    """승인만 실행으로 간다. 수정은 바뀐 값이 있으면 다시 검사하고, 알아듣지 못했으면 같은 처리안을 다시 묻는다."""
    if state.get("answer"):
        return END
    if state["decision"] == "approve":
        return "execute"
    changed = state["card"]["qty"] != state["qty"] or state["card"]["limit_price"] != state["limit_price"]
    return "check_edit" if changed else "approval"


def check_edit_node(state: InvestState) -> dict:
    if not 1 <= state["qty"] <= orders.MAX_QTY or state["limit_price"] <= 0:
        return {"answer": "수정한 수량이나 가격이 올바르지 않아요. 주문하지 않았어요."}
    return {}


def execute_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    """폰에 주문을 부탁한다. 폰은 가격 재확인 → 생체인증 → 증권사 주문 → 결과를 보낸다 (06-api-spec.md 4장)."""
    request = {
        "approval_id": state["approval_id"], "stock_code": state["stock_code"], "side": state["side"],
        "qty": state["qty"], "limit_price": state["limit_price"], "approved_price": state["limit_price"],
        "max_price_drift_pct": orders.MAX_PRICE_DRIFT_PCT, "idempotency_key": state["approval_id"],
    }
    result = pause("execute", request=request, text="폰 앱에서 가격을 다시 확인하고 실행해 주세요.")["result"]
    with connect(runtime.context.database_url) as conn:
        if result["status"] == "price_changed":
            audit(conn, state["user_id"], "price_changed",
                  {"approval_id": state["approval_id"], "approved": state["limit_price"], "current": result["current_price"]})
            return {"limit_price": result["current_price"]}  # 새 가격으로 다시 검사·승인 (FR-26)
        conn.execute(  # 같은 idempotency_key 결과가 또 오면 무시한다 (중복 주문 기록 방지)
            "INSERT INTO orders (approval_id, idempotency_key, broker, mode, side, qty, price, broker_order_no, status,"
            " filled_qty, filled_price, message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (idempotency_key) DO NOTHING",
            (state["approval_id"], result["idempotency_key"], BROKER, MODE, state["side"], state["qty"],
             state["limit_price"], result.get("broker_order_no"), result["status"], result.get("filled_qty", 0),
             result.get("filled_price"), result.get("message")),
        )
        audit(conn, state["user_id"], "order_result", {"approval_id": state["approval_id"], **result})
    return {"answer": format_result(state, result)}


def route_after_execute(state: InvestState) -> str:
    return END if state.get("answer") else "policy"


def format_result(state: InvestState, result: dict) -> str:
    head = f"{RESULT_LABELS[result['status']]} (모의투자)"
    order = f"{state['stock_name']} {state['qty']:,}주 {SIDE_LABELS[state['side']]} · 지정가 {won(state['limit_price'])}"
    lines = [head, order]
    if result.get("filled_qty"):
        lines.append(f"체결 {result['filled_qty']:,}주 × {won(result['filled_price'])}")
    if result.get("broker_order_no"):
        lines.append(f"주문번호 {result['broker_order_no']}")
    if result.get("message"):
        lines.append(result["message"])
    return "\n".join(lines)


# ---------- 그래프 ----------

def route_start(state: InvestState) -> str:
    return "order_values" if state.get("from_analysis") else "find_stock"


def route_after_values(state: InvestState) -> str:
    if state.get("answer"):
        return END
    return "set_price" if state.get("from_analysis") else "get_account"


def route_after_price(state: InvestState) -> str:
    if state.get("answer"):
        return END
    return "policy" if state.get("from_analysis") else "gather"


def route_after_verify(state: InvestState) -> str:
    return "invest_agent" if state["verifications"][-1]["verdict"] == "reject" else "policy"


def build_order_graph():
    builder = StateGraph(InvestState, context_schema=Context)
    for name, node in [
        ("find_stock", find_stock_node), ("check_target", check_target_node), ("order_values", order_values_node),
        ("get_account", get_account_node), ("set_price", set_price_node), ("gather", gather_node),
        ("invest_agent", invest_agent_node), ("verify_agent", verify_agent_node), ("policy", policy_node),
        ("blocked", blocked_node), ("prepare_approval", prepare_approval_node), ("approval", approval_node),
        ("check_edit", check_edit_node), ("execute", execute_node),
    ]:
        builder.add_node(name, node)

    builder.add_conditional_edges(START, route_start, ["order_values", "find_stock"])
    builder.add_conditional_edges("find_stock", end_if_answered("check_target"), ["check_target", END])
    builder.add_conditional_edges("check_target", end_if_answered("order_values"), ["order_values", END])
    builder.add_conditional_edges("order_values", route_after_values, ["set_price", "get_account", END])
    builder.add_conditional_edges("get_account", end_if_answered("set_price"), ["set_price", END])
    builder.add_conditional_edges("set_price", route_after_price, ["policy", "gather", END])
    builder.add_edge("gather", "invest_agent")
    builder.add_edge("invest_agent", "verify_agent")
    builder.add_conditional_edges("verify_agent", route_after_verify, ["invest_agent", "policy"])
    builder.add_conditional_edges("policy", route_after_policy, ["prepare_approval", "blocked"])
    builder.add_edge("blocked", END)
    builder.add_edge("prepare_approval", "approval")
    builder.add_conditional_edges("approval", route_after_approval, ["check_edit", "execute", "approval", END])
    builder.add_conditional_edges("check_edit", end_if_answered("policy"), ["policy", END])
    builder.add_conditional_edges("execute", route_after_execute, ["policy", END])
    return builder.compile()
