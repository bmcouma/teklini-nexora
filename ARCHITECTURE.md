# Architecture

## Why multi-agent, not a single model call

A single prompt asking a model to "diagnose this incident" produces a plausible-sounding answer
regardless of whether it is grounded in anything real. Splitting the work across agents with
narrow responsibilities makes each step checkable: the classifier's job is falsifiable (does the
category match the evidence?), the network agent's job is falsifiable (did it actually find the
signals it claims?), and the evidence reviewer exists specifically to catch the case where a
downstream agent's confidence outpaces its evidence. That structure is the actual value of the
multi-agent approach here, not the appearance of sophistication.

## When a specialized agent is appropriate vs. a deterministic tool

Tools are deterministic and reproducible: given the same input, a tool always returns the same
output, and that output is either data or an explicit "unavailable" marker. Tools do the actual
work of reading logs, checking DNS, or evaluating environment variables.

Agents decide *which* tools to call, interpret the combined results, and produce a natural-language
summary of what was found. An agent is appropriate when a decision requires weighing several
pieces of evidence against each other (is this a network problem or an application problem, given
these three signals?). A deterministic tool is preferable whenever the answer is a direct function
of the input data with no judgment involved (does this log line match a known error pattern?).

Keeping this split explicit is also what makes the system testable without mocking an LLM: every
tool in `src/nexora/tools/` has unit tests that assert on exact output, because tools never
depend on model sampling.

## How agents communicate

Agents do not call each other directly. They all read from and write to a single shared
`InvestigationState` object (`src/nexora/models/state.py`), which the orchestrator passes from
agent to agent in sequence. This keeps the data flow linear and inspectable: at any point in the
investigation, the full state (evidence collected so far, findings, review outcomes) is a single
object that can be logged, persisted, or returned to the API as-is.

An agent only ever appends to the sections of state it owns (the network agent appends to
`evidence` and `agent_findings`; it does not rewrite what the classifier already decided).

## How state is maintained

`InvestigationState` holds:

