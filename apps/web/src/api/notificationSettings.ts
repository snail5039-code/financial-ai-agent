import { getFixture } from "./client";
import type { NotificationSettingsData, NotificationSettingsEnvelope } from "../types/dashboard";

export async function getNotificationSettings(): Promise<NotificationSettingsEnvelope> {
  return getFixture<NotificationSettingsData>("/api/notification-settings");
}
