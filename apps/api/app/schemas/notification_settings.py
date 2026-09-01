from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class NotificationSettingsEnvelope(FixtureEnvelope):
    data: NotificationSettingsData
