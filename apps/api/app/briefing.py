"""아침 브리핑 (docs/plan/12-todo-by-stage.md 1-1).

사용자마다 하루 한 번 만든다.
  1. 보유·관심 종목 소식: 최근 공시 제목·원문 링크 (공개 데이터)
  2. 오늘 한도: 1일 한도, 규칙에 걸린 요청 없는 날
  3. 오늘의 매수 제안 (맞춤 모드만): 후보는 코드가 고르고, 지금 분석과 똑같이 투자 AI → 검증 AI를 거친다.
     투자 AI가 매수 검토라고 하고 검증 AI가 승인·조건부 승인한 것만 싣는다.
     주문은 만들지 않는다 (승인 만료 10분이라 장 전에 만료됨). 앱의 "주문하기"가 평소 주문 흐름을 시작한다.

실행: uv run python -m app.briefing [--email 사용자]   (자동 실행은 .env MORNING_BRIEF_TIME, 기본 꺼짐)
"""

import argparse
import json
import logging
import threading
from datetime import datetime, time, timedelta
from types import SimpleNamespace

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.agents.analysis import (gather_node, invest_agent_node, route_after_verify, save_proposal, verify_agent_node,
                                 volatility_rank, CLAIM_LABELS)
from app.agents.query import latest_snapshot
from app.agents.state import new_request
from app.clock import KST
from app.db import connect
from app.functions.orders import KRX_HOLIDAYS, WORST_CASE_DROP_PCT
from app.functions.suitability import buy_block_reason, stock_risk_grade
from app.routers.orders import today as today_summary
from app.routers.policy import profile_summary

MAX_CANDIDATES = 3   # 하루에 분석하는 후보 수 = Gemini 비용 상한 (후보마다 투자·검증 AI, 재검토 최대 2번)
NEWS_DAYS = 3        # 이 날 수 안의 공시를 "최근 소식"으로 본다 (주말을 넘겨도 금요일 공시가 보이게)


def is_trading_day(day) -> bool:
    return day.weekday() < 5 and day not in KRX_HOLIDAYS


def pick_candidates(conn, profile: dict, held: set[str], watching: list[str] = ()) -> list[dict]:
    """아직 갖고 있지 않고 내 성향 규칙상 매수를 제안할 수 있는 분석 대상. 관심 종목을 먼저, 그다음 최근 공시가 있는 종목.

    ponytail: "관심 종목 · 최근 공시가 있다"만으로 고른다. 가격 흐름·재무 점수로 순위를 매기려면 여기서 바꾼다
    """
    rows = conn.execute(
        """
        SELECT s.code, s.name FROM stocks s
        LEFT JOIN (SELECT stock_code, max(filed_at) AS latest FROM disclosures
                   WHERE filed_at >= (now() AT TIME ZONE 'Asia/Seoul')::date - %(days)s GROUP BY stock_code) d
               ON d.stock_code = s.code
        WHERE s.is_target AND (d.latest IS NOT NULL OR s.code = ANY(%(watching)s))
        ORDER BY s.code = ANY(%(watching)s) DESC, d.latest DESC NULLS LAST, s.code
        """,
        {"days": NEWS_DAYS, "watching": list(watching)},
    ).fetchall()
    picks = []
    for row in rows:
        if row["code"] in held:
            continue
        reason = buy_block_reason(profile["mode"], profile.get("risk_level"), profile.get("flags") or [],
                                  stock_risk_grade(row["code"]), volatility_rank(conn, row["code"]))
        if reason is None:
            picks.append({"code": row["code"], "name": row["name"]})
        if len(picks) == MAX_CANDIDATES:
            break
    return picks


def analyze(database_url: str, base: dict, code: str, name: str) -> dict:
    """채팅의 분석 그래프와 같은 노드를 차례로 부른다 (fetch 멈춤 대신 서버의 최근 스냅샷을 쓴다)."""
    runtime = SimpleNamespace(context=SimpleNamespace(database_url=database_url))
    state = {**base, "stock_code": code, "stock_name": name, "query": f"{name} 오늘 매수할 만한가"}
    state |= gather_node(state, runtime)
    while True:
        state |= invest_agent_node(state)
        state |= verify_agent_node(state, runtime)
        if route_after_verify(state) != "invest_agent":
            return state


def pick_entry(conn, state: dict, proposal_id: str) -> dict:
    proposal, verification, sources = state["proposal"], state["verifications"][-1], state["sources"]
    close = conn.execute("SELECT close, trade_date FROM stock_prices WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 1",
                         (state["stock_code"],)).fetchone()
    return {
        "stock_code": state["stock_code"], "stock_name": state["stock_name"], "proposal_id": proposal_id,
        "verdict": verification["verdict"], "summary": verification["summary"], "conditions": verification["conditions"],
        "claims": [{"type": CLAIM_LABELS[c["type"]], "text": c["text"],
                    "sources": [sources[s]["title"] for s in c["source_ids"] if s in sources]} for c in proposal["claims"][:3]],
        "risks": proposal["risks"][:3],
        "last_close": close and close["close"], "close_date": close and str(close["trade_date"]),
        # 1주 기준 최악의 경우 (처리안과 같은 기준)
        "worst_case_loss": close and close["close"] * WORST_CASE_DROP_PCT // 100,
    }


