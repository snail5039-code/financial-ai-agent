import type { LucideIcon } from "lucide-react";
import type { components } from "./api.generated";

/**
 * Screen-specific data types below are aliases onto `./api.generated.ts`,
 * which `npm run generate:types` produces from the FastAPI OpenAPI schema
 * (`apps/api`). Re-run that script whenever a backend response shape changes
 * — this file should never hand-author a field that the backend already
 * describes. See `docs/handoff/01-current-state.md` (FRONTEND-006) for why.
 *
 * One kind of type stays hand-written even though it describes API data:
 * dict-shaped fields (`Record<"conservative" | "balanced" | ..., X>`). The
 * backend narrows these keys with `propertyNames.enum` in the JSON Schema,
 * but openapi-typescript widens them to `{ [key: string]: X }`. The `*Key`
 * unions below restore the literal keys for exhaustive `Record` types, via
 * `Api`'s override param.
 *
 * `linkPage`/`page` fields (the ones pointing at this app's own `PageKey`
 * union) don't need that treatment: every backend model narrows them with a
 * `Literal[...]` of the specific page keys it can point to, so the generated
 * type is already a valid (subset) `PageKey`. Keep it that way on the backend
 * — a plain `str` there would silently widen the frontend type back to
 * `string` and this file would need an override again to compensate.
 *
 * Every field with a Pydantic default (`Optional[int] = None`, `= "KRW"`, ...)
 * comes out of openapi-typescript marked `?`, since JSON Schema has no way to
 * say "always present, but has a default". A FastAPI response model always
 * serializes every field though, so nothing is genuinely absent — only `| null`
 * on nullable fields is meaningful. `Api<T>` strips that spurious optionality.
 */
type Data<T> = T extends Array<infer U>
  ? Array<Data<U>>
  : T extends object
    ? { [K in keyof T]-?: Data<T[K]> }
    : T;
type Api<T, U extends Record<string, unknown> = Record<never, never>> = Omit<Data<T>, keyof U> & U;

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

/**
 * Safety metadata every local fixture response carries. `externalConnections`
 * is 0 for every screen except Company Detail, which honestly reports 1 while
 * its filings just came from a live, read-only OpenDART call — see
 * `getCompanyDetail` in `../api/companyDetail` for the one place a non-zero
 * value is expected and allowed through `assertFixtureEnvelope`.
 */
export interface FixtureEnvelope<TData> {
  generatedAt: string;
  dataAsOf: string;
  sourceLabel: string;
  isMock: true;
  paperOnly: true;
  executed: false;
  externalConnections: number;
  disclaimer: string;
  data: TData;
}

/* 대시보드 화면 ----------------------------------------------------------- */

export type ChartPoint = Api<components["schemas"]["DashboardChartPoint"]>;
export type EvidenceItem = Api<components["schemas"]["DashboardEvidence"]>;
export type Holding = Api<components["schemas"]["DashboardHolding"]>;
export type DashboardSummary = Api<components["schemas"]["DashboardSummary"]>;
export type DashboardDecision = Api<components["schemas"]["DashboardDecision"]>;
export type DashboardData = Api<components["schemas"]["DashboardData"], { currency: "KRW" }>;
export type DashboardEnvelope = FixtureEnvelope<DashboardData>;

/* 계좌 화면 ------------------------------------------------------------- */

export type AccountSummary = Api<components["schemas"]["AccountSummary"]>;
export type AssetClassRow = Api<components["schemas"]["AssetClassRow"]>;
export type CurrencyRow = Api<components["schemas"]["CurrencyRow"]>;
export type ReturnRow = Api<components["schemas"]["ReturnRow"]>;
export type CashFlowRow = Api<components["schemas"]["CashFlowRow"]>;
export type AccountData = Api<components["schemas"]["AccountData"], { currency: "KRW" }>;
export type AccountEnvelope = FixtureEnvelope<AccountData>;

/* 에이전트 단계 화면 ----------------------------------------------------- */

export type AgentStage = "analysis" | "verification" | "execution";
export type ExecutionGrade = "자동 실행" | "간편 승인" | "강화 승인" | "실행 금지";

