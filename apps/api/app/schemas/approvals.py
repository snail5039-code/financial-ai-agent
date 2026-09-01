from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FixtureEnvelope, Tone

# Numeric conventions match docs/backend/07-dashboard-api.md: money is an
# integer, no formatted strings in the payload.

ApprovalCategory = Literal["conditional", "verified", "attention"]

# The only state this app can ever put an order in. There is no "executed" or
# "filled" value here — approving a demo order never creates a real one.
DecisionStatus = Literal["pending", "approved", "rejected"]


class ApprovalOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    company: str
    code: str
    side: Literal["매수", "매도"]
    quantity: int
    price: int
    amount: int
    # Verification review label, fixed regardless of the user's decision
    # (e.g. "조건부 승인", "출처 미확인"). Does not change after approve/reject.
    reviewLabel: str
    category: ApprovalCategory
    # This is the field that changes. Starts "pending"; becomes "approved" or
    # "rejected" only through this app's own approve/reject endpoint.
    decisionStatus: DecisionStatus
    verification: str
    expiresAt: str
    policyLabel: str
    policyPassed: bool
    sourceLabel: str
    warningTitle: str
    warningDetail: str
    tone: Tone
    decidedAt: str | None = None


class ApprovalsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    orders: list[ApprovalOrder] = Field(min_length=1)


class ApprovalsEnvelope(FixtureEnvelope):
    data: ApprovalsData


class ApprovalActionEnvelope(FixtureEnvelope):
    """Returned by approve/reject. `data` is the single order that changed."""

    data: ApprovalOrder
