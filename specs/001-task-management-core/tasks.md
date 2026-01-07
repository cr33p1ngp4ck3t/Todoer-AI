# Tasks: Core Task Management

**Input**: Design documents from `/specs/001-task-management-core/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are requested in the spec (Unit, Integration, E2E).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

-   **[P]**: Can run in parallel (different files, no dependencies)
-   **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
-   Include exact file paths in descriptions

## Path Conventions

-   **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

-   [X] T001 Create backend and frontend project structure per plan.md
-   [X] T002 [P] Initialize FastAPI project with SQLModel and Alembic in backend/
-   [X] T003 [P] Initialize Next.js project with TailwindCSS in frontend/
-   [X] T004 Organize project files: create models, api, and services directories in backend/src/
-   [X] T005 [P] Configure linting and formatting (Black, ESLint, Prettier) in root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

-   [X] T006 Setup Neon DB connection and Alembic migrations framework in backend/
-   [X] T007 [P] Implement JWT/Session authentication framework in backend/src/api/auth.py
-   [X] T008 [P] Setup base API routing and health check in backend/src/main.py
-   [X] T009 Create User model in backend/src/models/user.py
-   [X] T010 Configure structured JSON logging in backend/src/lib/logging.py
-   [X] T011 Setup .env configuration management in both backend and frontend

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

Concurrency: Document “last write wins” in backend/src/services/task_service.py.

Deletion: Permanent removal only; note this in backend/src/api/tasks.py.

Auth: All queries scoped by authenticated user (per‑user isolation baseline).

## Phase 3: User Story 1 - Basic Task Lifecycle (Priority: P1) 🎯 MVP

**Goal**: Enable creation, viewing, updating, and deletion of tasks with multi-user isolation.

**Independent Test**: A user can create a task, see it in their private list, edit it, and delete it.

### Tests for User Story 1

-   [ ] T012 [P] [US1] Unit tests for Task model validation in backend/tests/test_models.py
-   [ ] T013 [P] [US1] Integration tests for Task CRUD endpoints in backend/tests/test_tasks.py
-   [ ] T014 [US1] Playwright E2E test for Task CRUD flow in frontend/tests/e2e/tasks.spec.ts

### Implementation for User Story 1

-   [X] T015 [P] [US1] Create Task model (title, description, status) in backend/src/models/task.py
-   [X] T016 [US1] Implement TaskService with CRUD and user isolation in backend/src/services/task_service.py
-   [X] T017 [US1] Create Task endpoints (GET, POST, PATCH, DELETE) in backend/src/api/tasks.py
-   [X] T018 [US1] Create API client service in frontend/src/services/api.ts
-   [X] T019 [US1] Build Task List and Creation UI in frontend/src/app/dashboard/page.tsx
-   [X] T020 [US1] Implement Task Delete and Update actions in frontend/src/components/TaskItem.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

Add concurrent update test in backend/tests/test_tasks.py (simulate two PATCH calls).

Ensure TaskService enforces per‑user isolation consistently.

## Phase 4: User Story 2 - Task Completion and Status (Priority: P1)

**Goal**: Allow users to toggle task status between pending and completed.

**Independent Test**: User clicks a checkbox on a task, and its status reflects "completed" in the UI and DB.

### Tests for User Story 2

-   [ ] T021 [P] [US2] Unit tests for status transition logic in backend/tests/test_logic.py
-   [ ] T022 [US2] E2E test for task completion toggle in frontend/tests/e2e/completion.spec.ts

### Implementation for User Story 2

-   [X] T023 [US2] Add status toggle endpoint or expand PATCH in backend/src/api/tasks.py
-   [X] T024 [US2] Implement Checkbox component with status sync in frontend/src/components/TaskItem.tsx (inline)
-   [X] T025 [US2] Add visual "completed" styles (strikethrough) in frontend/src/components/TaskItem.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

Status toggle must respect per‑user isolation.

Completed tasks remain visible unless explicitly filtered.

## Phase 5: User Story 3 - Organizational Tools: Priorities & Tags (Priority: P2)

**Goal**: Categorize tasks with tags and assign priority levels.

**Independent Test**: Create a "High" priority task with "Work" and "Urgent" tags; verify visibility.

### Tests for User Story 3

-   [ ] T026 [P] [US3] Unit tests for Tag and Priority schemas in backend/tests/test_schemas.py
-   [ ] T027 [US3] Integration test for tag-based filtering in backend/tests/test_filtering.py

### Implementation for User Story 3

-   [X] T028 [P] [US3] Create Tag model and TaskTag association in backend/src/models/task.py
-   [X] T029 [P] [US3] Update Task model with priority enum in backend/src/models/task.py
-   [X] T030 [US3] Implement Tag management in TaskService at backend/src/services/task_service.py
-   [X] T031 [US3] Add Priority selector and Tag input to frontend/src/components/TaskForm.tsx
-   [X] T032 [US3] Display Priority and Tags on frontend/src/components/TaskItem.tsx

**Checkpoint**: All user stories should now be independently functional

Tags: Free‑form strings in Phase II/III.

Plan schema for per‑user tag library in Phase IV.

## Phase 6: User Story 4 - Discovery: Search, Filter, & Sort (Priority: P2)

**Goal**: Find tasks using text search, metadata filters, and sorting.

**Independent Test**: Search for "Groceries" and filter by "High" priority; verify only matching tasks show.

### Implementation for User Story 4

-   [X] T033 [US4] Implement search, filter, and sort logic in backend/src/services/task_service.py
-   [X] T034 [US4] Update GET /tasks endpoint parameters in backend/src/api/tasks.py
-   [X] T035 [US4] Create SearchBar component in frontend/src/components/SearchBar.tsx
-   [X] T036 [US4] Create FilterControls component in frontend/src/components/FilterControls.tsx
-   [X] T037 [US4] Build SortDropdown in frontend/src/components/SortDropdown.tsx

**Checkpoint**: All user stories should now be independently functional

Add pagination params (limit, offset) to GET /tasks.

Filters/sorts reset on load in Phase II; DB persistence planned for Phase IV.

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

-   [ ] T038 [P] Run and validate all tests (Pytest + Playwright)
-   [ ] T039 [P] Update docs/ and finalize README.md
-   [ ] T040 Final code cleanup and performance optimization
-   [ ] T041 Run quickstart.md validation to ensure reproducible setup
-   [ ] T042 Create Docker multi-stage builds for production readiness

Observability: Add /health/ready and /health/live endpoints for K8s probes.

Security: JWT/session auth enforced; secrets via env/K8s secrets.

## Dependencies & Execution Order

### Phase Dependencies

-   **Setup (Phase 1)**: No dependencies - can start immediately
-   **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
-   **User Stories (Phase 3+)**: All depend on Foundational phase completion
    -   Sequential priority order (P1 → P2 → P3) recommended for single agents

### User Story Dependencies

-   **User Story 1 (P1)**: Independent after Phase 2.
-   **User Story 2 (P1)**: Builds on US1 UI/API.
-   **User Story 3 (P2)**: Independent logic, integrates into US1/US2 views.
-   **User Story 4 (P2)**: Depends on Task/Tag/Priority data being queryable.

### Parallel Opportunities

-   T002, T003 (Backend/Frontend init)
-   T012, T013 (US1 Tests)
-   T028, T029 (US3 Models)
-   Different user stories (US1-US4) once Foundation is solid.

---

## Parallel Example: User Story 3 Models

```bash
# Launch models for User Story 3 together:
Task: "Create Tag model and TaskTag association in backend/src/models/tag.py"
Task: "Update Task model with priority enum in backend/src/models/task.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (The MVP!)

### Incremental Delivery

-   Add User Story 2 (Completion)
-   Add User Story 3 (Categorization)
-   Add User Story 4 (Search/Discovery)

---

## Notes

-   [P] tasks = different files, no dependencies
-   [Story] label maps task to specific user story for traceability
-   Verify tests fail before implementing (Red phase)
-   Commit after each task group
-   Simple login required per FR-008

