export type ReportRangeKey = "week" | "month" | "quarter";
export type ReportTopicKey =
  | "return"
  | "risk"
  | "cash"
  | "benchmark"
  | "alpha"
  | "samsung"
  | "hynix"
  | "naver"
  | "approved"
  | "rejected"
  | "blocked"
  | "source"
  | "volatility"
  | "slippage"
  | "tax";

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

export interface ReportDetail {
  key: ReportTopicKey;
  title: string;
  summary: string | ((range: ReportRange) => string);
  facts: Array<[string, string]> | ((range: ReportRange) => Array<[string, string]>);
}

export const weeklyReportSafetyCopy =
  "모의투자 · 화면 검토용 가상 예시 · 실제 주문 아님 · 실제 성과 아님 · 실제 계좌·API·DB 미연결 · 외부 요청 0건";

export const reportRanges: Record<ReportRangeKey, ReportRange> = {
  week: {
    label: "2026.08.19~2026.08.25",
    shortLabel: "1주",
    start: "128,420,000원",
    end: "130,180,000원",
    profit: "+1,760,000원",
    portfolio: "+1.37%",
    benchmark: "+0.82%",
    alpha: "+0.55%p",
    drawdown: "-0.64%",
    drawdownLabel: "가상 주간 저점",
    formula: "수익률 계산: 1,760,000 ÷ 128,420,000 = 1.37%",
    portfolioBar: 74,
    benchmarkBar: 48,
    alphaBar: 32
  },
  month: {
    label: "2026.07.26~2026.08.25",
    shortLabel: "1개월",
    start: "125,600,000원",
    end: "130,180,000원",
    profit: "+4,580,000원",
    portfolio: "+3.65%",
    benchmark: "+2.14%",
    alpha: "+1.51%p",
    drawdown: "-1.42%",
    drawdownLabel: "가상 월간 저점",
    formula: "수익률 계산: 4,580,000 ÷ 125,600,000 = 3.65%",
    portfolioBar: 82,
    benchmarkBar: 54,
    alphaBar: 41
  },
  quarter: {
    label: "2026.05.26~2026.08.25",
    shortLabel: "3개월",
    start: "121,900,000원",
    end: "130,180,000원",
    profit: "+8,280,000원",
    portfolio: "+6.79%",
    benchmark: "+3.91%",
    alpha: "+2.88%p",
    drawdown: "-2.35%",
    drawdownLabel: "가상 3개월 저점",
    formula: "수익률 계산: 8,280,000 ÷ 121,900,000 = 6.79%",
    portfolioBar: 88,
    benchmarkBar: 58,
    alphaBar: 49
  }
};

export const reportRows = [
  { key: "samsung", group: "기여·부담 종목", label: "삼성전자", value: "+420,000원", meta: "비중 6.65% · DEC-1042 연결", tone: "gain" },
  { key: "hynix", group: "기여·부담 종목", label: "SK하이닉스", value: "+610,000원", meta: "반도체 업종 기여", tone: "gain" },
  { key: "naver", group: "기여·부담 종목", label: "NAVER", value: "-180,000원", meta: "플랫폼 종목 부담", tone: "loss" },
  { key: "approved", group: "에이전트 처리 기록", label: "모의승인", value: "1건", meta: "승인 대기 화면과 연결", tone: "neutral" },
  { key: "rejected", group: "에이전트 처리 기록", label: "반려", value: "1건", meta: "근거 미확인으로 종료", tone: "neutral" },
  { key: "blocked", group: "에이전트 처리 기록", label: "정책 차단", value: "1건", meta: "DEC-1042 출처 미확인", tone: "warning" }
] as const satisfies ReadonlyArray<{ key: ReportTopicKey; group: string; label: string; value: string; meta: string; tone: "gain" | "loss" | "neutral" | "warning" }>;

export const reportRisks = [
  { key: "source", label: "출처 미확인 2건" },
  { key: "volatility", label: "20일 변동성 27.4%" },
  { key: "slippage", label: "슬리피지 미반영" },
  { key: "tax", label: "세금·수수료 단순화" }
] as const satisfies ReadonlyArray<{ key: ReportTopicKey; label: string }>;

