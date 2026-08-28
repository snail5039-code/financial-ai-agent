import type { PageKey } from "../types/dashboard";

export type RiskSeverity = "all" | "중대" | "높음" | "보통" | "낮음";
export type RiskCategory = "all" | "정책" | "출처" | "시장" | "승인" | "데이터";

export interface RiskEvent {
  id: string;
  time: string;
  title: string;
  decision: string;
  category: Exclude<RiskCategory, "all">;
  severity: Exclude<RiskSeverity, "all">;
  status: string;
  summary: string;
  cause: string;
  action: string;
  policy: string;
  linkPage: PageKey | null;
  linkText: string;
}

export const riskEvents: RiskEvent[] = [
  { id: "RISK-2041", time: "15:10", title: "출처 미확인 차단", decision: "DEC-1042", category: "출처", severity: "높음", status: "확인 대기", summary: "가상 제안의 근거 출처가 확인되지 않아 차단된 예시입니다.", cause: "공시 원문과 가격 출처가 실제 데이터에 연결되지 않았습니다.", action: "출처 미확인 표시와 차단 정책이 함께 적용됐는지 확인하세요.", policy: "출처 미확인 자동 차단", linkPage: "data", linkText: "데이터 연결 보기" },
  { id: "RISK-2042", time: "14:48", title: "종목 비중 한도 초과", decision: "DEC-1048", category: "정책", severity: "높음", status: "차단 유지", summary: "가상 주문 후 종목 비중이 정책 한도를 넘는 예시입니다.", cause: "예상 비중이 화면용 종목별 최대 비중 8.0%를 초과했습니다.", action: "예상 비중과 주문 수량을 투자 정책 화면에서 비교하세요.", policy: "종목별 최대 비중 8.0%", linkPage: "policy", linkText: "투자 정책 보기" },
  { id: "RISK-2043", time: "13:11", title: "승인 만료", decision: "DEC-1047", category: "승인", severity: "보통", status: "확인 완료", summary: "가상 승인 제한 시간이 지나 만료된 이벤트입니다.", cause: "화면용 승인 대기 시간이 10분을 넘었습니다.", action: "모의 거래 내역에서 만료 상태와 기준 시각을 확인하세요.", policy: "승인 만료 10분", linkPage: "trades", linkText: "모의 거래 내역 보기" },
  { id: "RISK-2044", time: "11:36", title: "변동성 경계 초과", decision: "DEC-1045", category: "시장", severity: "높음", status: "확인 대기", summary: "고정 예시 변동성이 화면용 정책 경계를 넘은 이벤트입니다.", cause: "최근 20일 변동성 예시가 정책 경계 28.0%를 초과했습니다.", action: "현재 시장 경보가 아님을 확인하고 가상 정책값을 검토하세요.", policy: "20일 변동성 경계 28.0%", linkPage: "policy", linkText: "투자 정책 보기" },
  { id: "RISK-2045", time: "10:02", title: "데이터 연결 미확인", decision: "연결 점검", category: "데이터", severity: "보통", status: "확인 대기", summary: "공시·가격·계좌 연결이 없는 목업 상태를 알리는 이벤트입니다.", cause: "API·DB·계좌 연결 없이 고정 배열만 사용하고 있습니다.", action: "데이터 연결 화면에서 외부 요청 0건과 미연결 상태를 확인하세요.", policy: "출처 미확인 자동 차단", linkPage: "data", linkText: "데이터 연결 보기" },
  { id: "RISK-2046", time: "09:24", title: "수수료·슬리피지 한계", decision: "DEC-1050", category: "시장", severity: "낮음", status: "확인 완료", summary: "비용 값이 실제 정산이 아닌 가정임을 알리는 이벤트입니다.", cause: "수수료·세금·슬리피지가 화면용 고정 가정으로만 표시됩니다.", action: "모의 거래 내역에서 비용 한계와 기준 통화를 확인하세요.", policy: "실제 비용 산출 없음", linkPage: "trades", linkText: "모의 거래 내역 보기" }
];

export const riskAlertsSafetyCopy =
  "모의투자 · 화면 검토용 가상 예시 · 실제 주문 아님 · 실제 계좌·API·DB 미연결 · 외부 요청 0건";
