import { getFixture } from "./client";
import type { PolicySettingsData, PolicySettingsEnvelope } from "../types/dashboard";

export async function getPolicySettings(): Promise<PolicySettingsEnvelope> {
  return getFixture<PolicySettingsData>("/api/policy-settings");
}
