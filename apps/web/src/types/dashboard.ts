import type { LucideIcon } from "lucide-react";

export type Tone = "neutral" | "info" | "success" | "warning" | "danger";
export type PageKey =
  | "dashboard"
  | "account"
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
  | "health"
  | "analysisAgent"
  | "verificationAgent"
  | "executionAgent";

export interface NavItem {
  label: string;
  group: "투자 운영" | "에이전트" | "문서" | "설정";
  icon: LucideIcon;
  page?: PageKey;
  badge?: string;
}

/**
 * Numeric API contract.
 *
 * Money fields are integers in `DashboardData.currency`. Percent fields are in
 * percent units, so 6.65 means 6.65%. Fields that do not apply to a row (cash
 * has no average price) are `null` rather than a placeholder string. All display
 * formatting lives in `src/lib/format.ts`.
 */

/** Safety metadata every local fixture response carries. */
export interface FixtureEnvelope<TData> {
  generatedAt: string;
  dataAsOf: string;
  sourceLabel: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: 0;
  disclaimer: string;
  data: TData;
}

export interface ChartPoint {
  label: string;
  portfolio: number;
  benchmark: number;
  event?: string | null;
}

export interface Holding {
  name: string;
  code: string;
  quantity: number | null;
  averagePrice: number | null;
  currentPrice: number | null;
  value: number;
  profit: number | null;
  profitRate: number | null;
  weight: number;
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

export interface DashboardSummary {
  totalAsset: number;
  todayProfit: number;
  todayProfitRate: number;
  principal: number;
  accumulatedProfit: number;
  cashWeight: number;
  lastVerifiedAt: string;
}

export interface DashboardDecision {
  company: string;
  code: string;
  decisionId: string;
  status: string;
  statusTone: Tone;
  proposal: string;
  limitPrice: number;
  limitAmount: number;
  targetWeightFrom: number;
  targetWeightTo: number;
  expiresAt: string;
  evidence: EvidenceItem[];
  checks: Array<{ label: string; value: string; tone: Tone }>;
  invalidConditions: string[];
}

export interface DashboardData {
  title: string;
  accountLabel: string;
  currency: "KRW";
  summary: DashboardSummary;
  holdings: Holding[];
  chart: ChartPoint[];
  decision: DashboardDecision;
}

export type DashboardEnvelope = FixtureEnvelope<DashboardData>;

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

/* 계좌 화면 ------------------------------------------------------------- */

export interface AccountSummary {
  totalAsset: number;
  investedAmount: number;
  cashAmount: number;
  principal: number;
  realizedProfit: number;
  unrealizedProfit: number;
  depositTotal: number;
  withdrawalTotal: number;
  lastVerifiedAt: string;
}

export interface AssetClassRow {
  label: string;
  value: number;
  weight: number;
  tone: Tone;
  note: string;
}

export interface CurrencyRow {
  code: string;
  label: string;
  value: number;
  weight: number;
  note: string;
}

export interface ReturnRow {
  period: string;
  profit: number;
  profitRate: number;
  /** Return with deposits and withdrawals removed. */
  netInvestmentRate: number;
  benchmarkRate: number;
}

export interface CashFlowRow {
  id: string;
  occurredAt: string;
  kind: "입금" | "출금";
  amount: number;
  memo: string;
}

export interface AccountData {
  title: string;
  accountLabel: string;
  accountKind: string;
  currency: "KRW";
  summary: AccountSummary;
  assetClasses: AssetClassRow[];
  currencies: CurrencyRow[];
  returns: ReturnRow[];
  cashFlows: CashFlowRow[];
  safetyCopy: string;
}

export type AccountEnvelope = FixtureEnvelope<AccountData>;

/* 에이전트 단계 화면 ----------------------------------------------------- */

export type AgentStage = "analysis" | "verification" | "execution";

export type ExecutionGrade = "자동 실행" | "간편 승인" | "강화 승인" | "실행 금지";

export interface AgentMetric {
  label: string;
  value: string;
  tone: Tone;
}

export interface AgentCapability {
  label: string;
  detail: string;
  /** Always false. Nothing on these screens is wired to a real source. */
  connected: false;
}

export interface AgentWorkField {
  label: string;
  value: string;
}

export interface AgentWorkItem {
  id: string;
  title: string;
  subtitle: string;
  decisionId: string;
  action: string;
  status: string;
  statusTone: Tone;
  userApprovalRequired: boolean;
  fields: AgentWorkField[];
  notes: string[];
  summary: string;
  linkPage: PageKey;
  linkLabel: string;
}

export interface AgentStageStep {
  stage: AgentStage;
  label: string;
  state: "done" | "current" | "waiting" | "blocked";
  detail: string;
}

export interface AgentScreenData {
  stage: AgentStage;
  title: string;
  agentName: string;
  roleSummary: string;
  status: string;
  statusTone: Tone;
  executionGrade: ExecutionGrade | null;
  pipeline: AgentStageStep[];
  metrics: AgentMetric[];
  capabilities: AgentCapability[];
  items: AgentWorkItem[];
  safetyCopy: string;
}

export type AgentScreenEnvelope = FixtureEnvelope<AgentScreenData>;

/* 승인 대기 화면 --------------------------------------------------------- */

export type ApprovalCategory = "conditional" | "verified" | "attention";

/** The only states an order can be in. There is no "executed" or "filled". */
export type DecisionStatus = "pending" | "approved" | "rejected";

export interface ApprovalOrder {
  id: string;
  company: string;
  code: string;
  side: "매수" | "매도";
  quantity: number;
  price: number;
  amount: number;
  /** Fixed verification review label; does not change after a decision. */
  reviewLabel: string;
  category: ApprovalCategory;
  /** The field that changes: pending -> approved | rejected. */
  decisionStatus: DecisionStatus;
  verification: string;
  expiresAt: string;
  policyLabel: string;
  policyPassed: boolean;
  sourceLabel: string;
  warningTitle: string;
  warningDetail: string;
  tone: Tone;
  decidedAt: string | null;
}

export interface ApprovalsData {
  orders: ApprovalOrder[];
}

export type ApprovalsEnvelope = FixtureEnvelope<ApprovalsData>;
/** Returned by approve/reject: `data` is the single order that changed. */
export type ApprovalActionEnvelope = FixtureEnvelope<ApprovalOrder>;
