# Repository readiness implementation plan

**Goal:** Make a fresh checkout installable, testable, and documented, with enforced CI checks.

**Architecture:** Retain FastAPI/SQLModel, Next.js, and the existing Helm chart. Use uv for Python locking, SQLite fixtures for offline tests, Playwright for frontend behavior, and Compose for a local PostgreSQL stack.

**Tech stack:** Python 3.11, uv, pytest, Ruff, Black, Node.js, Next.js, Playwright, Docker Compose, Helm, GitHub Actions.

**Spec:** User-supplied repository quality report. Existing code is authoritative where the automated report is inaccurate.

## Constraints

- Preserve existing task, authentication, chat, and OAuth interfaces while fixing demonstrated defects.
- Never run tests against a developer database or live AI/OAuth providers.
- Keep credentials out of version control and logs; bind the local stack to loopback.
- No speculative features, fabricated history, cloud deployment, or release tag.

## Deliverables and acceptance

- [ ] `backend/pyproject.toml`, `backend/uv.lock`, `backend/requirements.txt`: one dependency source, locked install and compatible export; verify `uv sync --locked` and compare the generated export with the tracked file.
- [ ] `backend/tests/`, `pyproject.toml`: repair fixtures, preserve meaningful existing assertions, replace manual auth scripts with API tests; run pytest with 60% coverage gate and no external services.
- [ ] Shared backend service/auth/health code: prove failing tests for task isolation, validation, refresh tokens, and unhealthy DB status before minimal fixes. Run Ruff and Black across source/tests.
- [ ] `frontend/`: runnable lint/typecheck/build and Playwright tests of user-visible flows using mocked API responses; fix browser API URL and Docker health check.
- [ ] Dockerfiles, ignore files, `docker-compose.yml`: locked installs, non-root runtime, PostgreSQL health dependency, persistent local data, runtime-native health probes. Validate Compose and run stack if Docker is available.
- [ ] `.github/workflows/ci.yml`, `.github/dependabot.yml`: backend/frontend gates, dependency audits, Helm lint/render, Compose smoke test on pushes and PRs.
- [ ] `README.md`, environment examples, contribution guidance: exact clean setup and test commands, required/optional variables, data persistence, and known deployment limits.

## Verification

Execute the documented backend and frontend commands. Inspect every failure and repair at the responsible layer. Validate Compose and Helm output, and review the final diff for leaked secrets, weakened checks, and unrelated changes. Record unavailable external verification explicitly.
