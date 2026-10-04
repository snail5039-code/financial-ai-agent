"""투자성향 설문 점수 계산과 성향별 기본 투자 정책.

설문 (v1, 5문항, 답마다 1~5점. 앱 화면 S-03이 이 순서대로 보여준다)
  1. 주식 같은 위험자산 투자 경험: 없음 / 1년 미만 / 1~3년 / 3~5년 / 5년 이상
  2. 이 돈을 투자해 둘 수 있는 기간: 6개월 미만 / 6개월~1년 / 1~2년 / 2~3년 / 3년 이상
  3. 투자 목적: 원금 지키기 / 예금 이자 정도 / 시장 평균 / 시장보다 높게 / 손실 감수하고 높은 수익
  4. 감당할 수 있는 손실: 손실 싫음 / -5% / -10% / -20% / -20% 넘어도 괜찮음
  5. 전체 금융자산 중 투자할 비중: 50% 이상 / 30~50% / 20~30% / 10~20% / 10% 이하

이 앱 안에서 쓰는 참고용 진단이다. 공식 적합성 진단이 아니다.
성향은 맞지 않는 투자를 막는 데만 쓴다 (INVEST_AGENT_PLAN.md 6장).
"""

from decimal import Decimal

QUESTION_COUNT = 5
LOSS_QUESTION_INDEX = 3  # 4번 문항: 감당할 수 있는 손실

LABELS = {
    1: "안정형",
    2: "안정추구형",
    3: "위험중립형",
    4: "적극투자형",
    5: "공격투자형",
}

# 성향 단계별 기본 한도. 1단계 값만 기획 문서(S-03)에 있고, 나머지는 임시로 정한 값이다
DEFAULT_POLICIES = {
    1: {"max_order_krw": 300_000, "max_daily_krw": 500_000, "max_weight_pct": Decimal("20")},
    2: {"max_order_krw": 500_000, "max_daily_krw": 1_000_000, "max_weight_pct": Decimal("25")},
    3: {"max_order_krw": 1_000_000, "max_daily_krw": 2_000_000, "max_weight_pct": Decimal("30")},
    4: {"max_order_krw": 2_000_000, "max_daily_krw": 5_000_000, "max_weight_pct": Decimal("40")},
    5: {"max_order_krw": 3_000_000, "max_daily_krw": 10_000_000, "max_weight_pct": Decimal("50")},
}

LIMIT_NAMES = {
    "max_order_krw": "1회 주문 한도",
    "max_daily_krw": "1일 주문 한도",
    "max_weight_pct": "한 종목 최대 비중",
}


def risk_level(answers: list[int]) -> int:
    """설문 답(1~5점 5개) → 성향 단계(1~5).

    합계 5~8점 1단계, 9~12점 2단계, 13~16점 3단계, 17~20점 4단계, 21~25점 5단계.
    단, 손실 문항 점수 + 1 단계를 넘지 않는다 ("손실 싫음"이면 최대 2단계).
    """
    if len(answers) != QUESTION_COUNT or any(a not in range(1, 6) for a in answers):
        raise ValueError(f"설문 답은 1~5 사이 숫자 {QUESTION_COUNT}개여야 해요")
    by_total = min((sum(answers) - QUESTION_COUNT) // 4 + 1, 5)
    return min(by_total, answers[LOSS_QUESTION_INDEX] + 1)


def lowered_policy(current: dict, level: int) -> dict:
    """설문을 다시 했을 때의 새 한도: 항목마다 지금 값과 새 기본값 중 작은 쪽.

    성향이 낮아지면 한도도 내려가고, 높아져도 저절로 올라가지는 않는다.
    """
    return {key: min(current[key], default) for key, default in DEFAULT_POLICIES[level].items()}


def policy_warnings(policy: dict, level: int) -> list[str]:
    """성향 기본값보다 높게 잡은 한도마다 경고 문장 하나."""
    return [
        f"{LIMIT_NAMES[key]}: 성향({LABELS[level]}) 기본값보다 높아요"
        for key, default in DEFAULT_POLICIES[level].items()
        if policy[key] > default
    ]