export type AgentMetric = Api<components["schemas"]["AgentMetric"]>;
export type AgentCapability = Api<components["schemas"]["AgentCapability"]>;
export type AgentWorkField = Api<components["schemas"]["AgentWorkField"]>;
export type AgentWorkItem = Api<components["schemas"]["AgentWorkItem"]>;
export type AgentStageStep = Api<components["schemas"]["AgentStageStep"]>;
export type AgentScreenData = Api<components["schemas"]["AgentScreenData"]>;
export type AgentScreenEnvelope = FixtureEnvelope<AgentScreenData>;

/* 승인 대기 화면 --------------------------------------------------------- */

export type ApprovalCategory = "conditional" | "verified" | "attention";
/** The only states an order can be in. There is no "executed" or "filled". */
export type DecisionStatus = "pending" | "approved" | "rejected";

export type ApprovalOrder = Api<components["schemas"]["ApprovalOrder"]>;
export type ApprovalsData = Api<components["schemas"]["ApprovalsData"]>;
export type ApprovalsEnvelope = FixtureEnvelope<ApprovalsData>;
/** Returned by approve/reject: `data` is the single order that changed. */
export type ApprovalActionEnvelope = FixtureEnvelope<ApprovalOrder>;

/* 리스크 알림 화면 -------------------------------------------------------- */

export type RiskCategory = "정책" | "출처" | "시장" | "승인" | "데이터";
export type RiskSeverity = "중대" | "높음" | "보통" | "낮음";

export type RiskEvent = Api<components["schemas"]["RiskEvent"]>;
export type RiskAlertsData = Api<components["schemas"]["RiskAlertsData"]>;
export type RiskAlertsEnvelope = FixtureEnvelope<RiskAlertsData>;

/* 모의 거래 내역 화면 ------------------------------------------------------ */

export type TradeStatus = "모의승인" | "반려" | "정책 차단" | "만료" | "대기";

export type TradeHistoryItem = Api<components["schemas"]["TradeHistoryItem"]>;
export type TradeRelatedLink = Api<components["schemas"]["TradeRelatedLink"]>;
export type TradeHistoryData = Api<components["schemas"]["TradeHistoryData"]>;
export type TradeHistoryEnvelope = FixtureEnvelope<TradeHistoryData>;

/* 포트폴리오 건강 화면 ----------------------------------------------------- */

export type HealthStatus = "확인 필요" | "차단" | "완료";
export type HealthGroupKey = "policy" | "source" | "risk" | "approval" | "strategy" | "stress" | "complete";

export type HealthGroup = Api<components["schemas"]["HealthGroup"]>;
export type HealthCheck = Api<components["schemas"]["HealthCheck"]>;
export type PortfolioHealthData = Api<components["schemas"]["PortfolioHealthData"]>;
export type PortfolioHealthEnvelope = FixtureEnvelope<PortfolioHealthData>;

/* 승인 전 근거 패킷 화면 --------------------------------------------------- */

export type EvidenceStatus = "확인" | "주의" | "차단";

export type EvidenceChecklistItem = Api<components["schemas"]["EvidenceChecklistItem"]>;
export type EvidencePacket = Api<components["schemas"]["EvidencePacket"]>;
export type EvidencePacketsData = Api<components["schemas"]["EvidencePacketsData"]>;
export type EvidencePacketsEnvelope = FixtureEnvelope<EvidencePacketsData>;

/* 감사 로그 화면 --------------------------------------------------------- */

export type AuditDecisionRow = Api<components["schemas"]["AuditDecisionRow"]>;
export type AuditStepEntry = Api<components["schemas"]["AuditStepEntry"]>;
export type AuditLogData = Api<components["schemas"]["AuditLogData"]>;
export type AuditLogEnvelope = FixtureEnvelope<AuditLogData>;

/* 결정 회고 화면 --------------------------------------------------------- */

export type DecisionReviewOutcome = "승인" | "반려" | "보류";

export type DecisionReviewItem = Api<components["schemas"]["DecisionReviewItem"]>;
export type DecisionReviewData = Api<components["schemas"]["DecisionReviewData"]>;
export type DecisionReviewEnvelope = FixtureEnvelope<DecisionReviewData>;

/* 에이전트 역할 상태 화면 -------------------------------------------------- */

export type AgentRoleState = "대기" | "승인 필요" | "실패 이력";

