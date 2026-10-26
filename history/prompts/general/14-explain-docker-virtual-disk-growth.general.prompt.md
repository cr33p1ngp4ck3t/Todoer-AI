---
id: "14"
title: "Explain Docker Virtual Disk Growth"
stage: "general"
date: "2026-10-26"
surface: "agent"
model: "gpt-6.1-sol"
feature: "none"
branch: "main"
user: "cr33p1ngp4ck3t"
command: "Docker storage cleanup"
labels: ["docker", "storage", "cache", "verlio", "handoff"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - docs/repository-readiness-handoff.md
  - C:/Users/anask/.docker/daemon.json
  - .cache/daemon-before-cleanup.json
  - .cache/docker-compact.txt
  - .cache/compact-docker-storage.ps1
tests:
  - Docker system df measured before and after cache cleanup
  - Verlio containers, images, and database volume verified intact
  - Docker filesystem usage measured at 18.1 GiB after cleanup
  - VHD file size, sparse state, host free space, and cache settings inspected
  - Compaction helper syntax checked and exact disk path validated
---

## Prompt

check the reason it went 34 GB was it config or it expande

## Response snapshot

Evidence showed both accumulated cache and VHD growth: Docker had 23.07 GB of build cache and global garbage collection retained 20GB. The VHD exposed roughly 1 TiB capacity and grew to 32.54 GiB on Windows. The file was not sparse and retained its size after deletions. Cache retention was reduced to 8GB with the original configuration saved.

## Outcome

- Impact: Reduced disposable cache while preserving Verlio.
- Tests: Cache reclamation, Docker usage, and Verlio resource checks completed.
- Files: Updated the handoff; lowered cache retention in the host daemon configuration; prepared an ignored compaction helper and saved original configuration.
- Next prompts: Approve the pending Windows UAC prompt, check the compaction log and VHD size, then restart Docker and verify Verlio health.
- Reflection: Docker usage and Windows VHD file size differ; cache cleanup frees guest blocks, but this non-sparse VHD requires compaction to shrink its file.

## Evaluation notes (flywheel)

- Failure modes observed: VHD retained its size after successful fstrim; offline compaction requires administrator access.
- Graders run and results (PASS/FAIL): Cache cleanup PASS; Verlio preservation PASS before temporary shutdown; filesystem usage target PASS; VHD compaction PENDING.
- Prompt variant (if applicable): Docker cleanup continuation
- Next experiment (smallest change to try): Complete the pending administrator compaction and measure the Windows file size.
