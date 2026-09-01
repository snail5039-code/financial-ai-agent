# 현재 상태 요약

기준일: 2026-09-01 KST

## ⚠️ 미커밋 작업 있음

작업 디렉터리에 `FRONTEND-006`~`FRONTEND-011`이 전부 완료됐지만 아직 커밋하지 않았다 (이 프로젝트는 사용자가 명시적으로 "커밋"이라고 지시할 때만 커밋한다). `git status`로 보면 아래가 미커밋 상태다:

- `apps/web/package.json`/`package-lock.json`, `apps/web/vite.config.ts`, `apps/web/src/types/dashboard.ts`(1112→352줄), 신규 `apps/web/src/types/api.generated.ts`, 신규 `apps/api/scripts/`(OpenAPI export 스크립트) — **FRONTEND-006** (OpenAPI→TS 타입 생성)
- `apps/web/src/components/AppShell.tsx`, `apps/web/src/api/approvals.ts`, `apps/web/src/pages/ApprovalQueuePage.tsx`, 신규 `apps/web/src/lib/useApprovalsPendingCount.ts` — **FRONTEND-006** (사이드바 「승인 대기」 배지 하드코딩 제거)
- 신규 `apps/web/playwright.config.ts`, `apps/web/e2e/`(dashboard/navigation/approvals 3개 스펙) — **FRONTEND-007** (Playwright e2e 도입)
- `apps/api/app/fixtures/{approvals,decisions}.py`, `apps/web/src/pages/{DashboardPage,ApprovalQueuePage}.tsx` — **FRONTEND-008** (`expiresAt`이 `dataAsOf`보다 이르던 문제 4건 전부 수정, 워크플로 3단계 하드코딩 표시 실제 상태 반영)
- `apps/api/app/schemas/{agent_role_status,agents,decision_review,risk_alerts,tax_fee_impact,trade_history}.py` — **FRONTEND-009** (`linkPage`/`page` 필드를 `str`에서 전용 `Literal`로 좁힘, `types/dashboard.ts`의 관련 오버라이드 6곳 제거)
- 신규 `apps/web/e2e/all-screens-load.spec.ts` — **FRONTEND-010** (23개 화면 전부를 순회하며 에러 화면·JS 예외 부재를 확인하는 얕은 회귀 스윕 추가)
- `apps/api/app/store/approvals.py`(SQLite 재작성), `apps/api/app/main.py`(`APPROVALS_DB_PATH` 환경변수, 기본 파일 경로), `apps/web/playwright.config.ts`(테스트는 `:memory:` 강제) — **FRONTEND-011** (`ApprovalStore`를 메모리 딕셔너리에서 SQLite로 전환, 사용자 요청)
- `.gitignore`, `README.md`, `docs/handoff/01-current-state.md`(이 파일), `docs/handoff/04-next-candidates.md`도 위 작업들에 맞춰 같이 수정했다.

**전부 검증 완료**: 백엔드 `uv run pytest`(venv 직접 실행 시 `apps/api/.venv/Scripts/python.exe -m pytest -q`) 110개 통과, 프론트 `npm run typecheck`·`npm run build` 통과, `npm run test:e2e`(Playwright) 3개 통과(연속 두 번 실행해 상태 오염 없음도 확인). 커밋 여부·범위는 사용자에게 확인 후 진행한다.

## 저장소 상태

