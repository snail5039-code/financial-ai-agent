"""주문 금액 계산, 정책 검사, 행동 코치 (FR-22, FR-23, docs/plan/09-investor-profile.md 5장).

AI 없이 코드로만 계산한다. 공시·뉴스에 이상한 문장이 섞여 있어도 이 검사는 속지 않는다.
금액은 원 단위 정수. 수수료·세금은 원 단위 아래를 버린 추정값이다 (실제 청구액은 증권사 기준).
"""

from datetime import date, datetime, time
from decimal import ROUND_DOWN, Decimal

from app.functions import metrics

# 매도 세금 (2026-01-01부터): 코스피 증권거래세 0.05% + 농어촌특별세 0.15% = 0.20%, 코스닥 0.20%
# 출처: 김앤장 "2026년 세법 및 시행령 개정사항의 주요 내용"
SELL_TAX_PCT = {"KOSPI": Decimal("0.20"), "KOSDAQ": Decimal("0.20")}
WORST_CASE_DROP_PCT = 10          # 처리안의 "최악의 경우": 10% 하락 시 손실
MARKET_OPEN, MARKET_CLOSE = time(9, 0), time(15, 30)  # 정규장 (공휴일 휴장은 아직 거르지 않음)
APPROVAL_MINUTES = 10             # 승인 요청 만료 (FR-25)
MAX_PRICE_DRIFT_PCT = 1           # 실행 직전 가격이 이만큼 넘게 바뀌면 다시 승인 (FR-26)
MAX_QTY = 1_000_000

# 행동 코치 기준
FREQUENT_TRADE_DAYS, FREQUENT_TRADE_COUNT = 7, 2    # 7일 안에 같은 종목을 이미 2번 거래했으면 (이번이 3번째)
HOT_RANK = 0.9                                     # 최근 5거래일 상승률이 분석 대상 중 상위 10%면 "급등"
CONCENTRATION_SHARE = Decimal("0.8")               # 주문 후 비중이 한도의 80%를 넘으면 분산 안내


# 오늘 주문한 금액 (docs/plan/07-database.md 4장). 1일 한도 검사와 홈의 "오늘 한도" 링이 같이 쓴다. SUM은 numeric이라 int로
TODAY_ORDERED_SQL = (
    "SELECT COALESCE(SUM(o.qty * o.price), 0) AS total FROM orders o"
    " JOIN approvals a ON a.id = o.approval_id JOIN proposals p ON p.id = a.proposal_id"
    " WHERE p.user_id = %s AND o.status IN ('accepted', 'filled', 'partially_filled')"
    " AND o.created_at >= date_trunc('day', now())"
)


def floor_won(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_DOWN))


def order_amount(qty: int, price: int) -> int:
    return qty * price


def fee_estimate(amount: int, fee_rate_pct: Decimal | None) -> int | None:
    """수수료 추정. 수수료율을 입력하지 않았으면 None (화면에 '수수료율 미입력')."""
    return None if fee_rate_pct is None else floor_won(Decimal(amount) * Decimal(fee_rate_pct) / 100)


def sell_tax(amount: int, market: str) -> int:
    return floor_won(Decimal(amount) * SELL_TAX_PCT[market] / 100)


# 한국거래소 휴장일 (주말 제외 평일만). 2026년 17일, 2025-12 한국거래소 발표 기준 (언론 보도로 확인)
# ponytail: 해마다 12월에 거래소가 다음 해 휴장일을 발표하면 여기에 더한다. 목록에 없는 해는 주말만 거른다
KRX_HOLIDAYS = {
    date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 3, 2),
    date(2026, 5, 1), date(2026, 5, 5), date(2026, 5, 25), date(2026, 6, 3), date(2026, 7, 17),
    date(2026, 8, 17), date(2026, 9, 24), date(2026, 9, 25), date(2026, 10, 5), date(2026, 10, 9),
    date(2026, 12, 25), date(2026, 12, 31),
}


def is_market_open(now: datetime) -> bool:
    return now.weekday() < 5 and now.date() not in KRX_HOLIDAYS and MARKET_OPEN <= now.time() <= MARKET_CLOSE


def account_values(snapshot: dict, stock_code: str, price: int, closes: dict[str, int]) -> tuple[int, int, int]:
    """(이 종목 보유 수량, 이 종목 평가액, 계좌 전체 평가액).

    이 종목은 주문 가격으로, 다른 종목은 서버의 최근 종가로, 그것도 없으면 평균 매입가로 평가한다.
    """
    held_qty, total = 0, snapshot["cash_krw"]
    for holding in snapshot["holdings"]:
        if holding["stock_code"] == stock_code:
            held_qty = holding["qty"]
            total += holding["qty"] * price
        else:
            total += holding["qty"] * closes.get(holding["stock_code"], holding["avg_price"])
    return held_qty, held_qty * price, total


