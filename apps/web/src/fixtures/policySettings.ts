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

export const policySettings = {
  generatedAt: "2026-08-28T15:20:00+09:00",
  dataAsOf: "2026-08-25T14:32:00+09:00",
  isMock: true,
  paperOnly: true,
  executed: false,
  externalConnections: 0,
  safetyCopy: "모의투자 · 가상 예시 · 실제 계좌·정책 저장·주문·API 호출 없음",
  numberRules: [
    { key: "maxWeight", label: "종목별 최대 비중", unit: "%", min: 1, max: 30, step: 0.1, decimals: 1, value: "8.0", help: "1.0~30.0%, 소수 첫째 자리" },
    { key: "maxOrder", label: "1회 최대 주문금액", unit: "원", min: 100000, max: 10000000, step: 100000, decimals: 0, value: "1000000", help: "100,000~10,000,000원" },
    { key: "maxLoss", label: "일일 최대 손실률", unit: "%", min: 0.5, max: 10, step: 0.1, decimals: 1, value: "3.0", help: "0.5~10.0%, 소수 첫째 자리" },
    { key: "minCash", label: "최소 현금 비중", unit: "%", min: 0, max: 50, step: 0.1, decimals: 1, value: "15.0", help: "0.0~50.0%, 직접 합산 충돌 아님" },
    { key: "volatility", label: "최근 20일 변동성 경계", unit: "%", min: 5, max: 80, step: 0.1, decimals: 1, value: "28.0", help: "5.0~80.0%" },
    { key: "expiry", label: "승인 만료", unit: "분", min: 1, max: 60, step: 1, decimals: 0, value: "10", help: "1~60분, 정수" }
  ] satisfies PolicyNumberRule[],
  checks: [
    { key: "limitOrder", label: "지정가 주문 허용", value: true },
    { key: "marketOrder", label: "시장가 주문 허용", value: false },
    { key: "blockUnknown", label: "출처 미확인 주문 자동 차단", value: true },
    { key: "blockCorrection", label: "정정 공시 미확인 주문 자동 차단", value: true }
  ] satisfies Array<{ key: PolicyCheckKey; label: string; value: boolean }>,
  preview: {
    decisionId: "DEC-1042",
    calculation: "10 x 71,200 = 712,000원",
    amount: 712000,
    nextWeight: 7.2,
    orderType: "지정가",
    sourceState: "미확인"
  }
};
