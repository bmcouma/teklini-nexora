import type {
  Incident,
  IncidentCreatePayload,
  IncidentSummary,
  InvestigationState,
} from "../types/nexora";

const BASE = "/api";

export type ApiErrorCode = "unauthorized" | "forbidden" | "request";

export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode;

  constructor(
    message: string,
    status: number,
    code: ApiErrorCode,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

const storage = typeof sessionStorage === "undefined" ? null : sessionStorage;
let apiKey = storage?.getItem("nexora-api-key") ?? "";

export function setApiKey(value: string): void {
  apiKey = value.trim();
  if (apiKey) {
    storage?.setItem("nexora-api-key", apiKey);
  } else {
    storage?.removeItem("nexora-api-key");
  }
}

export function hasApiKey(): boolean {
  return Boolean(apiKey);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  headers.set("Content-Type", "application/json");
  if (apiKey) headers.set("X-API-Key", apiKey);

  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    const code: ApiErrorCode = response.status === 401
      ? "unauthorized"
      : response.status === 403
        ? "forbidden"
        : "request";
    throw new ApiError(detail, response.status, code);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; app_name: string }>("/health"),

  version: () => request<{ version: string }>("/version"),

  listIncidents: () => request<IncidentSummary[]>("/incidents"),

  createIncident: (payload: IncidentCreatePayload) =>
    request<InvestigationState>("/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getIncident: (incidentId: string) => request<Incident>(`/incidents/${incidentId}`),

  getStatus: (incidentId: string) =>
    request<InvestigationState>(`/incidents/${incidentId}/status`),

  getEvidence: (incidentId: string) =>
    request<Record<string, unknown>[]>(`/incidents/${incidentId}/evidence`),

  getReport: (incidentId: string) =>
    request<InvestigationState["final_report"]>(`/incidents/${incidentId}/report`),

  reinvestigate: (incidentId: string) =>
    request<InvestigationState>(`/incidents/${incidentId}/investigate`, { method: "POST" }),

  approve: (incidentId: string, recommendationIndex: number, approved: boolean) =>
    request<InvestigationState>(`/incidents/${incidentId}/approve`, {
      method: "POST",
      body: JSON.stringify({ recommendation_index: recommendationIndex, approved }),
    }),
};
