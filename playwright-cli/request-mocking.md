# Request Mocking

Mock third-party services, deterministic failure modes, and rare edge cases. Avoid mocking the application behavior the test is meant to verify.

## CLI routes

```bash
playwright-cli route "**/*.png" --status=404
playwright-cli route "**/api/recommendations" --body='{"items":[]}'
playwright-cli route "**/api/health" --status=503
playwright-cli route-list
playwright-cli unroute "**/api/health"
playwright-cli unroute
```

Patterns commonly use:

- `**/api/users` for an exact path on any host.
- `**/api/users/**` for nested resources.
- `**/*.{png,jpg,jpeg,gif,webp}` for asset groups.

Register routes before navigation or before the request-triggering action.

## TypeScript response mocking

```typescript
import { test, expect } from '@playwright/test';

test('renders an empty state', async ({ page }) => {
  await page.route('**/api/products', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ products: [] }),
    }),
  );

  await page.goto('/products');
  await expect(page.getByText('No products found')).toBeVisible();
});
```

## Conditional routing

```typescript
await page.route('**/api/items/**', async route => {
  const request = route.request();

  if (request.method() === 'DELETE') {
    await route.fulfill({ status: 403, body: 'Forbidden' });
    return;
  }

  await route.continue();
});
```

Call exactly one of `fulfill`, `continue`, `fallback`, or `abort` for every handled request.

## Modify a real response

```typescript
await page.route('**/api/profile', async route => {
  const response = await route.fetch();
  const body = await response.json();
  await route.fulfill({
    response,
    json: { ...body, experimentalFeature: true },
  });
});
```

Use `fetch` when most of the real response should remain intact. Avoid it when the test must run fully offline.

## Failures and latency

```typescript
await page.route('**/api/payment', route => route.abort('connectionrefused'));

await page.route('**/api/search', async route => {
  await new Promise(resolve => setTimeout(resolve, 1_500));
  await route.continue();
});
```

Keep artificial delays short and targeted. Prefer asserting the loading state over adding fixed waits to the test.

## Request verification

```typescript
const requests: string[] = [];
page.on('request', request => {
  if (request.url().includes('/api/analytics')) requests.push(request.url());
});

await page.getByRole('button', { name: 'Buy' }).click();
expect(requests).toHaveLength(1);
```

For a single known request, `page.waitForRequest()` or `page.waitForResponse()` is simpler.

## GraphQL

Inspect `request.postDataJSON().operationName` and fulfill only the intended operation. Let unrelated operations continue.

## HAR replay

Use HAR recording when many stable third-party requests must be replayed together. Sanitize secrets before saving a HAR, keep it out of public repositories when it contains sensitive data, and refresh it when the upstream contract changes.

## Checklist

- Scope patterns narrowly.
- Register routes before requests begin.
- Keep response shape faithful to the real contract.
- Remove ad hoc routes with `unroute`.
- Never record secrets or production personal data in fixtures.
