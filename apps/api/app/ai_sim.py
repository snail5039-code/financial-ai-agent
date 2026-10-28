"""AI 판단 시험 (2단계, Gemini 비용이 든다). 앱의 분석 그래프(수집·투자 AI·검증 AI)를 날짜로 자른 DB(app.asof)에서 그대로 돌리고,
같은 구간을 규칙만(sim.py)으로 돌린 것과 비교한다. 하루 한 번(10:05)만 묻는다: 앱은 30분마다 묻지만 비용이 몇 배라서 줄였다.

    uv run python -m app.ai_sim dry  up        # AI를 가짜로 바꿔 배관만 확인 (무료)
    uv run python -m app.ai_sim rbcount up     # 매수는 규칙대로·매도만 AI: 새로 물어야 할 판단 수만 센다 (무료). rb up 6 이면 진짜 호출
    uv run python -m app.ai_sim run  up 12     # 진짜 호출. 구간(up/crash/flat), 비용 상한(달러)
판단마다 토큰·비용을 tools/data/ai_sim/<구간>.jsonl에 남긴다. 이어서 돌리면 이미 묻은 (날, 종목, 종류)는 다시 안 묻는다.
앞선 규칙: 새 매수는 하락장(KODEX 200이 20일 평균 아래)이면 안 한다, 강제 손절(-10%·-15%)은 규칙대로, 그 밖의 매도는 AI가 정한다.
서버 실행 때와 같게 NEWS_FETCH=off LIVE_DISCLOSURES=off 로 돌린다 (외부에서 지금 뉴스·공시를 받지 않게).
"""

import json
import os
import sys
from datetime import date, datetime
from functools import cache
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from psycopg import connect
from psycopg.rows import dict_row

from app import sim
from app.agents import analysis, llm
from app.agents.schemas import Claim, ProposalDraft, VerificationDraft
from app.agents.state import Context, new_request
from app.asof import WINDOWS, asof_url
from app.backtest import load_history

KST = ZoneInfo("Asia/Seoul")
OUT = sim.DATA / "ai_sim"
ASK_AT = "100500"
IN_PER_M, OUT_PER_M = 1.5, 7.5  # gemini-3.6-flash 표준가 (달러/100만 토큰). 절반가 설은 미확인이라 비싼 쪽으로 센다

SELL_QUESTION = (  # 앱 sellQuestion(reason: check)을 그대로 옮김
    "{name} 보유 중이야 (매입가 {avg:,}원, 지금 {pct:+.2f}%). 앞으로 몇 시간~며칠 안에 떨어질 가능성이 크면 지금 미리 팔아서 "
    "이익을 지키거나 손실을 막아야 하고, 더 오를 근거가 크면 계속 들고 있어야 해. 지금 팔아 확정하는 것과 들고 가는 것을 "
    "똑같이 비교해서 더 나은 쪽을 골라 줘 (보유가 기본값이 아니야). 장중 흐름(고점에서 밀리는지, 하락이 이어지는지), "
    "시장 전체 흐름(코스피·코스닥 지수, 며칠 연속 하락인지, 오른·내린 종목 수), 뉴스, 공시를 근거로 지금 팔아야 할까? "
    "급락 직후라면 지금 가격이 오늘 저점 근처인지, 저점에서 회복 중인지도 봐 줘. 공포에 저점에서 파는 건 피해야 해. "
    "시장 전체 하락은 그것만으로 팔 이유가 아니야. 팔려면 시장보다 뚜렷하게 약하거나 추세가 꺾였거나 악재 공시 같은 종목만의 근거가 있어야 해. "
    "판다면 전부 팔지 절반만 덜지도 정해 줘")


class Meter:
    """토큰 사용량을 센다 (LangChain 콜백). 비용은 입력 + (생각 포함) 출력"""

    def __init__(self):
        from langchain_core.callbacks import UsageMetadataCallbackHandler
        self.handler = UsageMetadataCallbackHandler()

    def tokens(self) -> tuple[int, int]:
        u = list(self.handler.usage_metadata.values())
        return sum(x["input_tokens"] for x in u), sum(x["output_tokens"] for x in u)

    def cost(self) -> float:
        i, o = self.tokens()
        return i * IN_PER_M / 1e6 + o * OUT_PER_M / 1e6


def install_meter() -> Meter:
    from langchain_google_genai import ChatGoogleGenerativeAI

    from app import config
    meter = Meter()

    @cache
    def chat_model(level: str):
        return ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, api_key=config.GEMINI_API_KEY, thinking_level=level,
                                      callbacks=[meter.handler])
    llm.chat_model = chat_model
    return meter


def install_fake() -> SimpleNamespace:
    """무료 배관 확인: 투자 AI는 늘 관망·보유, 검증 AI는 승인"""
    def write(context):
        return ProposalDraft(action="hold" if "보유 중이야" in context else "watch", claims=[Claim(text="가짜", type="opinion")],
                             counter_arguments=[], risks=[], invalid_if=[])
    llm.write_proposal = write
    llm.verify_proposal = lambda context: VerificationDraft(verdict="approve", checks=[], risk_fit="ok", summary="가짜")
    return SimpleNamespace(cost=lambda: 0.0, tokens=lambda: (0, 0))


