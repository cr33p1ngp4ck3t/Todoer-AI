# Repository readiness handoff

## Applied dependency correction after merge — 2026-10-27

The latest user-supplied Docker failure triggered another state check. Local HEAD and `origin/main` have advanced to `4ca7e93861f999ae65728a531d3339e6e6c929c0`; the workspace implementation is now committed through `1a91271`, but its merge reintroduced the incompatible dependency files. The actual working tree was clean and regression checks failed on four requirements/lock discrepancies, the bcrypt constraint, and unsupported ESLint plugin peers. Earlier statements that local manifests were compatible describe the pre-merge state.

Applied the corrections directly to `backend/pyproject.toml`, `backend/uv.lock`, `backend/requirements.txt`, `frontend/package.json`, and `frontend/package-lock.json`. Restored bcrypt 4.0.1 with `<4.1`, regenerated the hashed runtime export, and restored the tested frontend graph with ESLint 9.39.2 and TypeScript 5.9.3. Retained the workspace implementation and its frontend coverage command. Incoming Docker/CI/image changes were preserved; Docker already copies `/usr/local` and needed no edit.

All 21 focused backend tests and 17 frontend unit tests pass again, as do frontend lint and typechecking. Complete runtime export/hash and installed SDK contract checks pass. Regenerated [incoming-dependency-fixes.patch](incoming-dependency-fixes.patch) against the exact current merge commit; it now contains only the five dependency-file changes, already applied locally. Commit/push these corrections and deploy that corrected revision; production remains unchanged and the existing database migration still requires preparation. The earlier full application verification applies to the retained source and compatible installed dependency versions, not to the new container images or hosted CI.

## Public Render verification and build failure — 2026-10-27

User supplied https://todo-app-backend-odmr.onrender.com/ and then the Docker dependency-resolution failure. Read-only Playwright checks succeeded: `/`, `/health/ready`, and `/health/live` returned HTTP 200 with the expected API information, `ready`, and `alive`. `/openapi.json` was readable and advertised `Todo System API` version `1.0.0`. The version string does not identify a deployed commit.

The live schema is older than the local workspace implementation: no `/projects` routes or `/tasks/export` and `/tasks/import`; task create/update/response schemas omit recurrence and assignment fields; `SmartParseRequest` exposes only `text`. Deploying the new frontend against this API will leave workspace features unavailable. Do not infer database schema readiness from the health endpoints, which only establish connectivity.

The supplied Docker log confirms the previously identified requirements conflict: `google-generativeai 0.8.6` requires `google-ai-generativelanguage==0.6.15`, while the incoming requirements export pins `0.12.1`. The local runtime requirements are already compatible. A fresh offline locked export matched every requirement and hash, excluding its generated-command header; installed SDK metadata confirmed the exact Google dependency requirement. Related restored pins are grpcio-status 1.71.2, proto-plus 1.28.2, protobuf 5.29.6, and bcrypt 4.0.1. All 21 focused auth/infrastructure/dependency tests passed again.

README now records the actual backend origin, Docker-build evidence, verified public API limitations, and runtime export command. The existing [correction patch](incoming-dependency-fixes.patch) remains based on `origin/main` at `079e4aa`; reconcile it into the revision Render builds without overwriting the uncommitted workspace implementation. No new dependency upgrades, Git integration, push, deployment, or production mutation were performed. A local Docker rebuild was unavailable because the Docker daemon is not running. Database type/schema, deployed commit, authenticated operations, frontend CORS, and migrations remain unverified.

## Render and incoming dependency review — 2026-10-27

User confirmed the backend runs on Render and reported a GitHub pull with questionable fixes. Inspected the fetched range `33e505c..079e4aa`: 35 incoming commits change dependency manifests, images and CI actions. Local HEAD remains `33e505c` with the uncommitted workspace implementation; `origin/main` alone advanced. No incoming application-source changes exist in that range.

Confirmed incoming Docker Python/package-path mismatch, four requirements/lock discrepancies, ESLint plugin peer conflicts and TypeScript parser peer conflicts. A bcrypt 5 compatibility reproduction using its length-rejection contract also makes Passlib's legacy probe fail; an actual bcrypt 5 installation was not available. The current local compatible dependency graph was retained. Local Docker now copies `/usr/local` between identical Python images to prevent version-specific copy failures. Added three backend manifest/compatibility regressions, one frontend locked-peer regression, and targeted Dependabot exclusions.