export const reportDetails: Record<ReportTopicKey, ReportDetail> = {
  return: { key: "return", title: "기간 수익률", summary: (range) => `총자산 ${range.start}에서 ${range.end}으로 증가한 화면용 계산입니다.`, facts: (range) => [["기간", range.label], ["손익", range.profit], ["수익률", range.portfolio], ["벤치마크", range.benchmark]] },
  risk: { key: "risk", title: "기간 위험 요약", summary: "가상 저점 기준 최대 낙폭과 변동성 근접 여부를 함께 표시합니다.", facts: (range) => [["최대 낙폭", range.drawdown], ["20일 변동성", "27.4%"], ["정책 경계", "28.0%"], ["판정", range.drawdownLabel]] },
  cash: { key: "cash", title: "현금 비중", summary: "최소 현금 비중 15.0%보다 높은 18.4%로 표시되는 가상 상태입니다.", facts: [["현금성 자산", "23,953,000원"], ["총자산", "130,180,000원"], ["비중", "18.4%"], ["정책 하한", "15.0%"]] },
  benchmark: { key: "benchmark", title: "KOSPI 비교", summary: "포트폴리오와 벤치마크 수익률 차이를 기간별로 비교합니다.", facts: (range) => [["포트폴리오", range.portfolio], ["KOSPI", range.benchmark], ["초과수익", range.alpha], ["통화", "KRW"]] },
  alpha: { key: "alpha", title: "초과수익", summary: "벤치마크 대비 초과분은 가상 수익률 차이로만 계산합니다.", facts: (range) => [["포트폴리오", range.portfolio], ["벤치마크", range.benchmark], ["초과수익", range.alpha], ["세금", "미반영"]] },
  samsung: { key: "samsung", title: "삼성전자 기간 기여", summary: "가상 보유 종목 중 수익 기여가 큰 축으로 표시됩니다.", facts: [["기여 손익", "+420,000원"], ["비중", "6.65%"], ["연결 결정", "DEC-1042"], ["출처", "미확인 포함"]] },
  hynix: { key: "hynix", title: "SK하이닉스 기여", summary: "반도체 업종 상승을 화면용 기여 수치로 보여줍니다.", facts: [["기여 손익", "+610,000원"], ["비중", "13.90%"], ["상태", "관찰"], ["데이터", "가상 예시"]] },
  naver: { key: "naver", title: "NAVER 부담", summary: "플랫폼 종목의 기간 하락 기여를 손실 가능성 예시로 표시합니다.", facts: [["기여 손익", "-180,000원"], ["비중", "7.47%"], ["상태", "유지"], ["위험", "단기 변동"]] },
  approved: { key: "approved", title: "모의승인 기록", summary: "사용자 승인 과정을 거친 화면용 기록이며 실제 주문은 생성되지 않습니다.", facts: [["건수", "1건"], ["상태", "화면 상태 변경"], ["실제 주문", "없음"], ["연결", "승인 대기"]] },
  rejected: { key: "rejected", title: "반려 기록", summary: "근거 미확인 또는 정책 충돌로 종료된 가상 제안을 요약합니다.", facts: [["건수", "1건"], ["사유", "근거 미확인"], ["영향", "주문 없음"], ["연결", "감사 로그"]] },
  blocked: { key: "blocked", title: "정책 차단 기록", summary: "DEC-1042는 출처 미확인 상태라 기본 정책에서 차단 예시로 남습니다.", facts: [["건수", "1건"], ["결정", "DEC-1042"], ["차단 조건", "출처 미확인"], ["실제 주문", "없음"]] },
  source: { key: "source", title: "출처 미확인", summary: "일부 근거는 화면용 미확인 데이터로 표시되며 실제 투자 판단에 쓰지 않습니다.", facts: [["미확인", "2건"], ["처리", "정책 차단"], ["표시 방식", "텍스트 경고"], ["외부 요청", "0건"]] },
  volatility: { key: "volatility", title: "변동성 근접", summary: "20일 변동성 27.4%는 정책 경계 28.0%에 근접한 가상 위험입니다.", facts: [["현재", "27.4%"], ["경계", "28.0%"], ["차이", "0.6%p"], ["판정", "주의"]] },
  slippage: { key: "slippage", title: "슬리피지 한계", summary: "체결 가격 차이는 실제 시장 데이터 없이 단순 위험 항목으로만 표시합니다.", facts: [["반영", "미반영"], ["주문 유형", "지정가 예시"], ["영향", "미확인"], ["실거래", "없음"]] },
  tax: { key: "tax", title: "세금·수수료 단순화", summary: "세금과 수수료는 목업 범위 밖이므로 성과 계산에 실제 반영하지 않습니다.", facts: [["수수료", "단순화"], ["세금", "미반영"], ["성과", "가상"], ["통화", "KRW"]] }
};