def connect_asof(url: str, **kwargs):
    """앱의 connect는 options를 덮어써서 날짜로 자른 보기가 안 걸린다 (2026-10-28 미래 자료가 섞였다). 주소의 options를 그대로 쓴다"""
    import psycopg
    return psycopg.connect(url, connect_timeout=3, **kwargs)


analysis.connect = connect_asof


def judge(url: str, state: dict) -> dict:
    """앱 그래프의 수집 → 투자 AI → 검증 AI(반려되면 고쳐 쓰기, 최대 2번)만 돌린다. 계좌·현재가는 폰이 주는 값을 만들어 넣는다"""
    runtime = SimpleNamespace(context=Context(url))
    state = {**state, **analysis.gather_node(state, runtime)}
    while True:
        state |= analysis.invest_agent_node(state)
        state |= analysis.verify_agent_node(state, runtime)
        if analysis.route_after_verify(state) != "invest_agent":
            proposal = state["proposal"]
            return {"action": proposal["action"], "verdict": state["verifications"][-1]["verdict"],
                    "portion": proposal.get("sell_portion") or proposal.get("buy_portion"),
                    "text": "; ".join(c["text"] for c in proposal["claims"])[:600]}


def make_state(profile: dict, code: str, name: str, query: str, d: date, mins: list, day: dict, prev_close: int,
               book: sim.Book, index_daily: list, index_now: float, buy: bool, price: int) -> dict:
    seen = [b for b in mins if b["t"] <= ASK_AT]
    vol = sum(b["v"] for b in seen)
    when = datetime.combine(d, datetime.strptime(ASK_AT, "%H%M%S").time(), KST).isoformat()
    price_row = {"stock_code": code, "price": price, "as_of": when, "intraday": {
        "bars": [[b["t"], b["c"]] for b in seen], "change_pct": (price / prev_close - 1) * 100,
        "vwap": round(sum(b["c"] * b["v"] for b in seen) / vol) if vol else None,
        "high": max((b["h"] for b in seen), default=price), "open": day["o"]}}
    # KODEX 200으로 대신한 지수 (지수 분봉·일봉은 과거를 못 받는다)
    market = {"index": "KOSPI", "value": index_now, "change_pct": (index_now / index_daily[-1][1] - 1) * 100, "as_of": when,
              "daily": [(k, v) for k, v in reversed(index_daily)]}
    holdings = [{"stock_code": c, "name": c, "qty": p["qty"], "avg_price": int(p["avg"])} for c, p in book.pos.items()]
    state = new_request(query, [], profile)
    state |= {"user_id": str(profile["user_id"]), "thread_id": "sim", "client": "app", "stock_code": code, "stock_name": name,
              "snapshot": {"cash_krw": int(book.cash), "holdings": holdings, "fetched_at": when, "source": "app"},
              "prices": [price_row], "market": [market], "auto_origin": buy, "real_mode": False}
    if buy:
        state |= {"side": "buy", "user_directed": True}
    return state


