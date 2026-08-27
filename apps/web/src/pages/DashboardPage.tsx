import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleDot, XCircle } from "lucide-react";
import { getDashboard } from "../api/dashboard";
import { AppShell } from "../components/AppShell";
import { DataBoundaryNotice } from "../components/DataBoundaryNotice";
import { MockChart } from "../components/MockChart";
import { StatusPill } from "../components/StatusPill";
import type { DashboardData, EvidenceItem, PageKey, Tone } from "../types/dashboard";
import "./DashboardPage.css";

function toneIcon(tone: Tone) {
  if (tone === "success") return <CheckCircle2 size={14} />;
  if (tone === "warning") return <AlertTriangle size={14} />;
  if (tone === "danger") return <XCircle size={14} />;
  return <CircleDot size={14} />;
}

function EvidenceRow({ item, open }: { item: EvidenceItem; open?: boolean }) {
  const [expanded, setExpanded] = useState(Boolean(open));

  return (
    <div className="evidence-block">
      <button
        className="evidence-row"
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        <span>{item.title}</span>
        {expanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
      </button>
      {expanded ? (
        <div className={`evidence-detail ${item.tone}`}>
          <p>{item.detail}</p>
          <small>{item.source}</small>
        </div>
      ) : null}
    </div>
  );
}

interface DashboardPageProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function DashboardPage({ activePage, onNavigate }: DashboardPageProps) {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [decisionMessage, setDecisionMessage] = useState("");

  useEffect(() => {
    void getDashboard().then(setDashboard);
  }, []);

  const lastSync = useMemo(() => {
    if (!dashboard) return "대기";
    return dashboard.dataAsOf.slice(11, 16);
  }, [dashboard]);

  if (!dashboard) {
    return <div className="loading-screen">로컬 fixture를 불러오는 중</div>;
  }

  const main = (
    <section className="dashboard" aria-labelledby="dashboard-title">
      <section className="summary">
        <div>
          <div className="eyebrow">총자산</div>
          <div className="balance-row">
            <h1 id="dashboard-title">{dashboard.summary.totalAsset}</h1>
            <span className="gain">
              {dashboard.summary.todayProfit} <b>({dashboard.summary.todayProfitRate})</b> 오늘
            </span>
          </div>
          <p className="metrics">
            <span>투자원금 <b>{dashboard.summary.principal}</b></span>
            <i />
            <span>누적손익 <b className="gain">{dashboard.summary.accumulatedProfit}</b></span>
            <i />
            <span>현금 <b>{dashboard.summary.cashWeight}</b></span>
          </p>
          <p className="timestamps">
            기준 시각 {dashboard.dataAsOf.replace("T", " ").slice(0, 16)} <span>·</span> 마지막 검증 {dashboard.summary.lastVerified}
          </p>
        </div>
        <DataBoundaryNotice />
      </section>

      <section className="chart-section" aria-labelledby="chart-title">
        <div className="section-toolbar">
          <div className="segments" aria-label="기간 선택">
            {["1일", "1주", "1개월", "3개월", "올해", "1년"].map((label) => (
              <button className={label === "3개월" ? "selected" : ""} key={label} type="button">
                {label}
              </button>
            ))}
          </div>
          <div className="segments" aria-label="차트 보기">
            {["자산", "벤치마크", "낙폭"].map((label) => (
              <button className={label === "자산" ? "selected" : ""} key={label} type="button">
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="chart-head">
          <h2 id="chart-title">자산 변화</h2>
          <div className="legend">
            <span><i className="blue" />내 포트폴리오</span>
            <span><i className="gray" />벤치마크</span>
            <span><i className="event" />검증 이벤트</span>
          </div>
        </div>
        <MockChart points={dashboard.chart} />
      </section>

      <section className="holdings" aria-labelledby="holdings-title">
        <div className="holdings-head">
          <h2 id="holdings-title">보유 종목 <span>{dashboard.holdings.length}</span></h2>
          <span>평가금액 합계 <b>{dashboard.summary.totalAsset}</b></span>
        </div>
        <table>
          <thead>
            <tr>
              <th>종목</th>
              <th>수량</th>
              <th>평균단가</th>
              <th>현재가</th>
              <th>평가금액</th>
              <th>손익</th>
              <th>비중</th>
              <th>AI 상태</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.holdings.map((holding) => (
              <tr className={holding.selected ? "selected-row" : ""} key={holding.code}>
                <td>
                  <strong>{holding.name}</strong>
                  <small>{holding.code}</small>
                </td>
                <td>{holding.quantity}</td>
                <td>{holding.averagePrice}</td>
                <td>{holding.currentPrice}</td>
                <td>{holding.value}</td>
                <td className={holding.profit.startsWith("-") ? "loss" : holding.profit === "-" ? "" : "gain"}>
                  {holding.profit}
                  {holding.profitRate ? <small>{holding.profitRate}</small> : null}
                </td>
                <td>{holding.weight}</td>
                <td><StatusPill tone={holding.tone}>{holding.status}</StatusPill></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  );

  const inspector = (
    <aside className="inspector" aria-label="선택 결정 상세">
      <div className="inspector-scroll">
        <div className="inspector-header">
          <span className="eyebrow">현재 판단</span>
          <div className="decision-title">
            <div>
              <h2>{dashboard.decision.company}</h2>
              <span>{dashboard.decision.decisionId}</span>
            </div>
            <StatusPill tone={dashboard.decision.statusTone}>{dashboard.decision.status}</StatusPill>
          </div>
        </div>

        <div className="workflow" aria-label="에이전트 처리 단계">
          {["분석", "검증", "승인 대기"].map((step, index) => (
            <div className="workflow-item" key={step}>
              <div className={index < 2 ? "step done" : "step current"}>
                <i>{index < 2 ? <CheckCircle2 size={11} /> : null}</i>
                <b>{step}</b>
                <span>{index === 0 ? "14:28" : index === 1 ? "14:31" : "대기"}</span>
              </div>
              {index < 2 ? <div className={index === 0 ? "line done" : "line"} /> : null}
            </div>
          ))}
        </div>

        <section className="inspector-section proposal">
          <h3>제안</h3>
          <strong>{dashboard.decision.proposal}</strong>
          <dl>
            <div><dt>지정가</dt><dd>71,200원</dd></div>
            <div><dt>목표 비중</dt><dd>{dashboard.decision.targetWeight}</dd></div>
            <div><dt>최대 주문금액</dt><dd>{dashboard.decision.limitAmount}</dd></div>
          </dl>
        </section>

        <section className="inspector-section evidence">
          <h3>핵심 근거</h3>
          {dashboard.decision.evidence.map((item, index) => (
            <EvidenceRow item={item} key={item.title} open={index === 0} />
          ))}
        </section>

        <section className="inspector-section verification">
          <h3>시뮬레이션 검증 결과</h3>
          <dl>
            {dashboard.decision.checks.map((check) => (
              <div key={check.label}>
                <dt>{check.label}</dt>
                <dd className={check.tone}>{toneIcon(check.tone)}{check.value}</dd>
              </div>
            ))}
          </dl>
          <div className="warning">
            <b>변동성 주의</b>
            <p>최근 20일 변동성이 사용자 기준에 근접했습니다. 이 내용은 fixture 기반 예시입니다.</p>
          </div>
        </section>

        <details className="invalid-conditions">
          <summary>판단 무효 조건 <span>{dashboard.decision.invalidConditions.length}개</span></summary>
          <ul>
            {dashboard.decision.invalidConditions.map((condition) => (
              <li key={condition}>{condition}</li>
            ))}
          </ul>
        </details>
      </div>

      <div className="approval-panel">
        <div className="expiry">
          <span>이 모의승인은 <b>{dashboard.decision.expiresAt}</b>에 만료됩니다.</span>
          <small>승인해도 실제 주문은 생성되지 않습니다.</small>
        </div>
        {decisionMessage ? <div className="decision-message" aria-live="polite">{decisionMessage}</div> : null}
        <div className="actions">
          <button type="button" onClick={() => setDecisionMessage("반려 처리됨 · 로컬 화면 상태만 변경되었습니다.")}>반려</button>
          <button type="button" onClick={() => setDecisionMessage("모의승인됨 · 실제 주문은 생성되지 않았습니다.")}>
            {dashboard.decision.limitAmount} 한도 내 모의승인
          </button>
        </div>
        <p>모의투자 · 화면 검토용 예시 데이터</p>
      </div>
    </aside>
  );

  return (
    <AppShell
      title={dashboard.title}
      accountLabel={dashboard.accountLabel}
      lastSync={lastSync}
      activePage={activePage}
      onNavigate={onNavigate}
      main={main}
      inspector={inspector}
    />
  );
}
