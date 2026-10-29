"""1년 규칙 백테스트: 모의 자동매매의 규칙(후보 고르기·수량·장중 매수·손절·추세 이탈)을 과거 일봉·1분봉으로 다시 돌린다.

    uv run python -m app.sim need        # 날마다 후보를 골라 받아야 할 일봉 종목·1분봉(종목, 날)을 tools/data/에 쓴다
    python tools/kis_history.py daily …  # (위 목록대로 받기, 키는 개발 도구만 쓴다)
    uv run python -m app.sim run         # 전략별로 돌려 docs/reports/sim-YYYYMMDD.md에 쓴다

미래 정보 금지: D일 후보는 D−1일까지의 종가로 고른다 (아침 브리핑과 같다). 장중 판단은 그 시각까지의 1분봉만 본다.
ponytail: 투자 AI·검증 AI 판단, 장중 급등·거래대금 후보, 이익 돌려줌·시장 탓 미룸은 되돌리지 않는다 (규칙만). AI 판단은 2단계에서 얹는다.
매도는 AI 대신 규칙으로 본다: 강제 손절 −10% 절반·−15% 전부, 손절선 −7%(켜면), 종가가 20일 평균 아래면 종가에 판다.
"""

import argparse
import json
import random
import statistics
from bisect import bisect_left
from functools import cache
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

from psycopg.rows import dict_row

from app import config
from app.backtest import History, load_history, universe_on
from app.db import connect
from app.functions.metrics import volatility

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "tools" / "data"
KIS = DATA / "kis"
INDEX = "069500"  # KODEX 200: 코스피 대신 (지수 분봉은 과거가 없다)
START, TRAIN_END = date(2025, 10, 28), date(2026, 6, 30)  # 과거 1분봉은 2025-10-28부터. 앞 8개월로 고르고 뒤 4개월로 시험
PICKS, PICK_BUFFER = 3, 5  # 아침 후보 3개. 갖고 있는 종목은 건너뛰니 상위 5개 안에서 고른다 (그만큼 1분봉을 받아 둔다. 시간을 줄이려고 8 → 5)
HOT_5D = 0.10  # 5일 +10% 넘게 오른 종목은 사람 확인이라 자동매매가 사지 않는다
BUY_FEE, SELL_FEE, SELL_TAX = 0.00015, 0.00015, 0.0020
MAX_STOCK, RISK, MAX_EXPOSURE = 0.35, 0.02, 0.70  # auto_trader.dart autoMaxStockPct·autoRiskPct·autoMaxExposurePct
STOP, HARD, HARD_ALL = 0.93, 0.90, 0.85  # 손절선 −7%, 강제 손절 −10% 절반, −15% 전부
CHECKS = [f"{h:02d}{m:02d}00" for h in range(9, 12) for m in (5, 35) if (h, m) <= (11, 5)]  # 30분마다 다시 묻는다. 1분봉을 오전(09:00~11:29)만 받아 09:05~11:05까지만 본다 (앱은 15:20까지)


# ---------- 규칙 (auto_trader.dart·analysis.py와 같은 식) ----------

def trend(closes: list[int]) -> tuple[bool, float] | None:
    """(상승 추세인가, 20거래일 등락률 %). 종가가 20일 평균 위이고 20일 평균이 5거래일 전보다 높음 (briefing.trend_ranks)"""
    if len(closes) < 25:
        return None
    c = closes[-25:]
    ma, before = sum(c[-20:]) / 20, sum(c[-25:-5]) / 20
    return c[-1] >= ma and ma >= before, (c[-1] - c[-21]) * 100 / c[-21]


def vol_pct(closes: list[int]) -> float | None:
    """최근 20거래일 하루 등락률 표준편차 % (briefing.daily_vol_pct)"""
    r = closes[-21:]
    return statistics.pstdev(b / a - 1 for a, b in zip(r, r[1:])) * 100 if len(r) == 21 else None


