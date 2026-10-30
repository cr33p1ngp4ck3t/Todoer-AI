# Infrastructure and backend quality improvements

Goal: add Kubernetes policy scanning, reproducible Docker onboarding, request-aware
JSON logs with optional error tracking, and an 80% backend coverage gate.

Implement inline in the existing workspace. Preserve database volumes, require
generated local secrets, reuse JSONFormatter, and mock all external providers.

- [x] Pin kube-score in infrastructure CI after rendering Helm; gate Critical
  findings, document its grades, and resolve findings in the rendered chart.
- [x] Link both Dockerfiles from docs/ARCHITECTURE.md. Add non-overwriting local
  secret initialization and a Compose devcontainer with backend development tools.
- [x] Configure shared JSON logging at lifespan startup, carry request/user context
  through authentication and errors, and add an optional SENTRY_DSN SDK hook.
  Update env examples, dependency lock, and hashed runtime export together.
- [x] Add logging, provider fallback/streaming, and MCP failure tests. Fix fallback
  failures exposed by these tests. Raise coverage to 80 without exclusions.
- [x] Run locked pytest, lint/format checks, and policy/schema scans. Validate a
  clean tracked-file snapshot with Docker Compose, smoke tests, JSON logs, and
  the same backend tests inside Docker. Record actual output in Quick start.
