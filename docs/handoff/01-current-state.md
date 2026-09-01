# 현재 상태 요약

기준일: 2026-08-29 KST

## 저장소 상태

- 원본 작업공간: `C:\Users\snail\OneDrive\바탕 화면\new_idea`
- 기본 브랜치: `main`
- 원격 저장소: `https://github.com/snail5039-code/financial-ai-agent`
- 최신 커밋: `8d0c3a9946549d1f9e570e8086843d7f5068c88f` (`8d0c3a9 백엔드 헬스 API 골격 추가`)
- `main`과 `origin/main`은 `8d0c3a9` 기준으로 일치한다.
- `MOCKUP-015` 세금·수수료 영향 점검 화면은 완료·검증·커밋·푸시했다.
- `MOCKUP-016` 사용자 승인 이력·결정 회고 화면도 완료·검증·커밋·푸시했다.
- `MOCKUP-017` 에이전트별 역할 상태판은 완료·검증·커밋·푸시했다.
- `MOCKUP-018` 포트폴리오 변경 전/후 비교 화면은 완료·검증·커밋·푸시했다.
- `MOCKUP-019` 승인 전 근거 패킷 화면은 완료·검증·커밋·푸시했다.
- `FRONTEND-005` 승인 대기 행 접근성 구조 정리는 `b654282`로 완료·검증·커밋·푸시했다.
- `GOVERNANCE-001` 역할 작업 가시성 운영 규칙 강화는 `93d9375`로 완료·검증·커밋·푸시했다.
- `SYNC-001` 원본 작업공간 인수 문서 동기화는 완료·검증·커밋·푸시했다.

## 현재 제품 상태

- `MOCKUP-019` 승인 전 근거 패킷 화면까지 구현했다.
- 총 19개 정적 화면과 각 1440×900 캡처가 있다.
- React/Vite 프론트엔드 `apps/web`에는 정적 목업 19개에 대응하는 19개 화면 이전이 완료됐다.
- 승인 대기 화면의 주문 행 접근성 구조는 `FRONTEND-005`에서 정리됐다.
- `FRONTEND-FINAL-AUDIT` 최초 검증은 1440×900 하단 잘림 문제로 `실패`였고, `FRONTEND-FINAL-AUDIT-R1` 재작업 후 검증자 19세대가 `FRONTEND-FINAL-AUDIT-R1-V`에서 `통과` 판정했다.
- FastAPI 백엔드는 `apps/api`에 있고, 구현된 엔드포인트는 `GET /api/health`, `GET /api/dashboard`, `GET /api/account`, `GET /api/agents/{analysis|verification|execution}`, `GET /api/approvals`, `POST /api/approvals/{id}/{approve|reject}`다.
- `BACKEND-005`에서 이 프로젝트 최초의 쓰기 경로(승인·반려)를 메모리 저장소로 구현했다. 승인 대기 화면은 이제 백엔드에 연결됐고 `src/fixtures/approvals.ts`는 제거했다.
- `BACKEND-003`에서 대시보드 수직 슬라이스를 완료했다. 대시보드 화면은 서버 응답만 사용하고 프론트 `src/fixtures/dashboard.ts`는 제거됐다.
- 프론트-백엔드 통신은 Vite `server.proxy`를 통한 같은 출처 상대 경로 `/api/*`다. 브라우저가 절대 URL을 호출하지 않는다.
- 응답 계약은 금액 정수·비율 퍼센트 단위 원본 숫자이고, 화면 문자열은 프론트 `src/lib/format.ts`가 만든다.
- `BACKEND-004`에서 계좌·분석 에이전트·검증 에이전트·실행 에이전트 4개 화면을 새로 만들어 백엔드에 연결했다. React 화면은 19개에서 23개가 됐다.
- 이 4개는 정적 목업에 대응 파일이 없다. 목업 사이드바에 `href="#"` 메뉴만 있었고 화면이 없었다. `FINANCIAL_AI_AGENT_IDEA.md` 역할 정의를 근거로 새로 설계했다.
- React 네비게이션에서 누락돼 있던 「실행 에이전트」 항목도 복구했다.
- 정적 목업은 19개 기준서로 동결한다. 새 화면은 React에만 추가한다.
- 백엔드에 연결된 화면은 5개(대시보드·계좌·분석·검증·실행)이고, 나머지 18개는 아직 프론트 로컬 fixture를 사용한다.
- `/api/approvals` 등 나머지 경로는 아직 구현하지 않았으며 404가 기대 상태다.
- 실제 금융 데이터, 계좌, 주문, AI 실행, 외부 API, 운영 DB는 연결하지 않는다.

