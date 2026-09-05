import type { ReactNode } from "react";
import clsx from "clsx";

export default function StatCard({
  label,
  value,
  icon,
  trend,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  trend?: { value: string; positive: boolean };
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-ink-muted">{label}</div>
          <div className="text-2xl font-semibold text-ink mt-1">{value}</div>
        </div>
        {icon && <div className="text-primary-900 opacity-80">{icon}</div>}
      </div>
      {trend && (
        <div className={clsx("text-xs mt-2 font-medium", trend.positive ? "text-success" : "text-danger")}>
          {trend.value}
        </div>
      )}
    </div>
  );
}
