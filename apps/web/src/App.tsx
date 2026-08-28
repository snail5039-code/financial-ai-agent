import { useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { ApprovalQueuePage } from "./pages/ApprovalQueuePage";
import { AuditLogPage } from "./pages/AuditLogPage";
import { CompanyDetailPage } from "./pages/CompanyDetailPage";
import { DataConnectionsPage } from "./pages/DataConnectionsPage";
import { EvidencePacketPage } from "./pages/EvidencePacketPage";
import { PolicySettingsPage } from "./pages/PolicySettingsPage";
import { PortfolioChangeComparePage } from "./pages/PortfolioChangeComparePage";
import { RiskAlertsPage } from "./pages/RiskAlertsPage";
import { TradeHistoryPage } from "./pages/TradeHistoryPage";
import type { PageKey } from "./types/dashboard";

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");

  if (page === "approvals") {
    return <ApprovalQueuePage activePage={page} onNavigate={setPage} />;
  }

  if (page === "company") {
    return <CompanyDetailPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "evidence") {
    return <EvidencePacketPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "compare") {
    return <PortfolioChangeComparePage activePage={page} onNavigate={setPage} />;
  }

  if (page === "audit") {
    return <AuditLogPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "policy") {
    return <PolicySettingsPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "data") {
    return <DataConnectionsPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "trades") {
    return <TradeHistoryPage activePage={page} onNavigate={setPage} />;
  }

  if (page === "risks") {
    return <RiskAlertsPage activePage={page} onNavigate={setPage} />;
  }

  return <DashboardPage activePage={page} onNavigate={setPage} />;
}