## 다음 작업

- 다음 작업 후보는 감사 로그·결정 회고·역할 상태 등 나머지 화면이 이 승인 상태를 함께 반영하도록 결정(DEC) 데이터를 한 곳으로 모으는 것이다. 지금은 결정 ID가 16개 프론트 fixture 파일에 각각 흩어져 있어 승인해도 다른 화면은 갱신되지 않는다.
- 검증 방법 보완: 프록시 확인은 상태 코드만 보면 안 된다. Vite는 프록시가 꺼져 있어도 SPA fallback으로 200을 돌려주므로 `content-type`까지 확인한다.
- 화면 추가가 다시 필요해질 경우 다음 화면 번호는 `MOCKUP-020`이다.
- 현재 기본 추천은 새 화면 추가보다 React/Vite 19개 화면과 `GET /api/health`를 유지하면서 다음 백엔드 범위를 작게 분리하는 것이다.
- 풀스택 전환 계획은 루트 요약 문서와 `docs/fullstack/` 분할 문서로 나눴다.
- `BACKEND-CORS-001` CORS 헤더 명시화는 `BACKEND-003`에 흡수되어 완료됐다.
- 승인 흐름 착수 전 확정이 필요한 항목은 상태 저장소(메모리 vs SQLite)와 `allow_methods`에 `POST` 추가 시점이다.

## 최근 검증 메모

- `BACKEND-003`: `GET /api/dashboard` 구현과 프론트 대시보드 연결. 백엔드 `uv run pytest` 9개 통과, 프론트 `npm run typecheck`·`npm run build` 통과. 1440×900 렌더링에서 `.app-shell` 1392×852 유지, main·인스펙터 하단 잘림 없음, 문서 가로·세로 오버플로 0, 콘솔 오류 없음. 화면에 표시되는 모든 숫자 문자열이 이전 fixture 문자열과 동일함을 DOM에서 확인. 네트워크 요청 호스트가 전부 `127.0.0.1:5173`. 백엔드 중단 시 오류 안내와 재시도 버튼 표시, 백엔드 복구 후 재시도로 정상 복구 확인.
- `BACKEND-003` 부수 수정: 기존 대시보드 보유 종목 손익 셀의 색상 분기에서 현금 행이 `"-"`도 `startsWith("-")`에 걸려 `loss` 클래스를 받던 동작이 있었다. 숫자 계약으로 바뀌면서 `null` 분기로 정리됐다.
- `BACKEND-003` 남은 항목: `decision.expiresAt`(14:42)이 `dataAsOf`(15:20)보다 이르다. 기존 목업 fixture에서 이어진 값이라 숫자를 바꾸지 않았고, 승인 흐름에서 만료 기준을 다시 정해야 한다. 인스펙터 워크플로의 `14:28`과 "대기"는 아직 화면에 하드코딩돼 있다.

- `BACKEND-002-V`: 검증자 20세대가 `GET /api/health` 단독 구현을 `통과` 판정했다. 백엔드 테스트 2개 통과, HTTP 200 JSON 응답, 필수 안전값, `/api/dashboard` 404 기대 상태가 확인됐다.
- 위 `allow_headers` 후속 후보는 `BACKEND-003`에서 처리됐다. 현재 `allow_headers`는 `Accept`, `Accept-Language`, `Content-Type` 명시 목록이고 `allow_methods`는 `GET`이다.
- `FRONTEND-FINAL-AUDIT-R1-V`: 검증자 19세대가 React/Vite 19개 화면 최종 회귀를 `통과` 판정했다. `npm run typecheck`, `npm run build`, 19개 화면 1440×900 하단 잘림 해소, 사이드바 하단 안전 고지, 새 중대/높음 회귀 없음이 확인됐다.
- 남은 낮음 이슈: 기업 상세 숨김 보조 텍스트 `.chart-alt`, 세금·수수료/결정 회고/역할 상태의 테스트 훅 마커 내부 가로 overflow. 통과를 막지 않는 후속 정리 후보로 둔다.
- `FRONTEND-FINAL-AUDIT` 최초 판정은 `.app-shell`/`.workspace` 공통 높이 구조 때문에 16개 화면 하단 48px이 잘리는 `실패`였다. R1에서는 공통 레이아웃과 일부 화면 높이 정의를 조정했다.

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
