---
id: "11"
title: "Diagnose Docker WSL Storage"
stage: "general"
date: "2026-10-26"
surface: "agent"
model: "gpt-5"
feature: "none"
branch: "main"
user: "cr33p1ngp4ck3t"
command: "diagnose DockerDesktop/Wsl/ExecError"
labels: ["docker", "wsl", "storage", "repository-readiness", "handoff"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - docs/repository-readiness-handoff.md
  - history/prompts/general/11-diagnose-docker-wsl-storage.general.prompt.md
tests:
  - Docker Desktop daemon responded to docker version and docker info
  - WSL listed docker-desktop as running
  - Docker block devices and mounts inspected read-only
  - Host free space and Docker build-cache usage measured
  - Docker logs checked for WSL attach, SIGBUS, and read-only filesystem evidence
---

## Prompt

running wslexec: An error occurred while running the command. DockerDesktop/Wsl/ExecError: c:\windows\system32\wsl.exe -d docker-desktop -u root -e wsl-bootstrap run --base-image <home>/appdata/local/programs/dockerdesktop/resources/docker-desktop.iso --cli-iso <home>/appdata/local/programs/dockerdesktop/resources/wsl/docker-wsl-cli.iso --data-disk 1b94eced-4d9d-c84d-9081-46b5e40a1fb5: exit status 1 (stderr: [2026-10-26T12:58:44.789489963Z][wsl-bootstrap.version][W] failed to read component versions: open /opt/docker-desktop/componentsVersion.json: no such file or directory
[2026-10-26T12:58:44.791807027Z][wsl-bootstrap] provisioning data via data disk with id: 1b94eced-4d9d-c84d-9081-46b5e40a1fb5
[2026-10-26T12:58:44.792902408Z][wsl-bootstrap] pre-bootstrap complete
[2026-10-26T12:58:44.855501426Z][wsl-bootstrap][W] unprovisioning data: unmounting disk: invalid argument
Error: preparing environment: provisioning data: preparing block device /dev/sdd: detecting file system: device /dev/sdd is not usable: no such device or address
[2026-10-26T12:58:44.860828507Z][wsl-bootstrap][F] preparing environment: provisioning data: preparing block device /dev/sdd: detecting file system: device /dev/sdd is not usable: no such device or address
[main.main()
[	linuxkit/pkg/desktop/wsl-bootstrap/main.go:66 +0x111
, stdout: , wslErrorCode: DockerDesktop/Wsl/ExecError)

## Response snapshot

Diagnosed the failure as a transient Docker Desktop data-disk attachment symptom occurring alongside severe host storage pressure, not a repository or Compose defect. Docker subsequently recovered, but `D:` still had only 0.29 GiB free and Docker held 23.07 GB of build cache (15.95 GB reclaimable), so the live Compose rebuild remained unsafe and unverified. Updated the durable handoff without deleting Docker data.

## Outcome

- ✅ Impact: Preserved the recovered Docker state and documented the exact safe continuation path.
- 🧪 Tests: Docker/WSL status, mounts, free space, cache usage, and diagnostic logs were inspected read-only.
- 📁 Files: Updated the repository-readiness handoff and added this prompt-history record.
- 🔁 Next prompts: Free host capacity, cleanly restart WSL/Docker, then rebuild and run the three Compose smoke checks.
- 🧠 Reflection: The missing component-version file is incidental while Docker is running; near-zero host capacity plus SIGBUS/read-only logs is the actionable evidence.

## Evaluation notes (flywheel)

- Failure modes observed: WSL `/dev/sdd` attachment failure, Docker metadata becoming read-only, BuildKit SIGBUS, and only 0.29 GiB free on the relocated Docker data drive.
- Graders run and results (PASS/FAIL): Docker daemon/status PASS after recovery; storage headroom FAIL; live Compose smoke BLOCKED.
- Prompt variant (if applicable): Docker error continuation
- Next experiment (smallest change to try): Restore at least several gigabytes of `D:` capacity, restart Docker cleanly, and rerun the isolated Compose smoke test.
