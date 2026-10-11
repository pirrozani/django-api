# 07 — Deployment & operations

> Part of the [project docs](README.md). Prerequisites: [#5](https://github.com/pirrozani/django-api/issues/5) and [#7](https://github.com/pirrozani/django-api/issues/7) are done.

| ID | Item | Steps |
|---|---|---|
| OPS-01 | **Neon** database | Create a project + database and copy the connection string (`sslmode=require`). Optionally create a `dev` branch for local use. |
| OPS-02 | **Render** web service | New Web Service from this repo, branch `main`, free plan, region close to the Neon region. Set the env vars from [06-configuration.md](06-configuration.md), including `NUM_PROXIES` for the login throttle. Health check path `/api/health/`. |
| OPS-03 | **Seed production data (locally)** | With `DATABASE_URL` pointed at Neon in your shell, run `uv run python manage.py migrate` then `uv run python manage.py reset_demo` (or `populate` + `create_demo_user`). Both need `DEMO_PASSWORD` in that shell, and that value becomes the production demo password (re-running with a new one revokes the old token). Never commit the Neon URL. |
| OPS-04 | **CI (GitHub Actions)** | Backend: install → `ruff check` → `ruff format --check` → `check --deploy` (dummy prod env) → `test` (Postgres service container). Frontend: install → lint → typecheck → test → build. |
| OPS-05 | **Nightly demo reset** (optional) | Scheduled GitHub Action runs `reset_demo` against Neon with `DATABASE_URL`, `DEMO_USERNAME` and `DEMO_PASSWORD` stored as Actions secrets. Without `DEMO_PASSWORD` the whole reset rolls back. Render cron jobs are not free. |
| OPS-06 | **Branching** | `feature/*` → PR into `develop` → PR `develop` → `main` triggers deploys (Render auto-deploy, Cloudflare Workers Builds). |

## Render settings (OPS-02)

- **Build command:** `uv sync --frozen --no-dev && uv run python manage.py collectstatic --noinput && uv run python manage.py migrate --noinput`. Render's Python runtime adds uv automatically when `uv.lock` is in the repo root (pin it with `UV_VERSION` if needed), so no `pip install uv` step. A `build.sh` works too.
- **Start command:** `uv run gunicorn django_api.wsgi:application --bind 0.0.0.0:$PORT --workers 2`
- **Health check path:** `/api/health/`
- **HTTPS:** with `DEBUG=False`, settings trust Render's `X-Forwarded-Proto` header, redirect HTTP to HTTPS, mark session/CSRF cookies secure and send HSTS (`SECURE_HSTS_SECONDS`, default 3600). `/api/health/` is listed in `SECURE_REDIRECT_EXEMPT`, so Render's plain-HTTP probe reaches the view and gets 200 instead of a 301 (which Render would count as healthy without proving the app works). Host validation still applies: if the probe gets 400, its `Host` isn't in `ALLOWED_HOSTS`. Keep the path without `?db=1`: frequent probes that query the database would stop Neon's free compute from scaling to zero. Use `?db=1` for manual checks.
- **Static files:** WhiteNoise serves `collectstatic` output from `staticfiles/` (compressed, hashed names), so `/admin/` and the browsable API stay styled with `DEBUG=False`. Run `collectstatic` before serving with `DEBUG=False` (even locally): without the manifest, pages that use `{% static %}` return 500.
- **Accepted `check --deploy` warnings:** `security.W005` (HSTS `includeSubDomains`) and `security.W021` (HSTS preload). The service lives on a shared `onrender.com` subdomain, so neither applies.
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