def rule(name: str, label: str, limit, actual, ok: bool) -> dict:
    return {"rule": name, "label": label, "limit": limit, "actual": actual, "ok": ok}


def policy_check(side: str, qty: int, price: int, policy: dict, today_ordered_krw: int,
                 snapshot: dict | None, closes: dict[str, int], stock_code: str, now: datetime,
                 inputs: list[str]) -> dict:
    """PolicyResult (05-schemas.md 6장): 규칙마다 통과 여부. 하나라도 걸리면 처리안 전에 막는다."""
    amount = order_amount(qty, price)
    rules = [
        rule("market_hours", "장 운영 시간 (휴장일 제외 평일 09:00~15:30)", "09:00~15:30", f"{now:%a %H:%M}", is_market_open(now)),
        rule("max_order", "1회 주문 한도", policy["max_order_krw"], amount, amount <= policy["max_order_krw"]),
        rule("max_daily", "1일 주문 한도", policy["max_daily_krw"], today_ordered_krw + amount,
             today_ordered_krw + amount <= policy["max_daily_krw"]),
    ]
    if snapshot is None:
        rules.append(rule("account", "계좌 정보", "최근 30분 안의 잔고", "없음", False))
        return {"ok": False, "rules": rules, "weight_after": None}

    held_qty, position_value, total_value = account_values(snapshot, stock_code, price, closes)
    if side == "buy":
        rules.append(rule("cash", "현금", snapshot["cash_krw"], amount, amount <= snapshot["cash_krw"]))
    else:
        rules.append(rule("holdings", "보유 수량", held_qty, qty, qty <= held_qty))
    weight = metrics.weight_after_order(position_value, total_value, amount, side, inputs)
    if side == "buy":  # 비중 한도는 늘리는 쪽(매수)만 막는다
        rules.append(rule("max_weight", "한 종목 최대 비중 (%)", str(policy["max_weight_pct"]), str(weight["value"]),
                          weight["value"] is not None and weight["value"] <= Decimal(policy["max_weight_pct"])))
    return {"ok": all(r["ok"] for r in rules), "rules": rules, "weight_after": weight["value"]}


def coach_warnings(side: str, recent_trades: int, hot_rank: float | None, five_day_return: Decimal | None,
                   chases_hot_stocks: bool, weight_after: Decimal | None, max_weight_pct: Decimal,
                   gain_pct: Decimal | None, losing_holdings: list[str], cost_krw: int | None) -> list[str]:
    """손실로 이어지기 쉬운 행동을 짚는다. 막지는 않고 처리안에 경고로 보여준다 (자본시장연구원 2022, Barber·Odean 2000)."""
    warnings = []
    if recent_trades >= FREQUENT_TRADE_COUNT:
        cost = f" 이번 주문의 수수료·세금 추정은 {cost_krw:,}원이에요." if cost_krw else ""
        warnings.append(f"최근 {FREQUENT_TRADE_DAYS}일 동안 이 종목을 {recent_trades}번 거래했어요. "
                        f"자주 사고팔수록 비용 때문에 수익이 줄어들기 쉬워요.{cost}")
    if side == "buy" and hot_rank is not None and hot_rank > HOT_RANK and five_day_return and five_day_return > 0:
        warnings.append(f"최근 5거래일 {five_day_return}% 올라 분석 대상 중 가장 많이 오른 편이에요. "
                        "급등 직후 매수는 고점에 살 위험이 있어요."
                        + (" 퀴즈에서 급등주를 바로 사는 편이라고 답하셨어요." if chases_hot_stocks else ""))
    if side == "buy" and weight_after is not None and weight_after > Decimal(max_weight_pct) * CONCENTRATION_SHARE:
        warnings.append(f"주문 후 이 종목 비중이 {weight_after}%로 한도({max_weight_pct}%)에 가까워요. 여러 종목에 나누는 것도 생각해 보세요.")
    if side == "sell" and gain_pct is not None and gain_pct > 0 and losing_holdings:
        warnings.append(f"수익 중인 종목(+{gain_pct}%)을 팔고, 손실 중인 종목({', '.join(losing_holdings)})은 그대로예요. "
                        "오른 것만 먼저 팔고 떨어진 것을 오래 들고 있는 습관은 성과를 낮추기 쉬워요.")
    return warnings


def needs_hot_confirm(warnings: list[str], chases_hot_stocks: bool) -> bool:
    """급등 경고가 있고 퀴즈에서 급등주를 바로 산다고 답했으면 한 번 더 확인받는다."""
    return chases_hot_stocks and any("급등 직후" in w for w in warnings)


def price_drifted(approved_price: int, current_price: int) -> bool:
    return abs(Decimal(current_price - approved_price)) / approved_price * 100 > MAX_PRICE_DRIFT_PCT
