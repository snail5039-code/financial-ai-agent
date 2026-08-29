import type { LucideIcon } from "lucide-react";

export type Tone = "neutral" | "info" | "success" | "warning" | "danger";
export type PageKey =
  | "dashboard"
  | "company"
  | "approvals"
  | "taxFee"
  | "decisionReview"
  | "roleStatus"
  | "evidence"
  | "compare"
  | "audit"
  | "policy"
  | "data"
  | "trades"
  | "risks"
  | "notifications"
  | "backtest"
  | "rebalance"
  | "weekly"
  | "stress"
  | "health";

export interface NavItem {
  label: string;
  group: "투자 운영" | "에이전트" | "문서" | "설정";
  icon: LucideIcon;
  page?: PageKey;
  badge?: string;
}

export interface ChartPoint {
  label: string;
  portfolio: number;
  benchmark: number;
  event?: string;
}

export interface Holding {
  name: string;
  code: string;
  quantity: string;
  averagePrice: string;
  currentPrice: string;
  value: string;
  profit: string;
  profitRate: string;
  weight: string;
  status: string;
  tone: Tone;
  selected?: boolean;
}

export interface EvidenceItem {
  title: string;
  detail: string;
  source: string;
  tone: Tone;
}

export interface DashboardData {
  generatedAt: string;
  dataAsOf: string;
  isMock: true;
  disclaimer: string;
  title: string;
  accountLabel: string;
  summary: {
    totalAsset: string;
    todayProfit: string;
    todayProfitRate: string;
    principal: string;
    accumulatedProfit: string;
    cashWeight: string;
    lastVerified: string;
  };
  holdings: Holding[];
  chart: ChartPoint[];
  decision: {
    company: string;
    code: string;
    decisionId: string;
    status: string;
    statusTone: Tone;
    proposal: string;
    limitAmount: string;
    targetWeight: string;
    expiresAt: string;
    evidence: EvidenceItem[];
    checks: Array<{ label: string; value: string; tone: Tone }>;
    invalidConditions: string[];
  };
}

export type PortfolioChangeFilter = "all" | "up" | "down" | "check" | "none";

export interface PortfolioChangeAsset {
  id: string;
  name: string;
  ticker: string;
  currentWeight: number;
  nextWeight: number;
  amountChange: number;
  direction: "up" | "down";
  policyLabel: string;
  policyType: "pass" | "check" | "block";
  riskLabel: string;
  policyCheck: string;
  sourceState: string;
  summary: string;
}

export interface PortfolioChangeCompareData {
  id: string;
  title: string;
  summary: string;
  baseAmount: number;
  generatedAt: string;
  dataAsOf: string;
  sourceLabel: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: 0;
  safetyCopy: string;
  stats: {
    cashChange: string;
    riskChange: string;
    maxDrawdownChange: string;
    sectorConcentrationChange: string;
    approvalState: string;
  };
  assets: PortfolioChangeAsset[];
}

export type TaxFeeImpactFilter = "all" | "영향 작음" | "재검토" | "보류 권장" | "none";

export interface TaxFeeOrder {
  id: string;
  name: string;
  ticker: string;
  side: "매수" | "매도";
  market: string;
  currency: string;
  gross: number;
  fee: number;
  tax: number;
  slippage: number;
  fx: number;
  status: Exclude<TaxFeeImpactFilter, "all" | "none">;
  basis: string;
  period: string;
  assumption: string;
  summary: string;
  next: string;
  linkPage: PageKey;
}

export interface TaxFeeImpactData {
  title: string;
  generatedAt: string;
  dataAsOf: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: 0;
  safetyCopy: string;
  orders: TaxFeeOrder[];
}

export type DecisionReviewFilter = "all" | "승인" | "반려" | "보류" | "none";

export interface DecisionReviewItem {
  id: string;
  name: string;
  ticker: string;
  decision: Exclude<DecisionReviewFilter, "all" | "none">;
  memo: boolean;
  time: string;
  statusText: string;
  reason: string;
  memoText: string;
  policy: string;
  verification: string;
  source: string;
  pathDiff: string;
  chosen: string;
  alternate: string;
  pathCopy: string;
  focus: string;
  linkPage: PageKey;
  summary: string;
}

export interface DecisionReviewData {
  title: string;
  generatedAt: string;
  dataAsOf: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: 0;
  safetyCopy: string;
  decisions: DecisionReviewItem[];
}

export type AgentRoleStatusFilter = "all" | "대기" | "승인 필요" | "실패 이력" | "none";

export interface AgentRoleStatusItem {
  id: string;
  role: string;
  status: Exclude<AgentRoleStatusFilter, "all" | "none">;
  badge: string;
  task: string;
  wait: string;
  approval: boolean;
  history: string;
  decision: string;
  summary: string;
  conflict: string;
  linkPage: PageKey;
  linkLabel: string;
}

export interface AgentRoleStatusData {
  title: string;
  generatedAt: string;
  dataAsOf: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: 0;
  safetyCopy: string;
  roles: AgentRoleStatusItem[];
}
