export type BacktestStrategyKey = "conservative" | "balanced" | "aggressive";
export type BacktestPeriodKey = "3m" | "6m" | "1y";

export interface BacktestConfig {
  label: string;
  base: {
    ret: number;
    bench: number;
    dd: number;
    vol: number;
    win: number;
  };
}

export interface BacktestPeriod {
  label: string;
  range: string;
  factor: number;
  months: string[];
}

export interface BacktestRow {
  month: string;
  portfolio: number;
  benchmark: number;
  excess: number;
  drawdown: number;
  state: "초과" | "미달";
}

export const backtestConfigs: Record<BacktestStrategyKey, BacktestConfig> = {
  conservative: { label: "보수형", base: { ret: 2.4, bench: 1.8, dd: -3.2, vol: 8.6, win: 58 } },
  balanced: { label: "균형형", base: { ret: 4.8, bench: 3.1, dd: -6.4, vol: 13.2, win: 62 } },
  aggressive: { label: "공격형", base: { ret: 7.1, bench: 3.1, dd: -11.8, vol: 21.7, win: 55 } }
};

export const backtestPeriods: Record<BacktestPeriodKey, BacktestPeriod> = {
  "3m": { label: "3개월", range: "2026.05.26~08.25", factor: 0.55, months: ["2026.06", "2026.07", "2026.08"] },
  "6m": { label: "6개월", range: "2026.02.26~08.25", factor: 1, months: ["2026.04", "2026.05", "2026.06", "2026.07", "2026.08"] },
  "1y": { label: "1년", range: "2025.08.26~2026.08.25", factor: 1.75, months: ["2026.04", "2026.05", "2026.06", "2026.07", "2026.08"] }
};

export function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

export function getBacktestMetrics(strategy: BacktestStrategyKey, period: BacktestPeriodKey) {
  const config = backtestConfigs[strategy];
  const term = backtestPeriods[period];
  return {
    ret: config.base.ret * term.factor,
    bench: config.base.bench * term.factor,
    dd: config.base.dd * (period === "3m" ? 0.72 : period === "1y" ? 1.35 : 1),
    vol: config.base.vol * (period === "3m" ? 0.9 : period === "1y" ? 1.08 : 1),
    win: Math.max(40, config.base.win + (period === "3m" ? -3 : period === "1y" ? 2 : 0))
  };
}

export function getBacktestRows(strategy: BacktestStrategyKey, period: BacktestPeriodKey): BacktestRow[] {
  const term = backtestPeriods[period];
  const metrics = getBacktestMetrics(strategy, period);
  return term.months.map((month, index) => {
    const wave = [0.34, -0.16, 0.27, 0.08, 0.41][index];
    const portfolio = Number((metrics.ret / term.months.length + wave * (strategy === "aggressive" ? 2 : 1)).toFixed(1));
    const benchmark = Number((metrics.bench / term.months.length + [0.12, -0.08, 0.15, 0.04, 0.17][index]).toFixed(1));
    const drawdown = Number((-Math.abs(wave) * (Math.abs(metrics.dd) / 2.2) - 0.4).toFixed(1));
    return { month, portfolio, benchmark, excess: Number((portfolio - benchmark).toFixed(1)), drawdown, state: portfolio >= benchmark ? "초과" : "미달" };
  });
}

export const backtestSafetyCopy =
  "모의투자 · 화면 검토용 가상 예시 · 실제 주문 아님 · 실제 과거 데이터 아님 · 실제 성과 아님 · 실제 계좌·API·DB 미연결 · 외부 요청 0건";
