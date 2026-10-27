---
id: "18"
title: "Review Evaluation and Data Licensing"
stage: "general"
date: "2026-10-27"
surface: "agent"
model: "gpt-6.1-sol"
feature: "none"
branch: "main"
user: "cr33p1ngp4ck3t"
command: "review evaluation and investigate payouts"
labels: ["repository-readiness", "data-licensing", "branding", "attribution"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - README.md
  - helm/todo-app/Chart.yaml
  - docs/repository-readiness-handoff.md
  - docs/data-licensing-research.md
  - history/prompts/general/18-review-evaluation-and-data-licensing.general.prompt.md
tests:
  - Read-only browser check confirmed the renamed GitHub repository URL
  - Compared evaluation findings with environment examples, logging setup, tests, and CI
  - Reviewed DataFactor case studies, data-partner process, and website terms
  - Searched distinctive payout descriptions for independent corroboration
---

## Prompt

User messages in order, preserved verbatim:

```text
73
B
Overall
github.com/cr33p1ngp4ck3t/todo-app
todo-app
Frontend
22%
Backend
41%
Infra
37%
monorepo · +4 bonus
Source LOC
9,062
Volume
33.2
Mining rank
9· very high
Task capacity
~13
Task capacity estimates how much of this repository’s history could be mined into self-contained engineering tasks: changes that arrive with the tests that prove them. It is one of the inputs to the payout estimate below.

Todoer is a well-organized full-stack monorepo (FastAPI + SQLModel backend, Next.js + TypeScript frontend) built by a single author over about 300 days with 124 commits. CI is unusually mature for a solo project, running lint, format, typecheck, tests with coverage threshold, pip-audit, npm audit, Playwright e2e, and a full Docker Compose smoke test on every PR. Documentation, env handling, and reproducibility are strong; the main gaps are modest test breadth relative to total code, a single human contributor, and a few hardcoded-secret-looking shell snippets that are actually env-var passthroughs in k8s setup scripts rather than literal secrets.
judged by claude-sonnet-5

Buyer fit · what AI-training buyers now measure
✓
Builds & tests at HEADestimated
Test suite (pytest), CI runs it, lockfiles committed, likely to build and test cleanly at HEAD.
△
Task capacity
~13 mineable commits: sellable, but capacity multiplies value; small atomic feature+test commits grow it.
△
Genuine history
Single-author history: genuine, but a thinner mine than a team's back-and-forth.
✓
Self-contained
docker compose / devcontainer present, one command brings the whole thing up in isolation.
✗
Not a demo
The repo name reads as a demo/template/tutorial, and buyers filter these out before looking at quality.
Buyer criteria are evolving: beyond the quality score, buyers now weigh whether a repository installs, builds, and runs its own tests, whether it can be exercised in isolation, and how much genuinely mineable engineering history it holds. These signals are read from the repository’s artifacts. The assessment never executes your code.

Estimated payout
$80
up to $4,800 total per contributor · approximate, non-binding estimate, not an offer
buyer criteria are evolving: the buyer-fit signals also shape final offers
This estimate is reduced because it reads as a demo or template project and its commit history reads as thin. Estimates rise as the repository’s history and framing mature.
What DataFactor estimates it would pay to license this repository as AI training data. Quality drives the number: past a minimum volume, stronger code is worth far more than more code. Its history yields few self-contained, tested changes, though, which holds the estimate back. We learn most from commits where a change arrives with the tests that prove it. Final payout is subject to review and a partnership agreement.

Get in touch about this repository
Frontend · dimensions
33% of repo
64.7 · C
D
Architecture & Robustness
Typed TS with interfaces (TaskCreateProps, TaskUpdate) and layered services/api.ts, but errors handled via console.error + toast rather than structured logging or error tracking
55
B
Test Coverage
Only frontend/tests/app.spec.ts (Playwright) found; test_spec_files=11 total across repo, no frontend unit tests, coverage not enforced for frontend in CI
45
C
Code Cleanliness
Prettier (.prettierrc) and ESLint/typecheck run in CI; no file over 500 LOC (largest chart.tsx=320, TaskForm.tsx=315) but some shadcn ui boilerplate duplication across ui/ components
70
F
Docs & Onboarding
README documents frontend setup, env vars (.env.example), Playwright testing instructions, and repository layout table including frontend/src and frontend/tests
80
I
Security Hygiene
No secrets in frontend source; NEXT_PUBLIC_API_URL documented as public-only, npm audit gate in CI, but no schema validation library evident client-side
65
E
Dependency Health
frontend/package-lock.json committed, Dependabot configured for weekly updates, npm audit run in CI with --audit-level=high
70
H
CI/CD Maturity
.github/workflows/ci.yml runs npm ci, lint, typecheck, format:check, build, Playwright tests, and npm audit on every PR/push
80
K
History & Maintenance
git_stats shows 124 commits over 300 days but only 1 human author and 0 tags/releases, conventional_rate 0.97 suggests disciplined commit messages
55
Backend · dimensions
33% of repo
67.1 · C
D
Architecture & Robustness
Layered backend/src/api, services, models, lib directories; pydantic validation; health endpoint with DB check hides internal errors (test_health.py); logging via logging.getLogger but logging_framework reported null (no structured JSON logging detected by tool) despite README claiming JSON logging
65
B
Test Coverage
pytest with pytest-cov, --cov-fail-under=60 enforced in pyproject.toml; test_source_ratio 1:9 overall, 11 spec files covering health, tasks, auth, mcp_tools, llm_providers, database, models
55
C
Code Cleanliness
ruff+black enforced in CI (uv run ruff check / black --check); no god files over 500 LOC (largest mcp_server.py=386 LOC); pydantic schemas used consistently for input shapes
70
F
Docs & Onboarding
README details backend env vars, local dev with uv, migrations note (Alembic), CONTRIBUTING.md present, docker-compose for full stack, .env.example mostly complete (5 vars missing: ACCESS_TOKEN_EXPIRE_MINUTES, CI, DATABASE_URL, MICROSOFT_CLIENT_ID, PYTHON_DOTENV_DISABLED)
85
I
Security Hygiene
hardcoded_secret_hits=5 are all shell scripts passing $SECRET_KEY/$POSTGRES_PASSWORD env vars into kubectl --from-literal, not literal secrets; pydantic validation at API boundaries; pip-audit and npm audit gate dependencies
60
E
Dependency Health
backend/uv.lock committed, pip-audit run in CI with --require-hashes, Dependabot configured, requirements.txt regenerated and diff-checked in CI workflow
75
H
CI/CD Maturity
ci.yml backend job runs sync, requirements diff check, ruff, black, pytest, pip-audit, plus a separate infrastructure job doing helm lint and docker compose smoke test
85
K
History & Maintenance
124 commits, single author (cr33p1ngp4ck3t), span 300 days, no tags/releases (tag_count=0), conventional commit rate 0.97 indicates disciplined solo maintenance but no team/release signal
55
Infra · dimensions
33% of repo
58.2 · C
D
Architecture & Robustness
docker-compose.yml orchestrates Postgres+API+frontend with health checks per README; Helm chart requires existingSecret rather than generating credentials, showing some separation of config from code
50
C
Code Cleanliness
Helm charts and k8s manifests (17 files) exist alongside app code; no dedicated infra lint beyond helm lint --strict in CI; no IaC-specific linter like tflint found
65
F
Docs & Onboarding
README documents Helm chart usage (helm lint --strict, helm template), DEPLOYMENT.md referenced for cluster specifics, docker compose up --build --wait documented as local-only
75
I
Security Hygiene
Secret.existingSecret pattern in Helm avoids baking credentials in; CI generates ephemeral local .env secrets via python secrets.token_hex for compose smoke test; no policy/security scanner like checkov/tfsec present
55
E
Dependency Health
No terraform_present, infra deps limited to Helm/k8s manifests with no lockfile concept applicable; Dependabot covers app deps only, not infra charts
55
H
CI/CD Maturity
ci.yml infrastructure job runs helm lint --strict, helm template, docker compose config/up/health-check smoke test on every PR
70
K
History & Maintenance
Single author, 124 commits over 300 days, no infra-specific tags or changelog entries found
50
O
IaC Quality
Helm chart validated with helm lint --strict and helm template in CI (plan-like step) but no tfsec/checkov policy scanning, no remote state since no Terraform present (k8s_manifest_count=17, terraform_present=false)
45
```

```text
my repo name was also todo-app, so i changed it to what my URL is: Todoer AI to sound more confident and authentic
```

```text
oh eah and find out how and which companies got the payouts: Highlights: $120K to $2M
Ordinary operating companies licensing data they already had, with headcount, years covered and systems for each.

Software development · Eastern Europe · 2025

$760K

A software agency's client delivery repositories
A development agency licensed about 280 repositories built over a decade of client work, with full commit history and code review threads. An AI data company took the set after anonymization, paying per repository by quality tier.

Headcount
About 180 employees
Years covered
2013 to 2025
Data
About 280 git repositories with pull requests and code reviews
Buyer
An AI data company
Structure
Non-exclusive license, paid per repository
Travel technology · Latin America · 2025

$240K

A travel booking platform's code and history
A travel booking company licensed its search, booking and payments services together with seven years of commit history. The buyer valued the long record of real production changes more than the code at head.

Headcount
About 450 employees
Years covered
2017 to 2024
Data
Platform monorepo, about 30 services, issue tracker
Buyer
A frontier AI lab
Structure
Non-exclusive license, paid on delivery
Customer support · Central Europe · 2025

$380K

A contact center's German and French call recordings
A multilingual contact center licensed about 15,000 hours of recorded support calls with agent notes, after names, numbers and account details were removed. Non-English conversational audio is scarce, which kept the price per hour high.

Headcount
About 700 agents
Years covered
2018 to 2025
Data
Call recordings, transcripts and ticket outcomes
Buyer
A frontier AI lab
Structure
Exclusive license for AI training, two payments
Education technology · North America · 2025

$590K

A language-learning company's recorded lessons
A language-learning company licensed recorded one-to-one conversation lessons with transcripts and the tutor's corrections, with learner identities removed. Pairing each lesson with its corrections made the set useful for evaluation as well as training.

Headcount
About 200 employees, plus contract tutors
Years covered
2017 to 2025
Data
Lesson recordings, transcripts and tutor corrections
Buyer
Several AI developers
Structure
Non-exclusive licenses to three buyers
Professional services · Texas · 2025

$350K

A services firm's email, chat and ticket archive
A consulting firm of about 300 people licensed nine years of email, team chat and support tickets, de-identified before anything left its systems. The buyer wanted long, real threads of people coordinating work across teams.

Headcount
About 300 employees
Years covered
2016 to 2025
Data
Email, team chat, ticketing and shared documents
Buyer
An AI data company
Structure
One-time license, paid upfront
Architecture · Colorado · 2026

$690K

An architecture practice's drawing library
An architecture firm licensed about 35,000 drawings and models across residential and commercial projects, with client names and site addresses stripped from title blocks. The revision history between drafts added to the value.

Headcount
About 110 employees
Years covered
2010 to 2025
Data
CAD drawings, BIM models and revisions
Buyer
A frontier AI lab
Structure
Non-exclusive license, paid per file
Games · Western Europe · 2025

$480K

A game studio's shipped titles
An independent studio licensed the source code, build scripts and art assets of four shipped games, including the history of how each one was built. Complete, working projects of this kind are rare in training data.

Headcount
About 60 employees
Years covered
2013 to 2024
Data
Engine and gameplay code, assets and build history
Buyer
An AI data company
Structure
Non-exclusive license, paid on delivery
Financial technology · New York · 2026

$1.2M

A fintech company's monorepo and review history
A payments company licensed its main monorepo with eleven years of pull requests and the review discussion on each one. Secrets, customer data and internal hostnames were removed before delivery.

Headcount
About 450 employees
Years covered
2014 to 2025
Data
Monorepo, pull requests, code reviews and CI history
Buyer
A frontier AI lab
Structure
Exclusive for one year, then non-exclusive
```

```text
well they obfuscated the names, telling general idea
```

```text
since they have the idea of more contributers = more money i have personally 3-4 github accounts
```

```text
how about i commit with different account
```

## Response snapshot

Multiple accounts operated by one person remain one human contributor. Switching accounts to imply additional contributors would misrepresent the history and does not add genuine collaboration. Recommended real, tested changes and actual contributors instead.

Verified that GitHub redirects the old URL to Todoer-AI and updated README and Helm chart links. Reviewed DataFactor's anonymous case studies and licensing flow. The site withholds seller/buyer names and rounds figures; searches did not establish independent payment confirmation. Recorded that the user's 73/B score and $80 payout are non-binding estimates.

## Outcome

- Impact: Accurate repository branding, evaluation status, licensing research, and contributor guidance.
- Tests: Read-only source inspection and browser research; application tests were not rerun for documentation and chart metadata.
- Files: README, Helm chart metadata, readiness handoff, research note, and this prompt record.
- Next prompts: A concrete regression fix or frontend/infrastructure testing improvement.
- Reflection: Preserve genuine attribution and distinguish published payout claims from independently verified payments.

## Evaluation notes (flywheel)

- Failure modes observed: Static evaluation missed existing JSON logging and documented backend variables; original handoff overstated the payout as eligibility.
- Graders run and results: No fresh external grader or payout application.
- Prompt variant: Evaluation feedback followed by branding, research, and contributor-count questions.
- Next experiment: Add regression coverage for a real bug or meaningful behavior, paired with its implementation.
