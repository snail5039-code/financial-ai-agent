from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FixtureEnvelope, Tone

# Numeric conventions for this contract:
# - Money fields are integers in the currency named by `DashboardData.currency`.
# - Percent fields are in percent units, not ratios: 6.65 means 6.65%.
# - Display formatting (thousands separators, signs, suffixes) belongs to the client.


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totalAsset: int
    todayProfit: int
    todayProfitRate: float
    principal: int
    accumulatedProfit: int
    cashWeight: float
    lastVerifiedAt: str


class DashboardHolding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    code: str
    quantity: int | None = None
    averagePrice: int | None = None
    currentPrice: int | None = None
    value: int
    profit: int | None = None
    profitRate: float | None = None
    weight: float
    status: str
    tone: Tone
    selected: bool = False


class DashboardChartPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    portfolio: float
    benchmark: float
    event: str | None = None


class DashboardEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    detail: str
    source: str
    tone: Tone


class DashboardCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    tone: Tone


class DashboardDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    code: str
    decisionId: str
    status: str
    statusTone: Tone
    proposal: str
    limitPrice: int
    limitAmount: int
    targetWeightFrom: float
    targetWeightTo: float
    expiresAt: str
    evidence: list[DashboardEvidence]
    checks: list[DashboardCheck]
    invalidConditions: list[str]


class DashboardData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    accountLabel: str
    currency: Literal["KRW"] = "KRW"
    summary: DashboardSummary
    chart: list[DashboardChartPoint] = Field(min_length=1)
    holdings: list[DashboardHolding] = Field(min_length=1)
    decision: DashboardDecision


class DashboardEnvelope(FixtureEnvelope):
    data: DashboardData
