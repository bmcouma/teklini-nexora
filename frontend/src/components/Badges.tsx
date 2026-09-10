import type { InvestigationStage, RiskLevel, Severity } from "../types/nexora";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-orange/15 text-orange border border-orange/30",
  high: "bg-orange/10 text-orange/90 border border-orange/20",
  medium: "bg-cyan/10 text-cyan border border-cyan/20",
  low: "bg-silver/10 text-silver border border-silver/20",
  informational: "bg-silver/5 text-silver/70 border border-border",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`badge ${SEVERITY_STYLES[severity]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

const STAGE_LABELS: Record<InvestigationStage, string> = {
  submitted: "Submitted",
  classifying: "Classifying",
  planning: "Planning",
  investigating: "Investigating",
  reviewing: "Reviewing evidence",
  additional_investigation: "Additional investigation",
  root_cause_analysis: "Analyzing root cause",
  remediation: "Preparing remediation",
  awaiting_approval: "Awaiting approval",
  report_ready: "Report ready",
  failed: "Failed",
};

const STAGE_STYLES: Record<InvestigationStage, string> = {
  submitted: "bg-silver/10 text-silver border border-silver/20",
  classifying: "bg-cyan/10 text-cyan border border-cyan/20",
  planning: "bg-cyan/10 text-cyan border border-cyan/20",
  investigating: "bg-cyan/10 text-cyan border border-cyan/20",
  reviewing: "bg-cyan/10 text-cyan border border-cyan/20",
  additional_investigation: "bg-orange/10 text-orange border border-orange/20",
  root_cause_analysis: "bg-cyan/10 text-cyan border border-cyan/20",
  remediation: "bg-cyan/10 text-cyan border border-cyan/20",
  awaiting_approval: "bg-orange/15 text-orange border border-orange/30",
  report_ready: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  failed: "bg-red-500/10 text-red-400 border border-red-500/20",
};

export function StageBadge({ stage }: { stage: InvestigationStage }) {
  return <span className={`badge ${STAGE_STYLES[stage]}`}>{STAGE_LABELS[stage]}</span>;
}

export function CategoryBadge({ category }: { category: string }) {
  return (
    <span className="badge border border-border bg-graphite-3 text-silver">
      {category.replace("_", " ")}
    </span>
  );
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  medium: "bg-cyan/10 text-cyan border border-cyan/20",
  high: "bg-orange/15 text-orange border border-orange/30",
};

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return <span className={`badge ${RISK_STYLES[risk]}`}>{risk} risk</span>;
}
