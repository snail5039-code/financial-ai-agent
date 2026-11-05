"""급락 뒤 반등 매수 시험 (규칙만, AI 0원): 시총 상위 종목이 5일 사이 크게 빠졌을 때 사서 작게 먹고 짧게 끊는다.

    uv run python -m app.sim_rebound

종가 일봉만 쓴다. D일 종가로 신호를 보고 D일 종가에 산다 (앱이 15:20쯤 사는 것과 같다. 마감 가격 차이는 슬리피지로 반영).
미래 정보는 쓰지 않는다: 신호는 D일까지의 종가, 청산은 그 뒤 날의 종가로만 본다.
ponytail: 장중 가격·손절 갭·거래량은 모른다 (종가 기준이라 손절이 실제보다 늦게 걸린다). 기존 sim.py의 run()은 건드리지 않는다.
"""

import statistics
from dataclasses import dataclass
from datetime import date

from psycopg.rows import dict_row

from app import config
from app.backtest import load_history, universe_on
from app.db import connect
from app.sim import BUY_FEE, INDEX, SELL_FEE, SELL_TAX, START, TRAIN_END, closes_until, daily_bars, fin_bad, trading_days

SLIP = 0.001  # 사고팔 때 각각 0.1% 불리하게 (종가 근처 체결 오차)
MAX_POS, PER_POS, NEW_PER_DAY = 5, 0.10, 2  # 동시에 5종목, 종목당 총자산 10%, 하루 새로 2종목까지
HALF = date(2026, 4, 24)  # sim-20261101.md 전후반 경계와 같다


@dataclass
class Rebound:
    name: str
    drop: float  # 5일 등락률이 이 값 이하(예: −0.10)이면 신호
    take: float = 0.04  # +4% 넘으면 종가에 판다
    stop: float = -0.04  # −4% 아래면 종가에 판다
    hold: int = 5  # 최대 5거래일
    bear_only: bool = False  # 지수(KODEX 200)가 20일 평균 아래일 때만


def bear_on(index: dict, key: str) -> bool:
    ix = [index[k]["c"] for k in sorted(index) if k <= key][-20:]
    return len(ix) == 20 and ix[-1] < sum(ix) / 20


