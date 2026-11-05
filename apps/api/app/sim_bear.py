"""하락장 수익 시험 (규칙만, AI 0원): 상대강도·실적 급증 공시·저변동 우량·인버스 가속 하락.

    uv run python -m app.sim_bear

종가 일봉만 쓴다. D일 종가로 신호를 보고 D일 종가에 산다 (슬리피지 0.1% 반영). 앞 8개월로 정하고 뒤 4개월로 확인한다.
ponytail: 장중 손절 갭은 모른다 (종가 기준). 인버스는 KODEX 200 반대 수익으로 근사했다 (실제 상품 시세 없음).
"""

import json
import statistics
from bisect import bisect_right
from datetime import date
from pathlib import Path

from psycopg.rows import dict_row

from app import config
from app.backtest import load_history, universe_on
from app.db import connect
from app.sim import BUY_FEE, INDEX, SELL_FEE, SELL_TAX, TRAIN_END, closes_until, daily_bars, op_income_reports, trading_days, vol_ranks
from app.sim_rebound import HALF, MAX_POS, NEW_PER_DAY, PER_POS, SLIP, index_ret, stats


def make_ctx(h, days):
    ix = {k: v["c"] for k, v in daily_bars(INDEX).items()}
    ixs = [ix.get(f"{d:%Y%m%d}") for d in days]
    return {"h": h, "days": days, "ix": ixs}


def idx_ret(ctx, i: int, n: int):
    a, b = ctx["ix"][i], ctx["ix"][i - n] if i >= n else None
    return a / b - 1 if a and b else None


def bear(ctx, i: int) -> bool:
    w = [x for x in ctx["ix"][max(0, i - 19):i + 1] if x]
    return len(w) == 20 and w[-1] < sum(w) / 20