Created [incoming-dependency-fixes.patch](incoming-dependency-fixes.patch), explicitly based on remote commit `079e4aa`. Applied it only to ignored copies of the remote files under `.cache/incoming-review` and verified the correction contracts there. It has not been applied over the dirty workspace or merged into Git history. It restores the known tested frontend lock as a unit; incoming Radix/lucide dependency upgrades are deferred. Incoming Node-image and GitHub Actions changes remain in that artifact and require live build/hosted-CI verification.

Latest focused checks: 21 backend auth/infrastructure/dependency tests passed; 17 frontend unit tests passed with the existing API/date coverage gate; lint, Prettier and Ruff passed; Black formatting API passed the new Python test. The full 157-test backend and 17-scenario browser results below predate these manifest-only corrections. No unnecessary UI/build rerun was required because application source and installed dependencies were unchanged.

Added a Render section to README covering native build/start, direct browser API URL/CORS, explicit database migrations and persistence. The URL and Docker-build evidence were subsequently supplied and public checks succeeded as recorded above; database/deployed revision remain unknown. Earlier automatic approval review returned content-blocked on public Render/bcrypt metadata requests; an offline incoming npm install stopped with ENOTCACHED after reporting peer overrides. No remote merge, push, Render deployment or real database mutation occurred.

Next action: review the correction artifact in a checkout at the specified remote commit, then reconcile the local feature work without resetting it. Confirm the Render deployed revision/runtime/database and upgrade the existing schema before serving the workspace API.

## Workspace upgrade continuation — 2026-10-27

This section supersedes the older readiness metrics below for the current working tree. The earlier Compose and Helm evidence belongs to the preceding readiness pass, not this feature change.

Delivered all five requested upgrades: correct sorting/nullable edits/local deadlines, validated AI drafts with preview/fallback, daily/weekly/monthly recurrence, atomic personal JSON backups, and shared projects with invitation acceptance/assignments/owner-editor-viewer permissions. Rebuilt the dashboard, account screens, editors, task rows and theme. Added frontend API/date unit coverage and CI; strict Kubernetes schema validation and pod-policy checks are also in place.

Final local evidence:

- `backend/.venv/Scripts/python.exe -m pytest` from the root: 157 passed, 77.74% backend coverage (60% threshold). Migration tests preserve existing rows, permit reapplication, reverse the new fields, and roll back interrupted SQLite DDL.
- Ruff checks pass across backend source/tests and migration 010. Black's CLI stalled without completion; Black's `format_file_contents(fast=False)` verified all 50 source/test/new-migration files unchanged using PY311/88-column settings and AST safety, exit 0.
- Frontend build, lint/typecheck and Prettier pass. 16 Node unit tests pass, with 100% lines/functions and 98.31% branches across `api.ts` and `task-dates.ts`; this is not component-wide coverage. 17 Chromium browser tests pass in 33.2s. A focused rerun also passed the enlarged-backup regression using a valid JSON file over the old 2 MB limit.
- All 26 raw Kubernetes resources and CI YAML parse with existing js-yaml. App pod policies match backend UID 1000/frontend UID 1001 and disable privilege escalation/drop all capabilities. Actual kubeconform schemas and latest Helm rendering were not executed locally; downloads failed automatic approval review with internal/content-blocked errors. CI pins kubeconform 0.7.0 with checksum verification and Kubernetes 1.31 schemas, explicitly skipping Dapr Component CRDs.
- Playwright screenshots reviewed at 1440x1000 desktop and 390x844 mobile, light/dark, with a populated dashboard and task form. No horizontal overflow or framework overlay in checked states. The first login console had a missing-favicon 404; added the app icon. No page exceptions during task CRUD. Later interactive MCP commands were blocked by automatic approval review; configured Playwright regression tests completed successfully.

