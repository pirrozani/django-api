# 08 — Roadmap & open questions

> Part of the [project docs](README.md).

## Milestones

| Milestone | Scope | Exit criteria |
|---|---|---|
| **M0: Runs locally** | BE-00 ([#1](https://github.com/pirrozani/django-api/issues/1), [#2](https://github.com/pirrozani/django-api/issues/2)) | Fresh clone + `uv sync` → `check`, `migrate`, `populate`, `runserver` all work |
| **M1: Backend ready** | BE-01 → BE-09 | Tests green; v2 contract in Swagger; works on SQLite and Postgres locally |
| **M2: Backend live** | OPS-01 → OPS-03, BE-10 | `/api/health/` OK on Render; Swagger public; demo login works |
| **M3: Frontend MVP (local)** | FE-01 → FE-05 | Full CRUD against the local API |
| **M4: Frontend polished** | FE-06 → FE-08 | Loading/empty/error states, tests green, wake-up banner |
| **M5: Full stack live** | FE-09, CORS set to the real frontend URL | Live demo works end to end from a fresh browser |
| **M6: Portfolio polish** | FE-10, OPS-04, OPS-05 | READMEs with screenshots and links, CI badges, nightly reset |

## Open questions

| # | Question | Default if undecided |
|---|---|---|
| Q1 | Frontend repo name? | `django-blog-frontend` |
| Q2 | Buy a custom domain (e.g. `app.example.com` + `api.example.com` on Cloudflare DNS)? It would enable same-site HttpOnly cookies. | No, use platform subdomains |
| Q3 | Rename `api.User` → `Author` to remove confusion with `auth.User`? Requires a migration and API change. | No, label it "Authors" in the UI only |
| Q4 | Can the demo account delete data, or only create/edit? | Allow all, rely on `reset_demo` |
| Q5 | Python version on Render? | 3.12, pinned in `.python-version` by [#1](https://github.com/pirrozani/django-api/issues/1) |
| Q6 | Switch views to ViewSets + router (BE-05)? | Yes |
