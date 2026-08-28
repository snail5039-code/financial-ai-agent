import type { Tone } from "../types/dashboard";

export type CompanyEvidenceKind = "positive" | "negative" | "filing";

export interface CompanyEvidence {
  id: string;
  kind: CompanyEvidenceKind;
  title: string;
  subtitle: string;
  body: string;
  sourceLabel: string;
  tone: Tone;
}

export const companyDetail = {
  company: "삼성전자",
  code: "005930",
  market: "KOSPI",
  sector: "전기전자",
  generatedAt: "2026-08-28T15:20:00+09:00",
  dataAsOf: "2026-08-25T14:32:00+09:00",
  isMock: true,
  paperOnly: true,
  executed: false,
  externalConnections: 0,
  safetyCopy: "모의투자 · 가상 예시 · 실제 시세·공시·계좌·API 미연결 · 투자 권유 아님",
  price: {
    current: "71,200원",
    change: "+800원 · +1.14% 예시",
    holding: "120주",
    averagePrice: "68,420원",
    value: "8,544,000원",
    profit: "+333,600원 · +4.06%",
    weight: "6.65%"
  },
  chart: [
    { index: 1, price: 64800, y: 102 },
    { index: 2, price: 65900, y: 87 },
    { index: 3, price: 65300, y: 95 },
    { index: 4, price: 67400, y: 65 },
    { index: 5, price: 68100, y: 55 },
    { index: 6, price: 67700, y: 61 },
    { index: 7, price: 69600, y: 34 },
    { index: 8, price: 70400, y: 23 },
    { index: 9, price: 69800, y: 31 },
    { index: 10, price: 71000, y: 14 },
    { index: 11, price: 70600, y: 20 },
    { index: 12, price: 71200, y: 10 }
  ],
  metrics: [
    { label: "매출", value: "302.2조원", note: "+6.4%", tone: "success" as Tone },
    { label: "영업이익", value: "26.6조원", note: "이익률 8.8%", tone: "neutral" as Tone },
    { label: "영업현금흐름", value: "44.1조원", note: "+11.5%", tone: "success" as Tone },
    { label: "부채비율", value: "26.4%", note: "예시 평균 41.8%", tone: "neutral" as Tone },
    { label: "PER", value: "14.8배", note: "예시 비교 16.2배", tone: "neutral" as Tone },
    { label: "PBR", value: "1.3배", note: "예시 비교 1.6배", tone: "neutral" as Tone }
  ],
  evidence: [
    {
      id: "ev-cashflow",
      kind: "positive" as CompanyEvidenceKind,
      title: "영업현금흐름 개선",
      subtitle: "예시 수치 기반 해석",
      body: "44.1조원, 전년 대비 +11.5%로 설정된 화면용 예시입니다.",
      sourceLabel: "근거 예시",
      tone: "success" as Tone
    },
    {
      id: "ev-debt",
      kind: "positive" as CompanyEvidenceKind,
      title: "낮은 부채비율",
      subtitle: "예시 산업 평균 대비",
      body: "26.4%와 예시 산업 평균 41.8%를 비교한 가상 근거입니다.",
      sourceLabel: "근거 예시",
      tone: "success" as Tone
    },
    {
      id: "ev-profit",
      kind: "positive" as CompanyEvidenceKind,
      title: "영업이익 회복",
      subtitle: "이익률 8.8% 예시",
      body: "영업이익 26.6조원과 이익률 8.8%를 사용한 화면 예시입니다.",
      sourceLabel: "근거 예시",
      tone: "success" as Tone
    },
    {
      id: "ev-volatility",
      kind: "negative" as CompanyEvidenceKind,
      title: "단기 가격 변동성",
      subtitle: "가격 경로 불확실성",
      body: "최근 가격 변화가 확대됐다고 가정한 화면용 경고입니다.",
      sourceLabel: "근거 예시",
      tone: "warning" as Tone
    },
    {
      id: "ev-cycle",
      kind: "negative" as CompanyEvidenceKind,
      title: "업황 회복 지연 가능성",
      subtitle: "전망 불확실성",
      body: "전기전자 업황 회복이 지연될 수 있다는 가상 반대 시나리오입니다.",
      sourceLabel: "근거 예시",
      tone: "warning" as Tone
    },
    {
      id: "ev-limit",
      kind: "negative" as CompanyEvidenceKind,
      title: "예시 데이터 한계",
      subtitle: "실제 검증 미수행",
      body: "실제 시세와 공시를 연결하지 않아 투자 판단에 사용할 수 없습니다.",
      sourceLabel: "근거 예시",
      tone: "danger" as Tone
    }
  ],
  filings: [
    {
      id: "DEMO-FIL-001",
      kind: "filing" as CompanyEvidenceKind,
      title: "2026년 반기보고서 예시",
      subtitle: "2026.08.14 · 미확인",
      body: "실제 공시 원문과 연결되지 않은 화면 구조 검토용 항목입니다. 실제 공시 검증은 수행되지 않았습니다.",
      sourceLabel: "OpenDART 미연결 · 미확인",
      tone: "warning" as Tone
    },
    {
      id: "DEMO-FIL-002",
      kind: "filing" as CompanyEvidenceKind,
      title: "영업실적 잠정치 예시",
      subtitle: "2026.07.31 · 미확인",
      body: "실제 공시 원문과 연결되지 않은 화면 구조 검토용 항목입니다. 실제 공시 검증은 수행되지 않았습니다.",
      sourceLabel: "OpenDART 미연결 · 미확인",
      tone: "warning" as Tone
    },
    {
      id: "DEMO-FIL-003",
      kind: "filing" as CompanyEvidenceKind,
      title: "주요 경영사항 예시",
      subtitle: "2026.07.12 · 미확인",
      body: "실제 공시 원문과 연결되지 않은 화면 구조 검토용 항목입니다. 실제 공시 검증은 수행되지 않았습니다.",
      sourceLabel: "OpenDART 미연결 · 미확인",
      tone: "warning" as Tone
    }
  ]
};