Database upgrade is required **before starting the new API against existing tables**. Back up and stop serving first. From `backend/` with the same explicit DATABASE_URL: use `uv run --locked alembic upgrade head` for versioned databases, or `uv run --locked python -m src.lib.migrate_workspace` for known legacy unversioned create_all databases. The helper refuses versioned/unknown/partial schemas and applies only 010 without stamping old history. New empty databases still initialize on startup. Downgrade discards new project/recurrence/import metadata; a full database backup is the recovery source. See README for complete instructions and the Helm migration-baseline caveat.

Review fixed delayed-save reload races, creation-dialog dismissal during pending requests, hidden mobile navigation focus, mixed-case registered invitations, monthly anchors on unchanged edits, and legacy UTC parsing. Browser imports permit 20 MB and 1000 tasks; existing and previously imported source IDs are skipped, including after deleting an imported copy. Personal backups omit shared tasks/assignments and receive new task IDs/timestamps when imported.

Remaining checks: live providers/OAuth/microphone, PostgreSQL migration/concurrent completion, latest Compose/Helm/kubeconform and real Kubernetes deployment, hosted CI. Gemini's deprecated/broken SDK integration needs its own migration; asynchronous timeout does not bound blocking SDK calls. Raw Dapr statestore and Grafana examples still contain development credential defaults and need Secret configuration before deployment. No push, commit, release, deployment, fabricated attribution or real-database mutation was performed during this continuation. A repository payout increase has not been measured or promised.

Current first action: review the working diff, take the correct database upgrade path, and run hosted/deployment gates when publishing is authorized. The requested implementation and local feature checks are complete.

Date: 2026-10-27
Workspace: `D:\todo-app`
Branch: `main`
Goal: improve the repository-quality score through reproducible setup, CI, tests, documentation, dependency security, Compose, and Kubernetes/Helm hardening.

## Current state

On 2026-10-27, the user supplied the DataFactor evaluation: 73/100, grade B, with an estimated $80 payout. Frontend, backend, and infrastructure dimension scores were 64.7, 67.1, and 58.2; estimated task capacity was about 13. The evaluation is static analysis and does not execute the repository. DataFactor's terms describe scores and payouts as approximate, non-binding estimates, not an offer or commitment.

The user renamed the GitHub repository to `cr33p1ngp4ck3t/Todoer-AI`. A read-only browser check confirmed the old URL redirects to the new one. README and Helm chart source links now use the canonical URL; existing chart paths and Kubernetes resource identifiers retain their compatibility.

Review of the feedback confirmed that frontend unit tests and stronger manifest validation are useful follow-ups. JSON logging is already wired through `backend/src/lib/logging.py` and `backend/src/main.py`; `DATABASE_URL` and `ACCESS_TOKEN_EXPIRE_MINUTES` are already in `backend/.env.example`. Microsoft OAuth remains unimplemented, and `CI` and `PYTHON_DOTENV_DISABLED` are test controls rather than missing runtime secrets. Those findings do not justify adding an unused logging dependency or Microsoft credentials.

The user asked about multiple GitHub accounts. Accounts belonging to one person remain one human contributor. Preserve accurate author attribution; grow the useful history through real behavior changes with regression tests and actual collaboration.

Repository readiness work is implemented. The backend, frontend, dependency, Helm, YAML, shell, static configuration, and live Docker Compose smoke gates pass locally. The storage blocker was resolved by offline VHD compaction and a fresh image build.

The user authorized Docker cleanup with an approximately 20 GiB target and explicitly required preserving Verlio. Cache-only cleanup previously reclaimed 10.597 GB. DiskPart successfully compacted the Windows VHD from 32.54 GiB to 20.69 GiB, restoring 21.18 GiB free on `D:`. After fresh builds and test cleanup, the VHD is 22.42 GiB and `D:` has 19.32 GiB free. Verlio's app/database remain healthy, its worker is running, and its database volume is intact.

Docker/WSL are running after successful compaction. `.cache/docker-compact.log` records DiskPart success. Docker cache retention remains `8GB`; the original host configuration is saved in `.cache/daemon-before-cleanup.json`.

All 109 prepared local commits are complete, with fixes accompanied by regression tests and mechanical formatting separated. The helper resumed after correcting PowerShell's nested-array handling, missing new/deleted-file patch headers, and intermediate whitespace. The working tree was clean when that pass finished. The current continuation updates documentation and chart metadata; no push, tag, or release was created by this agent. `.cache/readiness-commits/completed.json` records the exact commit sequence.

