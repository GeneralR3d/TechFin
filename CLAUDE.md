# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev          # start dev server on localhost:3000
npm run build        # production build (use to verify no TS/compile errors)

# Database
npx prisma migrate dev --name <name>   # create + apply a new migration
npx prisma generate                     # regenerate Prisma client after schema changes
npm run db:seed                         # seed demo user (demo-user-001)
npx prisma studio                       # GUI to inspect DB
```

If you hit node module errors: `rm -rf node_modules .next package-lock.json && npm install`

## Architecture

### Prisma 7 (critical differences from Prisma 5/6)
- **No `url` in `schema.prisma`** — datasource URL lives in `prisma.config.ts` only
- **`PrismaClient` requires an adapter** — uses `@prisma/adapter-pg` + `pg` for local Postgres
- The singleton in `src/lib/prisma.ts` creates a `PrismaPg` adapter from `process.env.DATABASE_URL`
- `prisma.config.ts` loads `.env.local` via `dotenv` before the CLI reads it

### Auth / User model
- No real auth. Single hardcoded demo user: `id = "demo-user-001"`
- `src/lib/demo-user.ts` exports `DEMO_USER_ID` (reads `process.env.DEMO_USER_ID`, falls back to `"demo-user-001"`)
- All API routes use `DEMO_USER_ID` for all DB queries

### API routes (`src/app/api/`)
- `holdings/route.ts` — GET (list), POST (upsert by userId+ticker)
- `holdings/[id]/route.ts` — DELETE
- `tickers/route.ts` — GET with `?q=` search against hardcoded list in `src/lib/tickers.ts`
- `yahoo-finance/route.ts` — calls RapidAPI; falls back to mock if key is placeholder
- `reddit/route.ts` — `?subreddit=` param; OAuth `client_credentials` with in-memory token cache; falls back to mock
- `social/twitter`, `social/linkedin` — always return mock data (boilerplate)
- `sentiment/route.ts` — always returns mock from `src/lib/sentiment/mock-sentiment.ts`
- `suggestions/route.ts` — stub: mirrors user's own holdings as suggestions
- `user/me/route.ts` — GET `hasOnboarded`
- `user/onboarded/route.ts` — PATCH sets `hasOnboarded = true`

### External API clients (`src/lib/api/`)
All clients follow the same pattern: try real API, catch/warn and return mock data on failure.
- `yahoo-finance.ts` — `fetch` with `next: { revalidate: 300 }`
- `reddit.ts` — module-level token cache, refreshes on expiry or 401
- `twitter.ts`, `linkedin.ts` — mock-only, marked with `// TODO: Replace with real ...`

### Frontend data fetching
SWR hooks in `src/hooks/` — one per data domain. `useHoldings` does optimistic updates for add/delete.

### First-login onboarding
`FirstLoginDialog` in root `layout.tsx` → `useFirstLogin` hook checks `/api/user/me`. On save: POST each holding → PATCH `/api/user/onboarded`. Dialog is non-dismissable (blocks `onInteractOutside`).

### Path alias
`@/*` → `./src/*` (configured in `tsconfig.json`). All imports use `@/`.