- `incident` — the mutable incident record (category, severity, stage, iteration counters)
- `diagnostic_plan` — the task list produced by the planner
- `evidence` — every `Evidence` record collected across all agents, in order
- `agent_findings` — one `AgentFinding` per specialist agent run, each carrying its own evidence
- `review_findings` — the history of evidence-sufficiency checks
- `root_cause`, `recommendations`, `final_report` — populated in the later stages
- `activity_log` — a flat, human-readable trace of what happened, in order (this is what the
  frontend's Activity Log panel renders directly)

The API layer persists a JSON snapshot of this object per incident (`IncidentRecord.state_json` in
`src/nexora/api/db.py`). No secrets are ever written into it: log text is redacted before the
workflow starts, and no tool receives or returns credentials.

## How validation works

The `EvidenceReviewerAgent` (`src/nexora/agents/evidence_reviewer.py`) has two validation stages.
The first runs after diagnostic agents and checks whether evidence was actually collected and
whether specialist findings have support. In Gemini mode, a second review runs after ADK/Gemini
produces a proposed root cause. It checks cited IDs, recognizable evidence-to-claim signals,
contradictions, assumptions, and confidence. Unsupported model conclusions are downgraded to
`NEEDS_MORE_EVIDENCE` before recommendations are generated.

## How loops are controlled

The review loop (`NexoraOrchestrator._review_loop` in `src/nexora/agents/orchestrator.py`) is
bounded by two independent, configurable counters: `MAX_DIAGNOSTIC_ITERATIONS` (default 3) and
`MAX_REVIEW_ITERATIONS` (default 2). Both counters live on the `Incident` object itself, so they
persist correctly even if the investigation is resumed. If the limits are reached before the
reviewer is satisfied, the orchestrator proceeds to root cause analysis anyway, with the
available evidence and records the uncertainty explicitly rather than looping indefinitely.

## How safety boundaries are enforced

- **No shell access.** No tool in this version executes arbitrary shell commands. Tools call
  specific, narrow APIs (Python's `socket`, `ssl`, `httpx`) with fixed timeouts.
- **No destructive operations.** No tool modifies infrastructure, deletes data, or writes to a
  database other than Nexora's own incident store.
- **Risk-tiered recommendations.** `RemediationAdvisorAgent` classifies every recommendation as
  low, medium, or high risk. High-risk recommendations are marked `requires_approval: true` and
  the incident's stage moves to `awaiting_approval` until a human explicitly approves or declines
  each one via `POST /api/incidents/{id}/approve`. Nothing marked high-risk is ever executed
  automatically, in this version execution of any kind is not implemented at all; Nexora only
  observes and recommends.
- **Prompt injection defense.** User-provided logs are treated as data throughout the pipeline.
  In heuristic mode they are pattern-matched by deterministic regular expressions
  (`src/nexora/tools/log_tools.py`) and never reach a model. In Gemini mode the ADK prompt
  explicitly separates system instructions from incident/evidence data, treats that data as
  untrusted, and gives the model no Nexora tools or mutation capability. Structured output and
  evidence-ID validation are followed by a post-reasoning reviewer; these controls reduce risk
  but do not constitute a formal guarantee against every model failure.
- **Secret redaction.** `src/nexora/security/redaction.py` strips common credential patterns
  (AWS keys, bearer tokens, password fields, database connection strings, JWTs, PEM private key
  blocks) from submitted logs before the investigation workflow runs, and the redaction pattern
  count is recorded in the activity log so the user knows their input was modified.

## Component classification

| Component | Classification | Current behavior |
|---|---|---|
| `src/nexora/tools/*` | Deterministic tool | Read-only, bounded signal collection and parsing. No arbitrary shell execution. |
| `src/nexora/agents/classifier.py`, `planner.py`, specialist agents | Deterministic workflow logic | Rule-based routing and interpretation of tool output; reproducible in default mode. |
| `src/nexora/agents/orchestrator.py` | API/application infrastructure plus deterministic workflow logic | Owns sequencing, bounded loops, persistence-facing state flow, and stage transitions. |
| `src/nexora/agents/evidence_reviewer.py` | Validation/reviewer logic | Checks usable evidence, unsupported claims, unknown evidence references, assumptions, and contradictions. |
| `src/nexora/agents/root_cause_analyzer.py` | Deterministic workflow logic | Produces a rule-based conclusion or `NEEDS_MORE_EVIDENCE`. |
| `src/nexora/agents/gemini_reasoning.py` | ADK agent orchestration plus Gemini-powered reasoning | Builds real ADK `LlmAgent` instances and runs them through `InMemoryRunner`; receives serialized deterministic evidence only. |
| Google ADK | ADK agent/orchestration | Used in Gemini mode through `LlmAgent` and `InMemoryRunner`; heuristic mode remains independent of the optional dependency. |
| `src/nexora/api/*`, `services/*`, `models/*` | API/application infrastructure | HTTP, persistence, schemas, workflow entry point, and incident lifecycle. |

## ADK and Gemini integration

Nexora's Gemini mode uses Google's Agent Development Kit directly. The optional `adk` dependency
group installs the SDK; `GeminiReasoningAgent` constructs a root ADK `LlmAgent`, specialist ADK
sub-agents, and an ADK `InMemoryRunner`.

By default, `LLM_PROVIDER=heuristic` and no external model calls are made. Deterministic tools
produce observations and evidence, the reviewer validates them, and the rule-based analyzer
produces a reproducible conclusion. This is the supported demo and test path.

Setting `LLM_PROVIDER=gemini`, providing `GOOGLE_API_KEY`, and installing the `adk` extra enables
the ADK-backed `GeminiReasoningAgent`. It receives only serialized incident data and deterministic
evidence, treats that content as untrusted, requires structured JSON output, rejects unknown
evidence IDs, and maps the result to a conclusion with qualitative confidence. It cannot execute
Nexora tools or infrastructure mutations. Invalid, unavailable, or timed-out model output records
the provider failure and leaves the deterministic result in place.

The intended data flow is therefore:

`deterministic tools -> factual evidence -> ADK orchestration -> Gemini reasoning -> post-reasoning reviewer -> structured conclusion -> recommendation -> human approval`

## Evaluation results and known limitations

Running `python -m nexora.evaluation.run_eval` against the ten-case dataset in
`src/nexora/evaluation/dataset.py` currently produces:

- Root cause keyword accuracy: 90%
- Category classification accuracy: 60%
- Unsupported claims reaching the reviewer: 0
- Unsafe (unapproved) high-risk recommendations: 0

The category classification accuracy is the honest number for the current keyword-based
classifier, not a rounded-up one. Several evaluation cases (DNS failures described without the
literal word "DNS", disk exhaustion described without the literal phrase "disk") fall outside the
classifier's keyword list even though the root cause analyzer still identifies the correct root
cause from the log signal itself. This is a known, documented limitation of the heuristic
classifier, not a hidden one, and it is exactly the kind of gap that swapping in
`LLM_PROVIDER=gemini` for the classification step would close. The regression test
(`tests/evaluation/test_eval_regression.py`) enforces an 80% floor on root cause accuracy, which
is the metric most directly tied to whether the system is actually useful.
