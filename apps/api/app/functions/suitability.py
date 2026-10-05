"""성향에 맞는 행동만 제안하게 하는 규칙 (docs/plan/09-investor-profile.md 4·5장).

투자 AI에게 허용 행동 목록을 알려주고, AI가 그 밖의 행동을 내면 코드가 '관찰'로 바꾼다.
성향은 막는 데만 쓴다: 매도·보유·관찰은 막지 않고, 매수만 성향과 종목 위험등급으로 제한한다.
"""

# 종목 위험등급 1(매우 높음) ~ 6(매우 낮음). 국내 상장 주식은 원칙 2등급 (토스증권 준칙 별지 제17호)
DOMESTIC_STOCK_GRADE = 2
# 이 등급을 매수 제안받을 수 있는 최소 성향 단계. 결정 (2026-10-05): 완화안 — 2등급은 위험중립형(3)부터
MIN_LEVEL_FOR_GRADE = {1: 5, 2: 3}


def stock_risk_grade(stock_code: str) -> int:
    # ponytail: 투자주의·경고·관리종목(1등급) 데이터가 아직 없어 모두 2등급. KRX 시장경보 데이터를 붙이면 여기서 1등급을 준다
    return DOMESTIC_STOCK_GRADE


def allowed_actions(mode: str, risk_level: int | None, flags: list[str], grade: int, holds_stock: bool) -> list[str]:
    """투자 AI가 낼 수 있는 행동.

    - 일반 모드(퀴즈 안 함): 판단하지 않으므로 '관찰'만
    - 매도·보유: 이 종목을 갖고 있을 때만 (없으면 의미가 없음)
    - 매수: 생활비·빌린 돈이 아니고(no_buy_proposals), 성향 단계가 종목 위험등급 기준 이상일 때만
    """
    if mode != "custom":
        return ["watch"]
    actions = ["watch"]
    if holds_stock:
        actions += ["hold", "sell"]
    if "no_buy_proposals" not in flags and risk_level >= MIN_LEVEL_FOR_GRADE.get(grade, 1):
        actions.append("buy")
    return actions
