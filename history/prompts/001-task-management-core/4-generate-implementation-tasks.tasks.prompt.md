---
id: 4
title: Generate Implementation Tasks
stage: tasks
date: 2025-12-30
surface: agent
model: claude-opus-4-5-20251101
feature: 001-task-management-core
branch: 001-task-management-core
user: current-user
command: /sp.tasks
labels: ["tasks", "todo-system", "phase-ii", "implementation"]
links:
  spec: specs/001-task-management-core/spec.md
  plan: specs/001-task-management-core/plan.md
  tasks: specs/001-task-management-core/tasks.md
  ticket: null
  adr: null
  pr: null
files_yaml:
  - specs/001-task-management-core/tasks.md
tests_yaml: []
---

# Prompt
/sp.tasks
(Extracting tasks from spec, plan, data-model, and contracts)

# Response
I've generated the complete task list for the Core Task Management feature (Phase II). The tasks are organized into 7 phases, starting with Setup and Foundational infrastructure, followed by 4 phases dedicated to individual User Stories (CRUD, Completion, Organization, Discovery), and a final Polish phase.

# Outcome
- Total task count: 42
- Task count per user story:
  - US1 (MVP Lifecycle): 9 tasks
  - US2 (Completion): 5 tasks
  - US3 (Organization): 7 tasks
  - US4 (Discovery): 5 tasks
- Parallel opportunities identified for 12 tasks (marked [P]).
- Independent test criteria defined for each story phase.
- MVP scope clearly marked as Phase 1 through 3.
- All tasks strictly follow the `[ID] [P?] [Story] Description` format with file paths.
