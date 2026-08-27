import { useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { ApprovalQueuePage } from "./pages/ApprovalQueuePage";
import { EvidencePacketPage } from "./pages/EvidencePacketPage";
import type { PageKey } from "./types/dashboard";

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");

  if (page === "approvals") {
    return <ApprovalQueuePage activePage={page} onNavigate={setPage} />;
  }

  if (page === "evidence") {
    return <EvidencePacketPage activePage={page} onNavigate={setPage} />;
  }

  return <DashboardPage activePage={page} onNavigate={setPage} />;
}
