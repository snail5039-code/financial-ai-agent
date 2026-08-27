import type { Tone } from "../types/dashboard";

export interface ApprovalOrder {
  id: string;
  company: string;
  code: string;
  side: "매수" | "매도";
  quantity: number;
  price: number;
  amount: number;
  status: string;
  filter: "conditional" | "verified" | "attention";
  verification: string;
  expiry: string;
  policy: string;
  source: string;
  warning: string;
  warningText: string;
  tone: Tone;
}

export const approvalOrders: ApprovalOrder[] = [
  {
    id: "DEC-1042",
    company: "삼성전자",
    code: "005930",
    side: "매수",
    quantity: 10,
    price: 71200,
    amount: 712000,
    status: "조건부 승인",
    filter: "conditional",
    verification: "조건부",
    expiry: "14:42",
    policy: "통과 예시",
    source: "실제 공시 미연결 · 출처 미확인",
    warning: "변동성 주의",
    warningText: "지정가 이하에서만 유효한 화면용 조건입니다.",
    tone: "warning"
  },
  {
    id: "DEC-1043",
    company: "NAVER",
    code: "035420",
    side: "매도",
    quantity: 8,
    price: 220000,
    amount: 1760000,
    status: "검토 완료",
    filter: "verified",
    verification: "형식 확인",
    expiry: "14:51",
    policy: "통과 예시",
    source: "화면용 예시 · 실제 출처 미연결",
    warning: "가격 조건 확인",
    warningText: "지정가 조건은 실제 시세와 비교되지 않았습니다.",
    tone: "success"
  },
  {
    id: "DEC-1044",
    company: "KODEX 200",
    code: "069500",
    side: "매수",
    quantity: 20,
    price: 35000,
    amount: 700000,
    status: "정책 확인 필요",
    filter: "attention",
    verification: "한도 확인",
    expiry: "15:03",
    policy: "확인 필요",
    source: "화면용 예시 · 실제 출처 미연결",
    warning: "정책 확인 필요",
    warningText: "사용자 정책 한도를 실제 시스템에서 확인하지 않았습니다.",
    tone: "warning"
  },
  {
    id: "DEC-1045",
    company: "TIGER 미국S&P500",
    code: "360750",
    side: "매수",
    quantity: 15,
    price: 21000,
    amount: 315000,
    status: "출처 미확인",
    filter: "attention",
    verification: "출처 미확인",
    expiry: "15:10",
    policy: "확인 필요",
    source: "출처 미확인 · 확인으로 표시하지 않음",
    warning: "출처 주의",
    warningText: "외부 출처가 연결되지 않아 확인 완료로 취급할 수 없습니다.",
    tone: "danger"
  }
];
