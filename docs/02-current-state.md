# 02 — Current state (audit)

> Part of the [project docs](README.md). Audit date: 2026-10-09 · branch `develop` · Django 5.0.2 · DRF 3.14 · drf-spectacular 0.27 · SQLite · Python 3.12.0.

## Local environment health

> **Resolved by [#1](https://github.com/pirrozani/django-api/issues/1):** the environment is now rebuilt with uv (`pyproject.toml` + `uv.lock`, `.venv/`), and `manage.py check` passes. The audit findings below describe the state before #1.

**At audit time, the project did not start.** Any `manage.py` command crashed during logging setup:

```
AttributeError: module 'django.utils.termcolors' has no attribute 'get'
ValueError: Unable to configure formatter 'django.server'
```

Cause: the installed third-party packages inside the old `venv/` had been edited in place. 60 files differ from their published hashes, all modified on 2024-08-27 20:58. → **[#1](https://github.com/pirrozani/django-api/issues/1)**.

With the environment rebuilt ([#1](https://github.com/pirrozani/django-api/issues/1)) and the `.env` setup fixed ([#2](https://github.com/pirrozani/django-api/issues/2)), a fresh clone runs with `cp .env.example .env`.

## Domain model

| Model | Fields | Notes |
|---|---|---|
| `api.User` (`api/models/user.py`) | `id, first_name, last_name, username, mobile, password, email (unique), register_at` | A **content model** (blog authors). It is **not** Django's auth user. |
| `api.Blog` (`api/models/blog.py`) | `id, user (FK → api.User, cascade), title, content, created_at (date)` | |
| `auth.User` (Django built-in) | — | The **login account** used by Token/Basic auth. A token is auto-created by `api/signals.py`. |

> ⚠️ **Two different "users".** API consumers log in with a Django `auth.User`; the `/api/users/` resource manages `api.User` records (authors). Keep the distinction explicit in the frontend, which may label them **"Authors"**. Renaming the model is out of scope for v1 (see [08-roadmap.md](08-roadmap.md) Q3).

## Current endpoints (`api/urls.py`, mounted at `/api/`)

| Method | Path | Current response | Auth |
|---|---|---|---|
| GET | `/api/users/` | `{"Total": n, "Users": [...]}` | required |
| POST | `/api/users/` | `{"Users": {...}}` (201) | required |
| GET/PUT/DELETE | `/api/users/<id>` | object / object / `{"message": ...}` with 204 | required |
| GET | `/api/blogs/` | `{"Total": n, "Blogs": [...]}` | required |
| POST | `/api/blogs/` | `{"Blogs": {...}}` (201) | required |
| GET/PUT/DELETE | `/api/blogs/<id>` | object / object / empty 204 | required |
| GET | `/api/blogs/user/<user_id>` | `{"Total", "Blogs"}`, or **404 when the user has no blogs** | required |
| GET | `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/` | OpenAPI | public |
| — | `/admin/` | Django admin | session |

The target contract is in [03-api-contract.md](03-api-contract.md).

## Issue register

Every finding maps to a GitHub issue; status lives in the [issue tracker](https://github.com/pirrozani/django-api/issues).

| ID | Issue | Fix |
|---|---|---|
| L1 | Edited/corrupted packages in `venv/`, so nothing starts (**resolved**: rebuilt with uv) | [#1](https://github.com/pirrozani/django-api/issues/1) |
| L2 | `.env.example` has empty `SECRET_KEY`; `.env` path is relative to the CWD; `DEBUG=False` locally (**resolved**: absolute path, working local defaults) | [#2](https://github.com/pirrozani/django-api/issues/2) |
| A1 | No token-issuing endpoint, so the SPA can't log in | [#9](https://github.com/pirrozani/django-api/issues/9) |
| A2 | No CORS | [#8](https://github.com/pirrozani/django-api/issues/8) |
| A3 | SQLite only, so data is lost on Render | [#5](https://github.com/pirrozani/django-api/issues/5) |
| A4 | No gunicorn / whitenoise / `STATIC_ROOT` / security settings | [#7](https://github.com/pirrozani/django-api/issues/7) |
| A5 | `clear` uses `sqlite_sequence`, so it fails on Postgres (**resolved**: backend-agnostic flush SQL, new `reset_demo` command) | [#6](https://github.com/pirrozani/django-api/issues/6) |
| A6 | Password hash returned in responses; plain-text passwords stored via API (**resolved**: write-only, hashed on create/update, data migration hashes old rows) | [#3](https://github.com/pirrozani/django-api/issues/3) |
| A7 | `BasicAuthentication` first, so 401 responses can trigger the browser's native login popup | [#9](https://github.com/pirrozani/django-api/issues/9) |
| A8 | Inconsistent response shapes and status codes | [#10](https://github.com/pirrozani/django-api/issues/10) |
| A9 | No pagination or ordering | [#11](https://github.com/pirrozani/django-api/issues/11) |
| A10 | Blog responses only carry the author id, so the frontend needs N+1 calls | [#12](https://github.com/pirrozani/django-api/issues/12) |
| A11 | Dead PUT-relaxation hack in `UserSerializer`; no PATCH (**resolved**: hack removed, `PATCH /api/users/<id>` added) | [#3](https://github.com/pirrozani/django-api/issues/3) |
| A12 | Junk dependency `django-rest-framework==0.1.0` | [#1](https://github.com/pirrozani/django-api/issues/1) |
| A13 | Django 5.0 no longer receives security fixes (**resolved**: Django 5.2 LTS, DRF 3.18, drf-spectacular 0.30; transitive pins dropped from `pyproject.toml`) | [#4](https://github.com/pirrozani/django-api/issues/4) |
| A14 | `DoesNotExist = None` / `objects = None` on models (**resolved**: removed IDE stub attributes) | [#13](https://github.com/pirrozani/django-api/issues/13) |
| A15 | No tests; README is a placeholder | [#14](https://github.com/pirrozani/django-api/issues/14) |
| A16 | App starts with a placeholder or weak `SECRET_KEY` when `DEBUG` is off | [#17](https://github.com/pirrozani/django-api/issues/17) |
| A17 | `populate` writes phone numbers longer than `User.mobile` (20 chars), so seeding fails on Postgres | [#20](https://github.com/pirrozani/django-api/issues/20) |

## Unmerged branches

| Branch | Contents | Action |
|---|---|---|
| `feature/update-user_serializer` | `password` write-only, hashed on create, explicit field list, `PASSWORD_HASHERS` | Merged in [#3](https://github.com/pirrozani/django-api/issues/3); safe to delete. |
| `feature/add-container` | The commit above + `Dockerfile` / `.dockerignore` | Not used: the project runs without Docker (decision D7). Only the serializer commit is reused, via [#3](https://github.com/pirrozani/django-api/issues/3). |
