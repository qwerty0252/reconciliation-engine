interface MetricCardProps {
  title: string;
  value: string | number;
  loading?: boolean;
  color?: "blue" | "green" | "red" | "purple" | "yellow";
}

const colorMap = {
  blue: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  green: "text-green-400 bg-green-400/10 border-green-400/20",
  red: "text-red-400 bg-red-400/10 border-red-400/20",
  purple: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  yellow: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
};

export default function MetricCard({
  title,
  value,
  loading = false,
  color = "blue",
}: MetricCardProps) {
  return (
    <div
      className={`rounded-xl border p-4 ${colorMap[color]} backdrop-blur-sm`}
    >
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
        {title}
      </p>
      {loading ? (
        <div className="mt-2 h-7 w-24 bg-gray-700 animate-pulse rounded" />
      ) : (
        <p className="mt-2 text-3xl font-bold">{value}</p>
      )}
    </div>
  );
}
