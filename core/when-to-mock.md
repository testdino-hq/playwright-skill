# When to Mock vs Use Real Services

> **When to use**: When deciding whether to mock API calls, intercept network requests, or hit real services in your Playwright tests.
> **Prerequisites**: [core/locators.md](locators.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Quick Answer** -- **Mock at the boundary, test your stack end-to-end.** Mock third-party services you do not own (Stripe, SendGrid, OAuth providers, analytics). Never mock your own frontend-to-backend communication. Your tests should p...
- **Decision Flowchart**
- **Decision Matrix**
- **Mocking Strategies**
- **Full Mock (route.fulfill)** -- You want to completely replace a third-party API response. The most common mocking strategy.
- **Partial Mock (Modify Responses)** -- You want the real API call to happen but need to tweak the response -- injecting error states, adding edge-case data, or overriding a single field.
- **Record and Replay (HAR Files)** -- Complex API sequences with many endpoints (OAuth flows, multi-step wizards, dashboard data loading). Record once from a real session, replay deterministically. Update the recording periodically so mocks do not drift f...
- **Blocking Unwanted Requests** -- Third-party scripts (analytics, ads, chat widgets) slow down tests and add no value. Block them outright.
- **Real Service Strategies**
- **Against Staging Environment** -- You have a shared staging environment that mirrors production. Best for integration confidence.
- **Against Local Dev Server** -- Fastest feedback loop. Run your backend locally and test against it.
- **Against Test Containers** -- You need a fully isolated environment with databases, caches, and services. Best for reproducible CI runs.
- **Hybrid Approach** -- The strongest test suites combine real and mocked services. The principle: **mock what you do not own, run what you do.**
- **Fixture-Based Mock Control** -- Create a fixture that lets individual tests opt into mocking specific services while keeping everything else real.
- **Environment-Based Mocking** -- Split test projects by environment to run mocked tests in every CI push and full-integration tests nightly.
- **Verifying Mock Accuracy** -- Mock responses drift from real APIs over time. Guard against this.

## Decision table

| Scenario | Mock? | Why | Strategy |
|---|---|---|---|
| Your own REST/GraphQL API | Never | This IS the integration you are testing | Hit real API against staging or local dev |
| Your database (through your API) | Never | Data round-trips are the whole point of E2E | Seed via API or fixtures, never mock DB |
| Authentication (your auth system) | Mostly no | Auth bugs are critical; test the real flow | Use `storageState` to skip login in most tests, but keep a few real login tests |
| Stripe / payment gateway | Always | Costs money, rate-limited, flaky in CI | `route.fulfill()` with expected responses |
| SendGrid / email service | Always | Side effects (real emails), no UI to assert | Mock the API call, verify request payload |
| OAuth providers (Google, GitHub) | Always | Redirect-heavy, rate-limited, CAPTCHAs | Mock token exchange, test your callback handler |
| Analytics (Segment, Mixpanel) | Always | Fire-and-forget, no UI impact, slows tests | `route.abort()` or `route.fulfill()` |
| Maps / geocoding APIs | Always | Rate-limited, paid, slow | Mock with static responses |
| Feature flags (LaunchDarkly, etc.) | Usually | Control test conditions deterministically | Mock to force specific flag states |
| CDN / static assets | Never | Already fast, part of your infra | Let them load normally |
| Flaky external dependency | CI: mock, local: real | Keeps CI green, catches real issues locally | Conditional mocking based on environment |
| Slow external dependency | Dev: mock, nightly: real | Fast feedback in dev, full integration in nightly | Separate test projects in config |

## TypeScript patterns

### Record and Replay (HAR Files)

```typescript
import { test } from '@playwright/test';

// Record HAR — run this once, then commit the .har file
test('record API traffic for dashboard', async ({ page }) => {
  await page.routeFromHAR('tests/fixtures/dashboard.har', {
    url: '**/api/**',
    update: true, // record mode: forwards requests and saves responses
  });

  await page.goto('/dashboard');
  // Interact with the page to capture all relevant API calls
  await page.getByRole('tab', { name: 'Analytics' }).click();
  await page.getByRole('tab', { name: 'Users' }).click();
  await page.getByRole('button', { name: 'Load more' }).click();

  // HAR file is saved automatically when the page closes
});
```

### Blocking Unwanted Requests

```typescript
import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Block analytics and tracking — they slow tests and add no coverage
  await page.route('**/{google-analytics,segment,hotjar,intercom}.{com,io}/**', (route) => {
    route.abort();
  });

  // Block all image requests in tests that don't need them
  // await page.route('**/*.{png,jpg,jpeg,gif,svg,webp}', (route) => route.abort());
});

test('page loads fast without third-party scripts', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Related guides

- [core/network-mocking.md](network-mocking.md) -- detailed network interception patterns and API
- [core/api-testing.md](api-testing.md) -- testing your API directly with `request` context
- [core/authentication.md](authentication.md) -- when to mock auth vs test real login flows
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- building reusable mock fixtures
- [core/configuration.md](configuration.md) -- `webServer`, `baseURL`, and project configuration
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI setup for different test tiers
