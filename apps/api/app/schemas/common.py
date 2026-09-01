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
    `isMock`/`paperOnly`/`executed` are typed as literals so this contract can
    never claim a real trade happened. `externalConnections` is a plain,
    honest count instead: every screen still defaults to 0, except Company
    Detail, which reports 1 while its filings just came from a live OpenDART
    call (see app/routers/company_detail.py, app/integrations/opendart.py).
    OpenDART is read-only public disclosure data with no account or money
    involved — nothing else in this app is allowed to raise this above 0
    without the same explicit, narrow justification.
    """

    model_config = ConfigDict(extra="forbid")

    generatedAt: str
    dataAsOf: str
    sourceLabel: str
    isMock: Literal[True] = True
    paperOnly: Literal[True] = True
    executed: Literal[False] = False
    externalConnections: int = 0
    disclaimer: str
