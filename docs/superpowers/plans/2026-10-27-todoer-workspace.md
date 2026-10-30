# Todoer workspace implementation plan

Goal: deliver the requested task upgrades and a complete dashboard/auth redesign with regression proof.

Architecture: retain FastAPI, SQLModel, Next.js, existing UI primitives and authentication. Extend the shared task service once for access control, nullable updates, scheduling and import/export. The frontend consumes these APIs; no live provider or cloud connection is needed for tests.

## Scope and contracts

- Existing personal tasks remain private; existing request shapes continue to work.
- Task fields add `project_id`, `assignee_id`, `recurrence` (`daily`, `weekly`, `monthly`, or null), `recurrence_timezone` (IANA name, default UTC). A recurring task requires a due date. Completion produces one next occurrence; repeated completion cannot duplicate it. Monthly schedules preserve their original day where possible.
- PATCH distinguishes omitted values from explicit null for description, deadline, recurrence and assignment. Tags accept an empty list. Sort supports created_at, created_at_asc, priority and due_date.
- GET /projects lists accepted projects. POST /projects creates a name. GET /projects/{id} returns project plus members. POST /projects/{id}/invitations accepts email and role (editor/viewer); owner only, existing registered users, pending until acceptance. GET /projects/invitations lists the user's pending invitations. POST /projects/invitations/{id}/accept accepts own invitation. DELETE /projects/{id}/members/{user_id} removes a member and clears assignments; owner only. Creator is owner. Editors modify tasks; viewers read; nonmembers cannot access.
- GET /tasks/export returns a versioned JSON backup of personal tasks. POST /tasks/import accepts that backup, validates the whole payload before writes, imports personal tasks with deduplication, and returns imported/skipped counts. Shared task export is excluded to preserve project access rules.
- AI smart parse accepts text plus optional reference_time and timezone; validates provider JSON, handles outages/malformed responses, and returns a bounded draft with deadline/recurrence when provided. Frontend always previews before saving. No automatic AI deletions.
- Redesign dashboard, task form, edit modal, task rows, login/register, shared tokens and page metadata. Preserve accessible names and useful existing flows; add real navigation, project controls, backups and retry states.
- Frontend unit tests use Node's built-in test runner and existing TypeScript tooling; keep browser regression tests. Add relevant manifest assertions using installed tooling if available.
- Image generation is unavailable; implement the stated code-native design, inspect desktop/mobile/dark screenshots. Keep temporary QA artifacts ignored or outside source.
- No push, external deployment, fake attribution, or payout promises. Preserve existing local documentation changes.

## Tasks

- [x] Backend task fixes, recurrence, projects, backup APIs, migration and regression tests.
- [x] AI draft validation, reference-date/timezone handling, failure tests.
- [x] Frontend API/types/date utilities, unit tests and CI gate.
- [x] Complete dashboard, forms and auth redesign; wire all functional upgrades.
- [x] Browser regression tests for task clearing, recurrence, projects, backups and failures.
- [x] Infrastructure validation gate, pod-policy regression tests and documentation.
- [x] Backend/frontend verification, SQLite migration preservation check, desktop/mobile/dark visual review and final diff review.

Local Kubernetes schema execution remains unverified because validator downloads were blocked by automatic approval review. Helm/cluster/Compose verification from the earlier readiness pass does not validate this feature branch; hosted CI and deployment checks remain outstanding.

## Design system

True white main canvas, pale neutral sidebar, ink text, fine gray dividers, muted indigo accent. Dark mode uses charcoal surfaces and lavender accent. System sans typography, 32px workspace title, 14px control text, 8px spacing increments, 8–12px radii, subtle focus rings. Open task lists replace oversized gradient cards; useful counts replace dashboard filler. Task editor has an AI/manual switch, preview message, deadline/recurrence fields, project and assignee controls. Project owner controls and import/export live in a workspace menu.

## Progress

2026-10-27: Inspected current code, identified sort/field-clearing/date bugs; user authorized all upgrades and major UI changes. Backend and AI work will be delegated under the subagent-development skill while the root agent owns frontend integration. Tasks are split by nonoverlapping files; review and verification stay coordinated.

2026-10-27 completion: Implemented the scope using existing dependencies. Review fixed delayed-mutation refresh races, saving-dialog dismissal, offscreen keyboard navigation, mixed-case invitations, legacy UTC display, and an export/import file-size mismatch. Verification: 157 backend tests, 77.74% coverage; 16 API/date unit tests, 100% lines/functions and 98.31% branches across those modules; 17 Chromium scenarios; production build, lint/typecheck/Prettier, Ruff; Black formatting/AST checks over all 50 Python files using its API after the CLI stalled. Parsed all 26 raw Kubernetes resources and CI YAML. Migration preservation/reapply/downgrade/rollback tested on disposable SQLite only. Reviewed populated desktop1440x1000, mobile390x844 and dark screenshots; AI/OAuth/microphone live integration and PostgreSQL concurrency remain untested. No real database, remote repository or deployment changed.
