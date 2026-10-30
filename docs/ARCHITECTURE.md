# Local architecture

[docker-compose.yml](../docker-compose.yml) builds the FastAPI service from
[backend/Dockerfile](../backend/Dockerfile) with the `backend/` context and the
Next.js service from [frontend/Dockerfile](../frontend/Dockerfile) with the
`frontend/` context. PostgreSQL uses the official `postgres:16-alpine` image.
Startup follows health checks: PostgreSQL, API, then frontend.

Follow [Quick start](../README.md#quick-start-with-docker-compose) for the exact
Docker commands. The [.devcontainer](../.devcontainer/devcontainer.json) uses the
same Compose stack, generates local secrets without copying an env file, and
adds uv/Python and Node development tools. In VS Code select **Dev Containers:
Reopen in Container**; in Codespaces select **Create codespace**. The backend's
`development` build target includes locked test dependencies; production builds
use the final runtime target. Source is mounted at `/workspaces/todo-app`.
The devcontainer builds the browser with `/api` and proxies it to `backend:8000`
inside Compose. Open forwarded port 3000 in Codespaces; API calls use that same
origin rather than the browser's localhost. Optional OAuth still needs callbacks
and `FRONTEND_URL` configured for the forwarded HTTPS origin.

## API observability

Every log uses JSON with `timestamp`, `level`, `message`, `logger`, `request_id`,
and `user_id`. A valid UUID in `X-Request-ID` is reused; otherwise the API generates
one, returned in the same response header. Authentication supplies the user ID;
anonymous and startup logs use null. Context is cleared after each request.

Set the optional `SENTRY_DSN` to enable exception reporting at startup. Unhandled
exceptions include request ID and authenticated user ID in Sentry. Request bodies,
cookies, authentication headers, and stack-frame locals are not collected by this
explicit hook. Leaving the DSN empty keeps tracking disabled. The SDK is tested
with an in-memory transport and verified through a disposable Docker API.

## Sentry projects

Use separate `todo-backend` (FastAPI) and `todo-frontend` (Next.js) projects.
DSNs are configured in ignored local env files; checked-in examples remain blank
so forks do not send events to someone else's account. When switching accounts,
replace both DSNs and the frontend source-map organization in `next.config.ts`.

| Host | Variable | Value |
| --- | --- | --- |
| Render backend | `SENTRY_DSN` | DSN from the backend Sentry project. |
| Render backend | `SENTRY_ENVIRONMENT` | `production` |
| Vercel frontend | `NEXT_PUBLIC_SENTRY_DSN` | DSN from the frontend Sentry project. |
| Vercel frontend | `SENTRY_DSN` | The same frontend DSN, for server and edge errors. |
| Vercel frontend | `SENTRY_ENVIRONMENT` | `production` |

Save and redeploy both services. The browser DSN is read at build time, so Vercel
needs a new build. Optional `SENTRY_RELEASE` and `NEXT_PUBLIC_SENTRY_RELEASE` should
use the deployed commit, with matching frontend values at build and runtime.
Compose forwards the optional settings.

Next.js captures browser, React render, server, and edge errors and samples 100% of
development traces and 10% of production traces. It excludes user info, cookies,
HTTP headers/bodies, and URL query parameters from SDK collection. The backend
retains the explicit lightweight exception hook described above.

Source-map uploads are enabled when `SENTRY_AUTH_TOKEN` is present during the frontend
build, targeting `todo-frontend` in the organization configured in `next.config.ts`.
After switching accounts, create an upload token in the new organization. Configure it
in GitHub Actions repository secrets under that name; CI supplies it to `npm run
build`. For Vercel, add it to the project's build environment. It must never be a
`NEXT_PUBLIC_` variable or Docker build argument. Without the token, builds still
work but minified production frontend stack traces need source maps. The token and
production deployment are separate from the local ingest verification.

Account-switch verification on 2026-10-30 confirmed backend, browser and Next.js
server exceptions in the new organization. Temporary local routes were removed
after confirmation. Backend and server source frames were readable; the browser
event identifies its bundle and needs uploaded maps for original-source context.
Test issues remain available for inspection. Hosted DSNs and upload-token changes
must be applied in the hosting dashboards separately.

## Validation

On 2026-10-30, locked backend pytest passed locally: **196 passed, 82.22% coverage**,
above the 80% gate. The earlier isolated Docker run with networking disabled passed
**195 tests with 82.20% coverage**.
Chatbot and MCP service coverage was 100%. Frontend unit and browser suites each
passed 17 tests; production builds, lint, formatting, and type checks passed.
Backend and frontend dependency audits reported no known vulnerabilities.

A clean local clone with the pending source changes and independently generated
credentials passed `docker compose up --build --wait` and the registration, login,
CRUD, and refresh smoke test. The devcontainer Compose override also started all
three services healthy and passed that smoke test through its same-origin proxy.
VS Code and hosted Codespaces launch were not exercised.

Helm strict lint and kube-score passed, with warnings for unrestricted egress and
missing host anti-affinity. kubeconform validated 35 objects without errors and
skipped two Dapr `Component` objects requiring CRD schemas. Account-switch production
settings still need to be applied and verified on the hosting platforms.
