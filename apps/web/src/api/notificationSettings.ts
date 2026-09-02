import { getFixture, postFixture } from "./client";
import type { NotificationSettingsData, NotificationSettingsEnvelope, NotificationSeverity, NotificationTypeId } from "../types/dashboard";

export async function getNotificationSettings(): Promise<NotificationSettingsEnvelope> {
  return getFixture<NotificationSettingsData>("/api/notification-settings");
}

export interface NotificationApplyRequest {
  types: Record<NotificationTypeId, boolean>;
  defaultSeverity: NotificationSeverity;
}

export async function applyNotificationSettings(body: NotificationApplyRequest): Promise<NotificationSettingsEnvelope> {
  return postFixture<NotificationSettingsData>("/api/notification-settings/apply", body);
}
