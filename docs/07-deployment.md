# 07 — Deployment & operations

> Part of the [project docs](README.md). Prerequisites: [#5](https://github.com/pirrozani/django-api/issues/5) and [#7](https://github.com/pirrozani/django-api/issues/7) are done.

| ID | Item | Steps |
|---|---|---|
| OPS-01 | **Neon** database | Create a project + database and copy the connection string (`sslmode=require`). Optionally create a `dev` branch for local use. |
| OPS-02 | **Render** web service | New Web Service from this repo, branch `main`, free plan, region close to the Neon region. Set the env vars from [06-configuration.md](06-configuration.md). Health check path `/api/health/`. |
| OPS-03 | **Seed production data (locally)** | With `DATABASE_URL` pointed at Neon in your shell, run `uv run python manage.py migrate` then `uv run python manage.py reset_demo` (or `populate` + `create_demo_user`). Never commit the Neon URL. |
| OPS-04 | **CI (GitHub Actions)** | Backend: install → `ruff check` → `ruff format --check` → `check --deploy` (dummy prod env) → `test` (Postgres service container). Frontend: install → lint → typecheck → test → build. |
| OPS-05 | **Nightly demo reset** (optional) | Scheduled GitHub Action runs `reset_demo` against Neon with `DATABASE_URL` stored as an Actions secret. Render cron jobs are not free. |
| OPS-06 | **Branching** | `feature/*` → PR into `develop` → PR `develop` → `main` triggers deploys (Render auto-deploy, Cloudflare Workers Builds). |

## Render settings (OPS-02)

- **Build command:** `pip install uv && uv sync --frozen --no-dev && uv run python manage.py collectstatic --noinput && uv run python manage.py migrate --noinput`. A `build.sh` works too. If Render's Python runtime detects `uv.lock` natively, drop `pip install uv`.
- **Start command:** `uv run gunicorn django_api.wsgi:application --bind 0.0.0.0:$PORT --workers 2`
- **Health check path:** `/api/health/`
- **Optional:** commit a `render.yaml` blueprint so the setup is reproducible.

## Post-deploy smoke test

```bash
curl -s https://<backend>.onrender.com/api/health/              # {"status":"ok"}
curl -s https://<backend>.onrender.com/api/blogs/ | head -c 300  # paginated JSON, no auth needed
curl -s -X POST https://<backend>.onrender.com/api/auth/token/ \
     -d username=$DEMO_USERNAME -d password=$DEMO_PASSWORD        # {"token":"..."}
curl -sI -H "Origin: https://<frontend>.<account>.workers.dev" \
     https://<backend>.onrender.com/api/blogs/ | grep -i access-control-allow-origin
```
