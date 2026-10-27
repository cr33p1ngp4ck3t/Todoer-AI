# Todoer AI

A full-stack task workspace with personal lists, shared projects, recurring schedules, JSON backups, and AI task drafts. The backend uses FastAPI and SQLModel; the frontend uses Next.js and TypeScript. Groq/Gemini and Google/GitHub OAuth are optional integrations.

## What you can do

- Plan personal tasks with priorities, tags, deadlines, search, and newest/oldest/priority/deadline sorting. Clear optional details without losing other fields. Deadlines display in your local timezone.
- Preview an AI draft before saving it. Relative dates use your browser's timezone and reference time. If the provider fails, your text remains available for manual editing; ambiguous deadlines are left for you to choose. Voice input also opens a draft.
- Repeat tasks daily, weekly, or monthly. Completing an occurrence creates one successor from its scheduled deadline. Monthly schedules keep their original day when the next month permits it. Reopening and completing an occurrence again does not duplicate its successor.
- Create shared projects and invite registered accounts as editors or viewers. Invitations require acceptance; editors manage tasks and assignments, viewers read, and owners manage membership. Removing a member clears their assignments.
- Export personal tasks as version 1 JSON, then import up to 1,000 tasks per file (20 MB browser limit). Imports validate the entire file before writing, add new tasks, and skip existing or previously imported source IDs. Existing tasks are preserved. Shared tasks are excluded; recurrence anchors and successor state are retained. Imported tasks receive new IDs and timestamps. Deleting a previously imported task does not reset its source-ID deduplication record.

The workspace, editors, and account screens support mobile layouts, keyboard navigation, and light/dark themes.

## Quick start with Docker Compose

Install Docker with Compose v2 or newer, then clone this repository:

```sh
git clone https://github.com/cr33p1ngp4ck3t/Todoer-AI.git
cd Todoer-AI
cp .env.example .env
```

In PowerShell, use `Copy-Item .env.example .env`. Generate three separate values with `python -c "import secrets; print(secrets.token_hex(32))"` and put them in `.env` as `POSTGRES_PASSWORD`, `SECRET_KEY`, and `SESSION_SECRET`. Hex passwords avoid reserved characters in the database URL. Optional provider credentials can stay empty.

```sh
docker compose up --build --wait
```

Open <http://localhost:3000>, create an account, and sign in. API documentation is at <http://localhost:8000/docs>. Check database readiness at <http://localhost:8000/health> or `/health/ready`; `/health/live` checks only whether the process is alive.

Compose starts PostgreSQL, waits for it to become healthy, then starts the API and frontend. Ports bind to localhost. The API creates tables on first startup. PostgreSQL data persists across `docker compose down`; **`docker compose down --volumes` permanently deletes local data**. This is a local development setup, not a production deployment recipe.

The browser API URL is baked into the frontend build. After changing `NEXT_PUBLIC_API_URL`, rebuild with `docker compose up --build --wait`. A Docker-only hostname such as `backend` is not a usable browser URL.

## Local development

Prerequisites: Python 3.11, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Node.js 22 with npm. The backend lock supports Python 3.11–3.13; CI uses 3.11.

Backend, from the repository root:

```sh
cp backend/.env.example backend/.env
uv sync --project backend --locked
```

Set separate generated `SECRET_KEY` and `SESSION_SECRET` values in `backend/.env`. The example uses a local SQLite file; no PostgreSQL server is required for this path. Then start the API:

```sh
cd backend
uv run --locked uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal:

```sh
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

PowerShell users can replace each `cp` with `Copy-Item`. For a production frontend build, run `npm run build` followed by `npm run start`.

## Upgrading an existing database

Back up the database and stop the API before upgrading. New empty databases receive the current schema on first startup. Startup's `create_all` does **not** add columns to existing tables.

From `backend/`, use the same explicit `DATABASE_URL` as the running application (environment or `backend/.env`). For a database already managed by Alembic:

```sh
uv run --locked alembic upgrade head
```

For a legacy database created by this application's `create_all` with no Alembic version table:

```sh
uv run --locked python -m src.lib.migrate_workspace
```

The helper checks the known legacy schema, applies only the additive `010_workspace` transition, and preserves existing task/user/tag rows. It refuses versioned, unknown, or partial schemas and does not stamp historical migrations. Do not stamp a database to skip migrations. Review historical migrations before adopting Alembic for an unversioned database. The Helm init container uses Alembic, so an unversioned database needs this transition and a reviewed migration baseline before that deployment path.

