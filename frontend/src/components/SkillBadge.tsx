import { Check, AlertTriangle, X, HelpCircle } from "lucide-react";
import clsx from "clsx";

type Status = "MATCHED" | "PARTIAL" | "MISSING" | "VERIFIED" | "BASIC" | "REJECTED" | "EXTRACTED";

const CONFIG: Record<Status, { label: string; className: string; icon: any }> = {
  MATCHED: { label: "Matched", className: "badge-success", icon: Check },
  VERIFIED: { label: "Verified", className: "badge-success", icon: Check },
  PARTIAL: { label: "Partial", className: "badge-warning", icon: AlertTriangle },
  BASIC: { label: "Basic knowledge", className: "badge-warning", icon: AlertTriangle },
  MISSING: { label: "Missing", className: "badge-danger", icon: X },
  REJECTED: { label: "Not included", className: "badge-danger", icon: X },
  EXTRACTED: { label: "Unverified", className: "badge-neutral", icon: HelpCircle },
};

export default function SkillBadge({ label, status }: { label: string; status: Status }) {
  const cfg = CONFIG[status];
  const Icon = cfg.icon;
  return (
    <span className={clsx(cfg.className)}>
      <Icon className="w-3 h-3" />
      {label}
      <span className="opacity-60">· {cfg.label}</span>
    </span>
  );
}
