---
name: review-pr
description: Review a pull request (e.g. /review-pr 12) or the current feature branch against its linked GitHub issue and the repo rules (base branch, Closes #N, acceptance criteria, contract doc, migrations, tests, secrets), run the health check, api-sync and the api-reviewer agent, and give a verdict. Read-only; asks before posting the review on GitHub. Use when the user asks to review a PR or check that an issue was done correctly.
---

# /review-pr [N]

Check that a PR on `pirrozani/django-api` does what its issue asked and follows the rules in `CLAUDE.md`. The review is read-only: it never edits code, commits, pushes or merges.

## Input

`$ARGUMENTS` is a PR number (`12`, `#12`, or the PR URL), or nothing.
- **PR mode** (number given): review that PR.
- **Branch mode** (no number): review the current branch against `develop`. If an open PR exists for it (`gh pr list --head <branch> --state open`), switch to PR mode for that PR.

## Steps

1. **Resolve the target.**
   - PR mode: `gh pr view <N> --json number,title,body,state,isDraft,baseRefName,headRefName,files,commits`. If it isn't found, or it's closed/merged, say so and stop.
   - Branch mode: `git branch --show-current`. Refuse on `main` or `develop`.
   - Remember the current branch. Run `git fetch origin`. The diff range is `origin/develop...origin/<head>` (PR mode) or `origin/develop...HEAD` (branch mode).
2. **Load the linked issue.** Take the number from `Closes #N` in the PR body, or else from the `feature/<N>-…` branch name. Run `gh issue view <N> --json number,title,body,labels,state` and pull out its *Fix* steps and *Acceptance criteria* checkboxes. If there's no linked issue, flag it and continue.
3. **Process checks.** These are static, from the diff (`git diff <range> --stat`, `git diff <range>`) and the PR metadata:
   - The base is `develop` (never `main`). The branch matches `feature/<N>-<slug>`. The PR body has `Closes #N`.
   - Commit subjects (`git log <range> --format=%s`) use `feat|fix|refactor|chore|docs`.
   - **Scope:** each changed file maps to a step of the issue's *Fix*. Flag unrelated files.
   - If `api/` views, serializers or urls changed, `docs/03-api-contract.md` changed too.
   - If `api/models` changed, a migration is in the diff.
   - If dependencies changed, both `pyproject.toml` and `uv.lock` changed. There's no `requirements.txt` and nothing under `.venv/`/`venv/`.
   - No `.env` file, secrets, tokens or database URLs appear in the **added** lines.
   - New behaviour has tests under `api/tests/`.
4. **Get the code locally** for steps 5–7.
   - If `HEAD` is already the PR head, continue.
   - Otherwise, if `git status --short` is clean, **ask** before running `gh pr checkout <N>`.
   - If the user declines or the tree is dirty, mark steps 5–7 `SKIP` and go to step 8.
5. **Acceptance criteria.** For each checkbox:
   - Run it if it's a read-only command (`uv run python manage.py check`, `… test`, `curl` against a `runserver` started in the background and stopped afterwards). Otherwise verify it by reading the code.
   - Mark it `PASS`, `FAIL` or `UNVERIFIED`, with a one-line piece of evidence.
6. **Health check.** Run the `/health-check` steps. Use its issue-mapping table so failures already tracked by other open issues aren't blamed on this PR.
7. **API sync.** Only if `api/` changed: run the `/api-sync` steps in read-only mode (never `--write`).
8. **Code review.** Launch the `api-reviewer` agent and give it the diff range from step 1. Start it at the same time as steps 5–7.
9. **Restore.** If step 4 checked out another branch, `git switch` back to the branch you remembered in step 1.
10. **Report, then offer to post.**
    - Print the report (see Output).
    - PR mode: ask whether to post it. If yes, write it to a scratchpad file and run `gh pr review <N> --comment --body-file <file>`. Always use `--comment`: GitHub rejects approve and request-changes on your own PR.
    - Branch mode with no PR: if the verdict is ready, suggest `/pr`.

## Output

At most 30 lines:

```
Review: PR #12 <title> (feature/12-… → develop) · Issue #12 <title>
Process:  PASS | FAIL <rule> — <detail>       (expand failures only)
Criteria: [PASS|FAIL|UNVERIFIED|SKIP] <criterion> — <evidence>
Checks:   health-check <one line> · api-sync <IN SYNC | n drift items | not needed>
Code:     [HIGH|MEDIUM|LOW] file:line — problem — fix   (from api-reviewer)
Verdict:  Ready to merge | Changes needed (<n> blocking)
```

The verdict is **Changes needed** if any of these hold:
- there's a HIGH finding or a FAIL criterion;
- the base branch is wrong;
- the contract doc or a migration is missing;
- the diff contains a secret;
- the PR changes are out of scope.

Pre-existing failures tracked by other open issues are listed but don't block.

## Never

- Edit code, commit, push, merge, approve or close anything.
- Post to GitHub without confirmation. The repo is **public**, so never post secrets or `.env` values.
- Read `.env` or touch `.venv/`/`venv/`.
- Leave the user on a different branch from the one they started on.
- Mark a criterion `PASS` without evidence.
