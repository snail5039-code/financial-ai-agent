import { getFixture, postFixtureAction } from "./client";
import type { ApprovalActionEnvelope, ApprovalOrder, ApprovalsData, ApprovalsEnvelope } from "../types/dashboard";

export async function getApprovals(): Promise<ApprovalsEnvelope> {
  return getFixture<ApprovalsData>("/api/approvals");
}

export async function approveOrder(decisionId: string): Promise<ApprovalActionEnvelope> {
  return postFixtureAction<ApprovalOrder>(`/api/approvals/${decisionId}/approve`);
}

export async function rejectOrder(decisionId: string): Promise<ApprovalActionEnvelope> {
  return postFixtureAction<ApprovalOrder>(`/api/approvals/${decisionId}/reject`);
}