Migration preservation, reapplication, downgrade, and interrupted-upgrade rollback are tested on disposable SQLite databases. PostgreSQL upgrades and simultaneous completion requests still need validation in your deployment environment. Downgrading removes project/recurrence/import metadata; restore a full database backup to recover that feature data.

## Render backend

The backend is hosted at https://todo-app-backend-odmr.onrender.com. The supplied deployment log uses the backend Dockerfile; use `backend` as its build context. Confirm the database type and deployed commit before changing the service; there is no Render Blueprint in this repository. For a native Python service with root directory `backend`, use these commands:

```sh
# Build command
pip install --require-hashes -r requirements.txt
# Start command
uvicorn src.main:app --host 0.0.0.0 --port "$PORT"
```

Select a supported Python version (3.11–3.13), retain the service's existing `DATABASE_URL`, `SECRET_KEY`, and `SESSION_SECRET`, and set the health-check path to `/health/ready`. For a Docker service, keep `backend` as the Docker build context; its Dockerfile defaults to port 8000. Render must route to the container's listening port. Do not switch runtimes just to deploy this upgrade.

Back up the existing database, then run the appropriate migration **before new API code receives traffic**. With dependencies installed and the working directory at `backend` (or `/app` in the Docker image), use `alembic upgrade head` for a versioned database or `python -m src.lib.migrate_workspace` for a known unversioned legacy schema. Use a pre-deploy command if your service supports it, or a controlled maintenance session. Do not run database migrations during the image/build step or stamp an unknown schema. A local SQLite file needs persistent storage to survive replacement of the service filesystem; use the existing database's actual configuration when selecting the migration path.

If the browser calls Render directly, build the frontend with `NEXT_PUBLIC_API_URL=https://todo-app-backend-odmr.onrender.com` (the origin, without a trailing slash or added `/api`). Set Render's `CORS_ORIGINS` and `FRONTEND_URL` to the frontend's HTTPS origin. Task routes use `/tasks`; AI routes use `/api/chat/smart-parse`. Register OAuth callbacks at the direct Render origin under `/auth/oauth/<provider>/callback`. Rebuild the frontend after changing its API URL. Keep `/api` as the frontend base only when a configured same-origin gateway forwards it.

Public GET checks on 2026-10-27 returned HTTP 200 for `/`, `/health/ready` (`ready`), and `/health/live` (`alive`). The public OpenAPI schema still exposes the older API: no project or JSON backup routes, no recurrence fields, and no AI reference-time/timezone inputs. Deploy the backend workspace changes and migrate the existing database before enabling those features in the frontend. Health checks confirm connectivity, not workspace-schema compatibility; the deployed revision, database type, and frontend CORS configuration remain unverified. The Render dashboard and production data have not been changed.

The reported Docker build failure comes from incoming `requirements.txt` drift: `google-generativeai==0.8.6` requires `google-ai-generativelanguage==0.6.15`, while that export pins `0.12.1`. Regenerate the complete runtime export from the compatible lock rather than editing one version without its hashes:

```sh
uv export --project backend --locked --no-dev --no-emit-project --output-file backend/requirements.txt
```

The current local export already matches that lock, including hashes. [The incoming dependency review](docs/incoming-dependency-review.md) provides a correction against remote commit `079e4aa`, covering the stale export, legacy bcrypt constraint, and Docker package-copy path. It must be reconciled into the revision Render builds; local files alone do not repair a remote deployment.

## Configuration

Backend variables are read from `backend/.env` for local development. Compose reads the root `.env`. Never commit either file. The frontend example contains only public configuration; never put secrets in a `NEXT_PUBLIC_` variable.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy SQLite or PostgreSQL URL. Compose supplies the PostgreSQL URL. |
| `SECRET_KEY` | Required stable, random JWT signing secret. |
| `SESSION_SECRET` | Stable random secret for OAuth session cookies. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime; default 15. Refresh tokens last 30 days. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins; default `http://localhost:3000`. |
| `FRONTEND_URL` | Frontend origin used by OAuth redirects. |
| `DEFAULT_LLM_PROVIDER` | `groq` (default) or `gemini`; falls back to a configured provider. |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | Optional AI credentials; normal task management needs neither. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Optional Google OAuth application credentials. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | Optional GitHub OAuth application credentials. |
| `NEXT_PUBLIC_API_URL` | Browser-reachable API base URL, read at frontend build time. |
| `POSTGRES_PASSWORD` | Compose-only PostgreSQL password. |

