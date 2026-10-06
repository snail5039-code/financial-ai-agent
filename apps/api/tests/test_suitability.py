from decimal import Decimal

import pytest

from app.functions.suitability import allowed_actions, buy_block_reason, stock_risk_grade


def test_general_mode_only_watches() -> None:
    assert allowed_actions("general", None, [], 2, holds_stock=True) == ["watch"]


@pytest.mark.parametrize("level, can_buy", [(1, False), (2, False), (3, True), (4, True), (5, True)])
def test_grade_2_stock_buy_from_level_3(level: int, can_buy: bool) -> None:
    assert ("buy" in allowed_actions("custom", level, [], 2, holds_stock=False)) is can_buy


@pytest.mark.parametrize("level, can_buy", [(4, False), (5, True)])
def test_grade_1_stock_buy_only_level_5(level: int, can_buy: bool) -> None:
    assert ("buy" in allowed_actions("custom", level, [], 1, holds_stock=False)) is can_buy


def test_no_buy_flag_blocks_buy_even_for_aggressive() -> None:
    assert "buy" not in allowed_actions("custom", 5, ["no_buy_proposals"], 2, holds_stock=False)


def test_sell_and_hold_only_when_holding() -> None:
    assert set(allowed_actions("custom", 1, [], 2, holds_stock=True)) == {"watch", "hold", "sell"}
    assert allowed_actions("custom", 1, [], 2, holds_stock=False) == ["watch"]


def test_domestic_stock_is_grade_2() -> None:
    assert stock_risk_grade("005930") == 2


@pytest.mark.parametrize(
    "level, volatility, can_buy",
    [(3, "40", True), (3, "40.01", False), (4, "57.73", True), (4, "60.01", False), (5, "200", True), (4, None, True)],
)
def test_volatility_limit_for_buy(level: int, volatility: str | None, can_buy: bool) -> None:
    vol = Decimal(volatility) if volatility else None
    assert ("buy" in allowed_actions("custom", level, [], 2, holds_stock=False, volatility=vol)) is can_buy


def test_block_reason_explains_volatility() -> None:
    reason = buy_block_reason("custom", 3, [], 2, Decimal("57.73"))
    assert reason == "20일 변동성 57.73%가 위험중립형 한도 40%보다 큼"
    assert buy_block_reason("custom", 5, [], 2, Decimal("57.73")) is None
