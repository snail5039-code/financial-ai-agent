export type NotificationChannelId = "inapp" | "browser" | "email" | "messenger";
export type NotificationTypeId = "policy" | "source" | "approval" | "data" | "volatility" | "cost";
export type NotificationSeverity = "중대" | "높음" | "보통";

export interface NotificationChannel {
  id: NotificationChannelId;
  name: string;
  state: string;
  summary: string;
  enabled: boolean;
}

export interface NotificationType {
  id: NotificationTypeId;
  name: string;
  desc: string;
  enabled: boolean;
}

export const notificationChannels: NotificationChannel[] = [
  { id: "inapp", name: "앱 내부", state: "앱 내부만", summary: "화면 안 배지와 목록에만 표시합니다.", enabled: true },
  { id: "browser", name: "브라우저", state: "권한 요청 없음", summary: "브라우저 알림 권한은 요청하지 않습니다.", enabled: false },
  { id: "email", name: "이메일", state: "미연결", summary: "메일 서버와 계정은 연결하지 않았습니다.", enabled: false },
  { id: "messenger", name: "메신저", state: "미연결", summary: "메신저 앱과 외부 전송은 없습니다.", enabled: false }
];

export const notificationTypes: NotificationType[] = [
  { id: "policy", name: "정책 차단", desc: "종목 비중·주문 한도 같은 정책 이벤트", enabled: true },
  { id: "source", name: "출처 미확인", desc: "공시·가격 출처가 확인되지 않은 이벤트", enabled: true },
  { id: "approval", name: "승인 만료", desc: "사용자 승인 제한 시간이 지난 이벤트", enabled: true },
  { id: "data", name: "데이터 연결 문제", desc: "API·DB·계좌 미연결 상태 알림", enabled: true },
  { id: "volatility", name: "변동성 경계", desc: "화면용 변동성 기준 초과 이벤트", enabled: false },
  { id: "cost", name: "비용 한계", desc: "수수료·세금·슬리피지 가정 안내", enabled: false }
];

export function notificationSeverityLabel(severity: NotificationSeverity) {
  if (severity === "중대") return "중대만";
  if (severity === "보통") return "보통 포함";
  return "높음 이상";
}

export const notificationSafetyCopy =
  "모의투자 · 화면 검토용 가상 예시 · 실제 주문 아님 · 실제 계좌·API·DB 미연결 · 실제 알림 발송 없음 · 브라우저 권한 요청 없음 · 외부 요청 0건";
