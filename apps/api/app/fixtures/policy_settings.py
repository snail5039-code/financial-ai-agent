"""Local policy settings fixture. Ported from `src/fixtures/policySettings.ts`.

Number rule defaults, checks, and the "가상 정책 적용" flow are all
"저장되지 않는 화면 상태" by design — editing and applying happens purely in
frontend state after loading these initial values.
"""

from app.fixtures.decisions import DEC_1042, DEC_1042_TARGET_WEIGHT_FROM, DEC_1042_TARGET_WEIGHT_TO
from app.schemas.policy_settings import PolicyCheckRule, PolicyNumberRule, PolicyPreview, PolicySettingsData

POLICY_SETTINGS_DATA_AS_OF = "2026-08-25T14:32:00+09:00"

POLICY_SETTINGS_SOURCE_LABEL = "로컬 fixture"

POLICY_SETTINGS_DISCLAIMER = "모의투자 · 가상 예시 · 실제 계좌·정책 저장·주문·API 호출 없음"


def build_policy_settings_data() -> PolicySettingsData:
    return PolicySettingsData(
        safetyCopy=POLICY_SETTINGS_DISCLAIMER,
        numberRules=[
            PolicyNumberRule(key="maxWeight", label="종목별 최대 비중", unit="%", min=1, max=30, step=0.1, decimals=1, value="8.0", help="1.0~30.0%, 소수 첫째 자리"),
            PolicyNumberRule(key="maxOrder", label="1회 최대 주문금액", unit="원", min=100000, max=10000000, step=100000, decimals=0, value="1000000", help="100,000~10,000,000원"),
            PolicyNumberRule(key="maxLoss", label="일일 최대 손실률", unit="%", min=0.5, max=10, step=0.1, decimals=1, value="3.0", help="0.5~10.0%, 소수 첫째 자리"),
            PolicyNumberRule(key="minCash", label="최소 현금 비중", unit="%", min=0, max=50, step=0.1, decimals=1, value="15.0", help="0.0~50.0%, 직접 합산 충돌 아님"),
            PolicyNumberRule(key="volatility", label="최근 20일 변동성 경계", unit="%", min=5, max=80, step=0.1, decimals=1, value="28.0", help="5.0~80.0%"),
            PolicyNumberRule(key="expiry", label="승인 만료", unit="분", min=1, max=60, step=1, decimals=0, value="10", help="1~60분, 정수"),
        ],
        checks=[
            PolicyCheckRule(key="limitOrder", label="지정가 주문 허용", value=True),
            PolicyCheckRule(key="marketOrder", label="시장가 주문 허용", value=False),
            PolicyCheckRule(key="blockUnknown", label="출처 미확인 주문 자동 차단", value=True),
            PolicyCheckRule(key="blockCorrection", label="정정 공시 미확인 주문 자동 차단", value=True),
        ],
        preview=PolicyPreview(
            decisionId=DEC_1042.id,
            calculation=f"{DEC_1042.quantity} x {DEC_1042.price:,} = {DEC_1042.amount:,}원",
            amount=DEC_1042.amount,
            currentWeight=DEC_1042_TARGET_WEIGHT_FROM,
            nextWeight=DEC_1042_TARGET_WEIGHT_TO,
            orderType="지정가",
            sourceState="미확인",
        ),
    )
