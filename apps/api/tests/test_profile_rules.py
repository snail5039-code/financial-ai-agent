from decimal import Decimal

import pytest

from app.functions.profile import DEFAULT_POLICIES, lowered_policy, policy_warnings, risk_level


@pytest.mark.parametrize(
    "answers, level",
    [
        ([1, 1, 1, 1, 1], 1),  # 5점
        ([2, 2, 1, 2, 1], 1),  # 8점
        ([2, 2, 2, 2, 1], 2),  # 9점
        ([3, 3, 2, 2, 2], 2),  # 12점
        ([3, 3, 3, 3, 1], 3),  # 13점
        ([4, 4, 4, 4, 4], 4),  # 20점
        ([5, 4, 4, 4, 4], 5),  # 21점
        ([5, 5, 5, 5, 5], 5),  # 25점
    ],
)
def test_risk_level_by_total_score(answers: list[int], level: int) -> None:
    assert risk_level(answers) == level


def test_risk_level_capped_by_loss_answer() -> None:
    # 합계는 21점(5단계)이지만 "손실 싫음"(1점)이면 2단계까지만
    assert risk_level([5, 5, 5, 1, 5]) == 2
    assert risk_level([5, 5, 5, 3, 5]) == 4


@pytest.mark.parametrize("answers", [[], [3, 3, 3, 3], [3, 3, 3, 3, 3, 3], [0, 3, 3, 3, 3], [6, 3, 3, 3, 3]])
def test_risk_level_rejects_bad_answers(answers: list[int]) -> None:
    with pytest.raises(ValueError):
        risk_level(answers)


def test_lowered_policy_only_goes_down() -> None:
    current = {"max_order_krw": 100_000, "max_daily_krw": 5_000_000, "max_weight_pct": Decimal("50")}
    # 3단계 기본값: 100만 / 200만 / 30%
    assert lowered_policy(current, 3) == {
        "max_order_krw": 100_000,  # 사용자가 낮춰 둔 값은 그대로
        "max_daily_krw": 2_000_000,
        "max_weight_pct": Decimal("30"),
    }


def test_policy_warnings_only_for_limits_above_default() -> None:
    assert policy_warnings(DEFAULT_POLICIES[1], 1) == []
    above = {**DEFAULT_POLICIES[1], "max_order_krw": 300_001, "max_weight_pct": Decimal("20.01")}
    assert len(policy_warnings(above, 1)) == 2
