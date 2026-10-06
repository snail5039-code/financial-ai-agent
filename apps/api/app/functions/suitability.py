"""성향에 맞는 행동만 제안하게 하는 규칙 (docs/plan/09-investor-profile.md 4·5장).

투자 AI에게 허용 행동과 매수가 빠진 이유를 알려주고, AI가 그 밖의 행동을 내면 코드가 '관찰'로 바꾼다.
성향은 막는 데만 쓴다: 매도·보유·관찰은 막지 않고, 매수만 성향·종목 위험등급·변동성으로 제한한다.
"""

from app.functions.profile import LABELS

# 종목 위험등급 1(매우 높음) ~ 6(매우 낮음). 국내 상장 주식은 원칙 2등급 (토스증권 준칙 별지 제17호)
DOMESTIC_STOCK_GRADE = 2
# 이 등급을 매수 제안받을 수 있는 최소 성향 단계. 결정 (2026-10-05): 완화안 — 2등급은 위험중립형(3)부터
MIN_LEVEL_FOR_GRADE = {1: 5, 2: 3}
# 성향 단계별로 매수를 제안할 수 있는 변동성 순위 상한 (분석 대상 안에서, 0~1, 1이면 가장 출렁임).
# 결정 (2026-10-06): 고정 숫자(예: 40%)는 시장 상황에 따라 너무 엄격하거나 느슨해져서, 대상 안의 순위로 정한다.
#   위험중립형: 변동성 하위 1/3만 / 적극투자형: 가장 출렁이는 20% 제외 / 공격투자형: 제한 없음
# 분석 대상이 늘어도 같은 규칙을 쓴다 (docs/plan/10-coverage-expansion.md 2-6)
MAX_VOLATILITY_RANK_FOR_BUY = {3: 1 / 3, 4: 0.8}


def stock_risk_grade(stock_code: str) -> int:
    # ponytail: 투자주의·경고·관리종목(1등급) 데이터가 아직 없어 모두 2등급. KRX 시장경보 데이터를 붙이면 여기서 1등급을 준다
    return DOMESTIC_STOCK_GRADE


def buy_block_reason(mode: str, risk_level: int | None, flags: list[str], grade: int,
                     volatility_rank: float | None) -> str | None:
    """매수를 제안하면 안 되는 이유. 괜찮으면 None."""
    if mode != "custom":
        return "일반 모드(성향 퀴즈 안 함)라 판단하지 않음"
    if "no_buy_proposals" in flags:
        return "생활비나 빌린 돈으로 투자한다고 답함"
    if risk_level < MIN_LEVEL_FOR_GRADE.get(grade, 1):
        return f"{grade}등급 종목은 {LABELS[MIN_LEVEL_FOR_GRADE[grade]]} 이상만 매수 제안"
    limit = MAX_VOLATILITY_RANK_FOR_BUY.get(risk_level)
    if limit is not None and volatility_rank is not None and volatility_rank > limit:
        return (f"60일 변동성이 분석 대상 중 높은 편이라 (낮은 쪽부터 {volatility_rank:.0%} 위치) "
                f"{LABELS[risk_level]} 기준(낮은 쪽 {limit:.0%} 이내)을 넘음")
    return None


def allowed_actions(mode: str, risk_level: int | None, flags: list[str], grade: int, holds_stock: bool,
                    volatility_rank: float | None = None) -> list[str]:
    """투자 AI가 낼 수 있는 행동.

    - 일반 모드(퀴즈 안 함): 판단하지 않으므로 '관찰'만
    - 매도·보유: 이 종목을 갖고 있을 때만 (없으면 의미가 없음)
    - 매수: buy_block_reason이 없을 때만
    """
    if mode != "custom":
        return ["watch"]
    actions = ["watch"]
    if holds_stock:
        actions += ["hold", "sell"]
    if buy_block_reason(mode, risk_level, flags, grade, volatility_rank) is None:
        actions.append("buy")
    return actions
