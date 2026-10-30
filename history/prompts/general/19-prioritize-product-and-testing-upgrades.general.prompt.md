---
id: "19"
title: "Prioritize Product and Testing Upgrades"
stage: "general"
date: "2026-10-27"
surface: "agent"
model: "gpt-6.1-sol"
feature: "none"
branch: "main"
user: "cr33p1ngp4ck3t"
command: "recommend upgrades for repository value"
labels: ["product", "testing", "repository-readiness", "data-licensing"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - history/prompts/general/19-prioritize-product-and-testing-upgrades.general.prompt.md
tests:
  - Read-only comparison of task API, service, forms, tests, and feature checklist
---

## Prompt

User messages in order, preserved verbatim:

```text
soo what do you think of possible payout for this repo
```

```text
hmm, how about possible upgrades/features that might put up a front for the increase
```

## Response snapshot

The current defensible payout estimate is the supplied $80 figure, subject to acceptance and a written offer. Recommended prioritizing useful, tested changes rather than predicting an unsupported increase.

Inspected implementation and existing tests. Identified a mismatch between the frontend's oldest-first sort and backend accepted values, omitted updates when clearing edit-form fields, and browser date inputs without timezone offsets being interpreted as UTC. Recommended fixing these with regression tests, adding frontend unit coverage, then considering recurring tasks, reliable AI parsing, export/import, and infrastructure validation.

## Outcome

- Impact: Ranked potential upgrades based on actual implementation and evaluation gaps.
- Tests: Read-only source inspection; candidate issues were not reproduced through runtime tests.
- Files: Added this prompt record; no product behavior changed.
- Next prompts: Select a concrete upgrade or regression fix to implement.
- Reflection: Testable behavior and genuine usage matter more than feature count or cosmetic history.

## Evaluation notes (flywheel)

- Failure modes observed: Historical feature checklist overstates current features, including archived status and batch operations.
- Graders run and results: No external grader or application test suite run for this recommendation.
- Prompt variant: Payout expectations followed by upgrade prioritization.
- Next experiment: Reproduce one observed UI/API mismatch, implement the smallest complete fix with a regression test, then verify relevant gates.