- 원본 작업공간: `C:\Users\snail\OneDrive\바탕 화면\new_idea`
- 기본 브랜치: `main`
- 원격 저장소: `https://github.com/snail5039-code/financial-ai-agent`
- 최신 **커밋된** 상태: `f075f38 결정 ID 전수 대조, 놓쳤던 DEC-1043 충돌과 DEC-1042/1044 시점 불일치 수정`
- `main`과 `origin/main`은 `f075f38` 기준으로 일치한다. 이후 위 "미커밋 작업 있음"에 적은 변경이 작업 디렉터리에 쌓여 있다.
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
- FastAPI 백엔드는 `apps/api`에 있고, **23개 화면 전부**가 백엔드 엔드포인트에 연결됐다(`BACKEND-007`). 프론트 `apps/web/src/fixtures/`는 완전히 비었다.
- `BACKEND-005`에서 이 프로젝트 최초의 쓰기 경로(승인·반려)를 메모리 저장소로 구현했다. 승인 대기 화면은 이제 백엔드에 연결됐고 `src/fixtures/approvals.ts`는 제거했다.
- `BACKEND-003`에서 대시보드 수직 슬라이스를 완료했다. 대시보드 화면은 서버 응답만 사용하고 프론트 `src/fixtures/dashboard.ts`는 제거됐다.
- 프론트-백엔드 통신은 Vite `server.proxy`를 통한 같은 출처 상대 경로 `/api/*`다. 브라우저가 절대 URL을 호출하지 않는다.
- 응답 계약은 금액 정수·비율 퍼센트 단위 원본 숫자이고, 화면 문자열은 프론트 `src/lib/format.ts`가 만든다.
- `BACKEND-004`에서 계좌·분석 에이전트·검증 에이전트·실행 에이전트 4개 화면을 새로 만들어 백엔드에 연결했다. React 화면은 19개에서 23개가 됐다.
- 이 4개는 정적 목업에 대응 파일이 없다. 목업 사이드바에 `href="#"` 메뉴만 있었고 화면이 없었다. `FINANCIAL_AI_AGENT_IDEA.md` 역할 정의를 근거로 새로 설계했다.
- React 네비게이션에서 누락돼 있던 「실행 에이전트」 항목도 복구했다.
- 정적 목업은 19개 기준서로 동결한다. 새 화면은 React에만 추가한다.
- (`BACKEND-007` 이전 스냅샷: 당시 백엔드에 연결된 화면은 5개였다. 지금은 위에 적었듯 23개 전부다.)
- 실제 금융 데이터, 계좌, 주문, AI 실행, 외부 API, 운영 DB는 연결하지 않는다.

## 다음 작업