## Completed work

### Documentation and onboarding

- Added root `README.md` with clean-clone setup, local development, test, Compose, configuration, and deployment-limit documentation.
- Added `CONTRIBUTING.md` and root/backend/frontend environment examples.
- Added Docker ignore files and documented persistent-data deletion risk.
- Updated Kubernetes deployment guides to create Secrets from deployment-time environment values instead of committed placeholders.
- Added this handoff and the repository-readiness implementation plan under `docs/`.

### Reproducible dependencies and automation

- Added `backend/pyproject.toml`, `backend/uv.lock`, and a hashed `backend/requirements.txt` export.
- Confirmed the requirements export is deterministic under the exact CI command.
- Updated Next.js and `eslint-config-next` to 16.4.3; retained `frontend/package-lock.json`.
- Added GitHub Actions jobs for backend, frontend, dependency audits, Helm validation, Compose startup, and smoke checks.
- Added Dependabot configuration.
- Added `docker-compose.yml` for frontend, backend, and PostgreSQL.

### Backend quality and security

- Replaced manual root-level debug/test scripts with isolated pytest coverage under `backend/tests/`.
- Added fixtures that use SQLite and block live network/provider access.
- Added regression coverage for authentication, JWT compatibility/tampering/expiry, refresh rotation/revocation, database sessions, readiness, task ownership, validation, dates, and API behavior.
- Replaced vulnerable `python-jose` with `joserfc`; removed `python-jose`, `ecdsa`, and `rsa` from the dependency graph.
- Fixed missing-auth behavior, UUID JWT subjects, ownership checks, invalid task mutations, health/readiness responses, and internal-error disclosure.
- Removed database/session debug output and retained structured JSON logging.
- Fixed SQLAlchemy 2.1 selecting the uninstalled `psycopg` driver for generic PostgreSQL URLs. Application engines and Alembic now select the locked `psycopg2` driver while retaining explicit drivers, credentials, and query parameters; six startup regression cases cover PostgreSQL and SQLite.

### Frontend quality and routing

- Added ESLint, TypeScript checking, Prettier checks, Playwright configuration, and browser tests.
- Added six browser scenarios covering redirects, registration, login retry, OAuth gateway routing, expired sessions, and task CRUD.
- Fixed refresh-token cleanup, registration login, OAuth callback token handling, and browser API URL handling.
- Production images now default to the same-origin `/api` gateway; Compose explicitly keeps `http://localhost:8000` for local browser access.
- Fixed the Helm/raw-Kubernetes gateway contract: nginx strips the external `/api` prefix, while Uvicorn receives `--root-path /api` and trusted forwarded headers so generated OAuth callbacks retain the public prefix/host/scheme.

### Infrastructure and secret hygiene

- Improved both Dockerfiles with locked installs, non-root runtime users, and runtime-native health checks.
- Helm no longer generates placeholder credentials. It requires an existing Secret containing `DATABASE_URL`, `SECRET_KEY`, and `SESSION_SECRET`.
- Removed stale repository URLs and unused/insecure chart values.
- Split frontend and API ingresses so regex rewriting applies only to API traffic.
- Deleted the committed raw `k8s/secrets.yaml`; Minikube/cloud scripts now create Secrets from required environment variables.
- Minikube scripts require a URL-safe hexadecimal PostgreSQL password before embedding it in `DATABASE_URL`.
- Raw Kubernetes frontend runtime configuration was removed because `NEXT_PUBLIC_*` values are build-time inputs.

## Verification evidence

### Backend: passed

- Latest continuation: `backend/.venv/Scripts/python.exe -m pytest`
  - 106 passed
  - 70.36% coverage; threshold is 60%
- Ruff: all checks passed.
- Black CLI: 39 files unchanged; Ruff: all checks passed on the committed source/test state.
- `pip-audit --disable-pip --require-hashes`: no known vulnerabilities.
- Dependency residue scan: no `python-jose`, `ecdsa`, or `rsa` entries.
- The current backend virtual environment still runs Python 3.12.13.

### Frontend: passed

