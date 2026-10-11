# 06 — Configuration

> Part of the [project docs](README.md). Every variable listed here must also appear in `.env.example` (backend) or the frontend's `.env.example`.

## Backend (local `.env` / Render environment)

| Variable | Local dev | Production | Introduced by |
|---|---|---|---|
| `SECRET_KEY` | any generated value | strong random (Render "Generate") | exists ([#2](https://github.com/pirrozani/django-api/issues/2)) |
| `DEBUG` | `True` | `False` | exists |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | `<backend>.onrender.com` | exists |
| `DATABASE_URL` | unset (SQLite), a local Postgres (Docker) or a Neon dev branch | Neon **direct** (non `-pooler`) connection string with `sslmode=require` | [#5](https://github.com/pirrozani/django-api/issues/5) |
| `CONN_MAX_AGE` | unset (60 s) | unset (60 s); `0` only if you switch to Neon's pooled endpoint, which also needs `DISABLE_SERVER_SIDE_CURSORS = True` in `DATABASES['default']` | [#5](https://github.com/pirrozani/django-api/issues/5) |
| `DB_CONNECT_TIMEOUT` | unset (10 s; ignored on SQLite) | unset (10 s); keep it between 2 and 29 (psycopg turns `1` into 2 and `0` or less into its 130 s default; gunicorn's worker timeout is 30 s). A `connect_timeout` query parameter in `DATABASE_URL` takes precedence | [#29](https://github.com/pirrozani/django-api/issues/29) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | `https://<frontend>.<account>.workers.dev` | [#8](https://github.com/pirrozani/django-api/issues/8) |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | `https://<backend>.onrender.com` | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `SECURE_HSTS_SECONDS` | unset (ignored while `DEBUG=True`) | unset (3600 s); raise (e.g. `31536000`) once HTTPS is confirmed stable | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `SECURE_SSL_REDIRECT` | unset (ignored while `DEBUG=True`) | unset (`True`); set `False` only for tests/CI that run with `DEBUG=False` | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `DEMO_USERNAME` / `DEMO_PASSWORD` | `demo` / local value | set only where `create_demo_user` / `reset_demo` runs (both fail without a password; a staff username is refused) | [#9](https://github.com/pirrozani/django-api/issues/9) |
| `NUM_PROXIES` | unset (`0`: throttles use `REMOTE_ADDR`) | the number of proxies in front of gunicorn (Render: verify, likely `1`). Left at `0`, every visitor shares one login bucket (Render's proxy IP). Never set it higher than the real count: the extra `X-Forwarded-For` entries are client-controlled | [#9](https://github.com/pirrozani/django-api/issues/9) |
| `LOGIN_THROTTLE_RATE` | unset (`20/min`) | unset (`20/min`); per client IP (see `NUM_PROXIES`) and per gunicorn worker (local-memory cache); `<count>/<s|m|h|d>` form (e.g. `5/hour`), anything else stops startup with `ImproperlyConfigured` | [#9](https://github.com/pirrozani/django-api/issues/9) |
| `PYTHON_VERSION` | — | only if Render ignores `.python-version` | [#1](https://github.com/pirrozani/django-api/issues/1) |

Generate a secret key:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Frontend (local `.env.local` / Cloudflare build variables)

| Variable | Local dev | Production |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` | `https://<backend>.onrender.com` |

> Vite inlines `VITE_*` at **build time**. Changing the value requires a rebuild, and it must never contain secrets.

## Local development setup

1. Backend on `http://127.0.0.1:8000` (`uv sync` once, then `uv run python manage.py runserver`).
2. Frontend on `http://localhost:5173` (`npm run dev`).
3. They talk cross-origin through CORS, exactly like production, so CORS mistakes show up early. Don't use a Vite proxy.
