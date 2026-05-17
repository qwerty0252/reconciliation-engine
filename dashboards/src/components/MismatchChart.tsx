"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface MismatchChartProps {
  data: Record<string, number>;
}

export default function MismatchChart({ data }: MismatchChartProps) {
  const chartData = Object.entries(data).map(([type, count]) => ({
    name: type.replace(/_/g, " "),
    count,
  }));

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">
        Mismatch Distribution
      </h2>
      {chartData.length === 0 ? (
        <div className="h-40 flex items-center justify-center text-gray-500 text-sm">
          No mismatch data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#111827",
                border: "1px solid #374151",
                borderRadius: "8px",
                color: "#f9fafb",
                fontSize: "12px",
              }}
            />
            <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
