from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import FixtureEnvelope

NotificationChannelId = Literal["inapp", "browser", "email", "messenger"]
NotificationTypeId = Literal["policy", "source", "approval", "data", "volatility", "cost"]
NotificationSeverity = Literal["중대", "높음", "보통"]


class NotificationChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NotificationChannelId
    name: str
    state: str
    summary: str
    enabled: bool


class NotificationType(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NotificationTypeId
    name: str
    desc: str
    enabled: bool


class NotificationSettingsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    safetyCopy: str
    channels: list[NotificationChannel] = Field(min_length=1)
    types: list[NotificationType] = Field(min_length=1)
    defaultSeverity: NotificationSeverity
    # None until the first save — set to that save's server time afterward.
    appliedAt: str | None = None


class NotificationSettingsEnvelope(FixtureEnvelope):
    data: NotificationSettingsData


class NotificationApplyRequest(BaseModel):
    """Only `types`/`defaultSeverity` are saved — channels have no editable
    control on the screen (enabling browser/email/messenger would imply a
    real permission request or external connection this app never makes), so
    there is nothing user-set to persist for them."""

    model_config = ConfigDict(extra="forbid")

    types: dict[NotificationTypeId, bool]
    defaultSeverity: NotificationSeverity

    @model_validator(mode="after")
    def _require_every_type(self) -> "NotificationApplyRequest":
        missing = set(get_args(NotificationTypeId)) - self.types.keys()
        if missing:
            raise ValueError(f"missing types: {sorted(missing)}")
        return self