def run(h, s: Rebound, days: list[date]) -> dict:
    cash, pos, trades, eq = 10_000_000.0, {}, [], []
    index = daily_bars(INDEX)
    for i, d in enumerate(days):
        px = lambda c: h.close.get((d, c))
        # 1) 청산 (오늘 종가로 판단·체결)
        for code, p in list(pos.items()):
            c = px(code)
            if not c:
                continue
            p["age"] += 1
            ret = c / p["avg"] - 1
            if ret >= s.take or ret <= s.stop or p["age"] >= s.hold:
                got = p["qty"] * c * (1 - SLIP) * (1 - SELL_FEE - SELL_TAX)
                cash += got
                trades.append(got / (p["qty"] * p["avg"] * (1 + BUY_FEE)) - 1)
                del pos[code]
        # 2) 신호: 5일 등락률이 drop 이하인 종목 중 많이 빠진 순. 영업적자 종목 제외 (지금 규칙과 같다)
        held_val = sum(p["qty"] * (px(c) or p["avg"]) for c, p in pos.items())
        equity = cash + held_val
        if (not s.bear_only or bear_on(index, f"{d:%Y%m%d}")) and len(pos) < MAX_POS:
            sig = []
            for code in universe_on(h, d):
                cl = closes_until(h, code, d, 6)
                if code in pos or len(cl) < 6 or px(code) is None or cl[-1] != px(code):
                    continue
                r = cl[-1] / cl[-6] - 1
                if r <= s.drop and not fin_bad(code, d, "deficit"):
                    sig.append((r, code))
            for _, code in sorted(sig)[:NEW_PER_DAY]:
                if len(pos) >= MAX_POS:
                    break
                price = px(code) * (1 + SLIP)
                qty = int(min(equity * PER_POS, cash) // (price * (1 + BUY_FEE)))
                if qty >= 1:
                    cash -= qty * price * (1 + BUY_FEE)
                    pos[code] = {"qty": qty, "avg": price, "age": 0}
        eq.append((d, cash + sum(p["qty"] * (px(c) or p["avg"]) for c, p in pos.items())))
    return {"eq": eq, "trades": trades}


def stats(res: dict, a: date, b: date) -> str:
    e = [(d, v) for d, v in res["eq"] if a <= d <= b]
    start = next((v for d, v in reversed(res["eq"]) if d < a), 10_000_000.0)
    peak, mdd = start, 0.0
    for _, v in e:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return f"{e[-1][1] / start - 1:+.1%} ({mdd:.0%})"


def index_ret(days: list[date], a: date, b: date) -> str:
    ix = daily_bars(INDEX)
    s = next(ix[f"{d:%Y%m%d}"]["c"] for d in reversed(days) if d < a and f"{d:%Y%m%d}" in ix)
    return f"{ix[f'{b:%Y%m%d}']['c'] / s - 1:+.1%}"


def main() -> None:
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = [d for d in trading_days(full)]
    periods = [("1년", days[1], days[-1]), ("전반", days[1], HALF), ("후반", next(d for d in days if d > HALF), days[-1])]
    print(f"{days[0]} ~ {days[-1]}, {len(days)}거래일. 수익률 (최대 낙폭)\n")
    print("| 전략 | " + " | ".join(l for l, *_ in periods) + " | 거래 수 | 이긴 비율 | 건당 평균 |")
    print("|---|" + "---|" * (len(periods) + 3))
    print("| KODEX 200 그냥 보유 | " + " | ".join(index_ret(days, a, b) for _, a, b in periods) + " | | | |")
    for s in [Rebound(f"5일 {d:.0%} 이하 반등, {'하락장만' if bear else '항상'}", d, bear_only=bear) for bear in (False, True) for d in (-0.08, -0.12)]:
        res = run(full, s, days)
        t = res["trades"]
        print(f"| {s.name} | " + " | ".join(stats(res, a, b) for _, a, b in periods) +
              f" | {len(t)} | {sum(x > 0 for x in t) / len(t):.0%} | {statistics.mean(t):+.2%} |" if t else f"| {s.name} | 거래 없음 |")


# ---------- 시장 급락 때 지수 ETF 사서 며칠 들기 ----------

def panic_signal(h, d: date, ix: dict[str, int], days: list[date], i: int, drop: float, breadth: int) -> bool:
    """D일 종가까지의 정보로: KODEX 200 5일 등락률이 drop 이하이고, 5일 −10% 넘게 빠진 상위 종목이 breadth개 이상"""
    if i < 5 or not all(f"{days[i - k]:%Y%m%d}" in ix for k in (0, 5)):
        return False
    if ix[f"{d:%Y%m%d}"] / ix[f"{days[i - 5]:%Y%m%d}"] - 1 > drop:
        return False
    n = 0
    for code in universe_on(h, d):
        cl = closes_until(h, code, d, 6)
        n += len(cl) == 6 and cl[-1] / cl[-6] - 1 <= -0.10
    return n >= breadth


def run_etf(h, days: list[date], drop: float, breadth: int, frac: float, hold: int) -> dict:
    """신호가 뜨면 총자산의 frac만큼 KODEX 200을 종가에 사서 hold거래일 뒤 종가에 판다. ETF는 거래세 없음 (수수료만)"""
    ix = {k: v["c"] for k, v in daily_bars(INDEX).items()}
    cash, pos, eq, trades = 10_000_000.0, None, [], []  # pos: [수량, 매수가, 나이]
    for i, d in enumerate(days):
        c = ix.get(f"{d:%Y%m%d}")
        if c is None:
            eq.append((d, eq[-1][1] if eq else cash))
            continue
        if pos:
            pos[2] += 1
            if pos[2] >= hold:
                got = pos[0] * c * (1 - SLIP) * (1 - SELL_FEE)
                cash += got
                trades.append(got / (pos[0] * pos[1] * (1 + BUY_FEE)) - 1)
                pos = None
        if not pos and panic_signal(h, d, ix, days, i, drop, breadth):
            price = c * (1 + SLIP)
            qty = int(cash * frac // (price * (1 + BUY_FEE)))
            if qty >= 1:
                cash -= qty * price * (1 + BUY_FEE)
                pos = [qty, price, 0]
        eq.append((d, cash + (pos[0] * c if pos else 0)))
    return {"eq": eq, "trades": trades}


def etf_main() -> None:
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    periods = [("앞 8개월(정하기)", days[1], TRAIN_END), ("뒤 4개월(확인)", next(d for d in days if d > TRAIN_END), days[-1]), ("1년", days[1], days[-1])]
    print(f"{days[0]} ~ {days[-1]}. 수익률 (최대 낙폭)\n")
    print("| 설정 | " + " | ".join(l for l, *_ in periods) + " | 거래 수 | 이긴 비율 | 건당 평균 |\n|---|---|---|---|---|---|---|")
    print("| KODEX 200 그냥 보유 | " + " | ".join(index_ret(days, a, b) for _, a, b in periods) + " | | | |")
    for drop in (-0.04, -0.06):
        for breadth in (0, 20):
            for hold in (3, 5, 10):
                res = run_etf(full, days, drop, breadth, 0.5, hold)
                t = res["trades"]
                print(f"| 5일 {drop:.0%}↓, 급락종목 {breadth}개↑, {hold}일 보유, 자산 50% | " + " | ".join(stats(res, a, b) for _, a, b in periods) +
                      (f" | {len(t)} | {sum(x > 0 for x in t) / len(t):.0%} | {statistics.mean(t):+.2%} |" if t else " | 0 | | |"))


if __name__ == "__main__":
    import sys
    etf_main() if "etf" in sys.argv else main()