- `BACKEND-006`에서 결정 데이터 통합 1차를 완료했다. DEC-1042의 정적 사실과 실시간 승인 상태를 대시보드·승인 대기·에이전트 화면이 공유하고, 어느 화면에서 승인/반려해도 나머지가 즉시 반영된다.
- 이 작업 중 실제 콘텐츠 버그를 하나 발견해 고쳤다: `agents.py`의 검증 에이전트가 "NAVER 관찰 유지, 반려"라고 쓰던 항목이 승인 대기의 실제 "NAVER 매도 8주 대기중" 주문과 같은 DEC-1043 ID를 쓰고 있었다. 후자를 DEC-1057로 옮겨 분리했다.
- `BACKEND-007`에서 나머지 17개 화면(리스크 알림, 거래 내역, 포트폴리오 건강, 근거 패킷, 감사 로그, 결정 회고, 역할 상태, 주간 리포트, 세금·수수료, 변경 비교, 전략 조정, 백테스트, 기업 상세, 데이터 연결, 알림 설정, 투자 정책, 스트레스 테스트)를 전부 백엔드로 옮겼다. 모두 읽기 전용 `GET`이며 정책/알림 설정의 "가상 적용"은 여전히 저장되지 않는 화면 상태다.
- 이 과정에서 DEC-1043·DEC-1044도 `decisions.py` 공유 상수로 통합했고, `evidence_packets.py`가 DEC-1042 실시간 승인 상태를 반영하도록 새로 연결했다.
- 마이그레이션 중 실제 런타임 크래시를 하나 발견해 고쳤다: `TaxFeeImpactPage`, `DecisionReviewPage`, `AgentRoleStatusPage`, `PortfolioChangeComparePage` 4개 화면에서 조기 반환(로딩 중 return) 아래에 `useEffect`가 있어 React Hooks 순서 규칙을 위반하고 있었다. `useRef` 간접 참조로 고쳤다.
- 16개 결정 ID 전체의 서사 대조를 완료했다(`docs/backend/12-full-decision-id-audit.md`). BACKEND-006에서 절반만 고쳐졌던 DEC-1043 충돌(`agent_role_status.py` 2곳, `decision_review.py`)을 추가로 발견해 DEC-1057로 통일했고, `decision_review.py`가 갖고 있던 DEC-1042·DEC-1044 시점 충돌도 각각 DEC-1058·DEC-1059로 분리했다. 앞으로 같은 종류의 충돌을 잡는 회귀 테스트 2개를 추가했다(`test_no_row_contradicts_a_currently_pending_approval`, `test_no_role_claims_a_pending_decision_was_rejected`). `trade_history`/`weekly_report`/`risk_alerts`의 DEC-1042 재사용은 동시 모순이 아니라고 확인해 그대로 남겼다.
- 검증 방법 보완: 프록시 확인은 상태 코드만 보면 안 된다. Vite는 프록시가 꺼져 있어도 SPA fallback으로 200을 돌려주므로 `content-type`까지 확인한다.
- 화면 추가가 다시 필요해질 경우 다음 화면 번호는 `MOCKUP-020`이다.
- 현재 기본 추천은 새 화면 추가보다 React/Vite 19개 화면과 `GET /api/health`를 유지하면서 다음 백엔드 범위를 작게 분리하는 것이다.
- 풀스택 전환 계획은 루트 요약 문서와 `docs/fullstack/` 분할 문서로 나눴다.
- `BACKEND-CORS-001` CORS 헤더 명시화는 `BACKEND-003`에 흡수되어 완료됐다.
- 승인 흐름 착수 전 확정이 필요한 항목은 상태 저장소(메모리 vs SQLite)와 `allow_methods`에 `POST` 추가 시점이다.
- `FRONTEND-006`에서 `docs/backend/12-full-decision-id-audit.md`가 남긴 다음 우선순위 1·3번을 처리했다.
  - 사이드바 「승인 대기」 배지 하드코딩(`badge: "4"`)을 제거하고, `GET /api/approvals`의 실제 `pending` 개수를 쓰는 `useApprovalsPendingCount` 훅으로 바꿨다(`apps/web/src/lib/useApprovalsPendingCount.ts`). 승인/반려 호출이 `approvals:changed` 커스텀 이벤트를 쏘고, `AppShell`이 이를 구독해 같은 화면에서 승인해도 리페치 없이 즉시 갱신된다. 브라우저에서 승인 1건 후 배지가 4→3으로 바뀌는 것을 확인했다.
  - `apps/api`에 OpenAPI 스키마 export 스크립트(`scripts/export_openapi.py`)를 추가하고, `apps/web`에 `openapi-typescript`를 도입해 `npm run generate:types`(`apps/web/package.json`)로 `src/types/api.generated.ts`를 생성하도록 파이프라인을 연결했다. `types/dashboard.ts`(1112줄)를 이 생성 타입에 대한 별칭 중심으로 다시 썼고, 손으로 유지할 필요가 진짜로 있는 것만 남겼다: Dict 형태 응답 필드의 리터럴 키 유니언(OpenAPI의 `propertyNames.enum`이 코드젠에서 `{[key:string]:X}`로 뭉개짐), `linkPage`/`page`처럼 프론트 전용 `PageKey`를 가리키지만 백엔드 스키마엔 `string`으로만 잡히는 필드, 그리고 Pydantic 기본값 때문에 스키마에서 `?`가 붙는(실제로는 항상 내려오는) 필드의 옵셔널 제거(`Data<T>`/`Api<T,U>` 유틸리티). 결과적으로 파일이 1112줄→348줄로 줄었다. `npm run typecheck`·`npm run build` 통과, 백엔드 `pytest` 110개 통과, 브라우저로 백테스트·전략 조정·스트레스 테스트(Dict 타입 화면)와 리스크 알림→데이터 연결(`linkPage` 오버라이드) 이동을 직접 확인했다.
  - 이 과정에서 `types/dashboard.ts`에 실제로 있던 버그를 발견해 없앴다: `DecisionReviewItem`/`DecisionReviewData`, `AgentRoleStatusItem`/`AgentRoleStatusData`, `TaxFeeOrder`/`TaxFeeImpactData`, `PortfolioChangeAsset`/`PortfolioChangeCompareData`가 각각 두 번씩 선언돼 있었다(백엔드 연결 전 fixture 시절 타입이 지워지지 않고 남아 TS interface 병합으로 조용히 합쳐진 상태). 어느 페이지에서도 쓰지 않는 `PortfolioChangeFilter`/`TaxFeeImpactFilter`/`DecisionReviewFilter`/`AgentRoleStatusFilter`도 죽은 코드로 확인해 제거했다.
