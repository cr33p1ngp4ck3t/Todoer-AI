# Contributing

Follow the local setup and quality commands in [README.md](README.md). Use an isolated database for development; automated tests must never require personal credentials or call live providers.

Keep each change focused on one behavior. Include a regression test for bug fixes and tests for meaningful new behavior. Run backend lint/format/tests or frontend lint/typecheck/format/build/browser tests as appropriate before opening a pull request. CI must pass before merging.

Use concise conventional commit messages such as `fix: reject expired refresh tokens` or `test: cover task ownership`. Keep mechanical formatting separate from behavior changes when committing. Do not fabricate authors, dates, or releases.

Do not commit `.env` files, database dumps, access tokens, provider keys, or generated test reports. Document new configuration in the environment examples and README. Update dependency manifests and lockfiles together.
