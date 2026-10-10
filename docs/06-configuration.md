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
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | `https://<frontend>.<account>.workers.dev` | [#8](https://github.com/pirrozani/django-api/issues/8) |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | `https://<backend>.onrender.com` | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `SECURE_HSTS_SECONDS` | unset (ignored while `DEBUG=True`) | unset (3600 s); raise (e.g. `31536000`) once HTTPS is confirmed stable | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `SECURE_SSL_REDIRECT` | unset (ignored while `DEBUG=True`) | unset (`True`); set `False` only for tests/CI that run with `DEBUG=False` | [#7](https://github.com/pirrozani/django-api/issues/7) |
| `DEMO_USERNAME` / `DEMO_PASSWORD` | `demo` / local value | set only where `create_demo_user` runs | [#9](https://github.com/pirrozani/django-api/issues/9) |
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
