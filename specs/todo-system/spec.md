# Feature: Todo System (Phase II)

## Goal
- **Outcome:** A full-stack web application for task management with a FastAPI backend, Next.js frontend, and Neon (PostgreSQL) database.
- **User story:** As a user, I want to create, read, update, and delete tasks with priorities, tags, and search/filter capabilities so that I can stay organized.

## Requirements
### Functional
- **CRUD Operations:** Create, Read, Update, Delete tasks.
- **Task Status:** Mark tasks as complete/incomplete.
- **Metadata:** Support for priorities (Low, Medium, High) and multiple tags/categories.
- **Discovery:** Search tasks by title/description and filter by status, priority, or tags.
- **Ordering:** Sort tasks by creation date, due date, or priority.

### Non-functional
- **Performance:** API response time < 200ms for standard queries.
- **Observability:** Structured logging and `/health` endpoints.
- **Security:** Input validation on all API boundaries.

### Constraints
- **Tech Stack:** FastAPI (Python), Next.js (TypeScript), SQLModel, Neon DB (PostgreSQL).
- **Deployment:** Containerized via Docker.

## Interfaces
### API Endpoints
- `GET /tasks`: List tasks (supports query params: search, status, priority, tags, sort).
- `POST /tasks`: Create a new task.
- `GET /tasks/{id}`: Get task details.
- `PATCH /tasks/{id}`: Update task (partial update).
- `DELETE /tasks/{id}`: Delete task.
- `GET /health`: System health check.

### Request/Response Schemas (Simplified)
- **Task:** `{id: UUID, title: String, description: String, status: Enum, priority: Enum, tags: List[String], created_at: DateTime, updated_at: DateTime}`

### Errors
- Standardized envelope: `{error: {code: String, message: String, details: Object}}`
- Codes: `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_SERVER_ERROR`.

## Data
### Entities
- **Task:**
  - `id`: Primary Key (UUID)
  - `title`: String (Non-null, indexed)
  - `description`: String (Optional)
  - `status`: Enum (pending, completed)
  - `priority`: Enum (low, medium, high)
  - `created_at`: DateTime
  - `updated_at`: DateTime
- **Tag:** String (associated with Tasks)

### Migrations
- Managed via Alembic; reversible steps.

## Tests
### Unit
- Validation logic for task fields and tags.
- Priority parsing.
### Integration
- API endpoint verification with a test database.
- Search/filter logic across multiple tasks.
### E2E
- Full flow: Create task -> Search -> Complete -> Delete.

## Acceptance criteria
- [ ] API contract is stable and documented.
- [ ] Frontend UI integrates with all API endpoints.
- [ ] Neon DB connection is successful with automated migrations.
- [ ] All tests (Unit, Integration, E2E) pass.
- [ ] Health and readiness probes return 200 OK.

## Generation notes
- **Prompt:** Use locked SDD prompts for FastAPI/SQLModel and Next.js/Tailwind code generation.
- **Artifacts:** `backend/`, `frontend/`, `docker-compose.yml`, `alembic/`.
- **Post-gen checks:** Linting, type checking, and test execution.
