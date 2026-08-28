import type { Tone } from "../types/dashboard";

export type AuditStepKey = "analysis" | "verification" | "approval";
export type AuditSourceKey = "metrics" | "filing" | "policy";

export interface AuditDecision {
  id: string;
  company: string;
  status: string;
  runId: string;
  tone: Tone;
  initial: string[];
  verified: string[];
  changed: boolean[];
}

export const auditLogData = {
  generatedAt: "2026-08-28T15:20:00+09:00",
  dataAsOf: "2026-08-25T14:32:00+09:00",
  isMock: true,
  paperOnly: true,
  executed: false,
  externalConnections: 0,
  safetyCopy: "화면용 가상 실행 기록 · 실제 에이전트 실행·검증 API·주문 없음",
  labels: ["가격 유형", "수량", "최대 금액", "목표 비중", "무효 조건"],
  decisions: [
    {
      id: "DEC-1042",
      company: "삼성전자",
      status: "조건부 승인",
      runId: "DEMO-RUN-1042",
      tone: "warning" as Tone,
      initial: ["시장가 10주", "10주", "715,000원", "7.20%", "없음"],
      verified: ["지정가 71,200원", "10주", "712,000원", "7.20%", "가격·비중·정정 공시"],
      changed: [true, false, true, false, true]
    },
    {
      id: "DEC-1043",
      company: "NAVER",
      status: "검증 완료 예시",
      runId: "DEMO-RUN-1043",
      tone: "success" as Tone,
      initial: ["지정가 221,000원", "8주", "1,768,000원", "7.10%", "가격"],
      verified: ["지정가 220,000원", "8주", "1,760,000원", "7.10%", "가격·출처"],
      changed: [true, false, true, false, true]
    },
    {
      id: "DEC-1044",
      company: "KODEX 200",
      status: "정책 확인 필요",
      runId: "DEMO-RUN-1044",
      tone: "warning" as Tone,
      initial: ["지정가 35,000원", "20주", "700,000원", "17.10%", "가격"],
      verified: ["지정가 35,000원", "20주", "700,000원", "17.10%", "정책 확인 전 금지"],
      changed: [false, false, false, false, true]
    }
  ],
  steps: {
    analysis: {
      title: "분석 완료 단계",
      type: "유형 · AI 해석",
      input: "화면용 가상 수치",
      result: "최초 제안 생성 예시",
      risk: "실제 에이전트 실행 아님"
    },
    verification: {
      title: "검증 완료 단계",
      type: "유형 · 계산 / 정책 검사",
      input: "최초 제안과 화면용 정책 규칙",
      result: "지정가와 최대 금액 조건을 추가한 가상 결과입니다.",
      risk: "실제 공시·시세 미연결"
    },
    approval: {
      title: "승인 대기 단계",
      type: "유형 · 정책 검사",
      input: "검증 후 가상 제안",
      result: "실제 주문 없는 대기 상태",
      risk: "투자 판단·주문 사용 금지"
    }
  },
  sources: {
    metrics: {
      title: "재무 수치 가상 항목",
      type: "유형 · 계산",
      input: "8개 형식 비교",
      result: "형식 일치, 사실성 미확인",
      risk: "원문 확인 아님"
    },
    filing: {
      title: "공시 원문",
      type: "유형 · 사실",
      input: "실제 원문 입력 없음",
      result: "실제 공시 미연결·미확인",
      risk: "원문 미확인"
    },
    policy: {
      title: "정책 규칙 예시",
      type: "유형 · 정책 검사",
      input: "가상 규칙 3개",
      result: "예시 조건 비교",
      risk: "실제 정책 아님"
    }
  }
};
