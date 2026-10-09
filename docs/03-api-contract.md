# 03 — API contract (v2)

> Part of the [project docs](README.md). Status: **target**. The current API still differs (see [02-current-state.md](02-current-state.md)). Update this file whenever an endpoint changes.

The frontend has no consumers yet, so it is safe to standardize the contract now. Bump `SPECTACULAR_SETTINGS['VERSION']` to `2.0.0` when this lands.

## Conventions

- JSON only. Errors use DRF's default shape: `{"detail": "..."}` or field errors `{"field": ["msg"]}`.
- Lists are paginated: `{"count", "next", "previous", "results": [...]}` · `?page=N` · page size 10, configurable with `?page_size=` up to 50.
- `POST` returns **201 + the created object** (unwrapped). `DELETE` returns **204 with empty body**.
- `PATCH` supported for partial updates; `PUT` stays as a full replace.
- Default ordering: newest first (`-created_at`, `-id`).
- Trailing slashes on every route (`/api/blogs/<id>/`).
- Auth header: `Authorization: Token <token>`.

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/health/` | public | `{"status": "ok"}`. Optional `?db=1` runs `SELECT 1`. Used for wake-up. |
| POST | `/api/auth/token/` | public | body `{username, password}` → `{"token": "..."}` |
| POST | `/api/auth/logout/` | token | Deletes the token → 204 |
| GET | `/api/auth/me/` | token | `{id, username, is_staff}` of the logged-in account |
| GET | `/api/users/` | public | paginated; `?search=` on name/username/email (optional) |
| POST | `/api/users/` | token | password write-only, hashed |
| GET | `/api/users/<id>/` | public | |
| PUT/PATCH | `/api/users/<id>/` | token | hash the password if present |
| DELETE | `/api/users/<id>/` | token | 204, cascades blogs |
| GET | `/api/users/<id>/blogs/` | public | paginated. **Empty list → 200** with `results: []`. 404 only if the user doesn't exist. |
| GET | `/api/blogs/` | public | paginated; `?search=` on title (optional); `?author=<id>` filter |
| POST | `/api/blogs/` | token | body `{user, title, content}` |
| GET | `/api/blogs/<id>/` | public | |
| PUT/PATCH | `/api/blogs/<id>/` | token | |
| DELETE | `/api/blogs/<id>/` | token | 204 |
| GET | `/api/schema/` · `/api/schema/swagger-ui/` · `/api/schema/redoc/` | public | OpenAPI 3 |

`/api/blogs/user/<id>` is **dropped** (replaced by `/api/users/<id>/blogs/`). It has no consumers yet.

## Resource shapes

```jsonc
// User (author), password is never returned
{
  "id": 1,
  "first_name": "Robert",
  "last_name": "Oliver",
  "username": "lyang",
  "mobile": "(482)598-4678",
  "email": "breanna03@example.com",
  "register_at": "2021-06-11"
}

// Blog: `user` is the writable id, `author` is a read-only summary (avoids N+1 on the frontend)
{
  "id": 10,
  "user": 1,
  "author": { "id": 1, "username": "lyang", "first_name": "Robert", "last_name": "Oliver" },
  "title": "Doloremque et et.",
  "content": "…",
  "created_at": "2021-06-11"
}

// Paginated list
{ "count": 200, "next": "https://…/api/blogs/?page=2", "previous": null, "results": [ /* … */ ] }
```

## Related issues

[#9](https://github.com/pirrozani/django-api/issues/9) (auth routes) · [#3](https://github.com/pirrozani/django-api/issues/3) (password) · [#10](https://github.com/pirrozani/django-api/issues/10) (shapes/status codes) · [#11](https://github.com/pirrozani/django-api/issues/11) (pagination) · [#12](https://github.com/pirrozani/django-api/issues/12) (`author` field)
