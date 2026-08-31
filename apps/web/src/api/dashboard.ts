import { getFixture } from "./client";
import type { DashboardData, DashboardEnvelope } from "../types/dashboard";

export async function getDashboard(): Promise<DashboardEnvelope> {
  return getFixture<DashboardData>("/api/dashboard");
}
