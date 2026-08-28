# 현재 상태 요약

기준일: 2026-08-28 KST

## 저장소 상태

- 원본 작업공간: `C:\Users\snail\OneDrive\바탕 화면\new_idea`
- 기본 브랜치: `main`
- 원격 저장소: `https://github.com/snail5039-code/financial-ai-agent`
- 최신 완료 커밋: `93d9375 역할 작업 가시성 운영 규칙 강화`
- `MOCKUP-015` 세금·수수료 영향 점검 화면은 완료·검증·커밋·푸시했다.
- `MOCKUP-016` 사용자 승인 이력·결정 회고 화면도 완료·검증·커밋·푸시했다.
- `MOCKUP-017` 에이전트별 역할 상태판은 완료·검증·커밋·푸시했다.
- `MOCKUP-018` 포트폴리오 변경 전/후 비교 화면은 완료·검증·커밋·푸시했다.
- `MOCKUP-019` 승인 전 근거 패킷 화면은 완료·검증·커밋·푸시했다.
- `FRONTEND-005` 승인 대기 행 접근성 구조 정리는 `b654282`로 완료·검증·커밋·푸시했다.
- `GOVERNANCE-001` 역할 작업 가시성 운영 규칙 강화는 `93d9375`로 완료·검증·커밋·푸시했다.
- `main`과 `origin/main`은 `93d9375`에서 일치한다.

## 현재 제품 상태

- `MOCKUP-019` 승인 전 근거 패킷 화면까지 구현했다.
- 총 19개 정적 화면과 각 1440×900 캡처가 있다.
- React/Vite 프론트엔드 `apps/web`가 생성되어 대시보드, 승인 대기, 승인 전 근거 패킷 화면이 연결됐다.
- 승인 대기 화면의 주문 행 접근성 구조는 `FRONTEND-005`에서 정리됐다.
- 백엔드/FastAPI는 아직 생성하지 않았다.
- 실제 금융 데이터, 계좌, 주문, AI 실행, API, DB는 연결하지 않는다.

## 다음 작업

- 다음 작업은 `FINANCIAL_AI_FULLSTACK_PLAN.md`와 `docs/fullstack/00-readme.md` 기준으로 현재 React 프론트 상태와 향후 FastAPI fixture API 범위를 맞춰 확정하는 것이다.
- 화면 추가가 다시 필요해질 경우 다음 화면 번호는 `MOCKUP-020`이다.
- 현재 기본 추천은 새 화면 추가보다 기존 `apps/web` 프론트를 유지하면서 FastAPI fixture API를 별도 단계로 연결하는 것이다.
- 풀스택 전환 계획은 루트 요약 문서와 `docs/fullstack/` 분할 문서로 나눴다.
- 다음 실질 개발 후보는 FastAPI 골격과 로컬 fixture API 계약 정리다. 단, `AGENTS.md` 흐름에 따라 계획 승인 후 구현한다.

## 최근 검증 메모

- `MOCKUP-019` 신규 파일은 `mockup/financial-dashboard/evidence-packet.html`, `evidence-packet.css`, `evidence-packet.js`, `evidence-packet-1440x900.png`다.
- `MOCKUP-019`은 대체 독립 검증에서 `통과` 판정을 받았다. 검증자는 JS 문법, 1440×900 PNG, 1440×900 렌더링, 결정 4건, 필터 동기화, 금지 연결 패턴 부재, 안전 경계, 로컬 링크를 확인했다.
- `MOCKUP-019`은 `81b2a1d` 커밋에 포함해 원격 `main`에 푸시했다.
- `MOCKUP-019`은 실제 금융 데이터·계좌·주문·AI 실행·API·DB와 연결하지 않았다.
- `MOCKUP-018` 신규 파일은 `mockup/financial-dashboard/portfolio-change-compare.html`, `portfolio-change-compare.css`, `portfolio-change-compare.js`, `portfolio-change-compare-1440x900.png`다.
- `MOCKUP-018`은 대체 독립 검증에서 `통과` 판정을 받았다. 검증자는 JS 문법, 1440×900 PNG, 1440×900 렌더링, 필터 동기화, 금지 연결 패턴 부재, 안전 경계, 로컬 링크를 확인했다.
- `MOCKUP-018`은 실제 금융 데이터·계좌·주문·API·DB와 연결하지 않았고, `81b2a1d` 커밋에 포함해 원격 `main`에 푸시했다.
- `MOCKUP-017`은 대체 독립 검증에서 `통과` 판정을 받았다.
- 신규 파일은 `mockup/financial-dashboard/agent-role-status.html`, `agent-role-status.css`, `agent-role-status.js`, `agent-role-status-1440x900.png`다.
- `MOCKUP-017`은 실제 금융 데이터·계좌·주문·API·DB 및 실제 AI 실행과 연결하지 않았고, `81b2a1d` 커밋에 포함해 원격 `main`에 푸시했다.
- `FRONTEND-005`는 React/Vite `apps/web` 승인 대기 화면의 주문 행을 `button role="row"`에서 접근성 의미가 충돌하지 않는 선택 가능한 grid 행 구조로 정리했고, `b654282` 커밋에 포함해 원격 `main`에 푸시했다.
- `GOVERNANCE-001`은 공식 역할 작업 가시성, `create_thread` 기반 세대교체, 숨은 multi-agent 제한을 문서화했고, `93d9375` 커밋에 포함해 원격 `main`에 푸시했다.
- `MOCKUP-016`은 대체 독립 검증에서 최초 `실패`였고, 우측 인스펙터 잘림과 빈 결과 링크 R1 재작업 후 `MOCKUP-016-V-R1` 재검증에서 `통과` 판정을 받았다.
- 신규 파일은 `mockup/financial-dashboard/decision-review.html`, `decision-review.css`, `decision-review.js`, `decision-review-1440x900.png`다.
- `MOCKUP-016` 관련 커밋·푸시는 `13e0e6f`에 포함됐다.
- `MOCKUP-015`는 대체 독립 검증에서 최초 `조건부 통과`였고, 루트 README 누락 R1 재작업 후 `MOCKUP-015-V-R1` 재검증에서 `통과` 판정을 받았다.
- 신규 파일은 `mockup/financial-dashboard/tax-fee-impact.html`, `tax-fee-impact.css`, `tax-fee-impact.js`, `tax-fee-impact-1440x900.png`다.
- `MOCKUP-015` 관련 커밋·푸시는 `13e0e6f`에 포함됐다.
- `MOCKUP-014`는 검증자 8세대가 `통과` 판정했다.
- 검증자 7세대는 1차에서 조건부 통과를 냈고, R1/R2 재보고는 빈 결과로 종료됐다.
- 7세대가 지적한 하단 안전 고지 잘림 문제는 재작업 후 8세대 검증에서 해소 확인됐다.
