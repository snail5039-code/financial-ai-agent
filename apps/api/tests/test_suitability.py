import pytest

from app.functions.suitability import allowed_actions, stock_risk_grade


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
