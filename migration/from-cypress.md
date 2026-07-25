# Migrating from Cypress to Playwright

> **When to use**: Move a Cypress suite to TypeScript Playwright while preserving behavior, coverage, and CI confidence.

## Mindset shifts

- Replace queued command chains with explicit `async`/`await`.
- Replace global custom commands with typed fixtures, page objects, or helpers.
- Use lazy locators plus web-first assertions instead of retrying command chains.
- Treat tests as Node-based controllers of isolated browser contexts.
- Use multiple pages, contexts, and browsers directly when needed.
- Keep each test independent; seed state through APIs or fixtures.

## API mapping

| Cypress | TypeScript Playwright |
|---|---|
| `cy.visit(url)` | `await page.goto(url)` |
| `cy.get(selector)` | `page.locator(selector)` |
| `cy.contains(text)` | `page.getByText(text)` |
| `cy.findByRole(...)` | `page.getByRole(...)` |
| `.click()` | `await locator.click()` |
| `.type(value)` | `await locator.fill(value)` |
| `.should('be.visible')` | `await expect(locator).toBeVisible()` |
| `.should('have.text', value)` | `await expect(locator).toHaveText(value)` |
| `cy.url()` | `page.url()` or `expect(page).toHaveURL()` |
| `cy.intercept()` | `page.route()` |
| `cy.request()` | `request.get/post/...()` |
| `cy.session()` | Setup project plus `storageState` |
| `cy.within()` | Chain from a scoped locator |
| `cy.task()` | Call typed Node helpers or fixtures directly |

## TypeScript test

```typescript
import { test, expect } from '@playwright/test';

test('customer completes checkout', async ({ page }) => {
  await page.goto('/products');
  await page.getByRole('button', { name: 'Add to cart' }).click();
  await page.getByRole('link', { name: 'Cart' }).click();

  await expect(page.getByTestId('cart-item')).toHaveCount(1);
  await page.getByRole('button', { name: 'Checkout' }).click();
  await expect(page).toHaveURL(/checkout/);
});
```

Prefer role, label, and test-id locators over copied CSS selectors.

## Network interception

```typescript
test('shows an empty state', async ({ page }) => {
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

Register routes before navigation or the triggering action. Mock external dependencies and edge cases, not the application logic under test.

## Replace custom commands with fixtures

```typescript
import { test as base } from '@playwright/test';

type Fixtures = {
  createUser: (email: string) => Promise<string>;
};

export const test = base.extend<Fixtures>({
  createUser: async ({ request }, use) => {
    const created: string[] = [];
    await use(async email => {
      const response = await request.post('/api/test/users', { data: { email } });
      const user = await response.json() as { id: string };
      created.push(user.id);
      return user.id;
    });
    await Promise.all(created.map(id => request.delete(`/api/test/users/${id}`)));
  },
});
```

Use page objects for UI capabilities, fixtures for lifecycle, and helpers for stateless transformations.

## Authentication

Create an `auth.setup.ts` setup project, verify login, save `storageState`, and configure dependent projects to reuse it. Keep auth files gitignored and create one state file per role.

## Migration sequence

1. Install Playwright beside Cypress and use TypeScript defaults.
2. Match `baseURL`, timeouts, projects, and CI behavior.
3. Convert shared commands into fixtures, page objects, or helpers.
4. Establish reusable authenticated state.
5. Migrate one feature at a time, starting with stable critical paths.
6. Run both suites temporarily and compare coverage.
7. Convert interception and test-data setup.
8. Update CI artifacts, retries, and sharding.
9. Remove Cypress only after parity is verified.

## Common mistakes

- Carrying brittle CSS selectors into maintained tests.
- Using `waitForTimeout()` instead of an observable assertion.
- Forgetting `await` on actions or assertions.
- Registering routes after the request starts.
- Recreating global mutable state.
- Expecting `fill()` to emit every key event.
- Migrating giant files instead of vertical feature slices.

## Related guides

- [Locators](../core/locators.md)
- [Assertions and waiting](../core/assertions-and-waiting.md)
- [Fixtures and hooks](../core/fixtures-and-hooks.md)
- [Authentication](../core/authentication.md)
- [Network mocking](../core/network-mocking.md)