- `FRONTEND-007`에서 우선순위 2번(프론트 테스트 0개)을 처리했다. Playwright를 도입해(`apps/web/playwright.config.ts`, `apps/web/e2e/`) 핵심 흐름 3개를 커버했다: 대시보드 로드, 사이드바 내비게이션, 승인 대기 승인/반려(사이드바 배지·행 상태 전환 포함). 승인 저장소가 리셋 엔드포인트 없는 메모리 딕셔너리라는 점 때문에, 테스트는 개발자가 쓰는 8000/5173이 아니라 전용 포트(API 8010·웹 5174)에서 매 실행마다 새 FastAPI 프로세스로 뜨도록 구성했다(`vite.config.ts`의 `VITE_API_PORT`/`VITE_PORT` 지원). `npm run test:e2e`로 실행하며, 같은 스위트를 연달아 두 번 돌려 상태가 새지 않고 매번 통과하는 것을 확인했다.
- `FRONTEND-008`에서 `decision.expiresAt`이 `dataAsOf`보다 이르던 문제를 고쳤다. DEC-1042뿐 아니라 승인 대기 4건 전부(`DEC-1042`~`1045`)가 같은 문제였다 — 상대 순서·간격은 유지한 채 4개 전부 +1시간씩 밀었다. 대시보드·승인 대기 화면의 워크플로 3단계도 하드코딩된 `14:28`/"대기"만 보여주고 승인/반려 후에도 안 바뀌던 것을, 실제 `decision.decidedAt`을 반영하도록 고쳤다. 브라우저에서 승인 직후 "대기"→실제 승인 시각으로 바뀌는 것 확인. 백엔드 `pytest` 110개·프론트 `build` 통과.
- `FRONTEND-009`에서 `linkPage`/`page` 필드 타입 불일치를 고쳤다. `HealthCheck.linkPage`만 Pydantic `Literal`이고 `AgentWorkItem`/`TaxFeeOrder`/`DecisionReviewItem`/`AgentRoleStatusItem`/`RiskEvent`/`TradeRelatedLink`는 `str`이었다. 각 스키마 파일에 실제 fixture 값만 모은 전용 `Literal`(`AgentWorkItemLinkPage` 등)을 새로 만들어 좁혔다. 프론트에서 이 필드들을 `PageKey`로 좁히던 `Api<T, {linkPage: PageKey}>` 오버라이드 6곳이 이제 필요 없어져 `types/dashboard.ts`에서 지웠다(352줄). 백엔드 `pytest` 110개·프론트 `typecheck`/`build`/`test:e2e` 전부 통과.
- `FRONTEND-010`에서 Playwright 커버리지를 넓혔다. 기존 3개(대시보드·내비게이션·승인)는 깊은 흐름 검증이고, 나머지 20개 화면은 손으로 클릭해야만 회귀를 잡을 수 있었다. `e2e/all-screens-load.spec.ts`를 추가해 23개 화면 전부를 순회하며 `FixtureFallback`의 에러 화면과 uncaught JS 예외가 없는지만 얕게 확인한다. 화면별 세부 내용은 검증하지 않지만, "화면이 아예 안 뜬다"류의 회귀는 이제 전체 화면에서 잡힌다. 연속 3회 실행해 안정성 확인.
- `FRONTEND-011`에서 `ApprovalStore`를 SQLite로 전환했다(사용자가 Postgres 대안을 먼저 제안했으나, 로컬 단일 프로세스 데모에 외부 서비스 의존은 과하다고 판단해 SQLite로 확정). 4개 주문의 정적 사실(회사명·가격 등)은 그대로 `build_approval_orders()`에서 오고, 실제로 바뀌는 `decisionStatus`/`decidedAt`만 `approval_decisions` 테이블에 저장한다 — 재시작해도 결정이 없는 ID는 여전히 "pending"이라 재시딩이 필요 없는 구조. `ApprovalStore(db_path=":memory:")`가 기본값이라 `create_app()`을 인자 없이 호출하는 기존 21개 테스트 파일은 전혀 안 건드려도 격리가 유지된다. 실제 앱은 `app/main.py`가 `APPROVALS_DB_PATH` 환경변수(기본값 `apps/api/data/approvals.db`)로 실제 파일을 쓰고, Playwright e2e는 같은 변수를 `:memory:`로 오버라이드해 격리한다. FastAPI가 sync 라우터를 스레드풀에서 돌리는 점 때문에 `sqlite3.connect(..., check_same_thread=False)` + `threading.Lock`으로 접근을 직렬화했다. 브라우저로 DEC-1042 승인 후 서버를 완전히 재시작해 승인 상태가 유지되는 것, 나머지 3건은 그대로 pending인 것을 확인했다. 백엔드 `pytest` 110개(무변경), 프론트 `build`·`test:e2e`(연속 2회) 전부 통과.

