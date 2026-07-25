# Page Objects vs Fixtures vs Helpers

> **When to use**: Decide where reusable Playwright code belongs and avoid abstractions that mix UI behavior, lifecycle management, and stateless utilities.

## Quick decision

| Reusable concern | Choose | Example |
|---|---|---|
| Interactions with a page or component | Page object | `checkout.submitOrder()` |
| Setup, teardown, or dependency injection | Fixture | authenticated page, seeded record |
| Stateless transformation or assertion | Helper | `uniqueEmail()`, `expectToast()` |
| One short action used once | Inline code | a single button click |

Ask:

1. Does it represent user behavior in one UI area? Use a page or component object.
2. Does it own a resource lifecycle or provide test-scoped state? Use a fixture.
3. Is it pure or stateless? Use a helper.
4. Does abstraction make the test harder to read? Keep it inline.

## Page object

```typescript
import type { Page } from '@playwright/test';

export class CheckoutPage {
  constructor(private readonly page: Page) {}

  async goto(): Promise<void> {
    await this.page.goto('/checkout');
  }

  async enterShipping(address: string, email: string): Promise<void> {
    await this.page.getByLabel('Address').fill(address);
    await this.page.getByLabel('Email').fill(email);
    await this.page.getByRole('button', { name: 'Continue' }).click();
  }

  async submitOrder(): Promise<void> {
    await this.page.getByRole('button', { name: 'Place order' }).click();
  }
}
```

Use when several tests repeat meaningful UI workflows. Avoid locator-only containers and methods that merely rename `click()` or `fill()`.

## Fixture

```typescript
import { test as base } from '@playwright/test';
import { CheckoutPage } from '../pages/checkout.page';

type Fixtures = {
  checkout: CheckoutPage;
  orderId: string;
};

export const test = base.extend<Fixtures>({
  orderId: async ({ request }, use) => {
    const response = await request.post('/api/test/orders');
    const order = await response.json() as { id: string };
    await use(order.id);
    await request.delete(`/api/test/orders/${order.id}`);
  },

  checkout: async ({ page }, use) => {
    await use(new CheckoutPage(page));
  },
});

export { expect } from '@playwright/test';
```

Use fixtures for test-scoped dependencies and guaranteed teardown. Keep each fixture focused, declare dependencies explicitly, and perform cleanup after `use()`.

## Helper

```typescript
import { expect, type Page } from '@playwright/test';

export function uniqueEmail(prefix = 'user'): string {
  return `${prefix}-${crypto.randomUUID()}@example.test`;
}

export async function expectToast(page: Page, text: string): Promise<void> {
  await expect(page.getByRole('status')).toContainText(text);
}
```

Prefer pure helpers. If a helper accumulates UI state or many locator operations, promote it to a page/component object.

## Combine the three

```typescript
import { test, expect } from '../fixtures/app.fixture';
import { uniqueEmail } from '../helpers/test-data';

test('customer places an order', async ({ checkout, orderId, page }) => {
  const email = uniqueEmail('buyer');
  await checkout.goto();
  await checkout.enterShipping('123 Test Street', email);
  await checkout.submitOrder();

  await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
  await expect(page.getByText(orderId)).toBeVisible();
});
```

Keep orchestration visible in the test: fixtures provide state, page objects perform UI behavior, and helpers create or verify values.

## Ownership boundaries

- Page objects may depend on Playwright `Page`, `Locator`, or component objects.
- Fixtures may construct page objects and call APIs for setup or cleanup.
- Helpers should not own browsers, contexts, or hidden lifecycle state.
- Tests should remain readable as user scenarios.
- API setup should not be buried inside UI methods.

## Anti-patterns

- Putting database cleanup in a page object.
- Making every helper a fixture.
- Creating fixtures that perform unrelated setup for all tests.
- Building page objects before repeated behavior exists.
- Hiding all assertions inside abstractions.
- Sharing mutable module-level state.
- Creating “utility” classes with unrelated methods.

## Related guides

- [Page Object Model](page-object-model.md)
- [Fixtures and hooks](../core/fixtures-and-hooks.md)
- [Test data management](../core/test-data-management.md)
- [Test architecture](../core/test-architecture.md)
