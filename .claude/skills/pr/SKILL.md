---
name: pr
description: Open a pull request from the current feature branch into develop with "Closes #N", after running the health check. Asks before pushing. Use when the user asks to open, create or raise a PR, or after /fix is done.
---

# /pr

Open a PR for the current branch against `develop` on `pirrozani/django-api`.

## Steps

1. **Check the branch.**
   - Run `git branch --show-current`. Refuse on `main` or `develop`.
   - Get the issue number from `feature/<N>-…`. If the branch name has none, ask which issue it closes (or "none").
   - If `gh pr list --head <branch> --state open` already shows a PR, report its URL and stop.
2. **Check the tree.** Run `git status --short`.
   - If there are uncommitted changes, show them and ask whether to commit them (message `<type>: <summary> (#N)`, with the Claude Code co-author trailer) or stop.
   - Check `git log develop..HEAD --oneline` is not empty.
3. **Health check.** Run the `/health-check` steps. If any step fails for a reason this branch was supposed to fix, stop and report. Note pre-existing failures (tracked by other open issues) in the PR body instead.
4. **Contract check.**
   - Run `git diff develop...HEAD --stat`.
   - If `api/` views, serializers or urls changed, also check that `docs/03-api-contract.md` changed. If it didn't, warn and suggest `/api-sync`.
5. **Draft the PR.**
   - **Title:** `<type>: <issue title>`, where the type comes from the issue labels (`bug` → `fix`, `enhancement` → `feat`, `documentation` → `docs`).
   - **Body:**
     ```markdown
     ## Summary
     - <2–5 bullets: what changed and why>

     Closes #N

     ## Verification
     - [x] <each acceptance criterion and its result>
     - [x] /health-check: <one-line result>

     ## Checklist
     - [ ] Tests added/updated
     - [ ] docs/03-api-contract.md updated (if the API changed)
     - [ ] No secrets, `.env` values or database URLs in the diff

     🤖 Generated with [Claude Code](https://claude.com/claude-code)
     ```
   Show the title and body and **ask for confirmation before pushing**.
6. **Publish.**
   - `git push -u origin <branch>`
   - Write the body to a scratchpad file, then `gh pr create --base develop --head <branch> --title "<title>" --body-file <file>`
7. **Report** the PR URL in one line.

## Never

- Target `main`, force-push, or use `--no-verify`.
- Push without confirmation.
- Merge the PR. The user merges it.