export type AgentRoleStatusItem = Api<components["schemas"]["AgentRoleStatusItem"]>;
export type AgentRoleStatusData = Api<components["schemas"]["AgentRoleStatusData"]>;
export type AgentRoleStatusEnvelope = FixtureEnvelope<AgentRoleStatusData>;

/* 주간 투자 리포트 화면 ---------------------------------------------------- */

export type ReportRangeKey = "week" | "month" | "quarter";
export type ReportTopicKey =
  | "return" | "risk" | "cash" | "benchmark" | "alpha" | "samsung" | "hynix" | "naver"
  | "approved" | "rejected" | "blocked" | "source" | "volatility" | "slippage" | "tax";

export type ReportRange = Api<components["schemas"]["ReportRange"]>;
export type ReportFact = Api<components["schemas"]["ReportFact"]>;
export type ReportRow = Api<components["schemas"]["ReportRow"]>;
export type ReportRiskItem = Api<components["schemas"]["ReportRiskItem"]>;
export type ReportDetail = Api<
  components["schemas"]["ReportDetail"],
  {
    summaryByRange: Record<ReportRangeKey, string>;
    factsByRange: Record<ReportRangeKey, ReportFact[]>;
  }
>;

export type WeeklyReportData = Api<
  components["schemas"]["WeeklyReportData"],
  {
    ranges: Record<ReportRangeKey, ReportRange>;
    details: Record<ReportTopicKey, ReportDetail>;
  }
>;
export type WeeklyReportEnvelope = FixtureEnvelope<WeeklyReportData>;

/* 세금·수수료 영향 점검 화면 ------------------------------------------------ */

export type TaxFeeStatus = "영향 작음" | "재검토" | "보류 권장";

export type TaxFeeOrder = Api<components["schemas"]["TaxFeeOrder"]>;
export type TaxFeeImpactData = Api<components["schemas"]["TaxFeeImpactData"]>;
export type TaxFeeImpactEnvelope = FixtureEnvelope<TaxFeeImpactData>;

/* 포트폴리오 변경 전/후 비교 화면 ------------------------------------------- */

export type PortfolioChangePolicyType = "pass" | "check" | "block";

export type PortfolioChangeAsset = Api<components["schemas"]["PortfolioChangeAsset"]>;
export type PortfolioChangeStats = Api<components["schemas"]["PortfolioChangeStats"]>;
export type PortfolioChangeCompareData = Api<components["schemas"]["PortfolioChangeCompareData"]>;
export type PortfolioChangeCompareEnvelope = FixtureEnvelope<PortfolioChangeCompareData>;

/* 전략 조정(리밸런싱) 화면 -------------------------------------------------- */

export type RebalanceStrategyKey = "conservative" | "balanced" | "aggressive";
export type RebalanceAssetKey = "cash" | "market" | "samsung" | "sk" | "naver";

export type CurrentAllocation = Api<components["schemas"]["CurrentAllocation"]>;
export type RebalanceStrategy = Api<
  components["schemas"]["RebalanceStrategy"],
  { targets: Record<RebalanceAssetKey, number> }
>;
export type RebalanceProposal = Api<components["schemas"]["RebalanceProposal"]>;
export type RebalancePlanData = Api<
  components["schemas"]["RebalancePlanData"],
  {
    strategies: Record<RebalanceStrategyKey, RebalanceStrategy>;
    proposalsByStrategy: Record<RebalanceStrategyKey, RebalanceProposal[]>;
  }
>;
export type RebalancePlanEnvelope = FixtureEnvelope<RebalancePlanData>;

/* 백테스트 요약 화면 ------------------------------------------------------- */

export type BacktestStrategyKey = "conservative" | "balanced" | "aggressive";
export type BacktestPeriodKey = "3m" | "6m" | "1y";

export type BacktestConfig = Api<components["schemas"]["BacktestConfig"]>;
export type BacktestPeriod = Api<components["schemas"]["BacktestPeriod"]>;
export type BacktestMetrics = Api<components["schemas"]["BacktestMetrics"]>;
export type BacktestRow = Api<components["schemas"]["BacktestRow"]>;
export type BacktestSummaryData = Api<
  components["schemas"]["BacktestSummaryData"],
  {
    configs: Record<BacktestStrategyKey, BacktestConfig>;
    periods: Record<BacktestPeriodKey, BacktestPeriod>;
    metrics: Record<BacktestStrategyKey, Record<BacktestPeriodKey, BacktestMetrics>>;
    rows: Record<BacktestStrategyKey, Record<BacktestPeriodKey, BacktestRow[]>>;
  }
