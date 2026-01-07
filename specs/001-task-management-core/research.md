# Research: Core Task Management (Phase II)

## Decision: Tech Stack & Architecture

- **Backend:** FastAPI with SQLModel for rapid development and high performance. Python 3.11+.
- **Database:** Neon PostgreSQL (Free Tier) with Alembic for migrations.
- **Frontend:** Next.js (App Router) for SEO, performance, and server-side rendering.
- **Styling:** TailwindCSS for utility-first responsive design.
- **Authentication:** JWT for stateless API authentication, stored in secure cookies or local storage.
- **Deployment:** Docker-based deployments for consistency across environments.

## Rationale

- **FastAPI/SQLModel:** Provides excellent DX for Python developers, automatic OpenAPI docs, and type safety that mirrors the frontend.
- **Neon:** Offers a generous free tier with serverless Postgres, perfect for starting without cost.
- **Next.js:** Industry standard for React apps, easily deployed to Vercel.

## Alternatives Considered

- **Django:** Rejected as too "heavy" for a small Todo API compared to FastAPI's async speed.
- **SQLite:** Rejected in favor of Neon to ensure a production-ready PostgreSQL environment from Day 1.
- **Vite (React):** Rejected because Next.js App Router provides better routing and deployment optimizations out-of-the-box.

## Research Findings: Free Tier Limits

- **Neon:** 500MB storage, 0.25 vCPU limit in free tier. Sufficient for MVP.
- **Vercel:** Generous free tier for frontend hosting.
- **Fly.io/Render:** Free tier options for Dockerized containers, but require careful monitoring of resource usage.

## Patterns & Best Practices

- **Repository Pattern:** Wrap SQLModel session operations in service layers to keep API routes thin.
- **DTOs:** Explicit request/response schemas to decouple the DB model from the API contract.
- **JSON Logging:** Use structured logging for easier debugging and future observability integration (ELK/Grafana).