- `npm run format:check`: passed.
- `npm run lint`: passed with zero warnings.
- `npm run typecheck`: passed.
- `npm run build`: passed on Next.js 16.4.3.
- `npm test`: 6/6 Playwright scenarios passed.
- `npm audit --omit=dev --audit-level=high`: zero vulnerabilities.

### Dependencies and static infrastructure: passed

- uv lock export reproduces `backend/requirements.txt` byte-for-byte under the CI command.
- `docker compose config --quiet`: passed with disposable environment values.
- Helm 3.17.3 `lint --strict` and `template`: passed.
- Rendered Helm assertions passed for the API rewrite, FastAPI root path, external Secret, and absence of generated placeholder Secrets/runtime frontend config.
- Every raw `k8s/*.yaml` document parsed offline and contains `apiVersion`, `kind`, and `metadata.name`.
- All three deployment scripts pass Bash syntax after normalizing Windows working-tree line endings.
- `git diff --check`: passed (line-ending conversion warnings only).
- Final review found no remaining Critical or Important issue after the routing and setup-script fixes.

## Blocked or unverified

### Live Compose smoke test: passed after compaction

Fresh `--no-cache` builds completed without the earlier storage corruption. A runtime assert confirmed nonempty `/etc/passwd` and `/etc/group`, the non-root user, and standard-library imports. Live startup exposed and then verified the PostgreSQL-driver fix described above.

Verlio occupies port 3000 and a concurrently started ClawGuard backend occupies 8000. The ignored `.cache/compose-readiness-ports.yml` maps this disposable frontend to 3001 and backend to 8001. `NEXT_PUBLIC_API_URL`, `FRONTEND_URL`, and `CORS_ORIGINS` were set accordingly. Repository default ports were preserved.

- `docker compose -p todo-readiness-check -f docker-compose.yml -f .cache/compose-readiness-ports.yml up --no-build --wait --wait-timeout 240`: all three services healthy.
- `curl.exe --fail http://localhost:8001/health`: HTTP 200, `{"status":"healthy"}`.
- `curl.exe --fail http://localhost:3001/`: HTTP 200.
- The unchanged `scripts/smoke_test.py` was piped into `docker compose ... exec -T backend python -`, keeping its internal `localhost:8000` target scoped to the disposable backend. Registration, login, task CRUD, and refresh passed.
- `docker compose ... down --volumes --remove-orphans --rmi local`: disposable containers, network, database volume, and images removed.
- Post-cleanup inspection: Verlio app/database healthy, worker running, database volume present.

Historical storage failure evidence follows; it is no longer a current blocker.

Docker Desktop uses a relocated data VHD at:

`D:\DevData\relocated-2026-10-23\DockerDisk\docker_data.vhdx`

Observed host state:

- The VHD is 32.54 GiB before compaction. The filesystem inside it exposes roughly 1 TiB capacity and uses 18.1 GiB after cleanup.
- Drive `D:` now has 9.66 GiB free. It previously fell as low as 0.29 GiB.
- Build cache fell from 23.07 GB to 12.47 GB; 10.597 GB was reclaimed through cache-only pruning. Images, containers, and volumes were not pruned.
- Docker's global build-cache garbage collection was configured with `defaultKeepStorage: "20GB"`, contributing to the accumulation. Retention is now set to `8GB`.
- The VHD expanded with build data and retained its high-water file size. `fsutil sparse queryflag` reported it is not sparse. `fstrim` succeeded, but the Windows file size did not shrink; offline compaction is the remaining host cleanup step.
- Docker logged BuildKit `SIGBUS`, WSL `/dev/sdd` attach failures, and containerd metadata becoming read-only.
- Both project images completed their build once, and PostgreSQL reached healthy during a later `--no-build` startup.
- The exported backend image was corrupted by Docker storage: `/etc/passwd` and `/etc/group` were zero bytes and Python standard-library imports failed.
- After the reported bootstrap error, Docker Desktop 4.96.3 / Engine 29.9.2 recovered without a reset. `wsl --list --verbose` showed `docker-desktop` running, and `lsblk` showed `/dev/sdd` mounted as the Docker Desktop root plus `/dev/sdg` mounted as the data disk.
- The `componentsVersion.json` warning is not the actionable failure: the file is still absent while the daemon is healthy. The decisive risk remains exhausted host capacity and the earlier read-only/SIGBUS evidence.

