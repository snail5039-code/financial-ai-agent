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
  /** Live state, read from the same store the approvals queue writes to. */
  decisionStatus: DecisionStatus;
  decidedAt: string | null;
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

/* 리스크 알림 화면 -------------------------------------------------------- */

export type RiskCategory = "정책" | "출처" | "시장" | "승인" | "데이터";
export type RiskSeverity = "중대" | "높음" | "보통" | "낮음";

export interface RiskEvent {
  id: string;
  occurredAt: string;
  title: string;
  decisionRef: string;
  category: RiskCategory;
  severity: RiskSeverity;
  status: string;
  summary: string;
  cause: string;
  action: string;
  policy: string;
  linkPage: PageKey | null;
  linkText: string;
}

export interface RiskAlertsData {
  events: RiskEvent[];
  safetyCopy: string;
}

export type RiskAlertsEnvelope = FixtureEnvelope<RiskAlertsData>;

/* 모의 거래 내역 화면 ------------------------------------------------------ */

export type TradeStatus = "모의승인" | "반려" | "정책 차단" | "만료" | "대기";

export interface TradeHistoryItem {
  id: string;
  days: number;
  occurredAt: string;
  name: string;
  ticker: string;
  side: "매수" | "매도";
  qty: string;
  price: string;
  amount: string;
  status: TradeStatus;
  summary: string;
  fee: string;
  tax: string;
  slippage: string;
  policyResult: string;
  sourceState: string;
}

export interface TradeRelatedLink {
  label: string;
  page: PageKey | null;
  disabled: boolean;
}

export interface TradeHistoryData {
  items: TradeHistoryItem[];
  relatedLinks: TradeRelatedLink[];
  safetyCopy: string;
}

export type TradeHistoryEnvelope = FixtureEnvelope<TradeHistoryData>;

/* 포트폴리오 건강 화면 ----------------------------------------------------- */

export type HealthStatus = "확인 필요" | "차단" | "완료";
export type HealthGroupKey = "policy" | "source" | "risk" | "approval" | "strategy" | "stress" | "complete";

export interface HealthGroup {
  key: HealthGroupKey;
  label: string;
  score: number;
  status: HealthStatus;
  summary: string;
}

export interface HealthCheck {
  id: string;
  group: HealthGroupKey;
  title: string;
  status: HealthStatus;
  impact: "높음" | "보통" | "낮음";
  next: string;
  linkPage: PageKey;
  basis: string;
  summary: string;
  data: string;
  risk: string;
}

export interface PortfolioHealthData {
  groups: HealthGroup[];
  checks: HealthCheck[];
  overallScore: number;
  safetyCopy: string;
}

export type PortfolioHealthEnvelope = FixtureEnvelope<PortfolioHealthData>;

/* 승인 전 근거 패킷 화면 --------------------------------------------------- */

export type EvidenceStatus = "확인" | "주의" | "차단";

export interface EvidenceChecklistItem {
  title: string;
  status: EvidenceStatus;
  tone: Tone;
  summary: string;
  detail: string;
}

export interface EvidencePacket {
  id: string;
  company: string;
  code: string;
  status: string;
  statusTone: Tone;
  proposal: string;
  quantity: number;
  price: number;
  amount: number;
  targetWeightFrom: number;
  targetWeightTo: number;
  expiresAt: string;
  sourceState: string;
  safetyCopy: string;
  summary: string;
  calculation: { formula: string; result: string; rounding: string };
  cost: { fee: string; tax: string; slippage: string };
  risk: { concentration: string; volatility: string; invalidCondition: string };
  roles: Array<{ role: string; check: string; tone: Tone }>;
  approvalBoundary: string;
  items: EvidenceChecklistItem[];
  decisionStatus: DecisionStatus;
  decidedAt: string | null;
}

export interface EvidencePacketsData {
  packets: EvidencePacket[];
}

export type EvidencePacketsEnvelope = FixtureEnvelope<EvidencePacketsData>;

/* 감사 로그 화면 --------------------------------------------------------- */

export interface AuditDecisionRow {
  id: string;
  company: string;
  status: string;
  runId: string;
  tone: Tone;
  initial: string[];
  verified: string[];
  changed: boolean[];
}