def buy_room(cash: int, equity: int, invested: int, vol: float | None, half: bool) -> int:
    """auto_trader.dart buyRoom: 종목당 살 총액의 35%, 변동성 몫(총자산 2% / 하루 변동 2배), 주식 비중 70%까지"""
    cap = int((cash + 0) * MAX_STOCK)  # 살 총액 = 주문 가능 금액 전부 (오늘 쓴 돈은 cash에서 이미 빠졌다)
    if vol:
        cap = min(cap, int(equity * RISK / (2 * vol / 100)))
    room = min(cap // 2 if half else cap, cash, int(equity * MAX_EXPOSURE) - invested)
    return max(room, 0)


def falling(bars: list[dict]) -> bool:
    """analysis.falling_now: 5분 저가가 3번 연속 낮아지고 지금 가격이 VWAP 아래"""
    if len(bars) < 15:
        return False
    lows = [min(b["l"] for b in bars[i:i + 5]) for i in range(len(bars) - 15, len(bars), 5)]
    vol = sum(b["v"] for b in bars)
    vwap = sum(b["c"] * b["v"] for b in bars) / vol if vol else bars[-1]["c"]
    return lows[0] > lows[1] > lows[2] and bars[-1]["c"] < vwap


def sell_value(qty: int, price: float) -> float:
    return qty * price * (1 - SELL_FEE - SELL_TAX)


# ---------- 자료 ----------

def closes_until(h: History, code: str, t: date, n: int = 26) -> list[int]:
    out = [c for d in h.dates if d <= t and (c := h.close.get((d, code)))]
    return out[-n:]


_RANKS: dict = {}


def vol_ranks(h: History, t: date) -> dict[str, float]:
    """t일까지 60일 변동성의 같은 시장 안 순위 0~1 (analysis.volatility_ranks와 같은 식. 대상은 그날 시총 상위 코스피 100·코스닥 50)"""
    if t not in _RANKS:
        by_market: dict[str, dict[str, float]] = {}
        for code in universe_on(h, t):
            if (v := volatility(closes_until(h, code, t, 61), 60, [])["value"]) is not None:
                by_market.setdefault(h.market[code], {})[code] = v
        _RANKS[t] = {c: sum(1 for x in vs.values() if x <= v) / len(vs) for vs in by_market.values() for c, v in vs.items()}
    return _RANKS[t]


def candidates(h: History, t: date, held: set[str], count: int = PICKS, cap: float | None = None) -> list[str]:
    """t일 장 마감까지의 종가로 다음 날 아침 후보 (상승 추세 먼저, 20일 등락률 강한 순). 5일 +10% 급등은 뺀다.
    cap: 60일 변동성 순위가 이보다 높으면 뺀다 (앱은 0.8, suitability.MAX_VOLATILITY_RANK_FOR_BUY). 빼고 나서 count개를 채운다"""
    scored, ranks = [], vol_ranks(h, t) if cap else {}
    for code in universe_on(h, t):
        c = closes_until(h, code, t)
        if code in held or not (tr := trend(c)) or len(c) < 6 or c[-1] / c[-6] - 1 > HOT_5D:
            continue
        if cap and ranks.get(code, 0) > cap:
            continue
        scored.append((not tr[0], -tr[1], code))
    return [code for *_, code in sorted(scored)[:count]]


@cache
def op_income_reports() -> dict[str, list]:
    """종목 → [(접수일, 영업이익, 전년 같은 기간)] 접수일 오름차순. 연결 기준, 사업보고서는 연간 값, 그 밖은 올해 누적 (analysis.financial_basis와 같은 식)"""
    out: dict[str, list] = {}
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        for r in conn.execute("SELECT stock_code, reprt_code, rcept_no, amount, prev_amount, add_amount, prev_add_amount FROM financials "
                              "WHERE fs_div = 'CFS' AND account LIKE '영업이익%' ORDER BY rcept_no"):
            annual = r["reprt_code"] == "11011"
            now, before = (r["amount"], r["prev_amount"]) if annual else (
                r["add_amount"] if r["add_amount"] is not None else r["amount"],
                r["prev_add_amount"] if r["prev_add_amount"] is not None else r["prev_amount"])
            if now is not None:
                out.setdefault(r["stock_code"], []).append((date(int(r["rcept_no"][:4]), int(r["rcept_no"][4:6]), int(r["rcept_no"][6:8])), now, before))
    return out


def fin_bad(code: str, d: date, mode: str) -> bool:
    """d일 아침까지 접수된 가장 최근 정기보고서 기준 재무 악화. 재무가 없으면(미확인) 거르지 않는다"""
    rows = op_income_reports().get(code, [])
    i = bisect_left([x[0] for x in rows], d)  # d일 이전 접수만
    if not mode or i == 0:
        return False
    _, now, before = rows[i - 1]
    return now < 0 or (mode == "half" and before is not None and before > 0 and now < before / 2)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def daily_bars(code: str) -> dict[str, dict]:
    return {b["d"]: b for b in load_json(KIS / "daily" / f"{code}.json") or []}


def minute_bars(code: str, day: date) -> list[dict] | None:
    return load_json(KIS / "minute" / f"{code}_{day:%Y%m%d}.json")


# ---------- 돌리기 ----------

@dataclass
class Strategy:
    name: str
    entry: str = "intraday"  # intraday: 09:05부터 30분마다 / once: 10:30 한 번 / close: 종가에
    stop: bool = True  # 손절선 −7%
    early_down: bool = True  # 10시 전 지수 −1%면 안 삼 (10/26 사용자 결정)
    bear_buy: str = "half"  # 코스피 20일 평균 아래면 half: 절반만 / none: 안 삼 / full: 평소대로
    skip: float = 0.0  # 소음 점검용: 이 비율만큼 매수를 무작위로 건너뛴다 (seed로 고정)
    seed: int = 0
    vol_cap: float | None = None  # 60일 변동성 순위 상한 (앱 0.8). None이면 상한 없음 (지금까지 시뮬)
    fin_filter: str = ""  # 재무 악화 종목은 안 삼 — deficit: 영업적자 / half: 영업적자이거나 전년 같은 기간 영업이익이 반 이하


@dataclass
class Book:
    cash: float
    pos: dict = field(default_factory=dict)  # code → {qty, avg, half_done}
    trades: list = field(default_factory=list)  # (날, 종목, 매수/매도, 수량, 가격, 손익)
    days: list = field(default_factory=list)  # (날, 총자산, 주식 비중)
    no_minute: int = 0


def run(h: History, s: Strategy, days: list[date]) -> Book:
    book = Book(cash=10_000_000)
    rng = random.Random(s.seed)
    index = daily_bars(INDEX)
    for i in range(1, len(days)):
        prev, d = days[i - 1], days[i]
        key = f"{d:%Y%m%d}"
        bars = {code: daily_bars(code).get(key) for code in book.pos}
        # 1) 보유 종목: 장중 손절 (일봉 저가로), 종가에 20일 평균 이탈이면 매도
        for code, p in list(book.pos.items()):
            b = bars.get(code)
            if not b:
                continue
            for level, part in (([(STOP, "all")] if s.stop else []) + [(HARD, "half"), (HARD_ALL, "all")]):  # 높은 선부터
                if code not in book.pos:
                    break
                if b["l"] > p["avg"] * level or (part == "half" and p["half_done"]):
                    continue
                price = min(b["o"], p["avg"] * level)  # 시가가 선 아래로 갭하면 시가에
                qty = p["qty"] if part == "all" or p["qty"] < 2 else p["qty"] // 2
                _sell(book, d, code, qty, price, f"손절선 −7%" if level == STOP else "강제 −10% 절반" if part == "half" else "강제 −15% 전부")
                if code in book.pos and part == "half":
                    p["half_done"] = True
            if code in book.pos:
                c = closes_until(h, code, d, 20)
                if len(c) == 20 and b["c"] < sum(c) / 20:
                    _sell(book, d, code, book.pos[code]["qty"], b["c"], "20일 평균 이탈")
        # 2) 아침 후보 매수
        ix = [index[k]["c"] for k in sorted(index) if k < key][-20:]
        bear = len(ix) == 20 and ix[-1] < sum(ix) / 20
        if bear and s.bear_buy == "none":
            pass
        else:
            ix_prev = ix[-1] if ix else None
            ix_min = minute_bars(INDEX, d) or []
            picks = [c for c in candidates(h, prev, set(), PICK_BUFFER, s.vol_cap) if c not in book.pos and not fin_bad(c, d, s.fin_filter)][:PICKS]
            for code in picks:
                if s.skip and rng.random() < s.skip:
                    continue
                _try_buy(book, h, s, d, code, prev, half=bear and s.bear_buy == "half", ix_prev=ix_prev, ix_min=ix_min)
        # 3) 마감 값
        held = sum(p["qty"] * (daily_bars(c).get(key) or {"c": p["avg"]})["c"] for c, p in book.pos.items())
        equity = book.cash + held
        book.days.append((d, equity, held / equity if equity else 0))
    return book


def _equity(book: Book, d: date) -> tuple[float, float]:
    key = f"{d:%Y%m%d}"
    held = sum(p["qty"] * (daily_bars(c).get(key) or {"o": p["avg"]})["o"] for c, p in book.pos.items())
    return book.cash + held, held


def _try_buy(book: Book, h: History, s: Strategy, d: date, code: str, prev: date, half: bool, ix_prev, ix_min) -> None:
    day = daily_bars(code).get(f"{d:%Y%m%d}")
    if not day:
        return
    price, mins = None, minute_bars(code, d)
    if s.entry == "close":
        price = day["c"]
    elif not mins:
        book.no_minute += 1
        price = day["o"]  # 1분봉이 없으면 시가에 산 것으로 본다 (몇 건인지 결과에 적는다)
    else:
        for t in (["103000"] if s.entry == "once" else CHECKS):
            seen = [b for b in mins if b["t"] <= t]
            if not seen:
                continue
            if s.early_down and t < "100000" and ix_prev:
                ix_now = [b for b in ix_min if b["t"] <= t]
                if ix_now and ix_now[-1]["c"] / ix_prev - 1 <= -0.01:
                    continue
            if falling(seen):
                continue
            price = seen[-1]["c"]
            break
    if not price:
        return
    equity, invested = _equity(book, d)
    room = buy_room(int(book.cash), int(equity), int(invested), vol_pct(closes_until(h, code, prev, 21)), half)
    qty = int(room // (price * (1 + BUY_FEE)))
    if qty < 1:
        return
    book.cash -= qty * price * (1 + BUY_FEE)
    book.pos[code] = {"qty": qty, "avg": price, "half_done": False}
    book.trades.append((d, code, "buy", qty, price, 0.0))


def _sell(book: Book, d: date, code: str, qty: int, price: float, why: str = "") -> None:
    p = book.pos[code]
    got = sell_value(qty, price)
    book.cash += got
    book.trades.append((d, code, "sell", qty, price, got - qty * p["avg"] * (1 + BUY_FEE), why))
    p["qty"] -= qty
    if p["qty"] <= 0:
        del book.pos[code]


# ---------- 결과 ----------

def summary(book: Book, days: list[date], first: date, last: date) -> dict:
    index = daily_bars(INDEX)
    eq = {d: (e, x) for d, e, x in book.days}
    window = [d for d in days if first <= d <= last and d in eq]
    if len(window) < 2:
        return {}
    prev_day = days[days.index(window[0]) - 1]
    start = prev_e = eq[prev_day][0] if prev_day in eq else 10_000_000
    prev_x = eq[prev_day][1] if prev_day in eq else 0.0
    peak, mdd, up, down, upk, downk, bench = start, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0
    k_first = index.get(f"{prev_day:%Y%m%d}")
    for d in window:
        e, x = eq[d]
        r = e / prev_e - 1
        k0, k1 = index.get(f"{prev_day:%Y%m%d}"), index.get(f"{d:%Y%m%d}")
        k = k1["c"] / k0["c"] - 1 if k0 and k1 else 0.0
        bench *= 1 + prev_x * k  # 그 전날 든 주식 비중만큼 지수(KODEX 200)를 든 경우
        if k > 0:
            up, upk = up + r, upk + k
        elif k < 0:
            down, downk = down + r, downk + k
        peak = max(peak, e)
        mdd = min(mdd, e / peak - 1)
        prev_e, prev_x, prev_day = e, x, d
    sells = [t for t in book.trades if t[2] == "sell" and first <= t[0] <= last]
    k_last = index.get(f"{window[-1]:%Y%m%d}")
    return {"total": prev_e / start - 1, "mdd": mdd, "exposure": sum(eq[d][1] for d in window) / len(window),
            "up_capture": up / upk if upk else 0, "down_capture": down / downk if downk else 0,
            "sells": len(sells), "sell_win": sum(1 for t in sells if t[5] > 0) / len(sells) if sells else 0,
            "buys": sum(1 for t in book.trades if t[2] == "buy" and first <= t[0] <= last),
            "bench_same_exposure": bench - 1, "index": (k_last["c"] / k_first["c"] - 1) if k_first and k_last else 0}


STRATEGIES = [
    Strategy("지금 앱 규칙 (09:05부터 30분마다, 손절선 −7%)"),
    Strategy("10:30에 한 번만 매수", entry="once"),
    Strategy("종가에만 매수", entry="close"),
    Strategy("손절선 −7% 없음 (강제 손절·추세 이탈만)", stop=False),
    Strategy("하락장(코스피 20일 평균 아래)엔 새로 안 삼", bear_buy="none"),
    # 아래 둘은 위 결과를 보고 합친 탐색용이다 (이미 본 데이터에 맞춘 것이라 과적합 주의)
    Strategy("[합침] 종가 매수 + 하락장엔 안 삼", entry="close", bear_buy="none"),
    Strategy("[합침] 종가 매수 + 하락장엔 안 삼 + 손절선 −7% 없음", entry="close", bear_buy="none", stop=False),
]


def trading_days(h: History) -> list[date]:
    return [d for d in h.all_dates if d >= START]


def need() -> None:
    """받아야 할 일봉 종목과 1분봉(종목, 날): 날마다 후보 PICK_BUFFER개 + 지수 (보유 중이면 건너뛰니 여유 있게)"""
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    codes, minutes = {INDEX}, []
    for prev, d in zip(days, days[1:]):
        for code in candidates(full.until(prev), prev, set(), PICK_BUFFER):
            codes.add(code)
            minutes.append([code, f"{d:%Y%m%d}"])
        minutes.append([INDEX, f"{d:%Y%m%d}"])
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "need_daily.txt").write_text(" ".join(sorted(codes)), encoding="utf-8")
    (DATA / "need_minute.json").write_text(json.dumps(minutes), encoding="utf-8")
    print(f"일봉 {len(codes)}종목, 1분봉 {len(minutes)}개 (종목·날)")


def report() -> str:
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    periods = [("앞 8개월 (고르기)", days[1], TRAIN_END), ("뒤 4개월 (시험)", next(d for d in days if d > TRAIN_END), days[-1]),
               ("1년 전체", days[1], days[-1])]
    lines = [f"# 1년 규칙 백테스트 ({days[0]} ~ {days[-1]}, {len(days)}거래일)", "",
             "시작 1,000만 원. 아침 후보 3개(전날 종가 기준 상승 추세·20일 등락률 강한 순, 5일 +10% 급등 제외)를 앱 규칙(수량·장중 하락 중 매수 금지·"
             "10시 전 지수 −1% 매수 쉬기·하락장 절반)으로 사고, 강제 손절·손절선·20일 평균 이탈로 판다. 수수료 0.015%·매도세 0.20%. "
             "투자 AI·검증 AI 판단은 넣지 않았다 (규칙만). 과거 결과는 미래 수익을 보장하지 않는다.", "",
             "| 전략 | 기간 | 수익률 | 같은 비중 지수 | 지수(100%) | 최대 낙폭 | 평균 주식 비중 | 오른 날 따라감 | 내린 날 따라감 | 매수 | 매도 (이익 비율) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    notes = []
    for s in STRATEGIES:
        book = run(full, s, days)
        for label, a, b in periods:
            r = summary(book, days, a, b)
            if r:
                lines.append(f"| {s.name} | {label} | {r['total']:+.1%} | {r['bench_same_exposure']:+.1%} | {r['index']:+.1%} | {r['mdd']:.1%} | "
                             f"{r['exposure']:.0%} | {r['up_capture']:.2f} | {r['down_capture']:.2f} | {r['buys']} | {r['sells']} ({r['sell_win']:.0%}) |")
        if book.no_minute:
            notes.append(f"- {s.name}: 1분봉이 없어 시가에 산 것으로 본 매수 {book.no_minute}건")
    lines += ["", "## 읽는 법", "",
              "- **같은 비중 지수**: 그 전략이 날마다 든 주식 비중만큼 KODEX 200을 들었다면. 이걸 못 이기면 종목 고르기·타이밍이 손해라는 뜻",
              "- **오른 날·내린 날 따라감**: 지수가 오른(내린) 날 지수 등락 합 대비 계좌 등락 합. 오른 날은 높을수록, 내린 날은 낮을수록 좋다",
              "- 전략은 앞 8개월 결과로만 고르고, 뒤 4개월(폭락 포함)은 고른 뒤 확인만 한다", *notes]
    return "\n".join(lines)


def why_table(book: Book) -> list[str]:
    rows: dict[str, list[float]] = {}
    for t in book.trades:
        if t[2] == "sell":
            rows.setdefault(t[6] if len(t) > 6 else "", []).append(t[5])
    return [f"| {why or '기타'} | {len(v)} | {sum(1 for x in v if x > 0) / len(v):.0%} | {sum(v):+,.0f}원 | {sum(v) / len(v):+,.0f}원 |"
            for why, v in sorted(rows.items(), key=lambda kv: sum(kv[1]))]


def noise_report(runs: int = 20, skip: float = 0.1) -> str:
    """같은 전략에서 매수를 무작위로 skip 비율만큼 빼고 runs번 돌려 결과가 얼마나 흔들리는지 본다.
    전략끼리의 차이가 이 흔들림보다 작으면 그 차이는 믿을 수 없다 (거래가 몇 건만 달라져도 보유 종목이 갈라져 결과가 크게 달라지는 구조)"""
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    test_start = next(d for d in days if d > TRAIN_END)
    rows = [f"매수의 {skip:.0%}를 무작위로 건너뛰고 {runs}번 돌린 1년 수익률 분포 (시작 1,000만 원)", "",
            "| 전략 | 건너뛰기 없음 | 최저 | 중앙값 | 최고 | 뒤 4개월 최저 | 뒤 4개월 최고 |", "|---|---|---|---|---|---|---|"]
    for base in (STRATEGIES[0], STRATEGIES[2], STRATEGIES[4]):
        zero = summary(run(full, base, days), days, days[1], days[-1])["total"]
        full_r, test_r = [], []
        for seed in range(1, runs + 1):
            book = run(full, replace(base, skip=skip, seed=seed), days)
            full_r.append(summary(book, days, days[1], days[-1])["total"])
            test_r.append(summary(book, days, test_start, days[-1])["total"])
        rows.append(f"| {base.name} | {zero:+.1%} | {min(full_r):+.1%} | {statistics.median(full_r):+.1%} | {max(full_r):+.1%} | "
                    f"{min(test_r):+.1%} | {max(test_r):+.1%} |")
    return "\n".join(rows)


def gap_report() -> str:
    """후보 종목이 아침에 갭으로 오르고 장중에 되돌리는지: 전날 종가 → 시가(갭), 시가 → 종가(장중). KODEX 200과 나란히"""
    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        full = load_history(conn)
    days = trading_days(full)
    index = daily_bars(INDEX)
    gaps, intra, ix_gap, ix_intra = [], [], [], []
    for prev, d in zip(days, days[1:]):
        key, pk = f"{d:%Y%m%d}", f"{prev:%Y%m%d}"
        for code in candidates(full.until(prev), prev, set(), PICKS):
            b, pb = daily_bars(code).get(key), daily_bars(code).get(pk)
            if b and pb:
                gaps.append(b["o"] / pb["c"] - 1)
                intra.append(b["c"] / b["o"] - 1)
        ib, ipb = index.get(key), index.get(pk)
        if ib and ipb:
            ix_gap.append(ib["o"] / ipb["c"] - 1)
            ix_intra.append(ib["c"] / ib["o"] - 1)
    m = lambda xs: sum(xs) / len(xs) * 100
    rows = ["| | 평균 갭 (전날 종가→시가) | 평균 장중 (시가→종가) | 표본 |", "|---|---|---|---|",
            f"| 아침 후보 (상위 3) | {m(gaps):+.2f}% | {m(intra):+.2f}% | {len(gaps)} |",
            f"| KODEX 200 | {m(ix_gap):+.2f}% | {m(ix_intra):+.2f}% | {len(ix_gap)} |"]
    # 실제 매수 시각의 가격 → 그날 종가 (1분봉)
    at = {"09:05": [], "10:30": []}
    for prev, d in zip(days, days[1:]):
        for code in candidates(full.until(prev), prev, set(), PICKS):
            day, mins = daily_bars(code).get(f"{d:%Y%m%d}"), minute_bars(code, d)
            if not (day and mins):
                continue
            for label, t in (("09:05", "090500"), ("10:30", "103000")):
                seen = [b for b in mins if b["t"] <= t]
                if seen:
                    at[label].append(day["c"] / seen[-1]["c"] - 1)
    rows += ["", "| 매수 시각 | 그 가격 → 그날 종가 (평균) | 오른 날 비율 | 표본 |", "|---|---|---|---|"]
    rows += [f"| {label} | {m(v):+.2f}% | {sum(1 for x in v if x > 0) / len(v):.0%} | {len(v)} |" for label, v in at.items() if v]
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="1년 규칙 백테스트")
    parser.add_argument("command", choices=["need", "run", "why", "gap", "noise"])
    args = parser.parse_args()
    if args.command == "need":
        need()
    elif args.command == "noise":
        print(noise_report())
    elif args.command == "gap":
        print(gap_report())
    elif args.command == "why":
        with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
            full = load_history(conn)
        days = trading_days(full)
        for s in STRATEGIES:
            print(f"\n### {s.name}\n| 매도 이유 | 건수 | 이익 비율 | 합계 손익 | 건당 |\n|---|---|---|---|---|")
            print("\n".join(why_table(run(full, s, days))))
    else:
        text = report()
        out = ROOT / "docs" / "reports" / f"sim-{date.today():%Y%m%d}.md"
        out.write_text(text + "\n", encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
