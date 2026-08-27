import { useMemo, useState } from "react";
import { CheckCircle2, FileText } from "lucide-react";
import { AppShell } from "../components/AppShell";
import { DataBoundaryNotice } from "../components/DataBoundaryNotice";
import { StatusPill } from "../components/StatusPill";
import { approvalOrders, type ApprovalOrder } from "../fixtures/approvals";
import type { PageKey } from "../types/dashboard";
import "./ApprovalQueuePage.css";

const won = (value: number) => `${value.toLocaleString("ko-KR")}원`;
type FilterKey = "all" | ApprovalOrder["filter"];
type LocalState = "pending" | "approved" | "rejected";

interface ApprovalQueuePageProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function ApprovalQueuePage({ activePage, onNavigate }: ApprovalQueuePageProps) {
  const [filter, setFilter] = useState<FilterKey>("all");
  const [selectedId, setSelectedId] = useState(approvalOrders[0].id);
  const [states, setStates] = useState<Record<string, LocalState>>(() =>
    Object.fromEntries(approvalOrders.map((order) => [order.id, "pending"]))
  );

  const visibleOrders = useMemo(
    () => approvalOrders.filter((order) => filter === "all" || order.filter === filter),
    [filter]
  );
  const selected = approvalOrders.find((order) => order.id === selectedId) ?? visibleOrders[0] ?? approvalOrders[0];
  const selectedState = states[selected.id];

  function updateFilter(nextFilter: FilterKey) {
    const nextVisible = approvalOrders.filter((order) => nextFilter === "all" || order.filter === nextFilter);
    setFilter(nextFilter);
    if (nextVisible.length > 0 && !nextVisible.some((order) => order.id === selectedId)) {
      setSelectedId(nextVisible[0].id);
    }
  }

  function stateLabel(order: ApprovalOrder) {
    const state = states[order.id];
    if (state === "approved") return "모의승인됨";
    if (state === "rejected") return "반려됨";
    return order.status;
  }

  function decide(state: LocalState) {
    setStates((current) => ({ ...current, [selected.id]: state }));
  }

  const main = (
    <section className="approval-main" aria-labelledby="approval-title">
      <header className="approval-header">
        <div>
          <span className="eyebrow">투자 운영</span>
          <h1 id="approval-title">승인 대기</h1>
          <p>검증 결과와 주문 한도를 비교한 뒤 로컬 모의 상태만 변경합니다.</p>
        </div>
        <DataBoundaryNotice />
      </header>

      <div className="approval-toolbar">
        <div className="approval-summary">
          <strong>{visibleOrders.length}건</strong>
          <span>처리할 가상 요청</span>
        </div>
        <div className="segments approval-filters" role="group" aria-label="승인 상태 필터">
          {[
            ["all", "전체"],
            ["conditional", "조건부"],
            ["verified", "확인됨"],
            ["attention", "확인필요"]
          ].map(([key, label]) => (
            <button
              className={filter === key ? "selected" : ""}
              key={key}
              type="button"
              aria-pressed={filter === key}
              onClick={() => updateFilter(key as FilterKey)}
            >
              {label}
            </button>
          ))}
        </div>
        <span className="sync">마지막 검증 14:31</span>
      </div>

      <div className="orders-table" role="grid" aria-label="화면용 가상 승인 대기 주문">
        <div className="order-head" role="row">
          <span role="columnheader">상태</span>
          <span role="columnheader">종목 / 코드</span>
          <span role="columnheader">구분</span>
          <span role="columnheader">수량</span>
          <span role="columnheader">가격</span>
          <span role="columnheader">최대금액</span>
          <span role="columnheader">검증</span>
          <span role="columnheader">만료</span>
        </div>
        {visibleOrders.length ? (
          visibleOrders.map((order) => (
            <button
              className={order.id === selected.id ? "order-row selected" : "order-row"}
              key={order.id}
              type="button"
              role="row"
              aria-selected={order.id === selected.id}
              onClick={() => setSelectedId(order.id)}
            >
              <span role="gridcell"><StatusPill tone={states[order.id] === "pending" ? order.tone : "info"}>{stateLabel(order)}</StatusPill></span>
              <span role="gridcell"><strong>{order.company}</strong><small>{order.code}</small></span>
              <span className={order.side === "매수" ? "buy" : "sell"} role="gridcell">{order.side}</span>
              <span role="gridcell">{order.quantity}주</span>
              <span role="gridcell">{won(order.price)}</span>
              <span role="gridcell">{won(order.amount)}</span>
              <span role="gridcell">{order.verification}</span>
              <span role="gridcell">{order.expiry}</span>
            </button>
          ))
        ) : (
          <div className="empty-state">선택한 상태의 요청이 없습니다.</div>
        )}
      </div>
    </section>
  );

