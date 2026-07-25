# Testing Next.js Apps with Playwright

> **When to use**: Testing Next.js applications -- App Router, Pages Router, API routes, middleware, SSR pages, dynamic routes, and server components. This guide covers E2E testing patterns specific to Next.js behavior.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **Setup**
- **Playwright Config for Next.js** -- The single most important configuration detail: use `webServer` to let Playwright start and manage your Next.js server.
- **Environment Variables with `.env.test`** -- Next.js loads `.env.test` automatically when `NODE_ENV=test`. Use this for test-specific overrides.
- **Testing App Router Pages** -- Testing pages built with the Next.js App Router (`app/` directory). App Router pages are server components by default and may include streaming, suspense boundaries, and loading states.
- **Testing Pages Router (getServerSideProps / getStaticProps)** -- Testing pages built with the Pages Router (`pages/` directory) that use `getServerSideProps` or `getStaticProps` for data fetching.
- **Testing Dynamic Routes (`[slug]`, `[...catchAll]`)** -- Testing pages with dynamic segments like `/blog/[slug]`, `/products/[id]`, or catch-all routes like `/docs/[...path]`.
- **Testing API Routes** -- Testing Next.js API routes (`app/api/` or `pages/api/`) directly with Playwright's `request` context, or indirectly through UI interactions that call them.
- **Testing Middleware** -- Testing Next.js middleware that handles redirects, rewrites, authentication guards, geolocation-based routing, or header manipulation.
- **Testing Hydration and SSR/CSR Consistency** -- Verifying that server-rendered HTML matches the client-side hydrated output. Hydration mismatches cause visual flicker, broken interactivity, or React errors in the console.
- **Testing next/image Optimization** -- Verifying that `next/image` components render correctly, lazy load offscreen images, and serve optimized formats.
- **Authentication with NextAuth.js / Auth.js** -- Testing login flows in Next.js apps using NextAuth.js or Auth.js. Use a setup project to authenticate once, then reuse `storageState` across tests.
- **Framework-Specific Tips**
- **Dev Server vs Production Build**
- **Server Components Cannot Be Tested in Isolation** -- Next.js server components run on the server and produce HTML. Playwright tests the rendered output. You cannot import and render a server component in a Playwright test. Instead:
- **Handling Next.js Redirects** -- Next.js redirects (configured in `next.config.js`, middleware, or `redirect()` in server actions) are transparent to Playwright. After `page.goto()`, check `page.url()` to verify the final destination.
- **Turbopack Compatibility** -- If using Turbopack (`next dev --turbopack`), update your `webServer.command`:
- **Multiple webServer Entries (Next.js + API Backend)** -- If your Next.js app consumes a separate backend API:

## Decision table

| Don't Do This | Problem | Do This Instead |
|---|---|---|
| `await page.waitForTimeout(3000)` after navigation | Next.js client-side transitions are fast; arbitrary waits are wasteful and fragile | `await page.waitForURL('/expected-path')` or `await expect(locator).toBeVisible()` |
| Test `getServerSideProps` by importing and calling it directly | It depends on `context` (req/res) that Playwright cannot provide; it is a unit test concern | Navigate to the page and verify the rendered output |
| Mock your own API routes with `page.route()` | You are testing a fiction; your API handler may have bugs the mock hides | Let the real API route handle requests; mock only external services |
| Use `page.goto('http://localhost:3000/path')` with full URL | Breaks when port or host changes; ignores `baseURL` | Use `page.goto('/path')` and configure `baseURL` in config |
| Run `npm run build && npm run start` locally for every test run | Extremely slow feedback loop during development | Use `npm run dev` locally with `reuseExistingServer: true`; reserve production builds for CI |
| Test `next/image` by checking exact URL paths | `next/image` rewrites image URLs through `/_next/image`; paths change between dev and prod | Assert on `alt` text, visibility, `naturalWidth > 0`, and `srcset` existence |
| Skip `.env.test` and hardcode test values in config | Values scatter across config and test files; hard to maintain | Use `.env.test` for shared test values; `.env.test.local` for secrets |
| Test server actions by calling them as functions | Server actions are bound to the Next.js runtime; calling them outside a request context fails | Trigger server actions through their UI (form submissions, button clicks) |
| Ignore console errors during SSR tests | Hydration mismatches and server errors appear in the console and indicate real bugs | Listen for `page.on('console')` errors and fail the test if hydration warnings appear |

## TypeScript patterns

### Authentication with NextAuth.js / Auth.js

```typescript
// playwright.config.ts (auth-specific excerpt)
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'authenticated',
      use: { storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'unauthenticated',
      // No storageState -- tests run as logged-out user
      testMatch: '**/*.unauth.spec.ts',
    },
  ],
});
```

### Turbopack Compatibility

```typescript
webServer: {
  command: process.env.CI
    ? 'npm run build && npm run start'
    : 'npx next dev --turbopack',
  url: 'http://localhost:3000',
  reuseExistingServer: !process.env.CI,
},
```

## Guardrails

- **Testing App Router Pages:** You need to test isolated server component logic -- use unit tests for that. E2E tests verify the rendered result.
- **Testing Pages Router (getServerSideProps / getStaticProps):** Testing the data fetching functions directly -- that is a unit test concern. E2E tests verify what the user sees.
- **Testing Dynamic Routes (`[slug]`, `[...catchAll]`):** The route is static -- no dynamic segments involved.
- **Testing API Routes:** Unit testing API handler logic in isolation -- use a unit testing framework for that.
- **Testing Middleware:** The middleware logic is trivial -- a redirect from `/old` to `/new` can be verified with a simple navigation test.
- **Testing Hydration and SSR/CSR Consistency:** The page has no interactive client components -- pure server components do not hydrate.
- **Testing next/image Optimization:** You do not use `next/image` or image optimization is not a concern for your test.
- **Authentication with NextAuth.js / Auth.js:** Your app does not use session-based authentication.

## Related guides

- [core/configuration.md](configuration.md) -- base Playwright configuration patterns including `webServer`
- [core/authentication.md](authentication.md) -- authentication setup projects and `storageState` reuse
- [core/api-testing.md](api-testing.md) -- testing API routes directly with `request` context
- [core/network-mocking.md](network-mocking.md) -- mocking external APIs that Next.js API routes call
- [core/when-to-mock.md](when-to-mock.md) -- when to mock vs hit real services
- [core/react.md](react.md) -- React-specific patterns that apply to Next.js client components
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI setup with `npm run build` caching for Next.js
