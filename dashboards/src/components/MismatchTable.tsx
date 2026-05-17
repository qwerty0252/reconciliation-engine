interface Mismatch {
  id: string;
  mismatch_type: string;
  status: string;
  reference: string;
  source_system_a: string;
  source_system_b: string | null;
  description: string;
  created_at: string;
}

const severityBadge: Record<string, string> = {
  open: "bg-red-500/20 text-red-300",
  acknowledged: "bg-yellow-500/20 text-yellow-300",
  resolved: "bg-green-500/20 text-green-300",
};

export default function MismatchTable({
  mismatches,
}: {
  mismatches: Mismatch[];
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
        Open Mismatches
      </h2>
      {mismatches.length === 0 ? (
        <p className="text-gray-500 text-sm py-4 text-center">
          No open mismatches. All clear.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Reference</th>
                <th className="pb-2 pr-4">Systems</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2">Detected</th>
              </tr>
            </thead>
            <tbody>
              {mismatches.map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition"
                >
                  <td className="py-2 pr-4 font-mono text-xs text-blue-300">
                    {m.mismatch_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-2 pr-4 font-mono text-gray-300">
                    {m.reference}
                  </td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">
                    {m.source_system_a}
                    {m.source_system_b ? ` → ${m.source_system_b}` : ""}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        severityBadge[m.status] ?? "bg-gray-700 text-gray-300"
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="py-2 text-gray-500 text-xs">
                    {new Date(m.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
