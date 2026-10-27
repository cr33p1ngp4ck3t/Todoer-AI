---
id: "26"
title: "Confirm Frontend ESLint Peer Conflicts"
stage: "general"
date: "2026-10-27"
surface: "agent"
model: "GPT-6"
feature: "todoer-workspace"
branch: "main"
user: "cr33p1ngp4ck3t"
command: "verify supplied npm peer warnings"
labels: ["frontend", "eslint", "dependencies", "regression"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - docs/incoming-dependency-review.md
tests:
  - 17 frontend unit tests passed, including locked peer regression
  - Frontend typecheck passed
  - Frontend lint passed
  - Incoming jsx-a11y and React ESLint conflicts reproduced from remote lock
  - Local manifest, lock, installed versions and corrected artifact agree
---

## Prompt

```text
npm warn Could not resolve dependency:
npm warn peer eslint@"^3 || ^4 || ^5 || ^6 || ^7 || ^8 || ^9" from eslint-plugin-jsx-a11y@6.10.2
npm warn node_modules/eslint-config-next/node_modules/eslint-plugin-jsx-a11y
npm warn   eslint-plugin-jsx-a11y@"^6.10.0" from eslint-config-next@16.4.3
npm warn   node_modules/eslint-config-next
npm warn
npm warn Conflicting peer dependency: eslint@9.39.5
npm warn node_modules/eslint
npm warn   peer eslint@"^3 || ^4 || ^5 || ^6 || ^7 || ^8 || ^9" from eslint-plugin-jsx-a11y@6.10.2
npm warn   node_modules/eslint-config-next/node_modules/eslint-plugin-jsx-a11y
npm warn     eslint-plugin-jsx-a11y@"^6.10.0" from eslint-config-next@16.4.3
npm warn     node_modules/eslint-config-next
npm warn ERESOLVE overriding peer dependency
npm warn While resolving: eslint-plugin-react@7.37.5
npm warn Found: eslint@10.13.0
npm warn node_modules/eslint
npm warn   dev eslint@"^10" from the root project
npm warn   9 more (@eslint-community/eslint-utils, eslint-config-next, ...)
```

## Response snapshot

Confirmed the reported jsx-a11y and React peer ranges reject incoming ESLint 10.13.0 and accept local ESLint 9.39.2. The local frontend already uses compatible ESLint ^9 and TypeScript ^5; its manifest, installed versions, and lock agree. The existing correction patch restores that same frontend dependency graph. All 17 frontend unit tests, typechecking, and lint passed. Deployment needs the corrected manifest and lock together; peer override flags do not repair compatibility.

## Outcome

- Impact: Supplied npm warnings tied to the reviewed incoming dependency regression with direct contract proof.
- Tests: Frontend unit suite, typecheck, and lint passed; incoming conflicts reproduced and local/patched graph verified.
- Files: Incoming dependency review and prompt record; application manifests already compatible.
- Next prompts: Reconcile the correction artifact into the build revision and run npm ci with the paired manifest and lock.
- Reflection: Inspect the lock's actual package locations because npm can hoist plugins or nest them under eslint-config-next.

## Evaluation notes (flywheel)

- Failure modes observed: Incoming ESLint 10 exceeds jsx-a11y/React peer ranges; an initial inspection assumed nested local plugin locations and was corrected to enumerate the graph.
- Graders run and results: PASS for 17 unit tests, typecheck, lint, and compatible manifest/lock/installed graph; incompatible incoming peer contracts reproduced.
- Prompt variant: User supplied frontend install warnings after reporting the backend Docker resolution failure.
- Next experiment: Clean installation/build in the corrected deployment revision; no push or production change performed.
