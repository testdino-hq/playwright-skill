# Error States and Edge Cases

> **When to use**: Testing how your application handles errors, failures, boundary conditions, and unusual user behavior. These tests catch bugs that happy-path tests miss.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/network-mocking.md](network-mocking.md) for route interception

## Topic map

- **HTTP Error Status Codes** -- Testing that your application displays appropriate error pages or messages for 4xx and 5xx responses.
- **Network Failure and Offline Mode** -- Testing how the app behaves when the network is down, requests fail, or the connection is intermittent.
- **Aborting on Unexpected Requests (`test.abort()`, Playwright 1.60+)** -- A route handler sees a request that should *never* happen (a call to a forbidden endpoint, a leaked third-party request, a missing mock), and you'd rather fail loudly at the source than chase a confusing downstream as...
- **Empty States and Boundary Testing** -- Testing what the UI shows when there is no data, when inputs are at their minimum or maximum values, or when inputs contain special characters.
- **Loading States and Skeletons** -- Verifying that loading indicators, skeleton screens, or spinners appear during data fetching and disappear when data arrives.
- **Retry Behavior Testing** -- Testing that the application retries failed requests automatically or via a user-triggered "retry" button.
- **Browser Back/Forward Navigation** -- Testing that the application handles browser history navigation correctly — preserving state, URL updates, and content after going back or forward.
- **Concurrent User Actions** -- Testing that rapid user interactions do not cause race conditions — double-clicking submit, typing while data is loading, navigating during an async operation.
- **Graceful Degradation** -- Testing that the app continues to function when non-critical services fail (analytics, chat widget, recommendations).
- **Route handler is not intercepting requests** -- The URL pattern does not match, or the route was registered after the navigation that triggers the request.
- **`context.setOffline(true)` does not affect Service Worker** -- Service Workers have their own network handling. `setOffline` simulates offline at the browser level, but a Service Worker may serve cached responses.
- **Delayed route handler causes test timeout** -- The promise in the route handler never resolves, or the delay exceeds the test timeout.
- **`goBack()` does not navigate** -- There is no history entry to go back to. `goBack()` requires at least one previous navigation.

## Decision table

| Scenario | Approach | Key API |
|---|---|---|
| 404 page | Navigate to non-existent URL, assert error page | `page.goto('/nonexistent')` |
| 500 server error | Mock route with `status: 500` | `page.route(url, route => route.fulfill({ status: 500 }))` |
| Network failure | Abort the route | `route.abort('connectionfailed')` |
| Offline mode | Toggle offline on the browser context | `page.context().setOffline(true)` |
| Slow response | Delay route fulfillment with a Promise | `await new Promise(r => setTimeout(r, delay))` in route handler |
| Empty state | Mock API to return empty array | `route.fulfill({ json: [] })` |
| Boundary values | Fill inputs with min/max/special values | `locator.fill('A'.repeat(255))` |
| Loading skeleton | Delay route, assert skeleton visible, release, assert content | Promise-based route handler |
| Retry behavior | Track route call count, fail first N, succeed after | Counter in route handler |
| Browser history | Use `page.goBack()` and `page.goForward()` | Assert URL and content after navigation |
| Double submit | `dblclick()` on submit, verify single POST | Track requests in route handler |
| Third-party failure | Abort non-critical routes, verify core works | `route.abort()` on optional services |
| Console error monitoring | Listen for `pageerror` event | `page.on('pageerror', handler)` |

## TypeScript patterns

### Quick Reference

```typescript
// Mock a 500 server error
await page.route('**/api/data', (route) => route.fulfill({ status: 500 }));

// Simulate offline mode
await page.context().setOffline(true);

// Test empty state
await page.route('**/api/items', (route) =>
  route.fulfill({ status: 200, json: [] })
);

// Browser back/forward
await page.goBack();
await page.goForward();

// Abort a network request (simulate network failure)
await page.route('**/api/save', (route) => route.abort('connectionfailed'));
```

### Aborting on Unexpected Requests (`test.abort()`, Playwright 1.60+)

```typescript
import { test, expect } from '@playwright/test';

test('fails fast if the app calls a forbidden endpoint', async ({ page }) => {
  await page.route('**/api/**', (route) => {
    const url = route.request().url();
    if (url.includes('/api/admin/delete-all')) {
      // Stop now with a precise message instead of letting the page error out
      test.abort(`Blocked dangerous request: ${url}`);
    }
    return route.continue();
  });

  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Guardrails

- **HTTP Error Status Codes:** The error is handled silently (no user-facing feedback). Test via API or logs instead.
- **Network Failure and Offline Mode:** The app has no offline or error handling behavior to test.
- **Aborting on Unexpected Requests (`test.abort()`, Playwright 1.60+):** You can assert the condition in the test body — use `expect()` there. `test.abort()` shines in route handlers and fixtures, which run outside the test body.
- **Empty States and Boundary Testing:** Never. Every feature should have empty state and boundary tests.
- **Loading States and Skeletons:** The application renders synchronously with no loading indicators (SSR without client-side fetching).
- **Retry Behavior Testing:** The application has no retry mechanism.
- **Browser Back/Forward Navigation:** The app is a single-page application that does not use the browser history API. Focus on client-side routing tests instead.
- **Concurrent User Actions:** The UI has no async operations that could conflict with user actions.

## Related guides

- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- assertion strategies for error states
- [core/network-mocking.md](network-mocking.md) -- detailed network interception and mocking patterns
- [core/forms-and-validation.md](forms-and-validation.md) -- form validation error testing
- [core/flaky-tests.md](flaky-tests.md) -- fixing timing issues in error/edge case tests
- [core/service-workers-and-pwa.md](service-workers-and-pwa.md) -- offline-first and PWA testing patterns
- [core/multi-context-and-popups.md](multi-context-and-popups.md) -- testing concurrent browser contexts
