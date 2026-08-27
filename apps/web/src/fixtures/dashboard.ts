import type { DashboardData } from "../types/dashboard";

export const dashboardFixture: DashboardData = {
  generatedAt: "2026-08-27T16:30:00+09:00",
  dataAsOf: "2026-08-27T15:20:00+09:00",
  isMock: true,
  disclaimer: "화면 검토용 가상 예시이며 실제 계좌·주문·API와 연결되지 않습니다.",
  title: "투자 운영",
  accountLabel: "시뮬레이션 계좌",
  summary: {
    totalAsset: "128,450,000원",
    todayProfit: "+1,042,000원",
    todayProfitRate: "+0.82%",
    principal: "112,000,000원",
    accumulatedProfit: "+16,450,000원",
    cashWeight: "18.4%",
    lastVerified: "14:31"
  },
  chart: [
    { label: "6월 1주", portfolio: -1.2, benchmark: -0.8 },
    { label: "6월 3주", portfolio: 0.4, benchmark: 0.2 },
    { label: "7월 1주", portfolio: 1.8, benchmark: 1.1 },
    { label: "7월 3주", portfolio: 3.7, benchmark: 2.4 },
    { label: "8월 1주", portfolio: 5.2, benchmark: 3.1 },
    {
      label: "8월 2주",
      portfolio: 6.42,
      benchmark: 3.18,
      event: "검증 후 삼성전자 10주 모의승인 후보"
    },
    { label: "8월 4주", portfolio: 6.9, benchmark: 3.7 }
  ],
  holdings: [
    {
      name: "삼성전자",
      code: "005930",
      quantity: "120주",
      averagePrice: "68,420원",
      currentPrice: "71,200원",
      value: "8,544,000원",
      profit: "+333,600원",
      profitRate: "+4.06%",
      weight: "6.65%",
      status: "비중 확대 검토",
      tone: "warning",
      selected: true
    },
    {
      name: "SK하이닉스",
      code: "000660",
      quantity: "96주",
      averagePrice: "172,400원",
      currentPrice: "186,000원",
      value: "17,856,000원",
      profit: "+1,305,600원",
      profitRate: "+7.89%",
      weight: "13.90%",
      status: "관찰",
      tone: "neutral"
    },
    {
      name: "NAVER",
      code: "035420",
      quantity: "48주",
      averagePrice: "207,800원",
      currentPrice: "200,000원",
      value: "9,600,000원",
      profit: "-374,400원",
      profitRate: "-3.75%",
      weight: "7.47%",
      status: "유지",
      tone: "neutral"
    },
    {
      name: "KODEX 200",
      code: "069500",
      quantity: "610주",
      averagePrice: "33,980원",
      currentPrice: "35,000원",
      value: "21,350,000원",
      profit: "+622,200원",
      profitRate: "+3.00%",
      weight: "16.62%",
      status: "유지",
      tone: "neutral"
    },
    {
      name: "TIGER 미국S&P500",
      code: "360750",
      quantity: "2,260주",
      averagePrice: "19,320원",
      currentPrice: "21,000원",
      value: "47,460,000원",
      profit: "+3,796,800원",
      profitRate: "+8.70%",
      weight: "36.95%",
      status: "관찰",
      tone: "neutral"
    },
    {
      name: "현금성 자산",
      code: "KRW",
      quantity: "-",
      averagePrice: "-",
      currentPrice: "-",
      value: "23,640,000원",
      profit: "-",
      profitRate: "",
      weight: "18.40%",
      status: "대기",
      tone: "info"
    }
  ],
  decision: {
    company: "삼성전자",
    code: "005930",
    decisionId: "DEC-1042",
    status: "조건부 승인 후보",
    statusTone: "warning",
    proposal: "삼성전자 10주 지정가 매수",
    limitAmount: "712,000원",
    targetWeight: "6.65% → 7.20%",
    expiresAt: "14:42",
    evidence: [
      {
        title: "영업현금흐름 전년 동기 대비 개선",
        detail: "화면 구조 검토를 위한 가상 근거입니다. 실제 공시 원문은 연결되지 않았습니다.",
        source: "실제 공시 미연결 · 출처 미확인",
        tone: "warning"
      },
      {
        title: "부채비율이 산업 평균보다 낮음",
        detail: "fixture에 포함된 예시 수치만 사용합니다.",
        source: "가상 재무 지표",
        tone: "neutral"
      },
      {
        title: "메모리 가격 회복 구간 진입",
        detail: "실제 시세나 뉴스 API와 연결되지 않은 시나리오 문구입니다.",
        source: "화면 검토용 가설",
        tone: "warning"
      }
    ],
    checks: [
      { label: "재무 수치", value: "8/8 형식 일치", tone: "success" },
      { label: "출처 연결", value: "미확인", tone: "warning" },
      { label: "정책 한도", value: "통과 예시", tone: "success" },
      { label: "실제 주문", value: "생성 안 됨", tone: "success" }
    ],
    invalidConditions: [
      "지정가가 71,200원을 초과할 때",
      "목표 비중이 8%를 초과할 때",
      "최신 정정 공시가 확인될 때"
    ]
  }
};
