import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { CategoryBadge, SeverityBadge, StageBadge } from "../components/Badges";
import type { IncidentSummary } from "../types/nexora";

export function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listIncidents()
      .then(setIncidents)
      .catch((err) => setError(err.message));
  }, []);

  const active = incidents?.filter((i) => i.stage !== "report_ready") ?? [];
  const recent = incidents ?? [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-heading text-2xl font-semibold text-white">Incidents</h1>
          <p className="mt-1 text-sm text-silver/60">
            Investigations run by Nexora's multi-agent diagnostic system.
          </p>
        </div>
        <Link
          to="/new"
          className="rounded-md bg-cyan px-4 py-2 text-sm font-semibold text-graphite transition-opacity hover:opacity-90"
        >
          New Incident
        </Link>
      </div>

      {error && (
        <div className="mb-6 rounded-md border border-orange/30 bg-orange/10 px-4 py-3 text-sm text-orange">
          Could not load incidents: {error}. Confirm the API is running at /api.
        </div>
      )}

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total incidents" value={recent.length} />
        <StatCard label="Active investigations" value={active.length} />
        <StatCard
          label="Awaiting approval"
          value={recent.filter((i) => i.stage === "awaiting_approval").length}
        />
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-silver/40">
              <th className="px-5 py-3 font-medium">Incident</th>
              <th className="px-5 py-3 font-medium">Category</th>
              <th className="px-5 py-3 font-medium">Severity</th>
              <th className="px-5 py-3 font-medium">Stage</th>
              <th className="px-5 py-3 font-medium">Updated</th>
            </tr>
          </thead>
          <tbody>
            {incidents === null && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-silver/40">
                  Loading incidents...
                </td>
              </tr>
            )}
            {incidents?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-silver/40">
                  No incidents yet. Start one from the demo fixture or submit your own.
                </td>
              </tr>
            )}
            {incidents?.map((incident) => (
              <tr
                key={incident.incident_id}
                className="border-b border-border last:border-0 hover:bg-graphite-3"
              >
                <td className="px-5 py-3.5">
                  <Link
                    to={`/incidents/${incident.incident_id}`}
                    className="font-medium text-white hover:text-cyan"
                  >
                    {incident.title}
                  </Link>
                  <p className="mt-0.5 text-xs text-silver/40">{incident.incident_id}</p>
                </td>
                <td className="px-5 py-3.5">
                  <CategoryBadge category={incident.category} />
                </td>
                <td className="px-5 py-3.5">
                  <SeverityBadge severity={incident.severity as import("../types/nexora").Severity} />
                </td>
                <td className="px-5 py-3.5">
                  <StageBadge stage={incident.stage as import("../types/nexora").InvestigationStage} />
                </td>
                <td className="px-5 py-3.5 text-silver/50">
                  {new Date(incident.updated_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card px-5 py-4">
      <p className="text-xs uppercase tracking-wide text-silver/40">{label}</p>
      <p className="mt-1 font-heading text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}
