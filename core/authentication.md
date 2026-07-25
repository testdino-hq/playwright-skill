# Authentication Testing

> **When to use**: Any app that has login, session management, or protected routes. Authentication is the most common source of slow test suites -- get this right and your entire suite speeds up.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Storage State Reuse** -- You need authenticated tests and want to avoid logging in before every test. This is the default pattern for nearly every project.
- **In-Place State Refresh With `setStorageState()` (Playwright 1.59+)** -- You already have a browser context open and want to replace its cookies and local storage without destroying the context and creating a new one.
- **Global Setup Authentication** -- You want to authenticate once before the entire test suite runs, then reuse that session everywhere. The standard Playwright-recommended approach.
- **Per-Worker Authentication** -- Each parallel worker needs its own authenticated session to avoid race conditions. Essential when tests modify user state (profile updates, settings changes, data mutations).
- **Multiple Roles** -- Your app has role-based access control and you need to test that admins, regular users, and viewers see different things.
- **OAuth/SSO Mocking** -- Your app authenticates via a third-party OAuth provider (Google, GitHub, Okta, Auth0) and you cannot or should not hit the real provider in tests.
- **MFA Handling** -- Your app requires two-factor authentication (TOTP, SMS, email codes) and you need to handle it in tests.
- **Session Refresh** -- Your tokens expire during long test runs or your app uses short-lived JWTs that need refreshing.
- **Login Page Object** -- Multiple test files need to log in and you want consistent, maintainable login logic with proper error handling.
- **API-Based Login** -- You want the fastest possible authentication without any browser interaction. Ideal for generating `storageState` files in global setup or fixtures.
- **Unauthenticated Tests** -- Testing the login page, signup flow, password reset, public pages, authentication error handling, or redirect behavior for unauthenticated users.
- **UI Login vs API Login vs Storage State**
- **Global setup fails with "Target page, context or browser has been closed"** -- The login page redirected unexpectedly, or the browser closed before `storageState()` was called. Common when the login URL requires HTTPS but your test server uses HTTP.
- **Tests fail with 401 Unauthorized after running for a while** -- The session token saved in `storageState` has expired. Short-lived JWTs (15-minute expiry) will not survive a long test suite.
- **`storageState` file is empty or contains no cookies** -- `storageState()` was called before the login response set cookies. The login may be async (POST returns, then a redirect sets the cookie).
- **Different browsers get different cookies (cross-browser auth issues)** -- Some auth flows set cookies with `SameSite=Strict` or use browser-specific cookie behavior. Chromium and Firefox handle third-party cookies differently.
- **Parallel tests interfere with each other's sessions** -- Multiple workers share the same test account and one worker's actions (logout, password change, session invalidation) affect others.
- **OAuth mock does not work — still redirects to real provider** -- `page.route()` was registered after the navigation that triggers the OAuth redirect, or the route pattern does not match the actual redirect URL.

## Decision table

| Scenario | Approach | Speed | Isolation | When to Choose |
|---|---|---|---|---|
| Most tests need auth | Global setup + `storageState` | Fastest | Shared session | Default for nearly every project. Login happens once, all tests reuse the session file. |
| Tests modify user state | Per-worker fixture | Fast | Per worker | Tests update profile, change settings, or mutate data that could conflict between parallel workers. |
| Multiple user roles | Per-project `storageState` | Fastest | Per role | App has admin/user/viewer roles. Each project gets its own state file from global setup. |
| Testing the login page | No `storageState` | N/A | Full | Use `test.use({ storageState: { cookies: [], origins: [] } })` to override defaults. |
| OAuth/SSO provider | Mock the callback | Fast | Per test | Never hit real OAuth providers in CI. Mock the redirect or use API session injection. |
| MFA is required | TOTP generation or bypass | Moderate | Per test | Generate real TOTP codes from a shared secret, or use a test-mode bypass code. |
| Token expires mid-suite | Session refresh fixture | Fast | Per check | Fixture validates the session before use and re-authenticates if expired. |
| Single test needs different user | `loginAs(role)` fixture | Moderate | Per call | Rare: prefer per-project roles. Use when a single test must compare two roles side by side. |
| API-first app (no login UI) | API login via `request.post()` | Fastest | Per test | No browser needed for auth. Hit the API directly and capture cookies. |
| CI with long-running suites | API login + session check | Fastest | Per worker | Combine API login speed with session refresh for reliability over long runs. |

## TypeScript patterns

### Quick Reference

```typescript
// Storage state reuse — the #1 pattern for fast auth
await page.goto('/login');
await page.getByLabel('Email').fill('user@test.com');
await page.getByLabel('Password').fill('password');
await page.getByRole('button', { name: 'Sign in' }).click();
await page.context().storageState({ path: '.auth/user.json' });

// Reuse in config — every test starts authenticated, zero login overhead
{ use: { storageState: '.auth/user.json' } }

// API login — skip the UI entirely
const context = await browser.newContext();
const response = await context.request.post('/api/auth/login', {
  data: { email: 'user@test.com', password: 'password' },
});
await context.storageState({ path: '.auth/user.json' });
```

### Storage State Reuse

```typescript
// scripts/save-auth-state.ts — run once to generate the state file
import { chromium } from '@playwright/test';

async function saveAuthState() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('http://localhost:3000/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('s3cure!Pass');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');

  // Save cookies + localStorage to a file
  await context.storageState({ path: '.auth/user.json' });
  await browser.close();
}

saveAuthState();
```

## Guardrails

- **Storage State Reuse:** Tests require completely fresh sessions with no prior state, or you are testing the login flow itself.
- **In-Place State Refresh With `setStorageState()` (Playwright 1.59+):** Starting a brand-new isolated context is simpler, or when the test itself is validating the login flow from scratch.
- **Global Setup Authentication:** Different tests need different users, or your tokens expire faster than your suite runs.
- **Per-Worker Authentication:** Tests are read-only and a shared session is safe, or you only run tests serially.
- **Multiple Roles:** Your app has a single user role.
- **OAuth/SSO Mocking:** You have a dedicated test tenant on the OAuth provider and want true end-to-end coverage of the OAuth flow.
- **MFA Handling:** MFA is optional and you can disable it for test accounts.
- **Session Refresh:** Your test suite runs in under a few minutes and tokens outlast the entire run.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- custom fixtures for auth setup and teardown
- [core/configuration.md](configuration.md) -- `storageState`, projects, and global setup configuration
- [ci/global-setup-teardown.md](../ci/global-setup-teardown.md) -- global setup patterns and project dependencies
- [core/network-mocking.md](network-mocking.md) -- route interception patterns used in OAuth mocking
- [core/api-testing.md](api-testing.md) -- API request context used in API-based login
- [core/flaky-tests.md](flaky-tests.md) -- diagnosing auth-related flakiness
- [core/auth-flows.md](auth-flows.md) -- complete recipes for specific auth providers (Auth0, Okta, Firebase)