export interface AuditStepEntry {
  title: string;
  type: string;
  input: string;
  result: string;
  risk: string;
}

export interface AuditLogData {
  safetyCopy: string;
  labels: string[];
  decisions: AuditDecisionRow[];
  steps: { analysis: AuditStepEntry; verification: AuditStepEntry; approval: AuditStepEntry };
  sources: { metrics: AuditStepEntry; filing: AuditStepEntry; policy: AuditStepEntry };
}

export type AuditLogEnvelope = FixtureEnvelope<AuditLogData>;

/* 결정 회고 화면 --------------------------------------------------------- */

export type DecisionReviewOutcome = "승인" | "반려" | "보류";

export interface DecisionReviewItem {
  id: string;
  name: string;
  ticker: string;
  decision: DecisionReviewOutcome;
  memo: boolean;
  reviewedAt: string;
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
  safetyCopy: string;
  decisions: DecisionReviewItem[];
}

export type DecisionReviewEnvelope = FixtureEnvelope<DecisionReviewData>;

/* 에이전트 역할 상태 화면 -------------------------------------------------- */

export type AgentRoleState = "대기" | "승인 필요" | "실패 이력";

export interface AgentRoleStatusItem {
  id: string;
  role: string;
  status: AgentRoleState;
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
  safetyCopy: string;
  roles: AgentRoleStatusItem[];
}

export type AgentRoleStatusEnvelope = FixtureEnvelope<AgentRoleStatusData>;

/* 주간 투자 리포트 화면 ---------------------------------------------------- */

export type ReportRangeKey = "week" | "month" | "quarter";
export type ReportTopicKey =
  | "return" | "risk" | "cash" | "benchmark" | "alpha" | "samsung" | "hynix" | "naver"
  | "approved" | "rejected" | "blocked" | "source" | "volatility" | "slippage" | "tax";

export interface ReportRange {
  label: string;
  shortLabel: string;
  start: string;
  end: string;
  profit: string;
  portfolio: string;
  benchmark: string;
  alpha: string;
  drawdown: string;
  drawdownLabel: string;
  formula: string;
  portfolioBar: number;
  benchmarkBar: number;
  alphaBar: number;
}

export interface ReportFact {
  label: string;
  value: string;
}

export interface ReportRow {
  key: ReportTopicKey;
  group: string;
  label: string;
  value: string;
  meta: string;
  tone: "gain" | "loss" | "neutral" | "warning";
}

export interface ReportRiskItem {
  key: ReportTopicKey;
  label: string;
}

export interface ReportDetail {
  key: ReportTopicKey;
  title: string;
  summaryByRange: Record<ReportRangeKey, string>;
  factsByRange: Record<ReportRangeKey, ReportFact[]>;
}

export interface WeeklyReportData {
  safetyCopy: string;
  ranges: Record<ReportRangeKey, ReportRange>;
  rows: ReportRow[];
  risks: ReportRiskItem[];
  details: Record<ReportTopicKey, ReportDetail>;
}

export type WeeklyReportEnvelope = FixtureEnvelope<WeeklyReportData>;

/* 세금·수수료 영향 점검 화면 ------------------------------------------------ */

export type TaxFeeStatus = "영향 작음" | "재검토" | "보류 권장";

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
  status: TaxFeeStatus;
  basis: string;
  period: string;
  assumption: string;
  summary: string;
  next: string;
  linkPage: PageKey;
}

export interface TaxFeeImpactData {
  title: string;
  safetyCopy: string;
  orders: TaxFeeOrder[];
}

export type TaxFeeImpactEnvelope = FixtureEnvelope<TaxFeeImpactData>;

/* 포트폴리오 변경 전/후 비교 화면 ------------------------------------------- */

export type PortfolioChangePolicyType = "pass" | "check" | "block";

export interface PortfolioChangeAsset {
  id: string;
  name: string;
  ticker: string;
  currentWeight: number;
  nextWeight: number;
  amountChange: number;
  policyLabel: string;
  policyType: PortfolioChangePolicyType;
  riskLabel: string;
  policyCheck: string;
  sourceState: string;
  direction: "up" | "down";
  summary: string;
}

