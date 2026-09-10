import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, api } from "../lib/api";
import { CategoryBadge, RiskBadge, SeverityBadge, StageBadge } from "../components/Badges";
import type { InvestigationState } from "../types/nexora";

const AGENT_LABELS: Record<string, string> = {
  incident_classifier: "Incident Classifier",
  planner: "Planner",
  network_agent: "Network Agent",
  systems_agent: "Systems Agent",
  application_agent: "Application Agent",
  database_agent: "Database Agent",
  security_agent: "Security Agent",
  evidence_reviewer: "Evidence Reviewer",
  root_cause_analyzer: "Root Cause Analyzer",
  remediation_advisor: "Remediation Advisor",
  report_generator: "Report Generator",
  gemini_reasoning: "Gemini Reasoning",
};

export function InvestigationView() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const [state, setState] = useState<InvestigationState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState<number | null>(null);
  const [authError, setAuthError] = useState<"unauthorized" | "forbidden" | null>(null);

  function load() {
    if (!incidentId) return;
    api
      .getStatus(incidentId)
      .then(setState)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [incidentId]);

  async function handleApprove(index: number, approved: boolean) {
    if (!incidentId) return;
    setApproving(index);
    try {
      const updated = await api.approve(incidentId, index, approved);
      setState(updated);
    } catch (err) {
      if (err instanceof ApiError && (err.code === "unauthorized" || err.code === "forbidden")) {
        setAuthError(err.code);
      }
      setError(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setApproving(null);
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-8 py-8">
        <div className="rounded-md border border-orange/30 bg-orange/10 px-4 py-3 text-sm text-orange">
          {error}
        </div>
      </div>
    );
  }

  if (!state) {
    return <div className="px-8 py-8 text-silver/40">Loading investigation...</div>;
  }

  const { incident, agent_findings, evidence, root_cause, recommendations, final_report, activity_log } =
    state;

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      {authError && (
        <div className="mb-6 rounded-md border border-orange/30 bg-orange/10 px-4 py-3 text-sm text-orange">
          {authError === "unauthorized"
            ? "Authentication is required for this action. Enter a session API key in the sidebar."
            : "This API key is not allowed to approve recommendations."}
        </div>
      )}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-silver/40">
          <span>{incident.incident_id}</span>
          {incident.use_demo_data && (
            <span className="rounded-full bg-cyan/10 px-2 py-0.5 text-cyan">Demo data</span>
          )}
        </div>
        <h1 className="mt-1 font-heading text-2xl font-semibold text-white">{incident.title}</h1>
        <p className="mt-2 max-w-3xl text-sm text-silver/60">{incident.description}</p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <StageBadge stage={incident.stage} />
          <CategoryBadge category={incident.category} />
          <SeverityBadge severity={incident.severity} />
          {incident.affected_service && (
            <span className="badge border border-border bg-graphite-3 text-silver">
              {incident.affected_service}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          {state.reasoning_status !== "not_used" && (
            <div className="rounded-md border border-cyan/20 bg-cyan/5 px-4 py-3 text-xs text-silver/70">
              <span className="font-medium text-cyan">Reasoning:</span>{" "}
              {state.reasoning_status === "fallback_deterministic"
                ? "Gemini unavailable; deterministic fallback active."
                : state.reasoning_status === "completed"
                  ? "Gemini reasoning completed and was reviewed."
                  : "Gemini reasoning is not available for this investigation."}
            </div>
          )}
          <Section title="Agent Activity">
            <div className="flex flex-col gap-2">
              {agent_findings.length === 0 && (
                <p className="text-sm text-silver/40">No agents have run yet.</p>
              )}
              {agent_findings.map((finding, idx) => (
                <div
                  key={`${finding.agent}-${idx}`}
                  className="flex items-start justify-between gap-4 rounded-md border border-border bg-graphite-3 px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-white">
                      {AGENT_LABELS[finding.agent] ?? finding.agent}
                    </p>
                    <p className="mt-1 text-xs text-silver/60">{finding.summary}</p>
                  </div>
                  <span className="shrink-0 text-xs text-silver/40">
                    {finding.confidence_level} confidence
                  </span>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Root Cause">
            {root_cause ? (
              <div>
                <div className="flex items-start justify-between gap-4">
                  <p className="text-sm text-white">{root_cause.root_cause}</p>
                  <span className="shrink-0 text-xs text-silver/40">
                    {root_cause.confidence_level} confidence
                  </span>
                </div>
                {root_cause.alternative_causes.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-silver/50">Alternative causes</p>
                    <ul className="mt-1 list-inside list-disc text-xs text-silver/60">
                      {root_cause.alternative_causes.map((cause) => (
                        <li key={cause}>{cause}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {root_cause.uncertainties.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-silver/50">Remaining uncertainty</p>
                    <ul className="mt-1 list-inside list-disc text-xs text-silver/60">
                      {root_cause.uncertainties.map((u) => (
                        <li key={u}>{u}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-silver/40">Root cause analysis has not run yet.</p>
            )}
          </Section>

          <Section title="Recommendations">
            <div className="flex flex-col gap-3">
              {recommendations.length === 0 && (
                <p className="text-sm text-silver/40">No recommendations yet.</p>
              )}
              {recommendations.map((rec, idx) => (
                <div key={idx} className="rounded-md border border-border bg-graphite-3 px-4 py-3">
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-sm text-white">{rec.action}</p>
                    <RiskBadge risk={rec.risk} />
                  </div>
                  <p className="mt-1 text-xs text-silver/50">{rec.rationale}</p>
                  {rec.requires_approval && (
                    <div className="mt-3 flex items-center gap-2">
                      {rec.approved === null || rec.approved === undefined ? (
                        <>
                          <span className="text-xs text-orange">Human approval required</span>
                          <button
                            onClick={() => handleApprove(idx, true)}
                            disabled={approving === idx}
                            className="rounded-md bg-cyan/10 px-3 py-1 text-xs font-medium text-cyan hover:bg-cyan/15 disabled:opacity-50"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleApprove(idx, false)}
                            disabled={approving === idx}
                            className="rounded-md border border-border px-3 py-1 text-xs font-medium text-silver/60 hover:text-silver disabled:opacity-50"
                          >
                            Decline
                          </button>
                        </>
                      ) : (
                        <span
                          className={`text-xs ${rec.approved ? "text-emerald-400" : "text-silver/40"}`}
                        >
                          {rec.approved ? "Approved" : "Declined"}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>

          {final_report && (
            <Section title="Incident Report">
              <div className="flex flex-col gap-4 text-sm">
                <ReportField label="Verification steps" items={final_report.verification_steps} />
                <ReportField
                  label="Security considerations"
                  items={final_report.security_considerations}
                />
                {final_report.remaining_uncertainty.length > 0 && (
                  <ReportField
                    label="Remaining uncertainty"
                    items={final_report.remaining_uncertainty}
                  />
                )}
              </div>
            </Section>
          )}
        </div>

        <div className="flex flex-col gap-6">
          <Section title="Evidence">
            <div className="flex flex-col gap-3">
              {evidence.length === 0 && <p className="text-sm text-silver/40">No evidence yet.</p>}
              {evidence.map((e) => (
                <div key={e.evidence_id} className="rounded-md border border-border bg-graphite-3 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-silver/40">
                      {e.agent.replace("_agent", "")}
                    </span>
                    <span
                      className={`text-[10px] ${
                        e.reliability === "unavailable" ? "text-silver/30" : "text-cyan"
                      }`}
                    >
                      {e.reliability}
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs text-silver/70">{e.summary}</p>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Activity Log">
            <div className="flex flex-col gap-2 text-xs text-silver/50">
              {activity_log.map((line, idx) => (
                <p key={idx} className="border-l-2 border-border pl-2.5">
                  {line}
                </p>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-silver/40">{title}</h2>
      {children}
    </div>
  );
}

function ReportField({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-medium text-silver/50">{label}</p>
      <ul className="mt-1 list-inside list-disc text-xs text-silver/70">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
