# TypeScript Test Generation

Every CLI interaction exposes the equivalent Playwright action. Use the CLI to explore an authorized flow, then assemble the emitted actions into a focused TypeScript test.

## Record a flow

```bash
playwright-cli open http://localhost:3000/login
playwright-cli snapshot
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "$TEST_PASSWORD"
playwright-cli click e3
playwright-cli snapshot
playwright-cli close
```

Re-snapshot after navigation or substantial DOM changes. Copy semantic locator output, not ephemeral ref numbers, into the test.

## TypeScript result

```typescript
import { test, expect } from '@playwright/test';

test('user can sign in', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

Do not copy secrets from shell history. Replace recorded values with environment variables, fixtures, or test-data builders.

## Locator priority

Prefer, in order:

1. `getByRole()` with accessible name.
2. `getByLabel()` for form fields.
3. `getByPlaceholder()` or `getByText()` when semantics are unavailable.
4. `getByTestId()` for stable application contracts.
5. CSS only when no user-facing or explicit test contract exists.

Never carry snapshot refs such as `e12` into maintained tests.

## Add assertions

Generated actions describe what happened; assertions define what must be true:

```typescript
await expect(page).toHaveURL(/checkout/);
await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
await expect(page.getByTestId('cart-item')).toHaveCount(2);
await expect(page.getByRole('alert')).toContainText('Payment failed');
```

Assert meaningful outcomes after each important transition, not every click.

## Parameterize repeated scenarios

```typescript
const cases = [
  { query: 'keyboard', expected: 'Mechanical Keyboard' },
  { query: 'monitor', expected: '4K Monitor' },
] as const;

for (const item of cases) {
  test(`finds ${item.expected}`, async ({ page }) => {
    await page.goto('/search');
    await page.getByRole('searchbox').fill(item.query);
    await page.getByRole('searchbox').press('Enter');
    await expect(page.getByRole('link', { name: item.expected })).toBeVisible();
  });
}
```

Keep each generated test about one behavior. Move shared setup to fixtures rather than creating long recordings.

## Stabilize the test

- Replace fixed sleeps with web-first assertions.
- Wait for the resulting URL, response, or visible state.
- Use `Promise.all` only when an action and event must start together.
- Add a trace on first retry in config.
- Run the test repeatedly before committing it.

## Review checklist

- The target and test account are authorized.
- Locators reflect user-visible semantics.
- No snapshot refs remain.
- All code and filenames use TypeScript (`.ts`).
- Secrets and generated auth state are gitignored.
- Assertions cover the intended behavior.
- Cleanup is handled by fixtures or context isolation.
