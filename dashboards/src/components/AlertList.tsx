interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  created_at: string;
}

const severityStyle: Record<string, string> = {
  critical: "border-l-red-500 bg-red-500/5",
  warning: "border-l-yellow-500 bg-yellow-500/5",
  info: "border-l-blue-500 bg-blue-500/5",
};

const badgeStyle: Record<string, string> = {
  critical: "bg-red-500/20 text-red-300",
  warning: "bg-yellow-500/20 text-yellow-300",
  info: "bg-blue-500/20 text-blue-300",
};

export default function AlertList({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4 h-full">
      <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
        Active Alerts
      </h2>
      {alerts.length === 0 ? (
        <p className="text-gray-500 text-sm py-4 text-center">No active alerts.</p>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-72">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-l-2 rounded-r-lg p-3 ${
                severityStyle[alert.severity] ?? "border-l-gray-500 bg-gray-800"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-200 truncate">
                  {alert.title}
                </span>
                <span
                  className={`ml-2 shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
                    badgeStyle[alert.severity] ?? "bg-gray-700 text-gray-300"
                  }`}
                >
                  {alert.severity}
                </span>
              </div>
              <p className="text-xs text-gray-400 line-clamp-2">{alert.message}</p>
              <p className="text-xs text-gray-600 mt-1">
                {new Date(alert.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