The disposable `todo-readiness-check` containers, network, volume, project images, and diagnostic base-image tag were removed. Workspace download/build caches were also removed. No global Docker prune or data reset was performed.

The formerly blocked checks have now completed on the isolated ports documented above.

### External checks not performed

- Hosted GitHub Actions have not run because nothing was pushed.
- No real Kubernetes cluster installation was attempted.
- The user-provided evaluation reports 73/B and a non-binding $80 estimate. The feedback was reviewed against the code; no new scoring run was requested.
- No release/tag was created.

## First actions for the next chat

The host/storage, live Compose checks, and focused local commits are complete. Further readiness work should focus on meaningful frontend API-client regression tests and validation of rendered Kubernetes manifests. These checks have not been added during the payout-research continuation. Review local changes before publishing. Hosted CI and a real Kubernetes deployment remain unverified; do not push, tag, or publish without further user instructions.

### Completed continuation recipe (retain for reproduction)

1. Compaction completed; `.cache/docker-compact.log` records success. Preserve Verlio's images, containers, and database volume.
2. Restart Docker Desktop, confirm `docker info` succeeds, and verify all three Verlio containers are present and the app/database are healthy. Check free space before any rebuild; 10 GiB free is a safer target.
3. Rebuild from healthy storage; do not trust the earlier corrupted cache/image:

   ```powershell
   cd D:\todo-app
   $env:POSTGRES_PASSWORD = '0123456789abcdef0123456789abcdef'
   $env:SECRET_KEY = 'compose-validation-jwt-secret-32-bytes'
   $env:SESSION_SECRET = 'compose-validation-session-32-bytes'
   $env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
   $env:FRONTEND_URL = 'http://localhost:3000'
   $env:CORS_ORIGINS = 'http://localhost:3000'
   docker compose -p todo-readiness-check up --build --wait --wait-timeout 240
   ```

4. If the stack becomes healthy, run:

   ```powershell
   curl.exe --fail http://localhost:8000/health
   curl.exe --fail http://localhost:3000/
   backend/.venv/Scripts/python.exe scripts/smoke_test.py
   ```

5. Always remove the disposable stack afterward, using the same environment variables so Compose can parse:

   ```powershell
   docker compose -p todo-readiness-check down --volumes --remove-orphans
   ```

6. Re-run the documented backend/frontend gates if any source changes are made, then inspect `git diff --check` and the full diff.
7. The worktree was split into focused commits covering these groups:
   - docs/onboarding and reproducible dependency setup
   - backend tests and security/correctness fixes
   - frontend checks, browser regressions, and API gateway fix
   - CI, Compose, Helm, raw Kubernetes, and deployment scripts
8. Push only after review, observe hosted CI, then consider a real `v0.1.0` tag. Do not fabricate prior history, contributors, releases, or tags.

## Known follow-up risks (not blockers for this readiness pass)

- `google-generativeai` is deprecated; migrate separately to `google.genai`.
- Backend tests emit deprecation warnings for class-based Pydantic config and some Passlib APIs.
- Playwright passes but `next start` warns when `output: standalone` is enabled; the Docker runtime correctly uses `node server.js`. Aligning local test startup requires copying standalone static/public assets or a small test launcher and was not added.
- The default npm audit (including development dependencies) still reports moderate Tailwind 3 toolchain findings; the production audit is clean. Tailwind 4 is a separate breaking migration.
- Sustained history and multiple real contributors cannot be repaired cosmetically; continue landing real, tested changes over time.
- The working-tree diff is large and includes broad formatting/lockfile churn, increasing review and merge-conflict risk.
- Verlio shares the Docker data disk and must be preserved. Cache cleanup can slow subsequent rebuilds; cache retention is a garbage-collection target, not a hard limit on total Docker disk size.

## Deliberately skipped

- No Tailwind 4 migration.
- No Gemini SDK migration.
- No Docker global prune/reset or deletion of unrelated volumes/images.
- No push, PR, tag, or release.
- No fabricated maintenance history.