## 최근 검증 메모

- `BACKEND-003`: `GET /api/dashboard` 구현과 프론트 대시보드 연결. 백엔드 `uv run pytest` 9개 통과, 프론트 `npm run typecheck`·`npm run build` 통과. 1440×900 렌더링에서 `.app-shell` 1392×852 유지, main·인스펙터 하단 잘림 없음, 문서 가로·세로 오버플로 0, 콘솔 오류 없음. 화면에 표시되는 모든 숫자 문자열이 이전 fixture 문자열과 동일함을 DOM에서 확인. 네트워크 요청 호스트가 전부 `127.0.0.1:5173`. 백엔드 중단 시 오류 안내와 재시도 버튼 표시, 백엔드 복구 후 재시도로 정상 복구 확인.
- `BACKEND-003` 부수 수정: 기존 대시보드 보유 종목 손익 셀의 색상 분기에서 현금 행이 `"-"`도 `startsWith("-")`에 걸려 `loss` 클래스를 받던 동작이 있었다. 숫자 계약으로 바뀌면서 `null` 분기로 정리됐다.
- ~~`BACKEND-003` 남은 항목: `decision.expiresAt`(14:42)이 `dataAsOf`(15:20)보다 이르다. ... 인스펙터 워크플로의 `14:28`과 "대기"는 아직 화면에 하드코딩돼 있다.~~ `FRONTEND-008`에서 해결.

- `BACKEND-002-V`: 검증자 20세대가 `GET /api/health` 단독 구현을 `통과` 판정했다. 백엔드 테스트 2개 통과, HTTP 200 JSON 응답, 필수 안전값, `/api/dashboard` 404 기대 상태가 확인됐다.
- 위 `allow_headers` 후속 후보는 `BACKEND-003`에서 처리됐다. 현재 `allow_headers`는 `Accept`, `Accept-Language`, `Content-Type` 명시 목록이고 `allow_methods`는 `GET`이다.
- `FRONTEND-FINAL-AUDIT-R1-V`: 검증자 19세대가 React/Vite 19개 화면 최종 회귀를 `통과` 판정했다. `npm run typecheck`, `npm run build`, 19개 화면 1440×900 하단 잘림 해소, 사이드바 하단 안전 고지, 새 중대/높음 회귀 없음이 확인됐다.
- ~~남은 낮음 이슈: 기업 상세 숨김 보조 텍스트 `.chart-alt`, 세금·수수료/결정 회고/역할 상태의 테스트 훅 마커 내부 가로 overflow.~~ 재확인 결과 둘 다 버그가 아니다. `.chart-alt`는 의도된 스크린리더 전용(`position:absolute; 1px×1px; clip`) 패턴이다. 테스트 훅 마커는 `16×16px`·`overflow:hidden` 고정 박스라 안의 긴 텍스트가 흘러넘쳐도 박스 크기·문서 레이아웃에 영향이 없다 — 실제 1440×900 타깃 해상도에서 `document.documentElement.scrollWidth - clientWidth`가 `0`인 것을 확인했다(더 좁은 뷰포트에서 재 것처럼 보인 127px 오버플로는 뷰포트가 이 앱의 고정 1440×900 설계보다 좁아서 생긴 착시였다).
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
