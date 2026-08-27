import { dashboardFixture } from "../fixtures/dashboard";
import type { DashboardData } from "../types/dashboard";

export async function getDashboard(): Promise<DashboardData> {
  return dashboardFixture;
}
