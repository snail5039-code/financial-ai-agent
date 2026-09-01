import { getFixture, postFixtureAction } from "./client";
import { APPROVALS_CHANGED_EVENT } from "../lib/useApprovalsPendingCount";
import type { ApprovalActionEnvelope, ApprovalOrder, ApprovalsData, ApprovalsEnvelope } from "../types/dashboard";

export async function getApprovals(): Promise<ApprovalsEnvelope> {
  return getFixture<ApprovalsData>("/api/approvals");
}

export async function approveOrder(decisionId: string): Promise<ApprovalActionEnvelope> {
  const result = await postFixtureAction<ApprovalOrder>(`/api/approvals/${decisionId}/approve`);
  window.dispatchEvent(new Event(APPROVALS_CHANGED_EVENT));
  return result;
}

export async function rejectOrder(decisionId: string): Promise<ApprovalActionEnvelope> {
  const result = await postFixtureAction<ApprovalOrder>(`/api/approvals/${decisionId}/reject`);
  window.dispatchEvent(new Event(APPROVALS_CHANGED_EVENT));
  return result;
}
