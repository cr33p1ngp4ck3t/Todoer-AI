# Implementation Plan: Core Task Management

**Branch**: `001-task-management-core` | **Date**: 2025-12-30 | **Spec**: [specs/001-task-management-core/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-task-management-core/spec.md`

## Summary

The goal is to build the foundational Phase II Todo System consisting of a FastAPI backend and a Next.js frontend, using Neon (PostgreSQL) for persistence. This core feature enables task CRUD, prioritization, tagging, and multi-user isolation with simple session/JWT auth.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript 5.0+ (Node 20+)
**Primary Dependencies**: Next.js (App Router), FastAPI, SQLModel, Alembic, TailwindCSS, JWT
**Storage**: Neon PostgreSQL (Free Tier)
**Testing**: Pytest (Backend), Playwright (E2E)
**Target Platform**: Linux (Docker containers on Fly.io/Render and Vercel)
**Project Type**: Web application (Full-stack)
**Performance Goals**: API response < 200ms p95; List rendering < 500ms for 1k tasks
**Constraints**: < 200ms latency, free-tier resource limits, secrets in .env/K8s secrets
**Scale/Scope**: ~10k tasks per user, ~5-10 screens (Dashboard, Task Detail, Profile)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Spec-driven only**: All implementation driven by `spec.md` and this `plan.md`.
- [x] **Single source of truth**: No manual code edits; generation via Spec-Kit Plus + Claude Code.
- [x] **Observability first**: JSON logs and health checks included in Phase II.
- [x] **Security by default**: JWT/Session auth and secret management via `.env`.

## Project Structure

### Documentation (this feature)

```text
specs/001-task-management-core/
├── plan.md              # This file
├── research.md          # Implementation research
├── data-model.md        # DB schema and entities
├── quickstart.md        # Local dev setup
├── contracts/           # API schemas (OpenAPI)
└── checklists/          # Requirements validation
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # API routes and dependencies
│   ├── models/          # SQLModel entities
│   ├── services/        # Business logic
│   └── main.py          # Entry point and health checks
├── alembic/             # Migrations
├── tests/               # Pytest (Unit/Integration)
└── Dockerfile

frontend/
├── src/
│   ├── app/             # App Router pages
│   ├── components/      # UI components (Tailwind)
│   ├── services/        # API client
│   └── lib/             # Utilities
├── tests/               # Playwright (E2E)
└── Dockerfile

docker-compose.yml       # Local orchestration
```

**Structure Decision**: Web application structure with separated `backend/` and `frontend/` directories for deployment flexibility (Vercel vs Fly.io/Render).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
