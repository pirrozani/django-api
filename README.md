# django-api

Django REST Framework API (authors and blogs), the backend for a React SPA.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is pinned in `.python-version`.

```bash
cp .env.example .env            # then fill in SECRET_KEY
uv sync                         # creates .venv/ from uv.lock
uv run python manage.py migrate
uv run python manage.py populate --users 30 --articles 80
uv run python manage.py runserver
```

API docs: http://127.0.0.1:8000/api/schema/swagger-ui/

Add dependencies with `uv add <package>`; never edit `uv.lock` by hand.