export interface PortfolioChangeStats {
  cashChange: string;
  riskChange: string;
  maxDrawdownChange: string;
  sectorConcentrationChange: string;
  approvalState: string;
}

export interface PortfolioChangeCompareData {
  id: string;
  title: string;
  summary: string;
  baseAmount: number;
  safetyCopy: string;
  stats: PortfolioChangeStats;
  assets: PortfolioChangeAsset[];
}

export type PortfolioChangeCompareEnvelope = FixtureEnvelope<PortfolioChangeCompareData>;

/* 전략 조정(리밸런싱) 화면 -------------------------------------------------- */

export type RebalanceStrategyKey = "conservative" | "balanced" | "aggressive";
export type RebalanceAssetKey = "cash" | "market" | "samsung" | "sk" | "naver";

export interface CurrentAllocation {
  key: RebalanceAssetKey;
  name: string;
  ticker: string;
  weight: number;
}

export interface RebalanceStrategy {
  label: string;
  expectedReturn: string;
  volatility: string;
  drawdown: string;
  targets: Record<RebalanceAssetKey, number>;
}

export interface RebalanceProposal {
  key: RebalanceAssetKey;
  name: string;
  ticker: string;
  weight: number;
  target: number;
  delta: number;
  direction: "비중 확대" | "비중 축소";
  amount: string;
  policy: string;
  source: string;
  effect: string;
}

export interface RebalancePlanData {
  baseAmount: number;
  safetyCopy: string;
  currentAllocations: CurrentAllocation[];
  strategies: Record<RebalanceStrategyKey, RebalanceStrategy>;
  proposalsByStrategy: Record<RebalanceStrategyKey, RebalanceProposal[]>;
}

export type RebalancePlanEnvelope = FixtureEnvelope<RebalancePlanData>;

/* 백테스트 요약 화면 ------------------------------------------------------- */

export type BacktestStrategyKey = "conservative" | "balanced" | "aggressive";
export type BacktestPeriodKey = "3m" | "6m" | "1y";

export interface BacktestConfig {
  label: string;
}

export interface BacktestPeriod {
  label: string;
  range: string;
}

export interface BacktestMetrics {
  ret: number;
  bench: number;
  dd: number;
  vol: number;
  win: number;
}

export interface BacktestRow {
  month: string;
  portfolio: number;
  benchmark: number;
  excess: number;
  drawdown: number;
  state: "초과" | "미달";
}

export interface BacktestSummaryData {
  safetyCopy: string;
  configs: Record<BacktestStrategyKey, BacktestConfig>;
  periods: Record<BacktestPeriodKey, BacktestPeriod>;
  metrics: Record<BacktestStrategyKey, Record<BacktestPeriodKey, BacktestMetrics>>;
  rows: Record<BacktestStrategyKey, Record<BacktestPeriodKey, BacktestRow[]>>;
}

export type BacktestSummaryEnvelope = FixtureEnvelope<BacktestSummaryData>;

/* 기업 상세 화면 --------------------------------------------------------- */

export type CompanyEvidenceKind = "positive" | "negative" | "filing";

export interface CompanyChartPoint {
  index: number;
  price: number;
  y: number;
}

export interface CompanyMetric {
  label: string;
  value: string;
  note: string;
  tone: Tone;
}

export interface CompanyEvidenceItem {
  id: string;
  kind: CompanyEvidenceKind;
  title: string;
  subtitle: string;
  body: string;
  sourceLabel: string;
  tone: Tone;
}

export interface CompanyPricePanel {
  currentPrice: number;
  changeAmount: number;
  changeRatePercent: number;
  quantity: number;
  averagePrice: number;
  value: number;
  profit: number;
  profitRate: number;
  weight: number;
}

export interface CompanyDetailData {
  company: string;
  code: string;
  market: string;
  sector: string;
  safetyCopy: string;
  price: CompanyPricePanel;
  chart: CompanyChartPoint[];
  metrics: CompanyMetric[];
  evidence: CompanyEvidenceItem[];
  filings: CompanyEvidenceItem[];
}

export type CompanyDetailEnvelope = FixtureEnvelope<CompanyDetailData>;

/* 데이터 연결 상태 화면 ---------------------------------------------------- */

