# Project docs

Documentation for **django_api_project**, the Django REST API backend of a full-stack portfolio project. The React frontend lives in a separate repository and is deployed separately (see [01-architecture.md](01-architecture.md)).

> **Current status (2026-10-09):** the project does **not** start locally. Start with the [P0 issues](https://github.com/pirrozani/django-api/issues?q=is%3Aissue+is%3Aopen+label%3A%22priority%3A+P0%22): [#1](https://github.com/pirrozani/django-api/issues/1), then [#2](https://github.com/pirrozani/django-api/issues/2).

## Reading order

| # | Doc | What's in it |
|---|---|---|
| — | [GitHub issues](https://github.com/pirrozani/django-api/issues) | **Start here.** Everything that must be fixed, one issue per problem, labelled `priority: P0`–`P3` |
| 01 | [Architecture](01-architecture.md) | Goals, target architecture diagram, decision log, free-tier constraints |
| 02 | [Current state](02-current-state.md) | Audit of the repo today: models, endpoints, issue register, unmerged branches |
| 03 | [API contract](03-api-contract.md) | Target v2 API: conventions, endpoints, JSON shapes. The frontend builds against this. |
| 04 | [Backend plan](04-backend-plan.md) | Work items BE-00…BE-10 and which issues they resolve |
| 05 | [Frontend plan](05-frontend-plan.md) | React stack, structure, routes, work items FE-01…FE-10 |
| 06 | [Configuration](06-configuration.md) | Environment variables for both apps, local dev setup |
| 07 | [Deployment](07-deployment.md) | Neon, Render, Cloudflare, CI, seeding, OPS-01…OPS-06 |
| 08 | [Roadmap](08-roadmap.md) | Milestones M0–M6 and open questions |
| 09 | [References](09-references.md) | External links |
| — | [architecture-plan.md](architecture-plan.md) | The original single-file plan (2026-10-08) that the docs above were split from. The numbered docs and the issues are more detailed and take precedence where they differ. |

## Shared with the frontend repo

Copy these into the frontend repo's `docs/` folder and keep them in sync: [01-architecture.md](01-architecture.md), [03-api-contract.md](03-api-contract.md), [05-frontend-plan.md](05-frontend-plan.md), [06-configuration.md](06-configuration.md). When they disagree, **this repo's [03-api-contract.md](03-api-contract.md) wins**, because the backend owns the contract.

## Conventions

| Item | Meaning | Where |
|---|---|---|
| `#N` | A concrete defect or gap, with evidence and acceptance criteria | [GitHub issues](https://github.com/pirrozani/django-api/issues), template [`.github/ISSUE_TEMPLATE/fix.md`](../.github/ISSUE_TEMPLATE/fix.md) |
| `priority: P0`…`P3` | P0 = won't run locally · P1 = blocks deploy/frontend, or security · P2 = API quality the frontend needs · P3 = hygiene/portfolio | issue labels |
| `BE-NN` | Backend work item (groups issues + new features) | [04-backend-plan.md](04-backend-plan.md) |
| `FE-NN` | Frontend work item | [05-frontend-plan.md](05-frontend-plan.md) |
| `OPS-NN` | Deployment/operations task | [07-deployment.md](07-deployment.md) |
| `D#`, `Q#`, `M#` | Decision, open question, milestone | [01](01-architecture.md), [08](08-roadmap.md) |
| `A#`, `L#` | Audit finding | [02-current-state.md](02-current-state.md) |

## Recommended issue order

1. **M0, make it run:** #1 → #2
2. **Security first:** #3
3. **Upgrade on a working base:** #4
4. **Production settings:** #5 → #6 → #7 → #8
5. **Frontend-facing API:** #9 → #10 → #11 → #12 → #13
6. **Throughout:** #14 (add tests alongside each fix)

## Keeping docs current

- Fixing an issue → open a PR with `Closes #N`; merging it closes the issue.
- Changing an endpoint → update [03-api-contract.md](03-api-contract.md) in the same PR.
- New problem found → `/issue <description>` in Claude Code, or "New issue → Fix" on GitHub. Add it to the issue register in [02-current-state.md](02-current-state.md).
- New decision → add a row to the decision log in [01-architecture.md](01-architecture.md).

Claude Code helpers in this repo: `/issue`, `/resolve-issue`, `/pr`, `/health-check`, `/api-sync`, and the `api-reviewer` agent (see `CLAUDE.md`).
