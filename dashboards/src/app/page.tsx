"use client";

import useSWR from "swr";
import MetricCard from "@/components/MetricCard";
import MismatchTable from "@/components/MismatchTable";
import AlertList from "@/components/AlertList";
import MismatchChart from "@/components/MismatchChart";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useSWR(
    "/api/dashboard/summary",
    fetcher,
    { refreshInterval: 15000 }
  );

  const { data: mismatches } = useSWR(
    "/api/mismatches?status=open&limit=20",
    fetcher,
    { refreshInterval: 15000 }
  );

  const { data: alerts } = useSWR(
    "/api/alerts?status=open&limit=10",
    fetcher,
    { refreshInterval: 15000 }
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">BankOps Reconciliation Engine</h1>
          <p className="text-gray-400 text-sm mt-1">
            Operational visibility · Auto-refreshes every 15s
          </p>
        </div>
        <span className="text-xs text-green-400 bg-green-400/10 px-3 py-1 rounded-full">
          Live
        </span>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Transactions"
          value={summary?.total_transactions ?? "—"}
          loading={summaryLoading}
          color="blue"
        />
        <MetricCard
          title="Reconciled"
          value={summary?.reconciled_transactions ?? "—"}
          loading={summaryLoading}
          color="green"
        />
        <MetricCard
          title="Open Mismatches"
          value={summary?.open_mismatches ?? "—"}
          loading={summaryLoading}
          color={summary?.open_mismatches > 0 ? "red" : "green"}
        />
        <MetricCard
          title="Recon Success Rate"
          value={
            summary?.reconciliation_success_rate_pct != null
              ? `${summary.reconciliation_success_rate_pct}%`
              : "—"
          }
          loading={summaryLoading}
          color="purple"
        />
      </div>

      {/* Mismatch Chart + Alert List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <MismatchChart data={summary?.mismatch_count_by_type ?? {}} />
        </div>
        <div>
          <AlertList alerts={alerts?.data ?? []} />
        </div>
      </div>

      {/* Mismatch Table */}
      <MismatchTable mismatches={mismatches?.data ?? []} />
    </div>
  );
}
