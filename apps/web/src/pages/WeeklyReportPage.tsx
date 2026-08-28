import { useState } from "react";
import { AppShell } from "../components/AppShell";
import {
  reportDetails,
  reportRanges,
  reportRisks,
  reportRows,
  weeklyReportSafetyCopy,
  type ReportRangeKey,
  type ReportTopicKey
} from "../fixtures/weeklyReport";
import type { PageKey } from "../types/dashboard";
import "./WeeklyReportPage.css";

interface WeeklyReportPageProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function WeeklyReportPage({ activePage, onNavigate }: WeeklyReportPageProps) {
  const [rangeKey, setRangeKey] = useState<ReportRangeKey>("week");
  const [topicKey, setTopicKey] = useState<ReportTopicKey>("samsung");
  const range = reportRanges[rangeKey];
  const detail = reportDetails[topicKey];
  const facts = typeof detail.facts === "function" ? detail.facts(range) : detail.facts;
  const summary = typeof detail.summary === "function" ? detail.summary(range) : detail.summary;

  function selectRange(nextRange: ReportRangeKey) {
    setRangeKey(nextRange);
    setTopicKey((current) => current);
  }

  const main = (
    <section className="weekly-main" aria-labelledby="weekly-title">
      <header className="weekly-summary">
        <div>
          <span className="eyebrow">주간 요약</span>
          <h1 id="weekly-title">{range.profit}</h1>
          <p>총자산 {range.start}에서 {range.end}으로 증가했습니다.</p>
        </div>
        <div className="weekly-cards" aria-label="기간 핵심 지표">
          <MetricCard label="수익률" value={range.portfolio} meta={`KOSPI ${range.benchmark}`} topic="return" selected={topicKey === "return"} onSelect={setTopicKey} />
          <MetricCard label="최대 낙폭" value={range.drawdown} meta={range.drawdownLabel} topic="risk" selected={topicKey === "risk"} onSelect={setTopicKey} />
          <MetricCard label="현금 비중" value="18.4%" meta="정책 하한 15.0%" topic="cash" selected={topicKey === "cash"} onSelect={setTopicKey} />
        </div>
      </header>

      <section className="weekly-chart" aria-labelledby="weekly-chart-title">
        <div className="weekly-toolbar">
          <div className="segments" role="group" aria-label="리포트 기간">
            {(["week", "month", "quarter"] as ReportRangeKey[]).map((key) => (
              <button className={rangeKey === key ? "selected" : ""} key={key} type="button" aria-pressed={rangeKey === key} onClick={() => selectRange(key)}>
                {reportRanges[key].shortLabel}
              </button>
            ))}
          </div>
          <span>{range.formula}</span>
        </div>
        <div className="weekly-chart-head">
          <h2 id="weekly-chart-title">자산·벤치마크 비교</h2>
          <div className="weekly-legend"><span><i className="blue" />포트폴리오</span><span><i />KOSPI</span></div>
        </div>
        <div className="weekly-bars" aria-label="기간 수익률 막대">
          <ReturnBar label="내 포트폴리오" value={range.portfolio} bar={range.portfolioBar} topic="return" selected={topicKey === "return"} onSelect={setTopicKey} />
          <ReturnBar label="KOSPI" value={range.benchmark} bar={range.benchmarkBar} topic="benchmark" selected={topicKey === "benchmark"} onSelect={setTopicKey} />
          <ReturnBar label="초과수익" value={range.alpha} bar={range.alphaBar} topic="alpha" selected={topicKey === "alpha"} onSelect={setTopicKey} />
        </div>
      </section>

      <section className="weekly-grid">
        {["기여·부담 종목", "에이전트 처리 기록"].map((group) => (
          <article key={group}>
            <h2>{group}</h2>
            {reportRows.filter((row) => row.group === group).map((row) => (
              <button className={topicKey === row.key ? "weekly-row selected" : `weekly-row ${row.tone}`} key={row.key} type="button" aria-pressed={topicKey === row.key} onClick={() => setTopicKey(row.key)}>
                <span>{row.label}</span><b>{row.value}</b><small>{row.meta}</small>
              </button>
            ))}
          </article>
        ))}
      </section>

      <section className="weekly-risk-strip" aria-labelledby="weekly-risk-title">
        <h2 id="weekly-risk-title">주요 위험과 데이터 한계</h2>
        {reportRisks.map((risk) => (
          <button className={topicKey === risk.key ? "weekly-risk-chip selected" : "weekly-risk-chip"} key={risk.key} type="button" aria-pressed={topicKey === risk.key} onClick={() => setTopicKey(risk.key)}>
            {risk.label}
          </button>
        ))}
      </section>
      <footer className="weekly-disclaimer">{weeklyReportSafetyCopy}</footer>
    </section>
  );

  const inspector = (
    <aside className="weekly-inspector" aria-live="polite" aria-atomic="false">
      <div className="weekly-inspector-scroll">
        <header>
          <span className="eyebrow">선택 항목</span>
          <h2>{detail.title}</h2>
          <p>{summary}</p>
        </header>
        <section>
          <h3>계산 근거</h3>
          <dl>{facts.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>
        </section>
        <section>
          <h3>연결 화면</h3>
          <div className="weekly-links">
            <button type="button" onClick={() => onNavigate("company")}>기업 상세 보기</button>
            <button type="button" onClick={() => onNavigate("approvals")}>승인 대기 보기</button>
            <button type="button" onClick={() => onNavigate("audit")}>감사 로그 보기</button>
          </div>
        </section>
        <section className="weekly-limit-note">
          <h3>데이터 한계</h3>
          <p>모든 수치와 기록은 화면용 고정 예시입니다. 실제 금융 데이터, 주문, 계좌, API, DB와 연결되지 않습니다.</p>
        </section>
      </div>
      <footer>{weeklyReportSafetyCopy}</footer>
    </aside>
  );

  return <AppShell title="주간 투자 리포트" accountLabel="시뮬레이션 계좌" lastSync={range.label} activePage={activePage} onNavigate={onNavigate} main={main} inspector={inspector} />;
}

function MetricCard({ label, value, meta, topic, selected, onSelect }: { label: string; value: string; meta: string; topic: ReportTopicKey; selected: boolean; onSelect: (topic: ReportTopicKey) => void }) {
  return (
    <button className={selected ? "weekly-metric selected" : "weekly-metric"} type="button" aria-pressed={selected} onClick={() => onSelect(topic)}>
      <span>{label}</span><strong>{value}</strong><small>{meta}</small>
    </button>
  );
}

function ReturnBar({ label, value, bar, topic, selected, onSelect }: { label: string; value: string; bar: number; topic: ReportTopicKey; selected: boolean; onSelect: (topic: ReportTopicKey) => void }) {
  return (
    <button className={selected ? "weekly-bar selected" : "weekly-bar"} type="button" aria-pressed={selected} onClick={() => onSelect(topic)}>
      <span>{label}</span><i style={{ width: `${bar}%` }} /><b>{value}</b>
    </button>
  );
}
