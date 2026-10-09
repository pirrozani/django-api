# django-api

Django REST Framework API (authors and blogs), the backend for a React SPA.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is pinned in `.python-version`.

```bash
cp .env.example .env            # local defaults: DEBUG=True, localhost allowed
uv sync                         # creates .venv/ from uv.lock
uv run python manage.py migrate
uv run python manage.py populate --users 30 --articles 80
uv run python manage.py runserver
```

`.env.example` ships `SECRET_KEY=change-me`, which is fine for local work. To use a real key, generate one and paste it into `.env`:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Never commit `.env` or a real key; production values live in Render (see `docs/07-deployment.md`).

API docs: http://127.0.0.1:8000/api/schema/swagger-ui/

Add dependencies with `uv add <package>`; never edit `uv.lock` by hand.
