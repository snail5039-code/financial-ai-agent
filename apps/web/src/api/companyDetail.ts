import { getFixture } from "./client";
import type { CompanyDetailData, CompanyDetailEnvelope } from "../types/dashboard";

export async function getCompanyDetail(): Promise<CompanyDetailEnvelope> {
  return getFixture<CompanyDetailData>("/api/company-detail");
}
