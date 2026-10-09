---
name: fix
description: Implement one GitHub issue (e.g. /fix 9 or /fix #9) on a feature branch, verify its acceptance criteria, run the api-reviewer agent, and post the results on the issue. Use when the user asks to fix, implement, or work on an issue.
---

# /fix <issue number>

Implement exactly one GitHub issue from `pirrozani/django-api`.

## Input

`$ARGUMENTS` is an issue number (`9`, `#9`, or the issue URL). If it's missing, list open issues by priority (`gh issue list --state open --limit 50 --json number,title,labels`) and ask which one to do. Recommend the next one from "Recommended issue order" in `docs/README.md`.

## Steps

1. **Load the issue.** Run `gh issue view <N> --json number,title,body,labels,state`. If it's closed, say so and stop. If the issue touches the API, also read `docs/03-api-contract.md`.
2. **Check readiness.**
   - If any P0 issue (#1, #2) is still open and this issue needs the app to run, stop and recommend the P0 issue first. Check with `gh issue list --label "priority: P0" --state open`.
   - Check the issues the body depends on (Notes/Related) are closed, or warn.
   - Run `git status`. If the working tree is dirty, stop and ask what to do with the existing changes.
3. **Branch.** From an up-to-date `develop`: `git switch develop && git pull --ff-only && git switch -c feature/<N>-<slug>`. The slug is a short kebab-case version of the title. If you're already on `feature/<N>-…`, keep it.
4. **Implement** the issue's *Fix* section, and only that.
   - Follow the rules in `CLAUDE.md`. Dependencies go through `uv add`.
   - If the issue is wrong or incomplete compared with the code, tell the user and propose an issue edit rather than silently deviating.
5. **Add tests** for the acceptance criteria once the app runs (`api/tests/`, see #14).
6. **Verify.**
   - Run each acceptance-criteria command from the issue. Use `curl` against `runserver` only if it's needed; start it in the background and stop it afterwards.
   - Then run the `/health-check` steps.
   - If the API changed, run the `/api-sync` steps and update `docs/03-api-contract.md`.
7. **Review.** Launch the `api-reviewer` agent on the branch diff. Fix any high-severity findings, then re-run the affected checks.
8. **Report on the issue.** Ask first, then post a comment with `gh issue comment <N> --body-file <file>`. The comment lists each acceptance criterion as `[x]`/`[ ]` with a one-line result, plus the branch name. **Don't close the issue.** The PR's `Closes #N` does that when it merges.
9. **Report to the user** in ≤15 lines: branch, files changed, criteria passed/failed, review findings, follow-ups. Suggest `/pr` as the next step. **Don't commit or push** unless the user asks. If asked, use a `fix:`/`feat:`/`chore:` message that ends with `(#N)`.

## Never

- Edit files under `.venv/`/`venv/`, or read `.env`.
- Claim a criterion passed without running it.
- Bundle several issues in one branch unless the user asks.
