# 07 — Deployment & operations

> Part of the [project docs](README.md). Prerequisites: [#5](https://github.com/pirrozani/django-api/issues/5) and [#7](https://github.com/pirrozani/django-api/issues/7) are done.

| ID | Item | Steps |
|---|---|---|
| OPS-01 | **Neon** database | Create a project + database and copy the connection string (`sslmode=require`). Optionally create a `dev` branch for local use. |
| OPS-02 | **Render** web service | New Web Service from this repo, branch `main`, free plan, region close to the Neon region. Set the env vars from [06-configuration.md](06-configuration.md), including `NUM_PROXIES` for the login throttle (set it from the observed chain, see [Verify `NUM_PROXIES`](#verify-num_proxies)). Health check path `/api/health/`. |
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

## Verify `NUM_PROXIES`

Render doesn't document how many proxies sit in front of gunicorn, so set `NUM_PROXIES` from what its logs show ([#36](https://github.com/pirrozani/django-api/issues/36)). Each request logs `IP: <throttle ip> (remote_addr=<...>, x_forwarded_for=<raw header>)`, where `IP:` is the key the login throttle uses.

1. After the first deploy, from a machine whose public IP you know, send a spoofed header:

   ```bash
   curl -s https://<backend>.onrender.com/api/health/ -H 'X-Forwarded-For: 198.51.100.1'
   ```
2. In Render's logs, find that request's `x_forwarded_for=` chain. Find your real IP's position counted from the **right** end (last entry = 1): that number is `NUM_PROXIES`, because DRF reads the entry at `[-NUM_PROXIES]`. For example, `198.51.100.1, <your ip>` means `1`, and `198.51.100.1, <your ip>, 10.x.x.x` means `2`. The proxy that connects to gunicorn shows up in `remote_addr`, not in the chain.
3. Set `NUM_PROXIES` in Render's environment and redeploy.
4. Repeat the `curl`. The logged `IP:` must be your real IP, not `198.51.100.1` and not a Render address. Never set the value higher than the count you observed: the extra entries are client-controlled, so a client could pick its own throttle bucket.

**Observed on Render (2026-10-13): `NUM_PROXIES=3`.** Render appends to a client-supplied header. After the client's own entry come a Cloudflare edge and a Render load balancer, and `remote_addr` is a local proxy inside the container that doesn't add an entry. So the chain ends `…, <client>, <cloudflare edge>, <render lb>`, and the client is third from the right. With `1` the throttle keyed on the load balancer and with `2` on the Cloudflare edge, both shared by many visitors. Render's own health probe sends no header, so it falls back to `remote_addr`.

If logins start sharing one bucket again (everyone gets 429 together), Render's proxy topology changed: repeat these steps.
