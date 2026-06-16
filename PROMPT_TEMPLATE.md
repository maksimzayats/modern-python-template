# modern-python-template Project Creation Prompt

Use this after creating your own repository from the modern-python-template
template and opening that new repository in an LLM coding agent.

Before pasting the prompt below into the agent, replace the bracketed values and
remove any removable capability bullets you do not want. The edited prompt is
the setup input for your generated project.

```text
You are an LLM coding agent working in a newly created repository that was
created from the modern-python-template template.

Repository: [absolute path to my new repository]

Generated project identity:
- Project name: [Human-readable project name]
- Distribution name: [python-distribution-name]
- Python package name: [python_package_name]
- Current template import root: modern_python_template
- Short description: [one-sentence product description]
- Repository URL: [https://github.com/org/repo or none]
- Local browser origins: [http://localhost:3000, http://localhost:8000, ...]

Goal:
Create the generated project in this repository. Treat my edited prompt as the
setup source of truth. Do not use a separate interactive setup flow. Keep every
capability explicitly listed below and delete every removable capability that is
not listed.

Mandatory modern-python-template Base:
- Keep FastAPI delivery.
- Keep Django ORM, migrations, and admin.
- Keep dependency injection with diwire.
- Keep architecture guardrails.
- Keep tests, linting, formatting, and strict typing.

Removable capabilities to keep:
- Celery background tasks and beat scheduler.
- Authentication endpoints, JWT access tokens, and refresh sessions.
- Request throttling and rate limiting.
- Storage backends: local filesystem, local MinIO, and remote S3-compatible storage.
- Observability with Logfire/OpenTelemetry.
- MkDocs documentation site and docs publishing.
- Docker services: PostgreSQL, PgBouncer, Redis, and MinIO.
- GitHub workflows for CI and docs publishing.
- Example domains: health, user, and authentication.

Implementation rules:
- Start with `git status --short` and preserve existing user changes.
- Rename the project metadata, package imports, Docker/Compose names, settings,
  docs, tests, and examples to match the generated project identity.
- Write development `.env` values from the kept capabilities. Keep committed
  environment examples current and do not commit secrets.
- For every removable capability omitted from this prompt, delete its code,
  tests, docs, dependencies, settings, environment variables, Docker services,
  Make targets, and workflows. Do not leave dormant configuration behind.
- Remove template-only setup artifacts from the generated project unless I ask
  to keep them: `PROMPT_TEMPLATE.md`, `CONTEXT.md`, and `docs/adr/`.
- Keep controller, use-case/service, transaction, exception-contract, model, and
  dependency-injection conventions intact.
- Run `uv lock` after dependency changes.
- Validate with the narrowest meaningful checks, preferring `make lint` and
  `make test` when practical.
- Finish by summarizing changed files, removed capabilities, and exact checks
  run.
```