def build_briefing(database_url: str, user_id: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(KST)
    with connect(database_url, row_factory=dict_row) as conn:
        profile = profile_summary(conn, user_id)
        snapshot = latest_snapshot(conn, user_id)
        held = {h["stock_code"] for h in snapshot["holdings"]} if snapshot else set()
        watching = [r["stock_code"] for r in conn.execute(
            "SELECT stock_code FROM watchlist WHERE user_id = %s ORDER BY created_at", (user_id,)).fetchall()]
        news = conn.execute(
            """
            SELECT d.stock_code, s.name AS stock_name, d.title, d.url, d.filed_at,
                   CASE WHEN d.stock_code = ANY(%(held)s) THEN '보유' ELSE '관심' END AS why
            FROM disclosures d JOIN stocks s ON s.code = d.stock_code
            WHERE d.stock_code = ANY(%(codes)s) AND d.filed_at >= %(since)s ORDER BY d.filed_at DESC LIMIT 20
            """,
            {"held": list(held), "codes": list(held | set(watching)), "since": now.date() - timedelta(days=NEWS_DAYS)},
        ).fetchall()
        limits = today_summary(conn, user_id)
        candidates = pick_candidates(conn, profile, held, watching) if profile["mode"] == "custom" else []
        thread_id = None
        if candidates:  # 제안서는 대화(thread)에 묶여 저장된다. 브리핑마다 대화 하나를 만든다
            thread_id = str(conn.execute("INSERT INTO threads (user_id) VALUES (%s) RETURNING id", (user_id,)).fetchone()["id"])
            conn.commit()

    base = {**new_request("", [], profile), "user_id": user_id, "thread_id": thread_id, "client": "web",
            "snapshot": snapshot and {**snapshot, "fetched_at": snapshot["fetched_at"].isoformat(), "source": "server"}}
    picks, checked = [], []
    for candidate in candidates:
        state = analyze(database_url, base, candidate["code"], candidate["name"])
        verdict = state["verifications"][-1]["verdict"]
        with connect(database_url) as conn:
            proposal_id = save_proposal(conn, state)  # 기록 화면에서 근거·검증 과정을 볼 수 있게 저장
        checked.append({"stock_name": candidate["name"], "action": state["proposal"]["action"], "verdict": verdict})
        if state["proposal"]["action"] == "buy" and verdict in ("approve", "conditional"):
            with connect(database_url, row_factory=dict_row) as conn:
                picks.append(pick_entry(conn, state, proposal_id))

    content = {
        "mode": profile["mode"],
        "news": [{**n, "filed_at": str(n["filed_at"])} for n in news],
        "limits": limits,
        "picks": picks,
        "checked": checked,  # 분석했지만 제안하지 않은 것도 남긴다 (왜 비었는지 보이게)
        "snapshot_at": snapshot and snapshot["fetched_at"].isoformat(),
    }
    with connect(database_url) as conn:
        conn.execute(
            "INSERT INTO briefings (user_id, brief_date, content) VALUES (%s, %s, %s)"
            " ON CONFLICT (user_id, brief_date) DO UPDATE SET content = EXCLUDED.content, created_at = now()",
            (user_id, now.date(), Jsonb(content, dumps=lambda obj: json.dumps(obj, default=str))),
        )
    return content


def run_all(database_url: str | None = None, email: str | None = None) -> int:
    """브리핑을 만든다 (email이 없으면 모든 사용자). 만든 수를 돌려준다. 한 사람이 실패해도 다음 사람은 만든다."""
    with connect(database_url, row_factory=dict_row) as conn:
        users = conn.execute("SELECT id FROM users WHERE %s::text IS NULL OR email = %s", (email, email)).fetchall()
    made = 0
    for user in users:
        try:
            build_briefing(database_url, str(user["id"]))
            made += 1
        except Exception:
            logging.getLogger(__name__).exception("아침 브리핑 실패: %s", user["id"])
    return made


def seconds_until(at: time, now: datetime) -> float:
    """now 다음에 오는 거래일 at 시각까지 남은 초."""
    target = now.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    while not is_trading_day(target.date()):
        target += timedelta(days=1)
    return (target - now).total_seconds()


def run_daily(stop: threading.Event, at: time) -> None:
    """서버가 켜져 있는 동안 거래일마다 at 시각에 만든다."""
    while not stop.wait(seconds_until(at, datetime.now(KST))):
        run_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="아침 브리핑 만들기 (Gemini 호출이 생긴다)")
    parser.add_argument("--email", help="이 사용자만")
    print(f"만든 브리핑: {run_all(email=parser.parse_args().email)}개")
