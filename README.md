# django-api

Django REST Framework API for authors and blogs. It is the backend for a [React SPA](https://django-blog-frontend.pirrozani.workers.dev) that lives in a separate frontend repository (React + Vite + TypeScript, deployed on Cloudflare Workers). Reads are public; writes need a token, and an account can only change its own author and blogs.

Built with Django 5.2 LTS, DRF, drf-spectacular, Gunicorn and WhiteNoise, managed with [uv](https://docs.astral.sh/uv/).

## Live links

| What | URL |
|---|---|
| App (frontend) | https://django-blog-frontend.pirrozani.workers.dev |
| API | https://django-api-c2hh.onrender.com/api/ |
| Swagger UI | https://django-api-c2hh.onrender.com/api/schema/swagger-ui/ |
| Health | https://django-api-c2hh.onrender.com/api/health/ |

The free Render instance sleeps when idle, so the first request can take up to a minute.

## Demo credentials

A shared demo account (username from `DEMO_USERNAME`, default `demo`) is created by `reset_demo` or `create_demo_user`. Its password comes from `DEMO_PASSWORD` and is never committed. Locally you pick it yourself (see [Local setup](#local-setup)). The demo account can create blogs and edit or delete only those; seeded authors and blogs are read-only for it.

## Architecture

```mermaid
flowchart LR
    B[Browser] -->|HTTPS, static files| CF[Cloudflare Workers<br/>static assets<br/>React SPA]
    B -->|HTTPS, JSON + Token header| R[Render Web Service free<br/>Django + DRF + Gunicorn]
    R -->|TLS, DATABASE_URL| N[(Neon Postgres free)]
    GH1[GitHub: frontend repo] -->|push to main| CF
    GH2[GitHub: django-api] -->|push to main| R
```

Why each piece was chosen, and the free-tier trade-offs, are in [docs/01-architecture.md](docs/01-architecture.md).

| Path | What's there |
|---|---|
| `django_api/` | Project settings, URLs, management commands (`populate`, `clear`, `reset_demo`, `create_demo_user`) |
| `api/models/` | `User` (an author, not a login account) and `Blog` |
| `api/views/`, `api/serializers/` | Viewsets and serializers; every endpoint has `@extend_schema` |
| `api/tests/` | Test suite |
| `docs/` | Architecture, API contract, plans, configuration, deployment |

Login accounts are Django's `auth.User` with DRF token authentication. An author can be linked to one login account.

## Local setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git. uv installs Python 3.12 (pinned in `.python-version`) if it's missing.

```bash
git clone https://github.com/pirrozani/django-api.git
cd django-api
cp .env.example .env              # local defaults: DEBUG=True, SQLite, localhost allowed
```

Open `.env` and uncomment `DEMO_PASSWORD=`, giving it any password you like. Then:

```bash
uv sync                                       # creates .venv/ from uv.lock
uv run python manage.py migrate
uv run python manage.py reset_demo            # 30 authors, 80 blogs, plus the demo login and its author
uv run python manage.py runserver
```

Check it works:

```bash
curl -s http://127.0.0.1:8000/api/health/                 # {"status":"ok"}
curl -s http://127.0.0.1:8000/api/blogs/ | head -c 300    # paginated JSON, no login needed
curl -s -X POST http://127.0.0.1:8000/api/auth/token/ \
     -d username=demo -d password=<your DEMO_PASSWORD>     # {"token":"..."}
```

Swagger UI is at http://127.0.0.1:8000/api/schema/swagger-ui/. Click **Authorize** and enter `Token <your token>` to try writes.

### Other data commands

```bash
uv run python manage.py populate --users 30 --articles 80   # add fake authors and blogs
uv run python manage.py clear                               # delete all authors and blogs (demo author too)
uv run python manage.py create_demo_user                    # create or refresh the demo login only
uv run python manage.py createsuperuser                     # staff account for /admin/
```

### Postgres instead of SQLite

SQLite is used when `DATABASE_URL` is unset. To match production, run Postgres in Docker and set the URL in `.env`:

```bash
docker run -d --name django-api-db -p 5432:5432 \
  -e POSTGRES_USER=django -e POSTGRES_PASSWORD=django -e POSTGRES_DB=django_api postgres:17
# .env: DATABASE_URL=postgresql://django:django@localhost:5432/django_api
```

## Environment variables

`.env.example` lists every variable with comments; [docs/06-configuration.md](docs/06-configuration.md) gives local and production values for both apps. The ones you're most likely to touch:

| Variable | Local default | Purpose |
|---|---|---|
| `SECRET_KEY` | `change-me` | Only accepted with `DEBUG=True`; production needs a 50+ character key |
| `DEBUG` | `True` | `False` in production (enables HTTPS redirect, HSTS, secure cookies) |
| `DATABASE_URL` | unset (SQLite) | Postgres connection string |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Frontend origins allowed to call the API |
| `DEMO_PASSWORD` | unset | Password for the demo login; `reset_demo` fails without it |

Never commit `.env` or a real key. Production values live in Render's environment settings.

## Tests and lint

```bash
uv run python manage.py test           # whole suite
uv run python manage.py test api.tests.test_crud   # one module
uv run python manage.py check --deploy # production settings check (needs a production-like env)
```

The suite runs on whichever database `DATABASE_URL` points at, so run it once with it unset (SQLite) and once against Postgres. A process environment variable overrides `.env`, so `DATABASE_URL=sqlite:///db.sqlite3 uv run python manage.py test` forces SQLite without editing the file.

Code style: single quotes, class-based views, `@extend_schema` on every endpoint. Lint with `uvx ruff check .` and `uvx ruff format --check .` (ruff isn't a project dependency yet, see [#52](https://github.com/pirrozani/django-api/issues/52); CI is planned as OPS-04).

## Deployment

`main` deploys: Render builds the backend from it and Cloudflare Workers builds the frontend from its own repo. The database is Neon Postgres. Render's free tier has no shell, so migrations run in the build command and demo data is seeded from your machine with `DATABASE_URL` pointed at Neon.

- Build: `uv sync --frozen --no-dev && uv run python manage.py collectstatic --noinput && uv run python manage.py migrate --noinput`
- Start: `uv run gunicorn django_api.wsgi:application --bind 0.0.0.0:$PORT --workers 2`
- Health check path: `/api/health/`

Full steps, the smoke test and how to verify `NUM_PROXIES` are in [docs/07-deployment.md](docs/07-deployment.md).

## Contributing

Work is tracked in [GitHub issues](https://github.com/pirrozani/django-api/issues). Branch from `develop` as `feature/<N>-<slug>`, open the PR into `develop`, and release `develop` into `main`. Every API change updates [docs/03-api-contract.md](docs/03-api-contract.md) in the same PR. Add dependencies with `uv add <package>`; never edit `uv.lock` by hand.

## Docs

Everything else is in [docs/](docs/README.md): architecture, the API contract the frontend builds against, backend and frontend plans, configuration, deployment and roadmap.
