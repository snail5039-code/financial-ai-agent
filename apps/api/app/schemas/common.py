from typing import Literal

from pydantic import BaseModel, ConfigDict

Tone = Literal["neutral", "info", "success", "warning", "danger"]

# The only three states any decision can be in across every screen that
# references one. There is no "executed"/"filled" value — approving a demo
# decision never means a real order was placed. Defined once here so screens
# that both read and write a decision's status (dashboard, approvals) cannot
# each invent their own slightly different literal.
DecisionStatus = Literal["pending", "approved", "rejected"]


class FixtureEnvelope(BaseModel):
    """Common safety metadata carried by every local fixture response.

    Subclasses add a `data` field with the screen specific fixture body.
    The safety flags are typed as literals so a real connection cannot be
    represented by this contract at all.
    """

    model_config = ConfigDict(extra="forbid")

    generatedAt: str
    dataAsOf: str
    sourceLabel: str
    isMock: Literal[True] = True
    paperOnly: Literal[True] = True
    executed: Literal[False] = False
    externalConnections: Literal[0] = 0
    disclaimer: str
