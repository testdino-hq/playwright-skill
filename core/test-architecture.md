# Test Architecture: E2E vs Component vs API

> **When to use**: When deciding what kind of test to write for a feature. Before you write any test, ask: "What is the cheapest test that gives me confidence this works?"

## Topic map

- **Quick Answer** -- Most teams write too many E2E tests. Default to the **testing trophy** approach:
- **The Testing Trophy** -- The testing trophy (coined by Kent C. Dodds) replaces the traditional testing pyramid for modern web apps:
- **Decision Matrix**
- **When to Use E2E Tests**
- **When to Use Component Tests**
- **When to Use API Tests**
- **Combining Test Types** -- The most effective test suites layer all three types. Here is how they work together for a "user management" feature:
- **Layer 1: API Tests (60% of test count)** -- Cover every permutation of the backend logic. These are cheap to run and maintain.
- **Layer 2: Component Tests (30% of test count)** -- Cover every visual state and interaction of the UI components.
- **Layer 3: E2E Tests (10% of test count)** -- Cover only the critical path that proves the full stack works together.
- **The math** -- For this single feature, you might have:

## Decision table

| What You're Testing | Test Type | Why | Playwright Example |
|---|---|---|---|
| Login / auth flow | E2E | Cross-page, cookies, redirects, session state | Full browser flow with `storageState` |
| Form submission | Component | Isolated validation logic, error states, UX | Mount form component, test states |
| CRUD operations | API | Data integrity matters more than UI for create/update/delete | `request.post()`, `request.put()`, `request.delete()` |
| Search with results UI | Component + API | API test for query logic; component test for rendering results | Split: API for data, component for display |
| Cross-page navigation | E2E | Routing, history, deep linking are browser concerns | `page.goto()`, `page.waitForURL()` |
| Error handling (API errors) | API | Validate status codes, error shapes, edge cases without UI | `expect(response.status()).toBe(422)` |
| Error handling (UI feedback) | Component | Toast, banner, inline error rendering | Mount component, mock error response |
| Accessibility | Component | Test ARIA roles, keyboard nav per-component; faster than full E2E | `expect(locator).toHaveAttribute('aria-expanded')` |
| Responsive layout | Component | Viewport-specific rendering without full app overhead | `mount()` with viewport config |
| API integration (contract) | API | Validate response shapes, headers, auth independently | `request.get()` with schema validation |
| Real-time features (WebSocket) | E2E | Requires full browser environment for WebSocket connections | `page.evaluate()` with WebSocket listeners |
| Payment / checkout flow | E2E | Multi-step, third-party iframes, real-world reliability | Full browser flow, `frameLocator()` |
| Onboarding / wizard | E2E | Multi-step, state persists across pages | `test.step()` for each wizard stage |
| Individual widget behavior | Component | Toggle, accordion, date picker, modal -- isolated interactions | Mount component, test open/close/select |
| Permissions / authorization | API | Role-based access is backend logic; test without UI overhead | Request with different auth tokens |

## TypeScript patterns

### When to Use E2E Tests

```typescript
import { test, expect } from '@playwright/test';

// E2E: critical checkout flow -- this justifies the cost of a full browser
test.describe('checkout flow', () => {
  test.beforeEach(async ({ page }) => {
    // Seed data via API to keep E2E tests focused on the flow, not setup
    await page.request.post('/api/test/seed-cart', {
      data: { items: [{ sku: 'SHOE-001', qty: 1 }] },
    });
    await page.goto('/cart');
  });

  test('completes purchase with valid payment', async ({ page }) => {
    await test.step('review cart', async () => {
      await expect(page.getByRole('heading', { name: 'Your Cart' })).toBeVisible();
      await expect(page.getByText('Running Shoes')).toBeVisible();
      await page.getByRole('button', { name: 'Proceed to checkout' }).click();
    });

    await test.step('fill shipping details', async () => {
      await page.getByLabel('Full name').fill('Jane Doe');
      await page.getByLabel('Address').fill('123 Main St');
      await page.getByLabel('City').fill('Portland');
      await page.getByRole('combobox', { name: 'State' }).selectOption('OR');
      await page.getByLabel('ZIP code').fill('97201');
      await page.getByRole('button', { name: 'Continue to payment' }).click();
    });

    await test.step('enter payment', async () => {
      const paymentFrame = page.frameLocator('iframe[title="Payment"]');
      await paymentFrame.getByLabel('Card number').fill('4242424242424242');
      await paymentFrame.getByLabel('Expiration').fill('12/28');
      await paymentFrame.getByLabel('CVC').fill('123');
      await page.getByRole('button', { name: 'Place order' }).click();
    });

    await test.step('verify confirmation', async () => {
      await page.waitForURL('**/order/confirmation/**');
      await expect(page.getByRole('heading', { name: 'Order Confirmed' })).toBeVisible();
      await expect(page.getByText(/Order #\d+/)).toBeVisible();
    });
  });
});
```

## Related guides

- [core/test-organization.md](test-organization.md) -- file structure and naming conventions for each test type
- [core/api-testing.md](api-testing.md) -- deep-dive on Playwright's `request` API for HTTP testing
- [core/component-testing.md](component-testing.md) -- setting up and writing component tests with Playwright CT
- [core/authentication.md](authentication.md) -- auth flow testing patterns (E2E + `storageState` reuse)
- [core/when-to-mock.md](when-to-mock.md) -- when to mock network requests vs hit real services
- [pom/pom-vs-fixtures-vs-helpers.md](../pom/pom-vs-fixtures-vs-helpers.md) -- organizing shared test logic across layers