def run_window(key: str, budget: float, dry: bool, rule_buy: bool = False, count: bool = False) -> None:
    """rule_buy: 매수는 규칙대로(AI에게 안 묻고), 매도만 AI. count: 새로 물어야 할 판단 수만 센다(호출 안 함)"""
    base = os.environ["DATABASE_URL"]
    start, end = (date.fromisoformat(x) for x in WINDOWS[key])
    meter = install_fake() if dry or count else install_meter()
    missing = 0
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / f"{key}.jsonl"
    done = {}
    if log_path.exists() and not dry:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[(r["day"], r["code"], r["kind"])] = r
    with connect(base, row_factory=dict_row) as conn:
        full = load_history(conn)
        profile = {"mode": "custom", **conn.execute("SELECT user_id, risk_level, flags FROM investor_profiles LIMIT 1").fetchone()}
        names = {r["code"]: r["name"] for r in conn.execute("SELECT code, name FROM stocks WHERE is_target")}
    days = [x for x in sim.trading_days(full) if x <= end]
    days = days[max(0, days.index(next(x for x in days if x >= start)) - 1):]
    book, index = sim.Book(cash=10_000_000), sim.daily_bars(sim.INDEX)

    def ask(url: str, d: date, code: str, kind: str, state: dict) -> dict:
        if cached := done.get((f"{d}", code, kind)):
            return cached
        if count:
            nonlocal missing
            missing += 1
            return {"action": "hold", "verdict": "approve", "portion": None}
        if not dry and meter.cost() >= budget:
            raise SystemExit(f"비용 상한 ${budget} 도달. 여기서 멈춤 ({d}, 지금까지 ${meter.cost():.2f})")
        before = meter.tokens()
        r = judge(url, state)
        after = meter.tokens()
        r |= {"day": f"{d}", "code": code, "kind": kind, "tokens_in": after[0] - before[0], "tokens_out": after[1] - before[1]}
        if not dry:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return r

    for i in range(1, len(days)):
        prev, d = days[i - 1], days[i]
        k = f"{d:%Y%m%d}"
        url = asof_url(base, f"{d}")
        for code, p in list(book.pos.items()):  # 강제 손절은 규칙대로
            b = sim.daily_bars(code).get(k)
            for level, part in ((sim.HARD, "half"), (sim.HARD_ALL, "all")):
                if b and code in book.pos and b["l"] <= p["avg"] * level and not (part == "half" and p["half_done"]):
                    qty = p["qty"] if part == "all" or p["qty"] < 2 else p["qty"] // 2
                    sim._sell(book, d, code, qty, min(b["o"], p["avg"] * level), "강제 손절")
                    if code in book.pos and part == "half":
                        p["half_done"] = True
        ix = [index[x]["c"] for x in sorted(index) if x < k][-20:]
        bear = len(ix) == 20 and ix[-1] < sum(ix) / 20
        ix_min = [b for b in sim.minute_bars(sim.INDEX, d) or [] if b["t"] <= ASK_AT]
        ix_now = ix_min[-1]["c"] if ix_min else index[k]["o"]
        ix_daily = [(x, index[x]["c"]) for x in sorted(index) if x < k][-25:]

        def view(code: str):
            day = sim.daily_bars(code).get(k)
            mins = sim.minute_bars(code, d) or []
            seen = [b for b in mins if b["t"] <= ASK_AT]
            pc = (sim.daily_bars(code).get(f"{prev:%Y%m%d}") or {}).get("c")
            return day, mins, (seen[-1]["c"] if seen else (day or {}).get("o")), pc

        for code, p in list(book.pos.items()):  # 보유 종목: AI가 팔지 정한다
            day, mins, price, pc = view(code)
            if not (day and price and pc):
                continue
            q = SELL_QUESTION.format(name=names[code], avg=int(p["avg"]), pct=(price / p["avg"] - 1) * 100)
            r = ask(url, d, code, "sell", make_state(profile, code, names[code], q, d, mins, day, pc, book, ix_daily, ix_now, False, price))
            if r["action"] == "sell" and r["verdict"] in ("approve", "conditional"):
                sim._sell(book, d, code, p["qty"] if r["portion"] != "half" or p["qty"] < 2 else p["qty"] // 2, price, "AI 매도")
        if not bear:  # 하락장엔 새로 안 삼 (앱 규칙)
            for code in [c for c in sim.candidates(full, prev, set(), 30) if c in names and c not in book.pos][:sim.PICKS]:
                day, mins, price, pc = view(code)
                if not (day and price and pc):
                    continue
                equity, invested = sim._equity(book, d)
                room = sim.buy_room(int(book.cash), int(equity), int(invested), sim.vol_pct(sim.closes_until(full, code, prev, 21)), False)
                qty = int(room // (price * (1 + sim.BUY_FEE)))
                if qty < 1:
                    continue
                r = {"action": "buy", "verdict": "approve", "portion": None} if rule_buy else ask(url, d, code, "buy", make_state(profile, code, names[code], f"{names[code]} {qty}주 사줘", d, mins, day, pc, book,
                                                        ix_daily, ix_now, True, price) | {"qty": qty})
                if r["action"] == "buy" and r["verdict"] in ("approve", "conditional"):
                    qty = qty // 2 if r["portion"] == "half" and qty >= 2 else qty
                    book.cash -= qty * price * (1 + sim.BUY_FEE)
                    book.pos[code] = {"qty": qty, "avg": price, "half_done": False}
                    book.trades.append((d, code, "buy", qty, price, 0.0))
        held = sum(p["qty"] * (sim.daily_bars(c).get(k) or {"c": p["avg"]})["c"] for c, p in book.pos.items())
        book.days.append((d, book.cash + held, held / (book.cash + held)))
    rule = sim.run(full, sim.Strategy("규칙만 (10:30 한 번, 하락장엔 안 삼)", entry="once", bear_buy="none"), days)
    if count:
        print(f"[{key}] 새로 물어야 할 매도 판단 {missing}건")
        return
    print(f"[{key}] {days[1]}~{days[-1]}  비용 ${meter.cost():.2f}  토큰 {meter.tokens()}")
    for label, b in (("AI 판단", book), ("규칙만", rule)):
        print(label, sim.summary(b, days, days[1], days[-1]))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("dry", "run", "rbcount", "rb") or sys.argv[2] not in WINDOWS:
        sys.exit(__doc__)
    run_window(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.0, sys.argv[1] == "dry",
               rule_buy=sys.argv[1] in ("rb", "rbcount"), count=sys.argv[1] == "rbcount")
