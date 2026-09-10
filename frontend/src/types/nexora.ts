export type IncidentCategory =
  | "network"
  | "infrastructure"
  | "application"
  | "database"
  | "security"
  | "deployment"
  | "authentication"
  | "api"
  | "performance"
  | "unknown";

export type Severity = "informational" | "low" | "medium" | "high" | "critical";

export type InvestigationStage =
  | "submitted"
  | "classifying"
  | "planning"
  | "investigating"
  | "reviewing"
  | "additional_investigation"
  | "root_cause_analysis"
  | "remediation"
  | "awaiting_approval"
  | "report_ready"
  | "failed";

export interface Incident {
  incident_id: string;
  title: string;
  description: string;
  affected_service: string | null;
  environment: string | null;
  reported_severity: Severity | null;
  logs: string | null;
  use_demo_data: boolean;
  category: IncidentCategory;
  severity: Severity;
  stage: InvestigationStage;
  iteration_count: number;
  review_iteration_count: number;
  created_at: string;
  updated_at: string;
}

export type EvidenceSource =
  | "user_provided"
  | "uploaded_log"
  | "demo_fixture"
  | "tool_execution"
  | "unavailable";

export type EvidenceReliability = "high" | "medium" | "low" | "unavailable";

export interface Evidence {
  evidence_id: string;
  agent: string;
  tool: string | null;
  source: EvidenceSource;
  reliability: EvidenceReliability;
  summary: string;
  detail: string | null;
  collected_at: string;
}

export interface AgentFinding {
  agent: string;
  summary: string;
  evidence: Evidence[];
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  notes: string | null;
}

export interface ReviewFinding {
  sufficient: boolean;
  justification: string;
  missing_evidence: string[];
  unsupported_claims: string[];
  contradictions: string[];
  assumptions: string[];
  recommendation: string;
}

export interface DiagnosticTask {
  task_id: string;
  objective: string;
  assigned_agent: string;
  required_tools: string[];
  validation_criteria: string;
  status: "pending" | "in_progress" | "completed" | "skipped";
}

export interface DiagnosticPlan {
  objective: string;
  known_facts: string[];
  unknowns: string[];
  hypotheses: string[];
  tasks: DiagnosticTask[];
  stopping_conditions: string[];
}

export interface RootCause {
  root_cause: string;
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  supporting_evidence: Evidence[];
  alternative_causes: string[];
  uncertainties: string[];
}

export type RiskLevel = "low" | "medium" | "high";

export interface Recommendation {
  action: string;
  risk: RiskLevel;
  rationale: string;
  requires_approval: boolean;
  approved: boolean | null;
}

export interface IncidentReport {
  incident_id: string;
  generated_at: string;
  incident_summary: string;
  severity: Severity;
  category: IncidentCategory;
  affected_system: string | null;
  observed_symptoms: string[];
  known_facts: string[];
  evidence_collected: Evidence[];
  investigation_performed: string[];
  root_cause: RootCause;
  recommended_resolution: Recommendation[];
  verification_steps: string[];
  security_considerations: string[];
  remaining_uncertainty: string[];
  is_demo_data: boolean;
}

export interface InvestigationState {
  incident: Incident;
  diagnostic_plan: DiagnosticPlan | null;
  evidence: Evidence[];
  agent_findings: AgentFinding[];
  review_findings: ReviewFinding[];
  root_cause: RootCause | null;
  recommendations: Recommendation[];
  final_report: IncidentReport | null;
  activity_log: string[];
  reasoning_mode: string;
  reasoning_status: string;
  reasoning_error: string | null;
}

export interface IncidentSummary {
  incident_id: string;
  title: string;
  category: string;
  severity: string;
  stage: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentCreatePayload {
  title?: string;
  description?: string;
  affected_service?: string;
  environment?: string;
  reported_severity?: Severity;
  logs?: string;
  use_demo_data?: boolean;
}
