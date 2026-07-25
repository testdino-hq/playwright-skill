# Network Mocking

> **When to use**: Isolating your frontend from external services, simulating error states, testing loading/empty/error UI, speeding up tests by avoiding real network calls, and testing against APIs that don't exist yet.
> **Prerequisites**: [core/locators.md](locators.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Route Interception Basics** -- You need to intercept any HTTP request made by the page to fulfill, modify, or block it.
- **Mocking REST Responses** -- Your frontend depends on a REST API and you want deterministic, instant responses with controlled data.
- **Mocking GraphQL** -- Your frontend uses GraphQL and you want to mock specific queries or mutations by operation name.
- **Modifying Responses** -- You need the real API response but want to tweak specific fields -- inject test data, override feature flags, simulate edge cases in real data.
- **Request Blocking** -- Blocking analytics, ads, third-party scripts, images, or fonts to speed up tests and eliminate flakiness from external dependencies.
- **HAR Recording and Replay** -- You want to capture real network traffic once and replay it in tests for speed and determinism. Great for complex APIs with many endpoints or when API access is limited.
- **On-Demand HAR Recording in Tracing (Playwright 1.60+)** -- You want to capture network traffic for a *specific slice* of a test — one user flow, one step — instead of the whole session, and you want to start/stop recording from inside the test body.
- **Conditional Mocking** -- You need different responses based on the request method, body, headers, or query parameters. Common for paginated APIs, search endpoints, and role-based access.
- **Network Error Simulation** -- Testing how your UI handles server errors, timeouts, and connection failures. Essential for verifying error boundaries, retry logic, and degraded-mode UX.
- **Request Waiting** -- Synchronizing your test with network activity -- waiting for a request to be sent or a response to arrive before asserting on the UI.
- **Glob Patterns and URL Matching** -- You need to match URLs with wildcards, partial paths, or regex. Every `page.route()`, `waitForRequest()`, and `waitForResponse()` accepts glob patterns, strings, or regex.
- **Route handler never fires** -- The URL pattern does not match the actual request URL. Common when the base URL includes a port number, path prefix, or the request uses a different protocol.
- **Route handler fires but test still times out** -- The handler throws an error or never calls `fulfill`/`continue`/`abort`.
- **Mocked response is ignored -- app shows real data** -- The route is registered at the page level but the request is made by a service worker or a different browser context.
- **`route.fetch()` causes infinite loop** -- Playwright handles this correctly for the same route handler -- `route.fetch()` will not re-enter the handler that called it. But if you have multiple overlapping route handlers, they can interfere. Simplify to a sing...
- **HAR replay returns wrong responses** -- HAR files match requests by URL and sometimes by POST body. If the request body changes (e.g., timestamps, CSRF tokens), the match fails.

## Decision table

| Scenario | Use | Why |
|---|---|---|
| Frontend depends on an external API | `route.fulfill()` | Deterministic data, no external dependency, fast |
| Need to test real API but tweak one field | `route.fetch()` + modify + `route.fulfill()` | Uses real data as baseline, only overrides what you need |
| Testing happy path with real backend | `route.continue()` (or no route) | Full integration coverage |
| Block analytics/ads/third-party noise | `route.abort()` | Faster tests, no flakiness from external services |
| Complex API with many endpoints | `page.routeFromHAR()` with `update: true` | Record once, replay forever; minimal test code |
| Testing error handling (500, timeout) | `route.fulfill({ status: 500 })` or `route.abort('timedout')` | Simulate errors deterministically |
| Verify request payload sent by frontend | `page.waitForRequest()` + assertions | Confirms frontend sends correct data |
| Verify response data before UI check | `page.waitForResponse()` + assertions | Confirms data arrives before asserting on DOM |
| Multiple tests need the same mock | `context.route()` or fixture | Share routes across tests without repetition |
| Testing loading spinners / skeleton UI | `route.fulfill()` with a delay (via `setTimeout`) | Control exact timing of response |
| Paginated or search-based API | Conditional mock (check query params / body) | Dynamic responses based on request content |

## TypeScript patterns

### Quick Reference

```typescript
// Intercept and return fake data
await page.route('**/api/users', (route) =>
  route.fulfill({ json: [{ id: 1, name: 'Jane' }] })
);

// Modify a real response before it reaches the browser
await page.route('**/api/users', async (route) => {
  const response = await route.fetch();
  const json = await response.json();
  json.push({ id: 999, name: 'Injected' });
  await route.fulfill({ response, json });
});

// Block third-party scripts
await page.route('**/*.{png,jpg,svg}', (route) => route.abort());

// Wait for a specific request/response
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load' }).click();
await responsePromise;

// HAR replay — serve recorded responses
await page.routeFromHAR('tests/data/api.har', { url: '**/api/**' });
```

### Route Interception Basics

```typescript
import { test, expect } from '@playwright/test';

test('route interception basics', async ({ page }) => {
  // Intercept before navigating — routes must be set up first
  await page.route('**/api/users', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 1, name: 'Alice' }]),
    });
  });

  await page.goto('/dashboard');
  await expect(page.getByText('Alice')).toBeVisible();

  // Remove the route when done (important for cleanup)
  await page.unroute('**/api/users');
});

test('context-level routes apply to all pages', async ({ context, page }) => {
  // Routes on the context apply to every page in that context
  await context.route('**/api/config', (route) =>
    route.fulfill({ json: { theme: 'dark', locale: 'en' } })
  );

  await page.goto('/settings');
  await expect(page.getByText('Dark')).toBeVisible();
});
```

## Guardrails

- **Route Interception Basics:** You want to test the real integration between frontend and backend (use real API calls instead).
- **Mocking REST Responses:** You need to verify that your frontend sends the correct request body or headers to the real API (use `route.continue()` with `waitForRequest` instead).
- **Mocking GraphQL:** The GraphQL endpoint is part of your own backend and you want full integration coverage.
- **Modifying Responses:** You can fully mock the response. `route.fetch()` adds a real network round-trip, so it is slower.
- **Request Blocking:** The blocked resource is required for the feature under test.
- **HAR Recording and Replay:** API responses change frequently and stale recordings would cause false passes. Keep HAR files in version control and update them regularly.
- **On-Demand HAR Recording in Tracing (Playwright 1.60+):** You only need replay for mocking (use `routeFromHAR`), or you want HAR for the entire context (set `recordHar` at context creation). This API is for scoped, programmatic capture.
- **Conditional Mocking:** Simple static mocking suffices. Don't over-engineer route handlers.

## Related guides

- [core/when-to-mock.md](when-to-mock.md) -- decision framework for when to mock vs use real services
- [core/api-testing.md](api-testing.md) -- testing REST and GraphQL APIs directly (without a browser)
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- web-first assertions and `waitForResponse` patterns
- [core/authentication.md](authentication.md) -- mocking auth tokens and session state
- [core/error-and-edge-cases.md](error-and-edge-cases.md) -- error state testing patterns beyond network errors
- [core/service-workers-and-pwa.md](service-workers-and-pwa.md) -- handling service worker caching that interferes with mocks
