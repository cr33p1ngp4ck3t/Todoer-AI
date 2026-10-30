---
id: 28
title: Fix Vercel Frontend Build
stage: general
date: 2026-10-30
surface: agent
model: GitHub Copilot
feature: todoer-workspace
branch: main
user: cr33p1ngp4ck3t
command: diagnose and repair Vercel frontend build
labels: [frontend, vercel, build, lockfile, typescript]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/package-lock.json
  - frontend/src/services/api.ts
tests:
  - npm ci passed
  - npm run build passed
---

## Prompt

```text
Cloning github.com/cr33p1ngp4ck3t/Todoer-AI (Branch: main, Commit: d12ed2d)
Cloning completed: 602.000ms
Restored build cache from previous deployment (9NGJb9ftWUfr1zvd87fKLoRwKTjj)
Running "vercel build"
Vercel CLI 65.4.0
Installing dependencies...
npm warn Unknown env config "cache-dir". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
up to date in 4s
239 packages are looking for funding
  run `npm fund` for details
npm warn install-scripts 1 package has install scripts not yet covered by allowScripts:
npm warn install-scripts   unrs-resolver@1.11.1 (postinstall: napi-postinstall unrs-resolver 1.11.1 check)
npm warn install-scripts
npm warn install-scripts Run `npm install-scripts ls` to review, or `npm install-scripts approve <pkg>` to allow.
Detected Next.js version: 16.4.3
```

## Response snapshot

The supplied Vercel output ends before showing a build failure or success. Local validation exposed two actionable issues: the frontend package lock was out of sync with package.json, so npm ci failed; after synchronizing it, the production build found an invalid Headers() call in the current API client edit. Updated the lockfile, changed the call to new Headers(), and confirmed a clean install and production build succeed.

## Outcome

- ✅ Impact: Frontend dependency installation is reproducible and Next.js type-check/build passes.
- 🧪 Tests: npm ci and npm run build passed. npm ci still warns that the unrs-resolver install script is not approved by local npm policy.
- 📁 Files: Updated frontend/package-lock.json and corrected the keep-alive HEAD request headers in frontend/src/services/api.ts.
- 🔁 Next prompts: Redeploy the corrected revision; inspect the full Vercel log if the deployment still fails.
- 🧠 Reflection: The excerpt's npm warnings did not identify the blockers; reproducing the clean install and production build exposed them.

## Evaluation notes (flywheel)

- Failure modes observed: package.json/lock mismatch blocked npm ci; Headers was treated as a callable function, failing TypeScript.
- Graders run and results (PASS/FAIL): PASS - npm ci; PASS - npm run build.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Deploy the updated lockfile and API client change and inspect the complete build log.
