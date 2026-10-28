"""1년 규칙 백테스트(sim.py): 앱 규칙과 같은 식인지, 미래 정보를 쓰지 않는지, 손절·수량 계산을 확인한다. DB·인터넷 없이."""

from datetime import date, timedelta

from app import sim
from app.backtest import History

DAYS = [date(2026, 1, 1) + timedelta(days=i) for i in range(40)]


def market(prices: dict[str, list[int]], caps: dict[str, int]) -> History:
    close, cap_by_date = {}, {}
    for i, d in enumerate(DAYS):
        cap_by_date[d] = {}
        for code, series in prices.items():
            if i < len(series):
                close[(d, code)] = series[i]
                cap_by_date[d][code] = caps[code]
    return History(DAYS, close, cap_by_date, {c: "KOSPI" for c in prices}, {})


def test_trend_matches_the_app_rule() -> None:
    """briefing.trend_ranks: 종가가 20일 평균 위이고 20일 평균이 5거래일 전보다 높음"""
    rising = list(range(100, 125))
    up, change = sim.trend(rising)
    assert up and round(change, 1) == round((124 - 104) * 100 / 104, 1)
    assert sim.trend(list(range(125, 100, -1)))[0] is False  # 내리는 종목
    assert sim.trend(rising[:24]) is None  # 25거래일이 안 되면 뺀다


def test_buy_room_caps_by_stock_volatility_and_exposure() -> None:
    """auto_trader.dart buyRoom: 종목당 35%, 변동성 몫(총자산 2% / 하루 변동 2배), 주식 비중 70%까지, 절반이면 반"""
    assert sim.buy_room(cash=10_000_000, equity=10_000_000, invested=0, vol=None, half=False) == 3_500_000
    assert sim.buy_room(10_000_000, 10_000_000, 0, None, half=True) == 1_750_000
    assert sim.buy_room(10_000_000, 10_000_000, 0, vol=2.0, half=False) == 3_500_000  # 변동성 몫 500만 원 > 종목당 350만 원이라 350만 원
    assert sim.buy_room(10_000_000, 10_000_000, 0, vol=8.0, half=False) == 1_250_000  # 총자산 2% / (2×8%) = 12.5% → 125만 원
    assert sim.buy_room(10_000_000, 10_000_000, 6_900_000, None, half=False) == 100_000  # 비중 70%까지 10만 원 남음
    assert sim.buy_room(10_000_000, 10_000_000, 7_100_000, None, half=False) == 0
    assert sim.buy_room(1_000_000, 10_000_000, 0, None, half=False) == 350_000  # 현금보다 많이 쓰지 않는다


def test_falling_needs_three_lower_five_minute_lows_and_price_below_vwap() -> None:
    def bars(lows):
        out = []
        for g, low in enumerate(lows):
            out += [{"t": f"09{g * 5 + k:02d}00", "o": low + 5, "h": low + 10, "l": low + (0 if k == 0 else 3), "c": low + 4, "v": 100} for k in range(5)]
        return out
    assert sim.falling(bars([100, 90, 80])) is True
    assert sim.falling(bars([100, 90, 95])) is False  # 저가가 다시 올랐다
    assert sim.falling(bars([100, 90, 80])[:10]) is False  # 15분이 안 되면 판단하지 않는다


def test_sell_value_takes_fee_and_tax() -> None:
    assert round(sim.sell_value(100, 10_000)) == round(1_000_000 * (1 - 0.00015 - 0.0020))


def test_candidates_do_not_change_when_future_is_changed() -> None:
    """D일 후보는 D−1일까지의 종가로만 고른다 (미래 값을 바꿔도 같다)"""
    up = list(range(100, 140))
    down = list(range(140, 100, -1))
    base = {"A": up, "B": down, "C": [100 + (i % 3) for i in range(40)]}
    spiked = {"A": up[:30] + [1] * 10, "B": down[:30] + [999] * 10, "C": base["C"][:30] + [500] * 10}
    t = DAYS[29]
    caps = {"A": 3, "B": 2, "C": 1}
    a = sim.candidates(market(base, caps).until(t), t, set())
    b = sim.candidates(market(spiked, caps).until(t), t, set())
    assert a == b and a[0] == "A"  # 오르는 종목이 먼저, 5일 +10% 넘게 오른 급등은 뒤


def test_hot_five_day_surge_is_not_a_candidate() -> None:
    surge = [100] * 34 + [100, 105, 110, 115, 125, 140]  # 5일 +40%
    h = market({"A": surge, "B": list(range(100, 140))}, {"A": 2, "B": 1}).until(DAYS[39])
    assert "A" not in sim.candidates(h, DAYS[39], set())


def test_held_stock_is_skipped() -> None:
    h = market({"A": list(range(100, 140)), "B": list(range(100, 130))}, {"A": 2, "B": 1}).until(DAYS[29])
    assert sim.candidates(h, DAYS[29], {"A"}) == ["B"]


def test_sell_books_profit_after_costs() -> None:
    book = sim.Book(cash=0.0, pos={"A": {"qty": 10, "avg": 1_000.0, "half_done": False}})
    sim._sell(book, DAYS[0], "A", 4, 1_100.0)
    assert book.pos["A"]["qty"] == 6 and round(book.cash) == round(4 * 1_100 * (1 - 0.00215))
    sim._sell(book, DAYS[1], "A", 6, 900.0)
    assert "A" not in book.pos
    assert book.trades[-1][5] < 0  # 손실 매도


def test_fin_bad(monkeypatch):
    """접수일 전에는 보이지 않고, 적자·영업이익 반토막만 거른다. 재무가 없으면 거르지 않는다"""
    from datetime import date

    from app import sim
    sim.op_income_reports.cache_clear()
    monkeypatch.setattr(sim, "op_income_reports", lambda: {"A": [(date(2026, 3, 1), -5, 10)], "B": [(date(2026, 3, 1), 4, 10)], "C": [(date(2026, 3, 1), 6, 10)]})
    assert not sim.fin_bad("A", date(2026, 3, 1), "deficit")  # 접수일 당일 아침에는 아직 모른다
    assert sim.fin_bad("A", date(2026, 3, 2), "deficit") and sim.fin_bad("A", date(2026, 3, 2), "half")
    assert not sim.fin_bad("B", date(2026, 3, 2), "deficit") and sim.fin_bad("B", date(2026, 3, 2), "half")
    assert not sim.fin_bad("C", date(2026, 3, 2), "half") and not sim.fin_bad("Z", date(2026, 3, 2), "half")
    assert not sim.fin_bad("A", date(2026, 3, 2), "")
