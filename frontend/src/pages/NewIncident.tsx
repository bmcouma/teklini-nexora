import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../lib/api";
import type { Severity } from "../types/nexora";

const SEVERITY_OPTIONS: Severity[] = ["informational", "low", "medium", "high", "critical"];

export function NewIncident() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [affectedService, setAffectedService] = useState("");
  const [environment, setEnvironment] = useState("production");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [logs, setLogs] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<"unauthorized" | "forbidden" | null>(null);

  async function submit(useDemoData: boolean) {
    setSubmitting(true);
    setError(null);
    setAuthError(null);
    try {
      const state = await api.createIncident({
        title: useDemoData ? undefined : title,
        description: useDemoData ? undefined : description,
        affected_service: affectedService || undefined,
        environment: environment || undefined,
        reported_severity: severity || undefined,
        logs: logs || undefined,
        use_demo_data: useDemoData,
      });
      navigate(`/incidents/${state.incident.incident_id}`);
    } catch (err) {
      if (err instanceof ApiError && (err.code === "unauthorized" || err.code === "forbidden")) {
        setAuthError(err.code);
      }
      setError(err instanceof Error ? err.message : "Failed to create incident.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8 sm:py-8">
      <h1 className="font-heading text-2xl font-semibold text-white">New Incident</h1>
      <p className="mt-1 text-sm text-silver/60">
        Describe the problem and paste any relevant logs. Nexora treats logs as untrusted data and
        redacts common credential patterns before analysis.
      </p>

      {authError && (
        <div className="mt-4 rounded-md border border-orange/30 bg-orange/10 px-4 py-3 text-sm text-orange">
          {authError === "unauthorized"
            ? "This API requires authentication. Enter a session API key in the sidebar, then retry."
            : "This API key is not allowed to create incidents."}
        </div>
      )}

      <div className="mt-6 card p-6">
        <button
          type="button"
          onClick={() => submit(true)}
          disabled={submitting}
          className="mb-6 w-full rounded-md border border-cyan/30 bg-cyan/10 px-4 py-3 text-sm font-medium text-cyan transition-colors hover:bg-cyan/15 disabled:opacity-50"
        >
          Run demo investigation (Django 502 Bad Gateway)
        </button>

        <div className="mb-6 flex items-center gap-3 text-xs text-silver/40">
          <div className="h-px flex-1 bg-border" />
          or submit your own incident
          <div className="h-px flex-1 bg-border" />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(false);
          }}
          className="flex flex-col gap-4"
        >
          <Field label="Incident title">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. API returning 500 errors for authenticated users"
              className="input"
            />
          </Field>

          <Field label="Description">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
              placeholder="What is happening, since when, and who is affected?"
              className="input resize-none"
            />
          </Field>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Affected service">
              <input
                value={affectedService}
                onChange={(e) => setAffectedService(e.target.value)}
                placeholder="e.g. checkout-api"
                className="input"
              />
            </Field>
            <Field label="Environment">
              <input
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                placeholder="production, staging..."
                className="input"
              />
            </Field>
          </div>

          <Field label="Severity, if known">
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity)}
              className="input"
            >
              <option value="">Let Nexora classify severity</option>
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Logs">
            <textarea
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              rows={8}
              placeholder="Paste relevant log output. Do not include secrets; Nexora redacts common patterns automatically, but it is not a substitute for removing them yourself."
              className="input resize-none font-mono text-xs"
            />
          </Field>

          {error && (
            <div className="rounded-md border border-orange/30 bg-orange/10 px-4 py-3 text-sm text-orange">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 rounded-md bg-cyan px-4 py-2.5 text-sm font-semibold text-graphite transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Investigating..." : "Start Investigation"}
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-silver/60">{label}</span>
      {children}
    </label>
  );
}
