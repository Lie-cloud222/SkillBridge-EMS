# Maintaining SkillBridge EMS

How the application is kept maintainable as it grows. Each row is a technique,
where it lives, and what problem it prevents.

| Technique | Where | Problem it prevents |
|---|---|---|
| **Layered architecture** (view, form, service, repository, model) | `employees/views.py`, `services/`, `repositories/` | Business rules copied into every view |
| **Reusable decorators** | `employees/decorators.py` | Audit, rate-limit and cache-header code repeated in each view |
| **Split settings** (base, development, production) | `config/settings/` | Debug options or local databases reaching production |
| **Secrets in environment variables** | `.env` (ignored by Git), Render environment | Passwords and keys committed to the repository |
| **Pinned dependencies** | `requirements.txt` | "Works on my machine" installs |
| **Migrations checked in CI** | `python manage.py makemigrations --check` | A model change shipped without its migration |
| **Automated tests** | `employees/tests/` | Regressions when code is changed |
| **Continuous integration** | `.github/workflows/ci.yml` | Broken code reaching `main` |
| **Logging and audit trail** | `LOGGING` in settings, `employees.audit` logger, `logs/app.log` | Problems that cannot be diagnosed; no record of who did what |
| **Request logging middleware** | `employees/middleware/` | Slow pages going unnoticed |
| **Health check endpoint** | `GET /health/` | Silent outages; used by Render and uptime monitors |
| **Caching with signal-based invalidation** | `signals.py`, `EmployeeService` | Stale statistics after changes made outside the service |
| **Management commands** | `employees/management/commands/` | Manual, error-prone setup on each new environment |
| **Deployment checks** | `python manage.py check --deploy` | Insecure production settings |

## Decorators

| Decorator | Runs | Behaviour |
|---|---|---|
| `audit_action` | before and after | Before: logs who tried what. After: logs status and duration. Refusals and errors are logged and re-raised |
| `rate_limit` | before | Counts requests per user/IP; over the limit the view never runs and a 429 is returned |
| `no_store` | after | Adds no-store/private cache headers to responses showing salary |

They are applied to the class-based views with `method_decorator`. Applying them to `dispatch` means
they wrap the permission check, so denied and anonymous attempts are audited too.

## Routine tasks

**Before every commit**

```
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --keepdb
```

**Changing a model:** edit `models.py`, run `makemigrations`, read the generated file, run `migrate`,
run the tests, and commit the model and its migration together.

**Reading the logs:** `Get-Content logs\app.log -Tail 50` locally; the Logs tab on Render in production.
Search for `AUDIT refused` (blocked attempts) and `AUDIT rate-limited` (throttled users).

**Checking the live site:** open `https://<your-service>.onrender.com/health/`.
`{"status": "ok"}` means the app can reach its database; 503 means it cannot.

## Known limits

- The rate limiter and cache use `LocMemCache`, which is per process. Several workers would each keep
  their own counters; a shared cache such as Redis fixes this.
- The health check proves the database answers, not that every feature works.
- CI runs on SQLite while production uses PostgreSQL, so a database-specific bug could pass CI.