>;
export type BacktestSummaryEnvelope = FixtureEnvelope<BacktestSummaryData>;

/* 기업 상세 화면 --------------------------------------------------------- */

export type CompanyEvidenceKind = "positive" | "negative" | "filing";

export type CompanyChartPoint = Api<components["schemas"]["CompanyChartPoint"]>;
export type CompanyMetric = Api<components["schemas"]["CompanyMetric"]>;
export type CompanyEvidenceItem = Api<components["schemas"]["CompanyEvidenceItem"]>;
export type CompanyPricePanel = Api<components["schemas"]["CompanyPricePanel"]>;
export type CompanyDetailData = Api<components["schemas"]["CompanyDetailData"]>;
export type CompanyDetailEnvelope = FixtureEnvelope<CompanyDetailData>;

/* 데이터 연결 상태 화면 ---------------------------------------------------- */

export type DataConnectionKey =
  | "opendart" | "price" | "securities" | "database" | "report" | "unknown" | "stale" | "permission" | "paper";
export type DataConnectionKind = "blocked" | "mock";

export type DataConnectionFact = Api<components["schemas"]["DataConnectionFact"]>;
export type DataConnectionDetail = Api<components["schemas"]["DataConnectionDetail"]>;
export type DataConnectionCard = Api<components["schemas"]["DataConnectionCard"]>;
export type DataConnectionRow = Api<components["schemas"]["DataConnectionRow"]>;
export type DataQualityChip = Api<components["schemas"]["DataQualityChip"]>;
export type DataConnectionsData = Api<
  components["schemas"]["DataConnectionsData"],
  { details: Record<DataConnectionKey, DataConnectionDetail> }
>;
export type DataConnectionsEnvelope = FixtureEnvelope<DataConnectionsData>;

/* 알림 설정 화면 --------------------------------------------------------- */

export type NotificationChannelId = "inapp" | "browser" | "email" | "messenger";
export type NotificationTypeId = "policy" | "source" | "approval" | "data" | "volatility" | "cost";
export type NotificationSeverity = "중대" | "높음" | "보통";

export type NotificationChannel = Api<components["schemas"]["NotificationChannel"]>;
export type NotificationType = Api<components["schemas"]["NotificationType"]>;
export type NotificationSettingsData = Api<components["schemas"]["NotificationSettingsData"]>;
export type NotificationSettingsEnvelope = FixtureEnvelope<NotificationSettingsData>;

/* 투자 정책 화면 --------------------------------------------------------- */

export type PolicyNumberKey = "maxWeight" | "maxOrder" | "maxLoss" | "minCash" | "volatility" | "expiry";
export type PolicyCheckKey = "limitOrder" | "marketOrder" | "blockUnknown" | "blockCorrection";

export type PolicyNumberRule = Api<components["schemas"]["PolicyNumberRule"]>;
export type PolicyCheckRule = Api<components["schemas"]["PolicyCheckRule"]>;
export type PolicyPreview = Api<components["schemas"]["PolicyPreview"]>;
export type PolicySettingsData = Api<components["schemas"]["PolicySettingsData"]>;
export type PolicySettingsEnvelope = FixtureEnvelope<PolicySettingsData>;

/* 스트레스 테스트 화면 ----------------------------------------------------- */

export type StressScenarioKey = "rates" | "chips" | "fx" | "liquidity";
export type StressAssetKey = "cash" | "market" | "samsung" | "sk" | "naver";

export type StressAsset = Api<components["schemas"]["StressAsset"]>;
export type StressScenario = Api<
  components["schemas"]["StressScenario"],
  { shock: Record<StressAssetKey, number> }
>;
export type StressAssetImpact = Api<components["schemas"]["StressAssetImpact"]>;
export type StressTestData = Api<
  components["schemas"]["StressTestData"],
  {
    scenarios: Record<StressScenarioKey, StressScenario>;
    rowsByScenario: Record<StressScenarioKey, StressAssetImpact[]>;
  }
>;
export type StressTestEnvelope = FixtureEnvelope<StressTestData>;
