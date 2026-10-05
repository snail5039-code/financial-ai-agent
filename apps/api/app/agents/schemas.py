"""투자 AI 제안서와 검증 AI 판정 형식 (docs/plan/05-schemas.md).

AI는 이 칸만 채운다. 종목·수량·기준 시각·출처 정보·지표 값은 코드가 채운다.
"""

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["buy", "sell", "hold", "watch"]
Verdict = Literal["approve", "conditional", "reject", "user_judgement"]


class Claim(BaseModel):
    text: str = Field(description="근거 한 문장")
    type: Literal["fact", "calc", "inference", "opinion"] = Field(
        description="fact 사실 / calc 계산 / inference 추론 / opinion 의견"
    )
    source_ids: list[str] = Field(default_factory=list, description="근거 출처 ID. 사실·계산은 반드시 1개 이상")
    metric_ids: list[str] = Field(default_factory=list, description="쓴 지표 ID. 계산은 반드시 1개 이상")


class ProposalDraft(BaseModel):
    """투자 AI가 쓰는 부분."""

    action: Action = Field(description="허용 행동 중 하나")
    claims: list[Claim] = Field(min_length=1, max_length=8)
    counter_arguments: list[str] = Field(description="반대 근거")
    risks: list[str] = Field(description="주요 위험. 손실 가능성, 수수료·세금도 본다")
    invalid_if: list[str] = Field(description="이 판단이 틀린 것이 되는 조건")


class Check(BaseModel):
    target: str = Field(description="확인한 것. 예: claim:0, freshness, risk_fit, counter_arguments")
    result: Literal["pass", "warn", "fail"]
    detail: str = Field(description="무엇을 어떻게 확인했는지")
    source_ids: list[str] = Field(default_factory=list)


class VerificationDraft(BaseModel):
    """검증 AI가 쓰는 부분."""

    verdict: Verdict = Field(description="approve 승인 / conditional 조건부 승인 / reject 반려 / user_judgement 사용자 판단 필요")
    checks: list[Check]
    challenges: list[str] = Field(default_factory=list, description="반려일 때 투자 AI에게 보낼 반박·질문")
    conditions: list[str] = Field(default_factory=list, description="조건부 승인의 조건")
    risk_fit: Literal["ok", "warn", "mismatch"] = Field(description="사용자 성향과 맞는지")
    disagreements: list[str] = Field(default_factory=list, description="투자 AI와 의견이 다른 점 (사용자에게 보여줌)")
    summary: str = Field(description="한 줄 요약")