Register OAuth callback URLs as `http://localhost:8000/auth/oauth/google/callback` or `http://localhost:8000/auth/oauth/github/callback`. Microsoft OAuth is a commented example and is not implemented. Provider SDK/model availability can change; live AI and OAuth require separately configured accounts.

## Tests and quality checks

Run backend checks **from the repository root**:

```sh
uv run --project backend --locked ruff check backend/src backend/tests
uv run --project backend --locked black --check backend/src backend/tests
uv run --project backend --locked pytest
uv run --project backend --locked pip-audit --disable-pip --require-hashes -r backend/requirements.txt
```

Pytest uses a fresh in-memory SQLite database for each test, overrides the API session dependency, disables dotenv loading, and mocks AI providers. No live server, database credentials, or AI keys are needed. Coverage is printed and written to `coverage.xml`; the minimum is 60% across backend source.

Frontend checks:

```sh
cd frontend
npm ci
npm run lint
npm run typecheck
npm run format:check
npm run test:unit
npm run build
npx playwright install chromium
npm test
npm audit --omit=dev --audit-level=high
```

The unit gate uses Node's built-in test runner: 90% lines/functions and 80% branches across the API client and deadline utilities. It does not measure component coverage. Tests cover UTC, Karachi, and New York date conversions, including nonexistent local times. In PowerShell use `npm.cmd` if execution policy blocks `npm.ps1`.

On Linux, install browser system dependencies with `npx playwright install --with-deps chromium`. Playwright starts its configured local web server and tests authentication, task clearing and recurrence, AI previews, projects, backups, pending-save protection, request races, and mobile/dark navigation with mocked API responses. To exercise the real Compose backend instead, start the stack and run `python scripts/smoke_test.py` from the root. The smoke test creates a unique account and removes its test task; use a disposable local database.

GitHub Actions runs backend and frontend checks on every pull request and push to `main`, plus Helm lint/render, strict Kubernetes 1.31 schema checks with checksum-verified kubeconform v0.7.0, and a Compose build/start/API smoke test. Dapr `Component` resources require separate CRD validation and are explicitly excluded from the built-in schema check. Pod-policy tests verify app image users, dropped capabilities, and disabled privilege escalation. Schema checks do not constitute a security audit. Hosted CI results must be checked on GitHub after pushing.

## Repository layout

| Path | Responsibility |
| --- | --- |
| `backend/src/api/` | HTTP endpoints and authentication. |
| `backend/src/services/` | Task operations, AI provider clients, and MCP tools. |
| `backend/src/models/`, `backend/src/lib/` | SQLModel tables, sessions, OAuth setup, JSON logging. |
| `backend/tests/` | Isolated unit and API tests. |
| `frontend/src/` | Next.js pages, components, auth context, API client. |
| `frontend/tests/` | Browser regressions and API/date unit tests. |
| `helm/todo-app/`, `k8s/` | Existing Kubernetes deployment templates and experiments. |
| `specs/`, `history/` | Original specifications and development notes. |

The Helm chart can be checked with `helm lint --strict helm/todo-app` and `helm template todo helm/todo-app`. Build its frontend image with the default same-origin `/api` URL; the chart's nginx ingress removes that external prefix and tells FastAPI to include it in generated OAuth callback URLs. Before installing, create the Secret named by `backendSecrets.existingSecret` with `DATABASE_URL`, `SECRET_KEY`, and `SESSION_SECRET`; add AI or OAuth variables only when those integrations are enabled. The chart deliberately does not generate credentials. Existing Kubernetes/cloud instructions in [DEPLOYMENT.md](DEPLOYMENT.md) still need real registry, ingress, and database configuration. They do not replace the local setup above; no cluster is provisioned by CI. The optional raw Dapr statestore and Grafana examples still contain development credential defaults; configure credentials via Secrets before using them. The optional Gemini integration uses the deprecated `google-generativeai` SDK and needs migration before relying on it in production.

## Updating dependencies and contributing

Python dependencies live in `backend/pyproject.toml`. Update intentionally, then regenerate both lock and pip export:

```sh
uv lock --project backend
uv export --project backend --locked --no-dev --no-emit-project --output-file backend/requirements.txt
```

Commit `backend/uv.lock` and its generated `requirements.txt` together. `requirements.txt` is a compatibility export for Docker and pip, not a second editable dependency list. Commit npm changes with `frontend/package-lock.json`. Dependabot proposes weekly dependency updates.

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep fixes and their regression tests together in focused commits. Release tags should follow successful CI and an actual review.
