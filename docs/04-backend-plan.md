# 04 — Backend plan (this repo)

> Part of the [project docs](README.md). Work items are larger units of work; each one resolves one or more [GitHub issues](https://github.com/pirrozani/django-api/issues), which hold the detailed steps and acceptance criteria.

Suggested order: BE-00 → BE-01 → BE-02 → BE-03 → BE-04 → BE-05, then the rest.

| ID | Work item | Resolves | Done when |
|---|---|---|---|
| BE-00 | Make the project run locally | [#1](https://github.com/pirrozani/django-api/issues/1), [#2](https://github.com/pirrozani/django-api/issues/2) | `uv run python manage.py check` and `runserver` work on a fresh clone after `uv sync` |
| BE-01 | Dependencies & runtime upgrade | [#4](https://github.com/pirrozani/django-api/issues/4) | Django 5.2 LTS, DRF/drf-spectacular current in `uv.lock`, migrations apply cleanly |
| BE-02 | Environment-driven production settings | [#8](https://github.com/pirrozani/django-api/issues/8), [#5](https://github.com/pirrozani/django-api/issues/5), [#7](https://github.com/pirrozani/django-api/issues/7), [#17](https://github.com/pirrozani/django-api/issues/17) | Runs on SQLite (local) and Postgres (`DATABASE_URL`); `check --deploy` clean with production env vars |
| BE-03 | Authentication for the SPA | [#9](https://github.com/pirrozani/django-api/issues/9) | Token login/logout/me work; public reads; no Basic-auth popup |
| BE-04 | User serializer security | [#3](https://github.com/pirrozani/django-api/issues/3) | No response contains `password`; all stored passwords are hashed |
| BE-05 | API contract v2 | [#10](https://github.com/pirrozani/django-api/issues/10), [#11](https://github.com/pirrozani/django-api/issues/11), [#12](https://github.com/pirrozani/django-api/issues/12), [#13](https://github.com/pirrozani/django-api/issues/13) | Swagger matches [03-api-contract.md](03-api-contract.md); frontend type generation runs cleanly |
| BE-06 | Health endpoint | (new feature) | `GET /api/health/` → 200 `{"status":"ok"}` without auth; used as Render health-check path |
| BE-07 | Tests | [#14](https://github.com/pirrozani/django-api/issues/14) | `uv run python manage.py test` green locally and in CI |
| BE-08 | Lint & formatting | (new tooling) | `ruff check` and `ruff format --check` pass; one dedicated formatting commit |
| BE-09 | DB-agnostic `clear` + `reset_demo` | [#6](https://github.com/pirrozani/django-api/issues/6), [#20](https://github.com/pirrozani/django-api/issues/20) | `reset_demo` works on SQLite and Postgres |
| BE-10 | README | [#14](https://github.com/pirrozani/django-api/issues/14) | README has live links, setup, env vars, demo credentials, architecture |

## Implementation notes

- **ViewSets.** BE-05 is the natural moment to move from `APIView` classes to DRF `ModelViewSet` + `DefaultRouter`. That removes the repeated try/except-404 code and gives pagination, PATCH and consistent errors for free. Nested `users/<id>/blogs/` can be an `@action(detail=True)` on the user viewset.
- **Demo account.** BE-03 adds a `create_demo_user` management command that reads `DEMO_USERNAME`/`DEMO_PASSWORD` and is idempotent. The existing signal in `api/signals.py` creates its token.
- **Health endpoint.** Public, unthrottled, no DB hit by default; `?db=1` runs `SELECT 1`.
- **Schema files.** `schema.yaml`/`schema.json` are committed. Either regenerate them after BE-05 (`uv run python manage.py spectacular --file schema.yaml`, or `/api-sync --write`) or stop committing them and rely on `/api/schema/`.
- **Linting.** `uv add --dev ruff` and configure it in `pyproject.toml` (rules `E`, `F`, `I`, line length 120 to match existing code).
