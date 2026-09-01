from typing import Literal

from app.clock import now_kst_iso
from app.fixtures.approvals import build_approval_orders
from app.schemas.approvals import ApprovalOrder


class DecisionConflictError(Exception):
    """Raised when approve/reject targets an order that already left 'pending'."""

    def __init__(self, order: ApprovalOrder) -> None:
        self.order = order
        super().__init__(f"{order.id} is already {order.decisionStatus}")


class ApprovalStore:
    """In-memory pending/approved/rejected state for the demo orders.

    SQL follow-up: state lives only for this process's lifetime and resets on
    restart. When approvals need to survive a restart or be queried as an
    audit trail, replace this class's body with a SQLite-backed one that keeps
    the same list()/get()/decide() signatures — routers call only those three
    methods, so nothing above this file needs to change.
    """

    def __init__(self) -> None:
        self._orders: dict[str, ApprovalOrder] = {
            order.id: order for order in build_approval_orders()
        }

    def list(self) -> list[ApprovalOrder]:
        return list(self._orders.values())

    def get(self, decision_id: str) -> ApprovalOrder | None:
        return self._orders.get(decision_id)

    def decide(self, decision_id: str, status: Literal["approved", "rejected"]) -> ApprovalOrder:
        order = self._orders.get(decision_id)
        if order is None:
            raise KeyError(decision_id)
        if order.decisionStatus != "pending":
            raise DecisionConflictError(order)

        updated = order.model_copy(update={"decisionStatus": status, "decidedAt": now_kst_iso()})
        self._orders[decision_id] = updated
        return updated