def simulate(ctx, pick, only_bear: bool, stop=-0.07, maxhold=20, ma_exit=True) -> dict:
    h, days = ctx["h"], ctx["days"]
    cash, pos, eq, trades = 10_000_000.0, {}, [], []
    for i, d in enumerate(days):
        px = lambda c: h.close.get((d, c))
        for code, p in list(pos.items()):
            c = px(code)
            if not c:
                continue
            p["age"] += 1
            cl = closes_until(h, code, d, 20)
            if c / p["avg"] - 1 <= stop or p["age"] >= maxhold or (ma_exit and len(cl) == 20 and c < sum(cl) / 20):
                got = p["qty"] * c * (1 - SLIP) * (1 - SELL_FEE - SELL_TAX)
                cash += got
                trades.append(got / (p["qty"] * p["avg"] * (1 + BUY_FEE)) - 1)
                del pos[code]
        equity = cash + sum(p["qty"] * (px(c) or p["avg"]) for c, p in pos.items())
        if len(pos) < MAX_POS and (only_bear is False or bear(ctx, i) is (only_bear is True)):  # True: 하락장만, "bull": 상승장만
            for code in [c for c in pick(ctx, i, d) if c not in pos and px(c)][:NEW_PER_DAY]:
                if len(pos) >= MAX_POS:
                    break
                price = px(code) * (1 + SLIP)
                qty = int(min(equity * PER_POS, cash) // (price * (1 + BUY_FEE)))
                if qty >= 1:
                    cash -= qty * price * (1 + BUY_FEE)
                    pos[code] = {"qty": qty, "avg": price, "age": 0}
        eq.append((d, cash + sum(p["qty"] * (px(c) or p["avg"]) for c, p in pos.items())))
    return {"eq": eq, "trades": trades}


# ---------- 신호 ----------

def relative_strength(margin: float):
    """20일 수익률이 지수보다 margin 이상 높고, 종가가 자기 20일 평균 위. 5일 +10% 넘는 급등은 뺀다"""
    def pick(ctx, i, d):
        r_ix = idx_ret(ctx, i, 20)
        if r_ix is None:
            return []
        out = []
        for code in universe_on(ctx["h"], d):
            cl = closes_until(ctx["h"], code, d, 26)
            if len(cl) < 21 or cl[-1] / cl[-6] - 1 > 0.10 or cl[-1] < sum(cl[-20:]) / 20:
                continue
            if (r := cl[-1] / cl[-21] - 1) - r_ix >= margin:
                out.append((-r, code))
        return [c for _, c in sorted(out)]
    return pick


def earnings_jump(ratio: float):
    """정기보고서 접수 다음 거래일: 영업이익이 전년 같은 기간의 ratio배 이상(전년이 적자·0이면 흑자 전환). 시총 상위 대상만"""
    def pick(ctx, i, d):
        h, days = ctx["h"], ctx["days"]
        out = []
        for code in universe_on(h, d):
            rows = op_income_reports().get(code, [])
            dates = [r[0] for r in rows]
            j = bisect_right(dates, days[i - 2]) if i > 1 else 0  # 어제까지 접수된 것
            k = bisect_right(dates, days[i - 1]) if i else 0  # 오늘까지 접수된 것
            for r in rows[j:k]:
                _, now, before = r
                if now > 0 and (before is None or before <= 0 or now >= before * ratio) and h.close.get((d, code)):
                    out.append((-(now / before if before and before > 0 else 99), code))
        return [c for _, c in sorted(out)]
    return pick


def healthy(code: str, d: date) -> bool:
    rows = op_income_reports().get(code, [])
    k = bisect_right([r[0] for r in rows], d)
    return k > 0 and rows[k - 1][1] > 0 and (rows[k - 1][2] is None or rows[k - 1][1] >= rows[k - 1][2])


def low_vol(top: float):
    """60일 변동성 순위가 가장 낮은 top 비율 안, 영업이익이 흑자이고 줄지 않았고, 20일 수익률이 지수 이상"""
    def pick(ctx, i, d):
        r_ix = idx_ret(ctx, i, 20)
        ranks = vol_ranks(ctx["h"], d)
        out = []
        for code, rk in ranks.items():
            cl = closes_until(ctx["h"], code, d, 21)
            if rk <= top and len(cl) == 21 and healthy(code, d) and (r_ix is None or cl[-1] / cl[0] - 1 >= r_ix):
                out.append((rk, code))
        return [c for _, c in sorted(out)]
    return pick


def confirmed_bounce(drop: float):
    """바닥 확인 뒤 매수: 최근 10거래일 고점에서 drop 넘게 빠진 뒤, 그 저점(3일 전)에서 2일 연속 올랐을 때. 떨어지는 칼날은 안 잡는다"""
    def pick(ctx, i, d):
        out = []
        for code in universe_on(ctx["h"], d):
            cl = closes_until(ctx["h"], code, d, 10)
            if len(cl) == 10 and cl[-1] > cl[-2] > cl[-3] and cl[-3] == min(cl) and cl[-3] / max(cl) - 1 <= -drop:
                out.append((cl[-3] / max(cl), code))
        return [c for _, c in sorted(out)]
    return pick


def counter_trend(stock_up: float):
    """시장 역행: 오늘 KODEX 200이 −1% 이하인데 종목은 stock_up 이상 오른 날 (종가 매수)"""
    def pick(ctx, i, d):
        r = idx_ret(ctx, i, 1)
        if r is None or r > -0.01:
            return []
        out = []
        for code in universe_on(ctx["h"], d):
            cl = closes_until(ctx["h"], code, d, 2)
            if len(cl) == 2 and cl[-1] / cl[-2] - 1 >= stock_up:
                out.append((-(cl[-1] / cl[-2]), code))
        return [c for _, c in sorted(out)]
    return pick


def large_cap_rs(top_n: int, margin: float):
    """상대강도(1번)와 같되 그날 시가총액 상위 top_n개 대형주만"""
    inner = relative_strength(margin)
    def pick(ctx, i, d):
        caps = ctx["h"].caps(d)
        big = set(sorted(caps, key=caps.get, reverse=True)[:top_n])
        return [c for c in inner(ctx, i, d) if c in big]
    return pick


def breakout(n: int):
    """상승장용: 종가가 최근 n거래일 최고가를 넘고(신고가) 20일 평균 위. 5일 +10% 넘는 급등은 뺀다"""
    def pick(ctx, i, d):
        out = []
        for code in universe_on(ctx["h"], d):
            cl = closes_until(ctx["h"], code, d, n + 1)
            if len(cl) == n + 1 and cl[-1] > max(cl[:-1]) and cl[-1] / cl[-6] - 1 <= 0.10:
                out.append((-(cl[-1] / cl[0]), code))
        return [c for _, c in sorted(out)]
    return pick


# ---------- 거래량·거래대금 (tools/kis_volume.py로 받은 것) ----------

_VOL: dict = {}


def vols(code: str, d: date, n: int) -> list[tuple[int, int, int]]:
    """d일까지 최근 n거래일 (거래량, 거래대금, 종가). 받은 자료가 없으면 빈 목록"""
    if code not in _VOL:
        path = Path(__file__).resolve().parents[3] / "tools" / "data" / "kis" / "volume" / f"{code}.json"
        _VOL[code] = {r["d"]: (r["v"], r["a"], r["c"]) for r in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else {}
    rows = _VOL[code]
    return [rows[k] for k in sorted(rows) if k <= f"{d:%Y%m%d}"][-n:]


def volume_surge(mult: float, up: float):
    """거래량이 20일 평균의 mult배 이상이면서 종가가 하루 up 이상 오른 날 (큰 돈이 들어온 날)"""
    def pick(ctx, i, d):
        out = []
        for code in universe_on(ctx["h"], d):
            r = vols(code, d, 21)
            if len(r) == 21 and (avg := sum(x[0] for x in r[:-1]) / 20) > 0 and r[-1][0] >= mult * avg and r[-1][2] / r[-2][2] - 1 >= up:
                out.append((-r[-1][0] / avg, code))
        return [c for _, c in sorted(out)]
    return pick


def selling_exhaustion(mult: float, drop: float):
    """투매 소진: 5일 drop 넘게 빠졌고, 어제 거래량이 20일 평균의 mult배 이상이었다가 오늘은 어제의 절반 이하로 줄고 종가가 어제보다 높음"""
    def pick(ctx, i, d):
        out = []
        for code in universe_on(ctx["h"], d):
            r = vols(code, d, 22)
            if len(r) == 22 and (avg := sum(x[0] for x in r[:-2]) / 20) > 0 and r[-2][0] >= mult * avg and r[-1][0] <= r[-2][0] / 2 \
                    and r[-1][2] > r[-2][2] and r[-1][2] / r[-7][2] - 1 <= -drop:
                out.append((r[-1][2] / r[-7][2], code))
        return [c for _, c in sorted(out)]
    return pick


def leaders(top: float, margin: float):
    """주도주: 20일 평균 거래대금이 대상 종목 중 상위 top 비율이고 20일 수익률이 지수보다 margin 이상 높고 20일 평균 위"""
    def pick(ctx, i, d):
        r_ix = idx_ret(ctx, i, 20)
        if r_ix is None:
            return []
        amt = {}
        for code in universe_on(ctx["h"], d):
            r = vols(code, d, 20)
            if len(r) == 20:
                amt[code] = sum(x[1] for x in r) / 20
        cut = sorted(amt.values(), reverse=True)[max(int(len(amt) * top) - 1, 0)] if amt else 0
        out = []
        for code, a in amt.items():
            cl = closes_until(ctx["h"], code, d, 21)
            if a >= cut and len(cl) == 21 and cl[-1] / cl[0] - 1 - r_ix >= margin and cl[-1] >= sum(cl[1:]) / 20:
                out.append((-(cl[-1] / cl[0]), code))
        return [c for _, c in sorted(out)]
    return pick


# ---------- 인버스 (KODEX 200 반대 수익 근사) ----------

def inverse(ctx, drop5: float, below: float, breadth: int, hold: int, frac: float = 0.5) -> dict:
    h, days, ixs = ctx["h"], ctx["days"], ctx["ix"]
    eq, cur, left, trades, start = [], 10_000_000.0, 0, [], 0.0
    for i, d in enumerate(days):
        if left and ixs[i] and ixs[i - 1]:
            cur *= 1 + frac * (-(ixs[i] / ixs[i - 1] - 1) - 0.0064 / 250)
            left -= 1
            if not left:
                cur *= 1 - frac * 0.0007
                trades.append(cur / start - 1)
        elif not left and i >= 20 and ixs[i] and (r5 := idx_ret(ctx, i, 5)) is not None:
            ma = sum(x for x in ixs[i - 19:i + 1] if x) / 20
            if r5 <= drop5 and ixs[i] <= ma * (1 - below) and ma < sum(x for x in ixs[i - 24:i - 4] if x) / 20:  # 평균도 내리는 중
                n = sum(1 for code in universe_on(h, d) if len(cl := closes_until(h, code, d, 6)) == 6 and cl[-1] / cl[0] - 1 <= -0.10)
                if n >= breadth:
                    left, cur = hold, cur * (1 - frac * 0.0007)
                    start = cur
        eq.append((d, cur))
    return {"eq": eq, "trades": trades}


def main() -> None:
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    ctx = make_ctx(full, days)
    P = [("앞 8개월(정하기)", days[1], TRAIN_END), ("뒤 4개월(확인)", next(d for d in days if d > TRAIN_END), days[-1]),
         ("전반", days[1], HALF), ("후반", next(d for d in days if d > HALF), days[-1]), ("1년", days[1], days[-1])]
    print(f"{days[0]} ~ {days[-1]}. 수익률 (최대 낙폭). 현금만 들면 0%\n")
    print("| 시험 | " + " | ".join(l for l, *_ in P) + " | 거래 | 이긴 비율 | 건당 평균 |\n|---|" + "---|" * (len(P) + 3))
    print("| KODEX 200 그냥 보유 | " + " | ".join(index_ret(days, a, b) for _, a, b in P) + " | | | |")

    def row(name, res):
        t = res["trades"]
        print(f"| {name} | " + " | ".join(stats(res, a, b) for _, a, b in P) +
              (f" | {len(t)} | {sum(x > 0 for x in t) / len(t):.0%} | {statistics.mean(t):+.2%} |" if t else " | | | |"), flush=True)

    import sys
    if "volume" in sys.argv:
        for regime, tag in ((True, "하락장만"), (False, "항상")):
            for mult in (3.0, 5.0):
                row(f"V1 거래량 {mult:.0f}배↑·종가 +3%↑, {tag}", simulate(ctx, volume_surge(mult, 0.03), regime))
            for mult in (3.0, 5.0):
                row(f"V2 투매 소진(어제 {mult:.0f}배 거래량→오늘 절반↓·반등, 5일 −10%↓), {tag}", simulate(ctx, selling_exhaustion(mult, 0.10), regime))
            for top, m in ((0.2, 0.0), (0.2, 0.10), (0.4, 0.05)):
                row(f"V3 주도주 거래대금 상위 {top:.0%}·지수 +{m:.0%}p, {tag}", simulate(ctx, leaders(top, m), regime))
        return
    if "more" in sys.argv:
        for regime, tag in ((True, "하락장만"), (False, "항상")):
            for dp in (0.15, 0.25):
                row(f"5 바닥 확인 반등 고점 −{dp:.0%}↓, {tag}", simulate(ctx, confirmed_bounce(dp), regime))
            for up in (0.02, 0.04):
                row(f"6 시장 −1%↓인 날 +{up:.0%}↑ 역행주, {tag}", simulate(ctx, counter_trend(up), regime))
            for m in (0.05, 0.15):
                row(f"7 대형주 30 상대강도 +{m:.0%}p, {tag}", simulate(ctx, large_cap_rs(30, m), regime))
        for n in (20, 60):
            row(f"8 {n}일 신고가 돌파, 상승장만", simulate(ctx, breakout(n), "bull"))
            row(f"8 {n}일 신고가 돌파, 항상", simulate(ctx, breakout(n), False))
        return
    for only_bear in (True, False):
        tag = "하락장만" if only_bear else "항상"
        for m in (0.10, 0.20):
            row(f"1 상대강도 지수보다 +{m:.0%}p, {tag}", simulate(ctx, relative_strength(m), only_bear))
        for ratio in (1.5, 2.0):
            row(f"2 영업이익 {ratio}배↑ 공시 다음날, {tag}", simulate(ctx, earnings_jump(ratio), only_bear))
        for top in (0.25, 0.4):
            row(f"3 저변동 하위 {top:.0%}·흑자, {tag}", simulate(ctx, low_vol(top), only_bear))
    for drop5, below, breadth, hold in ((-0.05, 0.03, 10, 3), (-0.05, 0.03, 20, 3), (-0.08, 0.05, 20, 3), (-0.05, 0.03, 10, 5)):
        row(f"4 인버스 50%: 5일 {drop5:.0%}↓·평균 {below:.0%} 아래·급락 {breadth}개↑, {hold}일", inverse(ctx, drop5, below, breadth, hold))


if __name__ == "__main__":
    main()
