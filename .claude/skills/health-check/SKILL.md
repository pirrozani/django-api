---
name: health-check
description: One-pass, read-only health check of the Django project (environment integrity, system checks, migration drift, tests, deploy checks), with each failure mapped to its GitHub issue. Use when the user asks whether the project runs, after dependency changes, or as the verification step of /fix and /pr.
---

# /health-check

Run each step once, from the repo root. Don't stop at the first failure (except where noted), and don't modify any files.

## Steps

1. **Environment integrity:** `python .claude/skills/health-check/verify_venv.py`. It checks `.venv`, falling back to the legacy `venv`.
   - If no `pyproject.toml`/`uv.lock` exists → FAIL "not migrated to uv yet" → #1. Skip steps 2–5.
   - If it reports modified files → FAIL → #1. Still try step 2 to show the symptom.
2. **System check:** `uv run python manage.py check`
3. **Migration drift:** `uv run python manage.py makemigrations --check --dry-run`
4. **Tests:** `uv run python manage.py test` (report counts, not full output)
5. **Deploy check** with dummy production values (never real secrets):
   ```bash
   DEBUG=False SECRET_KEY=dummy-health-check-key-not-secret-0123456789abcdefghijklmnop \
   ALLOWED_HOSTS=example.onrender.com uv run python manage.py check --deploy
   ```
   Report the warning IDs only (e.g. `security.W004`).

Cap each command with a 5-minute timeout.

## Mapping failures to issues

| Symptom | Issue |
|---|---|
| Modified/missing package files, `termcolors has no attribute 'get'`, no `uv.lock` | #1 |
| `SECRET_KEY setting must not be empty`, `.env` not found | #2 |
| `django-rest-framework` installed | #1 |
| Django 5.0.x installed | #4 |
| `sqlite_sequence` errors on Postgres | #6 |
| `security.W004/W008/W012/W016` and similar | #7 |
| `UnorderedObjectListWarning` | #11 |
| Unknown failure | Suggest `/issue <symptom>` |

Before recommending an issue, check that it's still open (`gh issue view <N> --json state`). If it's closed, the failure is a regression: suggest reopening it or filing a new issue.

## Output

At most 15 lines: one line per step (`PASS`/`FAIL`/`SKIP` plus a short reason), then the open issues to work on next, in the order given in `docs/README.md`. Show raw output only for the specific failing lines (≤10 lines).
