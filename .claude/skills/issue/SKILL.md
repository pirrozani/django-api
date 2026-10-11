---
name: issue
description: Investigate a problem in this repo and file it as a GitHub issue filled in with the project's fix template (Problem / Evidence / Impact / Fix / Acceptance criteria / Notes), with priority and type labels. Use when the user asks to create, open, file, log or draft an issue, or reports a bug/gap that should be tracked.
---

# /issue <short description>

Turn a problem description into a complete GitHub issue on `pirrozani/django-api` using `.github/ISSUE_TEMPLATE/fix.md`.

## Input

`$ARGUMENTS` is a short description of the problem (e.g. `blog list is slow`). If it's empty, ask what the issue is about. If the user passes `--dry-run`, stop after step 5 and don't create anything.

## Steps

1. **Load context.**
   - Read `.github/ISSUE_TEMPLATE/fix.md`. Its section headings and footer line are the required structure.
   - Read the issue register in `docs/02-current-state.md` and the BE table in `docs/04-backend-plan.md`.
2. **Check for duplicates.** Run `gh issue list --state all --search "<2–4 keywords>" --limit 20`. If an existing issue already covers it, show it and ask whether to comment on it instead.
3. **Investigate (read-only).** Find the relevant code with Grep/Read and collect **real evidence**:
   - `file:line` references with what the code does;
   - error text, or a command that reproduces the problem.

   Run commands only if they're read-only (e.g. `uv run python manage.py check`, `curl` against a running dev server).
   Never read `.env`, and never invent line numbers. If you can't confirm something, say so in Evidence.
4. **Fill every section** of the template, in the same order and with the same headings:
   - **Problem:** one or two sentences.
   - **Evidence:** bullets with `file:line`, plus a code block for errors.
   - **Impact:** who or what breaks, and when.
   - **Fix:** numbered steps; short code snippets only where they remove ambiguity. Dependencies use `uv add`, commands use `uv run python manage.py …`.
   - **Acceptance criteria:** `- [ ]` checkboxes, each one a command or observable result.
   - **Notes / risks:** alternatives not taken, follow-ups.
   - **Footer:** `**Priority:** Px · **Blocks:** … · **Work item:** BE-xx · **Related:** #N, …`. Link docs with absolute URLs (`https://github.com/pirrozani/django-api/blob/develop/docs/<file>.md`). Remove all HTML comments from the template.
5. **Choose labels.**
   - **Type:** `bug` (something is wrong), `enhancement` (missing capability or improvement), or `documentation`.
   - **Priority (exactly one):** `priority: P0` (won't run locally), `priority: P1` (blocks deploy/frontend, or security), `priority: P2` (API quality the frontend needs), `priority: P3` (hygiene/portfolio).
   - Add `security` when it applies.

   Title: imperative or descriptive, ≤ 70 characters, no `FIX-` prefix.
6. **Show the draft** (title, labels, full body) and **ask for confirmation**. Apply any requested changes.
7. **Create it.**
   - Write the body to a file in the scratchpad.
   - Run `gh issue create --title "<title>" --label "<type>" --label "priority: Px" [--label security] --body-file <file>`.
8. **Update docs.**
   - Add a row to the issue register in `docs/02-current-state.md`: the next free `A#` id, a one-line summary, and the issue link.
   - If it belongs to a BE work item, add the link to that row's "Resolves" column in `docs/04-backend-plan.md`.
9. **Report** the issue URL and the doc rows you added, in ≤ 5 lines.

## Never

- Create an issue without showing the draft and getting a yes (unless the user explicitly said to skip confirmation).
- Put secrets, `.env` values, tokens or database URLs in an issue: the repo is **public**.
- Create several issues for one problem. Create one issue, and suggest follow-ups in Notes instead.
