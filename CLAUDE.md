# CLAUDE.md — django_api_project

> **Scope note:** the global `~/.claude/CLAUDE.md` describes an unrelated project (master-thesis: LLM fine-tuning, `adapters/`, training runs). **None of it applies here.** Follow this file for this repo.

## What this is

Django 5 + Django REST Framework API (users/authors and blogs) that serves as the **backend for a React SPA** in a separate repo. Portfolio project, deployed on free tiers: Render (backend), Neon (Postgres), Cloudflare Workers (frontend). GitHub: `pirrozani/django-api`.

**Sources of truth:**
- **Work to do:** [GitHub issues](https://github.com/pirrozani/django-api/issues), labelled `priority: P0`–`P3`, written with `.github/ISSUE_TEMPLATE/fix.md`
- **Docs:** `docs/README.md` (index, recommended issue order), `docs/03-api-contract.md` (target API the frontend builds against), `docs/04-backend-plan.md` (work items BE-xx)

## Current state

The project **does not start** until issue **#1** is done: packages inside the old `venv/` were edited in place, and the fix is to rebuild with **uv**. Don't try to work around it by patching `venv/`. Until #1 lands, `pyproject.toml`/`uv.lock` don't exist yet, so `uv run` commands won't work.

## Stack & layout

- Python 3.12, managed with **uv** (`pyproject.toml`, `uv.lock`, `.python-version`, environment in `.venv/`). Add dependencies with `uv add`; never hand-edit the lock. Settings via `django-environ` reading `.env`.
- `django_api/`: project (settings, urls, management commands `populate`, `clear`).
- `api/`: app: `models/` (`User` = authors, **not** login accounts; `Blog`), `serializers/`, `views/` (APIView classes), `urls.py`, `signals.py` (auto-creates tokens for `auth.User`), `middleware.py` (request logging).
- OpenAPI via drf-spectacular: `/api/schema/swagger-ui/`.
- Login accounts are `django.contrib.auth.User` + DRF `TokenAuthentication`.

## Commands (Windows, Git Bash)

```bash
uv sync                                         # create/refresh .venv from uv.lock
uv run python manage.py check
uv run python manage.py migrate
uv run python manage.py populate --users 30 --articles 80
uv run python manage.py clear
uv run python manage.py runserver
uv run python manage.py test
python .claude/skills/health-check/verify_venv.py   # environment integrity (stdlib only)
```

## Claude Code helpers

| Helper | Use |
|---|---|
| `/issue <description>` | Investigate a problem and draft a GitHub issue from the fix template (asks before creating) |
| `/resolve-issue <N>` | Implement issue #N on `feature/<N>-<slug>`, verify acceptance criteria, report on the issue |
| `/pr` | Health check, then open a PR to `develop` with `Closes #N` (asks before pushing) |
| `/review-pr [N]` | Review PR #N (or the current branch) against its issue and the repo rules, with a verdict (asks before posting) |
| `/health-check` | One-pass local checks, with each failure mapped to its issue |
| `/api-sync` | Compare the generated OpenAPI schema with `docs/03-api-contract.md` |
| `api-reviewer` agent | DRF-focused review of the branch diff; `/resolve-issue` runs it before reporting |

Hooks in `.claude/settings.json` block reading `.env` and editing files inside `.venv/`/`venv/`.

## Rules

1. **Never edit anything under `.venv/` or `venv/`.** If a library looks broken, rebuild with `uv sync` (or see #1).
2. **Never read `.env`** (it holds secrets). Use `.env.example` to learn the variables.
3. Branch from `develop` as `feature/<N>-<slug>`; PRs go `feature/*` → `develop` → `main`. `main` deploys. Never commit or open PRs directly against `main`.
4. Commit only when the user asks. Use the existing prefixes: `feat`, `fix`, `refactor`, `chore`, `docs`.
5. PRs that resolve an issue include `Closes #N`. Every API change updates `docs/03-api-contract.md` in the same PR. New problems become issues (`/issue`), not TODO comments.
6. Keep the existing code style: single quotes, class-based views, `@extend_schema` on every endpoint, a short comment above each method.
7. Never commit secrets or database URLs. Production values live in Render/Cloudflare env settings.
8. Don't push, create issues/PRs, deploy, or touch external services (GitHub, Render, Neon, Cloudflare) without explicit confirmation.
