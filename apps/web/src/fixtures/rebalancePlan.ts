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

export interface RebalanceProposal extends CurrentAllocation {
  target: number;
  delta: number;
  direction: "비중 확대" | "비중 축소";
  amount: string;
  policy: string;
  source: string;
  effect: string;
}

export const rebalanceBaseAmount = 130_180_000;

export const currentAllocations: CurrentAllocation[] = [
  { key: "cash", name: "현금성 자산", ticker: "KRW", weight: 18.4 },
  { key: "market", name: "KODEX 200", ticker: "069500", weight: 31.6 },
  { key: "samsung", name: "삼성전자", ticker: "005930", weight: 7.2 },
  { key: "sk", name: "SK하이닉스", ticker: "000660", weight: 22.8 },
  { key: "naver", name: "NAVER", ticker: "035420", weight: 20.0 }
];

export const rebalanceStrategies: Record<RebalanceStrategyKey, RebalanceStrategy> = {
  conservative: { label: "보수형", expectedReturn: "연 +4.2%", volatility: "8.6%", drawdown: "-5.1%", targets: { cash: 30, market: 34, samsung: 7, sk: 15, naver: 14 } },
  balanced: { label: "균형형", expectedReturn: "연 +6.8%", volatility: "13.2%", drawdown: "-8.4%", targets: { cash: 18, market: 32, samsung: 8, sk: 22, naver: 20 } },
  aggressive: { label: "공격형", expectedReturn: "연 +9.4%", volatility: "21.7%", drawdown: "-14.8%", targets: { cash: 10, market: 24, samsung: 10, sk: 31, naver: 25 } }
};

export function signedPoint(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%p`;
}

export function getRebalanceProposals(strategy: RebalanceStrategyKey): RebalanceProposal[] {
  const targets = rebalanceStrategies[strategy].targets;
  return currentAllocations
    .filter((asset) => Math.abs(targets[asset.key] - asset.weight) >= 0.1)
    .map((asset) => {
      const delta = Number((targets[asset.key] - asset.weight).toFixed(1));
      const amount = Math.round(((Math.abs(delta) / 100) * rebalanceBaseAmount) / 1000) * 1000;
      return {
        ...asset,
        target: targets[asset.key],
        delta,
        direction: delta > 0 ? "비중 확대" : "비중 축소",
        amount: `약 ${amount.toLocaleString("ko-KR")}원`,
        policy: asset.key === "samsung" && targets[asset.key] >= 8 ? "한도 경계" : "화면상 범위",
        source: "가격·잔고 고정 예시",
        effect: `${asset.name} 비중을 ${asset.weight.toFixed(1)}%에서 ${targets[asset.key].toFixed(1)}%로 조정하는 가상 제안입니다.`
      };
    });
}

export const rebalanceSafetyCopy =
  "모의투자 · 화면 검토용 가상 예시 · 실제 주문 아님 · 실제 주문 생성 없음 · 실제 체결 없음 · 실제 계좌·API·DB 미연결 · 외부 요청 0건";
