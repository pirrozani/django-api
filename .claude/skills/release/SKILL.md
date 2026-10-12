---
name: release
description: Ship develop to main end to end (preflight, health check, changelog, version bump, release PR merged with a merge commit, tag, GitHub release, back-merge into develop). Asks before every push, merge, tag and release. Use when the user asks to release, cut a release, ship or deploy develop to main. Supports --dry-run.
---

# /release [major|minor|patch|<x.y.z>] [--dry-run]

Release `develop` into `main` on `pirrozani/django-api`. The bump defaults to `minor`. `main` deploys to Render, so every outward step waits for an explicit yes.

With `--dry-run`, run steps 1–3 and print the plan from step 5, then stop. A dry run creates no release branch, commit, push, PR, tag or release.

## Steps

1. **Preflight.** Refuse and stop if any check fails, saying which one.
   - `git fetch origin --tags --prune`
   - `git status --short` is empty (clean tree).
   - `git rev-parse develop` == `git rev-parse origin/develop`, and the same for `main`. If a local branch is missing, create it from `origin`; if it differs, refuse (don't pull or reset for the user).
   - `git log origin/main..origin/develop --oneline` is not empty (something to release).
   - `git merge-base --is-ancestor origin/main origin/develop` succeeds. If not, `main` has commits `develop` lacks: refuse and suggest merging `main` into `develop` first.
   - `gh pr list --base main --state open` shows no other release PR. If one exists, report it and stop.
   - `gh api repos/pirrozani/django-api --jq .allow_merge_commit` is `true`, or step 6 can't merge with a merge commit.
2. **Health check** on `develop`: `git switch develop`, then run the `/health-check` steps. Stop if any step fails.
3. **Changelog and version.**
   - Commits: `git log origin/main..origin/develop --no-merges --format='- %s (%h)'`.
   - Closing issues: `git log origin/main..origin/develop --format=%B | grep -oiE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?):? #[0-9]+' | grep -oE '[0-9]+' | sort -un`. For each, `gh issue view <N> --json number,title,state` and keep the open ones.
   - Current version: the `version = "…"` line in `pyproject.toml`. **Never derive it from git tags.** `pyproject.toml` is the source of truth (an old, out-of-sequence `1.0.0` tag was removed for #43).
   - Next version: bump `major` (`X+1.0.0`), `minor` (`X.Y+1.0`) or `patch` (`X.Y.Z+1`); an explicit `<x.y.z>` must be valid semver and greater than the current version.
   - Refuse if `git tag -l <x.y.z>` or `git ls-remote --tags origin <x.y.z>` already exists. Report the clash; the skill never deletes or moves tags.
   - Warn (don't refuse) if `git tag --sort=-v:refname | head -1` is higher than `<x.y.z>`, naming the tag.
4. **Version bump** (skipped on `--dry-run`).
   - `git switch -c release/<x.y.z> origin/develop`
   - Change only the `version = "…"` line in `pyproject.toml`, then `uv lock`. `git diff --stat` must show only `pyproject.toml` and `uv.lock`; otherwise stop and report.
   - `git commit -am "chore: bump version to <x.y.z>"` with the Claude Code co-author trailer.
5. **Show the plan** and **ask for confirmation**:
   ```
   Release <current> → <x.y.z>   (develop <sha> → main <sha>)
   Commits (<n>):
   - …
   Will close: #11 <title>, #27 <title>
   Already closed: #…   (if any)
   Next: push release/<x.y.z>, open PR into main
   ```
   On `--dry-run`, print the plan with the header `DRY RUN, nothing pushed` and stop here.
   If the user says no, `git switch develop` and offer to delete the local branch (`git branch -D release/<x.y.z>`).
6. **Release PR.**
   - Write the body to a scratchpad file:
     ```markdown
     ## Release <x.y.z>

     <commit list from step 3>

     Closes #11
     Closes #27

     Merge with a **merge commit**, never squash or rebase, or the `Closes` lines in the squash commits are lost.

     🤖 Generated with [Claude Code](https://claude.com/claude-code)
     ```
   - **Ask**, then `git push -u origin release/<x.y.z>` and `gh pr create --base main --head release/<x.y.z> --title "release: <x.y.z>" --body-file <file>`.
   - Show the PR URL and its checks (`gh pr checks <PR>`). If any check is failing or pending, don't offer the merge: report it and suggest `gh pr checks <PR> --watch`. Otherwise **ask before merging**, reminding the user that merging deploys to Render.
   - `gh pr merge <PR> --merge --delete-branch`. This also deletes the local branch and switches to `main`. Never `--squash`, `--rebase`, `--admin` or `--auto`.
7. **Tag, GitHub release and back-merge.**
   - `git fetch origin`, then confirm `git rev-parse origin/main` equals `gh pr view <PR> --json mergeCommit --jq .mergeCommit.oid`. Stop if they differ.
   - **Ask**, then `git tag -a <x.y.z> origin/main -m "Release <x.y.z>"` and `git push origin <x.y.z>`.
   - **Ask**, then write the changelog (step 3 commits plus the closed issues) to a scratchpad file and run `gh release create <x.y.z> --title "<x.y.z>" --notes-file <file> --verify-tag --latest`.
   - **Ask**, then `git switch develop`, `git pull --ff-only`, `git merge --no-ff <x.y.z> -m "Merge tag '<x.y.z>' into develop"` and `git push origin develop`.
   - If `release/<x.y.z>` still exists locally, `git branch -d release/<x.y.z>`.
8. **Verify** and report in at most 15 lines:
   - Every issue from step 3 is `CLOSED` (`gh issue view <N> --json state`). If one is still open, say so and don't close it by hand: check that its `Closes` line reached `main`.
   - `git rev-parse origin/main` == `git rev-parse <x.y.z>^{commit}`.
   - `git merge-base --is-ancestor origin/main origin/develop` succeeds.
   - Report the PR URL, the tag, the release URL (`gh release view <x.y.z> --json url`) and the closed issues.
   - Suggest checking `GET /api/health/` on the live Render URL once the deploy finishes.

## Never

- Push to `main` directly, force-push, use `--no-verify`, or merge with squash or rebase.
- Push, merge, tag or create a release without a yes for that step. One yes doesn't cover the next step.
- Move, delete or re-create existing tags.
- Close issues by hand or edit files other than `pyproject.toml` and `uv.lock`.

## If a step fails midway

Stop and report what's done and what isn't. Don't undo pushed work. Resume from the failed step: the release branch, PR or tag already exists, so check it instead of recreating it.