  const inspector = (
    <aside className="approval-inspector" aria-live="polite" aria-atomic="false">
      <div className="inspector-scroll">
        <header className="order-detail-header">
          <span className="eyebrow">선택 주문</span>
          <div className="decision-title">
            <div>
              <h2>{selected.company}</h2>
              <span>{selected.id} · {selected.code}</span>
            </div>
            <StatusPill tone={selectedState === "pending" ? selected.tone : "info"}>{stateLabel(selected)}</StatusPill>
          </div>
        </header>

        <div className="workflow" aria-label="처리 단계">
          {["분석", "검증", "승인 대기"].map((step, index) => (
            <div className="workflow-item" key={step}>
              <div className={index < 2 ? "step done" : "step current"}>
                <i>{index < 2 ? <CheckCircle2 size={11} /> : null}</i>
                <b>{step}</b>
                <span>{index < 2 ? "완료" : selected.expiry}</span>
              </div>
              {index < 2 ? <div className={index === 0 ? "line done" : "line"} /> : null}
            </div>
          ))}
        </div>

        <section className="inspector-section proposal">
          <h3>주문 조건</h3>
          <strong>{selected.company} {selected.quantity}주 지정가 {selected.side}</strong>
          <dl>
            <div><dt>지정가</dt><dd>{won(selected.price)}</dd></div>
            <div><dt>최대 금액</dt><dd>{won(selected.amount)}</dd></div>
            <div><dt>계산식</dt><dd>{selected.quantity} × {selected.price.toLocaleString("ko-KR")} = {won(selected.amount)}</dd></div>
          </dl>
        </section>

        <section className="inspector-section verification">
          <h3>시뮬레이션 검증 결과</h3>
          <dl>
            <div><dt>정책 한도</dt><dd className={selected.policy.includes("통과") ? "success" : "warning"}>{selected.policy}</dd></div>
            <div><dt>근거 출처</dt><dd className="warning">{selected.source}</dd></div>
            <div><dt>실제 주문</dt><dd className="success">생성 안 됨</dd></div>
          </dl>
          <div className="warning">
            <b>{selected.warning}</b>
            <p>{selected.warningText}</p>
          </div>
        </section>
      </div>

      <div className="approval-panel">
        <div className="expiry">
          <span>이 모의승인은 <b>{selected.expiry}</b>에 만료됩니다.</span>
          <small>실제 주문·체결은 생성되지 않습니다.</small>
        </div>
        {selectedState !== "pending" ? (
          <div className="decision-message" aria-live="polite">
            {selectedState === "approved" ? "모의승인됨 · 실제 주문은 생성되지 않았습니다." : "반려됨 · 가상 요청이 종료되었습니다."}
          </div>
        ) : null}
        <div className="actions">
          <button type="button" disabled={selectedState !== "pending"} onClick={() => decide("rejected")}>반려</button>
          <button type="button" disabled={selectedState !== "pending"} onClick={() => decide("approved")}>
            {won(selected.amount)} 한도 내 모의승인
          </button>
        </div>
        <button className="evidence-link" type="button" onClick={() => onNavigate("evidence")}>
          <FileText size={13} aria-hidden="true" />
          근거 패킷 보기
        </button>
        <p>모의투자 · 화면 검토용 가상 예시</p>
      </div>
    </aside>
  );

  return (
    <AppShell
      title="승인 대기"
      accountLabel="시뮬레이션 계좌"
      lastSync="14:31"
      activePage={activePage}
      onNavigate={onNavigate}
      main={main}
      inspector={inspector}
    />
  );
}
