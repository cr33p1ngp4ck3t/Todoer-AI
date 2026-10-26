# Repository readiness handoff

Date: 2026-10-26
Workspace: `D:\todo-app`
Branch: `main`
Goal: improve the repository-quality score through reproducible setup, CI, tests, documentation, dependency security, Compose, and Kubernetes/Helm hardening.

## Current state

Repository readiness work is implemented. The backend, frontend, dependency, Helm, YAML, shell, static configuration, and live Docker Compose smoke gates pass locally. The storage blocker was resolved by offline VHD compaction and a fresh image build.

The user authorized Docker cleanup with an approximately 20 GiB target and explicitly required preserving Verlio. Cache-only cleanup previously reclaimed 10.597 GB. DiskPart successfully compacted the Windows VHD from 32.54 GiB to 20.69 GiB, restoring 21.18 GiB free on `D:`. After fresh builds and test cleanup, the VHD is 22.42 GiB and `D:` has 19.32 GiB free. Verlio's app/database remain healthy, its worker is running, and its database volume is intact.

Docker/WSL are running after successful compaction. `.cache/docker-compact.log` records DiskPart success. Docker cache retention remains `8GB`; the original host configuration is saved in `.cache/daemon-before-cleanup.json`.

All 109 prepared local commits are complete, with fixes accompanied by regression tests and mechanical formatting separated. The helper resumed after correcting PowerShell's nested-array handling, missing new/deleted-file patch headers, and intermediate whitespace. The working tree is clean. No push, tag, or release was created. `.cache/readiness-commits/completed.json` records the exact commit sequence.

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
- The repository has not been rescored.
- No release/tag was created.

## First actions for the next chat

The host/storage, live Compose checks, and focused local commits are complete. Review the local commits before publishing. Hosted CI, a real Kubernetes deployment, and rescoring remain unverified; do not push, tag, or publish without further user instructions.

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
