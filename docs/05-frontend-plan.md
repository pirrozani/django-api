# 05 — Frontend plan (separate repo)

> Part of the [project docs](README.md). Copy this file (and [03-api-contract.md](03-api-contract.md), [06-configuration.md](06-configuration.md)) into the frontend repo as its starting point.

## Stack

| Concern | Choice |
|---|---|
| Build | Vite + React + TypeScript (strict) |
| Routing | React Router (v7, data/library mode) |
| Server state | TanStack Query v5 |
| HTTP | Thin `fetch` wrapper (or `openapi-fetch`) that injects `Authorization: Token <t>` and normalises errors |
| API types | `openapi-typescript` generated from `/api/schema/` → `src/api/schema.d.ts` |
| Forms | React Hook Form + Zod |
| Styling | Tailwind CSS (or CSS Modules; pick one and stay consistent) |
| Testing | Vitest + React Testing Library + MSW (mock API) |
| Quality | ESLint + Prettier + `tsc --noEmit` |
| Hosting | Cloudflare Workers static assets via `wrangler` |

## Proposed structure

```
frontend/
├─ src/
│  ├─ api/            # client.ts (fetch wrapper), schema.d.ts (generated), endpoints per resource
│  ├─ auth/           # AuthProvider, useAuth, RequireAuth route guard, token storage
│  ├─ features/
│  │  ├─ blogs/       # BlogListPage, BlogDetailPage, BlogFormPage, hooks (useBlogs, useBlog, mutations)
│  │  └─ users/       # UserListPage, UserDetailPage (+ their blogs), UserFormPage, hooks
│  ├─ components/     # Layout, Navbar, Pagination, ErrorState, EmptyState, Spinner, WakeUpBanner, ConfirmDialog
│  ├─ routes.tsx
│  └─ main.tsx
├─ src/mocks/         # MSW handlers
├─ wrangler.jsonc
├─ .env.example       # VITE_API_URL=
└─ README.md
```

## Routes

| Path | Page | Auth |
|---|---|---|
| `/` | Redirect to `/blogs` | public |
| `/login` | Login form → token | public |
| `/blogs` | Paginated list, search | public |
| `/blogs/:id` | Detail with author link | public |
| `/blogs/new`, `/blogs/:id/edit` | Create/edit form | required |
| `/users` | Paginated authors list | public |
| `/users/:id` | Author profile + their blogs | public |
| `/users/new`, `/users/:id/edit` | Create/edit form | required |
| `*` | 404 page | public |

Delete actions sit behind a confirm dialog and require auth.

## Work items

| ID | Work item | Done when |
|---|---|---|
| FE-01 | Scaffold: Vite React TS, ESLint/Prettier, Tailwind, Vitest, folders, `.env.example` | `npm run lint`, `typecheck`, `test`, `build` all pass on an empty app |
| FE-02 | API layer: `npm run gen:api` (`openapi-typescript $VITE_API_URL/api/schema/ -o src/api/schema.d.ts`); fetch wrapper with base URL, token header, JSON parsing, typed `ApiError` mapping DRF `detail` and field errors | Typed calls compile against the generated schema |
| FE-03 | Auth: login page, `AuthProvider` (token in `localStorage`, `/api/auth/me/` on boot), logout, `RequireAuth` guard, auto-logout on 401 | Protected routes redirect to `/login` and back after login |
| FE-04 | Blogs: list (pagination via `?page`, search), detail, create/edit form (author select from `/api/users/`), delete | Full CRUD against the local API |
| FE-05 | Users: list, profile with that author's blogs, create/edit (password on create, optional on edit), delete | Full CRUD against the local API |
| FE-06 | UX states: loading skeletons, empty states, error boundary, toasts for mutations, query invalidation | Every page handles loading/empty/error |
| FE-07 | Tests: MSW-backed tests for login, list + pagination, form validation, protected-route redirect | `npm test` green in CI |
| FE-08 | Wake-up banner: ping `/api/health/` on load. If there's no response in ~2 s, show "Waking up the free server, this can take up to a minute…" until it responds | Banner appears on a cold backend and disappears on response |
| FE-09 | Deploy: `wrangler.jsonc` with `assets.directory = "./dist"` and `assets.not_found_handling = "single-page-application"`; connect via Cloudflare Workers Builds; `VITE_API_URL` as a **build-time** variable | Deep links like `/blogs/3` work after refresh in production |
| FE-10 | README: screenshots/GIF, live link, demo credentials, stack, architecture | Linked from the backend README too |

## Token storage trade-off (document in the frontend README)

`localStorage` is used for simplicity on a demo app. It is readable by any XSS on the page; mitigations are React's default escaping, no `dangerouslySetInnerHTML`, and rotatable tokens (logout deletes the token server-side). HttpOnly cookies would be safer but don't work reliably cross-site (`workers.dev` ↔ `onrender.com`) without a shared custom domain ([08-roadmap.md](08-roadmap.md) Q2).
