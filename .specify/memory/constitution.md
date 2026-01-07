# Vision & Scope

- **Mission:** Build a spec-driven Todo system that evolves from a full-stack web app into an AI-powered, cloud-native platform.
- **Outcome:** A reproducible, fully documented implementation where specs—not manual coding—drive all deliverables.
- **Scope:** Phases II–V with explicit features, AI integrations, and deployments; bonus features layered into chatbot and cloud phases.

---

## Principles & Constraints

- **Spec-driven only:** All implementation generated via Spec-Kit Plus + Claude Code. No manual coding.
- **Single source of truth:** Markdown specs and constitution govern requirements, interfaces, and acceptance.
- **Observability first:** Health, readiness, logs, metrics, and traceability across phases.
- **Security by default:** Least privilege, secret management, and safe data handling.

---

## Phase Overview & Deliverables

### Phase II — Full-Stack Web Application
- **Tech:** Next.js, FastAPI, SQLModel, Neon DB
- **Features:** CRUD, priorities, tags, search/filter, sort
- **Deliverables:** API + UI, DB migrations, e2e tests, deployment configs
- **Acceptance:** API contract stable; UI passes e2e; Neon connected with migrations

### Phase III — AI-Powered Todo Chatbot
- **Tech:** OpenAI ChatKit, Agents SDK, MCP SDK
- **Features:** Natural language management (reschedule, create, update), recurring tasks, due dates, reminders
- **Deliverables:** Chat flows, agent skills, MCP tools, evaluation prompts
- **Acceptance:** NL commands map to deterministic actions; tests cover intents and edge cases

### Phase IV — Local Kubernetes Deployment
- **Tech:** Docker, Minikube, Helm, kubectl-ai, kagent
- **Features:** Clustered services, health/readiness, secrets, scaling
- **Deliverables:** Helm charts, K8s manifests, local cluster runbook, observability
- **Acceptance:** Pods healthy; `/health` and `/ready` pass; logs/metrics visible

### Phase V — Advanced Cloud Deployment
- **Tech:** Kafka, Dapr, DigitalOcean DOKS
- **Features:** Event streaming, service orchestration, production hardening
- **Deliverables:** DOKS cluster, Dapr components, Kafka topics, SLOs
- **Acceptance:** Cloud endpoints healthy; events processed; SLOs met

---

## Bonus Features
- **Reusable intelligence (+200):** Subagents, shared skills, spec-documented interfaces
- **Cloud-native blueprints (+200):** Agent-installable Helm/Dapr/Kafka blueprints
- **Urdu support (+100):** Urdu intents, UI labels, chatbot responses
- **Voice commands (+200):** Voice input pipeline, transcription, intent mapping

---

## Governance & Change Control
- **Proposal:** Changes via PR to specs; include rationale, impact, and updated acceptance tests.
- **Review:** Constitution owner + phase leads approve; CI validates spec completeness.
- **Versioning:** Semantic versioning for specs and generated artifacts; changelog per phase.
- **Freeze points:** Each phase locks after acceptance; only hotfixes allowed post-freeze.

---

## Quality Gates & Acceptance
- **Spec completeness:** Feature spec must include requirements, interfaces, test matrix, and edge cases.
- **Generated parity:** Code must match spec—no manual edits; diffs reviewed.
- **Testing:** Unit, integration, e2e, and NL intent tests; coverage thresholds per phase.
- **Observability:** Health/readiness endpoints, structured logs, metrics; trace IDs across services.
- **Security:** Secrets via env/secret stores; input validation; least privilege DB/K8s roles.

---

## Interfaces & Contracts
- **API (Phase II+):**
  - Endpoints: `/tasks`, `/tasks/{id}`, `/search`, `/filters`, `/sort`
  - Schemas: Task, Tag, Priority, Recurrence, Reminder
  - Errors: Standardized error envelope; idempotent operations where applicable

- **Chatbot (Phase III+):**
  - Intents: create/update/delete/reschedule/complete/query
  - Tools: MCP tools for DB ops; Agents SDK skills for task actions
  - Fallbacks: Deterministic fallback chain; confidence thresholds

- **K8s (Phase IV+):**
  - Probes: `/health`, `/health/ready`, `/health/live`
  - Config: Helm values for env, secrets, resources, autoscaling

- **Cloud (Phase V):**
  - Events: Kafka topics for task events; Dapr pub/sub components
  - SLOs: Availability, latency, error rate targets

---

## Data Model & Persistence
- **Entities:** Task, Tag, Priority, RecurrenceRule, Reminder
- **Constraints:** Non-null title; optional description; due date/timezone; recurrence validation
- **Indexes:** Status, priority, due_date; text search on title/description
- **Migrations:** Spec-driven SQLModel/Alembic; reversible and tested

---

## Testing Strategy
- **Unit:** Pure functions, validators, recurrence logic
- **Integration:** API + DB, chatbot intent → action, MCP tool calls
- **E2E:** UI flows, voice commands, Urdu intents
- **Performance:** Latency budgets for chatbot and API; probe response times
- **Chaos (Phase V):** Event loss/retry, partition handling, backpressure

---

## Deployment & Operations
- **Docker:** Multi-stage builds; pinned Python/Node versions; slim images
- **Minikube:** Helm charts; local secrets; ingress; resource requests/limits
- **DOKS:** Managed cluster; Dapr sidecars; Kafka service; autoscaling
- **Runbooks:** Startup, health, rollback, incident response
- **Monitoring:** Logs, metrics, traces; dashboards per phase

---

## Tooling & Reproducibility
- **Spec authoring:** Markdown + Spec-Kit Plus templates
- **Generation:** Claude Code with locked prompts; artifact checksums
- **CI/CD:** Validate spec completeness, run tests, build images, deploy to targets
- **Artifacts:** Store generated code, charts, manifests with spec version tags

---

## Security & Compliance
- **Secrets:** Env/secret stores; never commit secrets
- **Access:** RBAC for DB/K8s; scoped tokens for cloud
- **Data:** PII-safe; encryption in transit; backups for Neon/Kafka where applicable

---

## Appendix — Spec Template (per feature)

```markdown
# Feature: <name>

## Goal
- **Outcome:** …
- **User story:** As a <role>, I want <capability> so that <benefit>.

## Requirements
- **Functional:** …
- **Non-functional:** …
- **Constraints:** …

## Interfaces
- **API/Chatbot:** endpoints/intents, request/response schemas
- **Errors:** standardized envelopes and codes

## Data
- **Entities:** fields, validation, indexes
- **Migrations:** steps and rollback

## Tests
- **Unit:** cases
- **Integration:** cases
- **E2E:** flows
- **Edge cases:** …

## Acceptance criteria
- **Pass conditions:** …
- **Metrics:** latency, correctness, coverage

## Generation notes
- **Prompt:** stable prompt for Claude Code
- **Artifacts:** files expected
- **Post-gen checks:** diffs, lint, format, run tests
```