export type DataConnectionKey =
  | "opendart" | "price" | "securities" | "database" | "report" | "unknown" | "stale" | "permission" | "paper";
export type DataConnectionKind = "blocked" | "mock";

export interface DataConnectionFact {
  label: string;
  value: string;
}

export interface DataConnectionDetail {
  key: DataConnectionKey;
  title: string;
  summary: string;
  facts: DataConnectionFact[];
}

export interface DataConnectionCard {
  key: DataConnectionKey;
  label: string;
  value: string;
  note: string;
}

export interface DataConnectionRow {
  key: DataConnectionKey;
  name: string;
  status: string;
  detail: string;
  note: string;
  kind: DataConnectionKind;
}

export interface DataQualityChip {
  key: DataConnectionKey;
  label: string;
}

export interface DataConnectionsData {
  safetyCopy: string;
  details: Record<DataConnectionKey, DataConnectionDetail>;
  cards: DataConnectionCard[];
  rows: DataConnectionRow[];
  qualityChips: DataQualityChip[];
}

export type DataConnectionsEnvelope = FixtureEnvelope<DataConnectionsData>;

/* 알림 설정 화면 --------------------------------------------------------- */

export type NotificationChannelId = "inapp" | "browser" | "email" | "messenger";
export type NotificationTypeId = "policy" | "source" | "approval" | "data" | "volatility" | "cost";
export type NotificationSeverity = "중대" | "높음" | "보통";

export interface NotificationChannel {
  id: NotificationChannelId;
  name: string;
  state: string;
  summary: string;
  enabled: boolean;
}

export interface NotificationType {
  id: NotificationTypeId;
  name: string;
  desc: string;
  enabled: boolean;
}

export interface NotificationSettingsData {
  safetyCopy: string;
  channels: NotificationChannel[];
  types: NotificationType[];
  defaultSeverity: NotificationSeverity;
}

export type NotificationSettingsEnvelope = FixtureEnvelope<NotificationSettingsData>;

/* 투자 정책 화면 --------------------------------------------------------- */

export type PolicyNumberKey = "maxWeight" | "maxOrder" | "maxLoss" | "minCash" | "volatility" | "expiry";
export type PolicyCheckKey = "limitOrder" | "marketOrder" | "blockUnknown" | "blockCorrection";

export interface PolicyNumberRule {
  key: PolicyNumberKey;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  decimals: number;
  value: string;
  help: string;
}

export interface PolicyCheckRule {
  key: PolicyCheckKey;
  label: string;
  value: boolean;
}

export interface PolicyPreview {
  decisionId: string;
  calculation: string;
  amount: number;
  currentWeight: number;
  nextWeight: number;
  orderType: string;
  sourceState: string;
}

export interface PolicySettingsData {
  safetyCopy: string;
  numberRules: PolicyNumberRule[];
  checks: PolicyCheckRule[];
  preview: PolicyPreview;
}

export type PolicySettingsEnvelope = FixtureEnvelope<PolicySettingsData>;

/* 스트레스 테스트 화면 ----------------------------------------------------- */

export type StressScenarioKey = "rates" | "chips" | "fx" | "liquidity";
export type StressAssetKey = "cash" | "market" | "samsung" | "sk" | "naver";

export interface StressAsset {
  key: StressAssetKey;
  name: string;
  ticker: string;
  weight: number;
}

export interface StressScenario {
  label: string;
  description: string;
  loss: number;
  drawdown: number;
  cash: string;
  alerts: number;
  shock: Record<StressAssetKey, number>;
  assumption: string;
  weak: string;
  policy: string;
  responses: string[];
}

export interface StressAssetImpact {
  key: StressAssetKey;
  name: string;
  ticker: string;
  weight: number;
  shock: number;
  contribution: number;
  state: "높음" | "주의" | "관리";
}

export interface StressTestData {
  safetyCopy: string;
  baseAmount: number;
  assets: StressAsset[];
  scenarios: Record<StressScenarioKey, StressScenario>;
  rowsByScenario: Record<StressScenarioKey, StressAssetImpact[]>;
}

export type StressTestEnvelope = FixtureEnvelope<StressTestData>;
