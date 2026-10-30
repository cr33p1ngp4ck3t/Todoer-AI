# Neon agent setup and task-loading repair

Setup completed on 2026-10-30 following the [official agent setup](https://neon.com/prompts/agent-setup.md) and [Neon skill](https://neon.com/.well-known/agent-skills/neon/SKILL.md).

## Agent configuration

- Neon CLI 8.14.0 is installed globally and browser sign-in completed.
- The global Codex `neon-postgres` plugin 2.3.0 includes nine Neon skills and the OAuth MCP server at `https://mcp.neon.tech/mcp`. Restart Codex to load it; MCP OAuth may request separate consent on first use.
- Existing MCP servers, plugins and other Codex configuration entries were preserved, verified with secret-free checksums. No duplicate standalone Neon MCP entry was added.
- The ignored `.neon` file links this workspace to its existing database project. Linking used `--no-env-pull --no-config`; existing env files, database URLs, ORM, driver and application auth remain in use.

The installation command was:

```sh
neon plugins --global --agent codex -y
```

## Production repair

The published frontend, `https://todoerai.vercel.app`, already passed Render's CORS allowlist. The task query failed because the Neon database was at Alembic revision `009_add_due_date` and lacked `project_id`, `assignee_id`, `recurrence`, `recurrence_timezone`, `recurrence_day`, `recurrence_spawned` and `predecessor_id`. Startup's `create_all` created workspace tables but did not alter the existing task table.

The existing additive `010_workspace` migration was tested on a temporary branch using the production Docker image and a direct database connection. Validation reproduced the task failure before migration, then checked successful task queries, readiness, trusted/untrusted CORS origins, migration reapplication and unchanged legacy-row fingerprints. The validated migration was applied to production with a five-second lock timeout and a 60-second statement timeout. The production Alembic revision and all seven columns were verified afterward; the user confirmed tasks load at the published frontend. The temporary validation branch was then deleted.

For future repairs, preserve a backup before migrating. Restoring a backup wholesale would discard later writes; use a reviewed recovery procedure if needed. Keep account, project, branch and backup identifiers in private operational records.

The API's CORS middleware now surrounds its server-error middleware, so allowed browser origins can read generic error responses and `X-Request-ID`. The exact-origin allowlist remains enforced. Backend regression tests passed: **196 tests, 82.22% coverage**. The backend Docker build and isolated Neon migration/API checks passed.

For future migrations, retain the application's pooled connection and use the same database's direct connection for migration tools. Test against an isolated branch before production. Never run `neon env pull` over an existing application env file without reviewing the intended changes.
