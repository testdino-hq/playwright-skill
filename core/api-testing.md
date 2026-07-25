# API Testing

> **When to use**: Testing REST or GraphQL APIs directly — validating endpoints, seeding test data, or verifying backend behavior without browser overhead.
> **Prerequisites**: [core/configuration.md](configuration.md) for `baseURL` setup, [core/fixtures-and-hooks.md](fixtures-and-hooks.md) for custom fixture patterns.

## Topic map

- **APIRequestContext Basics** -- Making HTTP requests in any test — GET, POST, PUT, PATCH, DELETE with headers, query params, and request bodies.
- **API Test Structure** -- Writing dedicated API test suites that do not need a browser.
- **Request Fixtures** -- Multiple tests need an authenticated API client, or you want to share request configuration (headers, base URL, auth tokens) across a test suite.
- **JSON Response Assertions** -- Validating response status, headers, and body structure after every API call.
- **GraphQL Testing** -- Your backend exposes a GraphQL API and you want to test queries, mutations, variables, and error handling.
- **API Data Seeding** -- E2E tests need specific data to exist before running. API seeding is 10-100x faster than UI-based setup.
- **Schema Validation** -- Verifying that API responses match a contract — field types, required fields, value constraints. Catches backend regressions early.
- **Error Response Testing** -- Every API has error paths. Test them. A missing 401 test today is a security hole tomorrow.
- **File Upload via API** -- Testing file upload endpoints with multipart form data — document uploads, image processing, CSV imports.
- **Chained API Calls** -- Testing multi-step workflows — create, read, update, delete sequences; order flows; state machine transitions. This verifies the API's behavior as an integrated system, not just isolated endpoints.
- **"Request failed: connect ECONNREFUSED 127.0.0.1:3000"** -- The API server is not running, or `baseURL` points to the wrong host/port.
- **"response.json() failed — body is not valid JSON"** -- The endpoint returned HTML (error page), plain text, or an empty body instead of JSON.
- **"401 Unauthorized" when using `request` fixture** -- The built-in `request` fixture does not carry browser cookies or auth tokens automatically. It starts with a clean slate.
- **GraphQL returns 200 but data is null** -- Always destructure and check both `data` and `errors`.
- **Tests pass locally but fail in CI** -- Different environments, database state, or missing environment variables.

## Decision table

| Scenario | Use API Tests | Use E2E Tests | Why |
|---|---|---|---|
| Validate response status/body/headers | Yes | No | No browser needed; 10-100x faster |
| Test business logic (calculations, rules) | Yes | No | API tests isolate backend logic from UI |
| Verify form submission creates correct data | Seed via API, submit via UI | Yes | UI test validates the form; API check confirms persistence |
| Test error messages shown to user | No | Yes | Error rendering is a UI concern |
| Validate pagination, filtering, sorting | Yes | Maybe both | API test for correctness; E2E test only if the UI logic is complex |
| Seed test data for E2E tests | Yes (fixture) | No | API seeding is fast and reliable |
| Test auth flows (login/logout/RBAC) | Yes for token/session logic | Yes for UI flow | Both matter: API protects resources, UI guides users |
| Verify file upload processing | Yes | Only if testing file picker UI | API test validates backend processing |
| Contract/schema regression testing | Yes | No | Schema tests run in milliseconds |
| Test third-party webhook handling | Yes | No | Webhooks are API-to-API; no UI involved |
| Verify redirect behavior after action | No | Yes | Redirects are browser/navigation concerns |
| Test real-time updates (WebSocket + API trigger) | API triggers | E2E verifies | Seed via API, observe in browser |

## TypeScript patterns

### Quick Reference

```typescript
// Standalone API test — no browser launched
import { test, expect } from '@playwright/test';

test('GET /api/users returns user list', async ({ request }) => {
  const response = await request.get('/api/users');
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('application/json');
  const body = await response.json();
  expect(body.users).toHaveLength(3);
  expect(body.users[0]).toMatchObject({ id: expect.any(Number), email: expect.any(String) });
});
```

### API Test Structure

```typescript
// playwright.config.ts — API project runs without a browser
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'api',
      testDir: './tests/api',
      use: {
        baseURL: 'https://api.example.com',
        extraHTTPHeaders: {
          'Accept': 'application/json',
        },
      },
    },
    {
      name: 'e2e',
      testDir: './tests/e2e',
      use: {
        baseURL: 'https://app.example.com',
        browserName: 'chromium',
      },
    },
  ],
});
```

## Guardrails

- **APIRequestContext Basics:** You need to test browser-rendered responses (redirects, cookies set via `Set-Cookie` with `HttpOnly`). Use a browser test instead.
- **API Test Structure:** You need to assert on UI state after an API call — use a combined test with `page` and `request` fixtures.
- **Request Fixtures:** A single test makes one-off API calls. Use the built-in `request` fixture directly.
- **JSON Response Assertions:** Never skip these. Every API test should assert on status and body.
- **GraphQL Testing:** Your API is purely REST. Use the standard HTTP methods instead.
- **API Data Seeding:** The test specifically validates the creation flow through the UI. Seed everything *except* what you are testing.
- **Schema Validation:** You only need to check one or two specific fields. Use `toMatchObject` instead.
- **Error Response Testing:** Never skip error testing.

## Related guides

- [core/configuration.md](configuration.md) — `baseURL`, `extraHTTPHeaders`, and `webServer` config
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) — custom fixture patterns for reusable API clients
- [core/authentication.md](authentication.md) — auth patterns including token-based API auth
- [core/network-mocking.md](network-mocking.md) — mocking API responses in E2E tests (opposite of this guide)
- [core/test-architecture.md](test-architecture.md) — when to use API tests vs E2E vs component tests
- [core/when-to-mock.md](when-to-mock.md) — when to hit real APIs vs mock them
