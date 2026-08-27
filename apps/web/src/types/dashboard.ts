import type { LucideIcon } from "lucide-react";

export type Tone = "neutral" | "info" | "success" | "warning" | "danger";
export type PageKey = "dashboard" | "approvals" | "evidence";

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
