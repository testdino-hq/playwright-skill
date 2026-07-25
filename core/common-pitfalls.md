# Common Pitfalls

> **When to use**: When learning Playwright, reviewing tests for common mistakes, or onboarding new team members to your test suite.
The 20 most common Playwright mistakes, ordered by how frequently they appear in real codebases. Each pitfall includes the symptom, root cause, and a complete fix.

## Topic map

- **Pitfall 1: Using `page.waitForTimeout()` Instead of Assertions** -- Replace every `waitForTimeout` with a web-first assertion or an explicit wait for a specific condition.
- **Pitfall 2: Not Awaiting Async Operations** -- Always `await` every Playwright call. Enable the `@typescript-eslint/no-floating-promises` ESLint rule.
- **Pitfall 3: Using CSS Selectors Instead of Role-Based Locators** -- Use Playwright's built-in locators that target accessible roles, labels, text, and test IDs.
- **Pitfall 4: Asserting on `isVisible()` Return Value Instead of `expect().toBeVisible()`** -- Always use `expect(locator).toBeVisible()`, which auto-retries until the element appears or the timeout expires.
- **Pitfall 5: Sharing Mutable State Between Parallel Tests** -- Use test-scoped fixtures with unique data. Never store mutable state in module-level variables.
- **Pitfall 6: Not Using `baseURL` (Hardcoding Full URLs)** -- Set `baseURL` in `playwright.config` and use relative paths in all tests.
- **Pitfall 7: Using `page.$()` Instead of `page.locator()`** -- Always use `page.locator()`, `page.getByRole()`, or other locator methods.
- **Pitfall 8: Not Handling Navigation After Form Submission** -- Wait for the navigation to complete before asserting on the new page.
- **Pitfall 9: Testing Against `localhost` in CI Without `webServer` Config** -- Use the `webServer` config option to start your app automatically.
- **Pitfall 10: Using `innerHTML` for Text Assertions Instead of `toHaveText()`** -- Use `expect(locator).toHaveText()` or `expect(locator).toContainText()` for auto-retrying text assertions.
- **Pitfall 11: Over-Mocking (Mocking Your Own API)** -- Only mock external third-party services. Test your own API for real. Use `webServer` to run your backend during tests.
- **Pitfall 12: Not Using `test.describe` for Grouping** -- Group related tests with `test.describe`. Use it for scoping shared setup, configuration overrides, and logical organization.
- **Pitfall 13: Using `beforeAll` for Per-Test Setup** -- Use `beforeEach` for per-test setup, or use test-scoped fixtures for setup that needs teardown.
- **Pitfall 14: Storing Test Data in Variables Shared Between Tests** -- Each test must create its own data. Use fixtures for shared setup logic.
- **Pitfall 15: Deep Nesting of `test.describe` Blocks** -- Limit nesting to 2 levels maximum. Use separate files instead of deep nesting.
- **Pitfall 16: Not Configuring Retries Differently for Local vs CI** -- Zero retries locally (fail fast), 1-2 retries in CI (catch infrastructure blips).
- **Pitfall 17: Running All Browsers in Every CI Run** -- Run Chromium on every PR. Run all browsers in a nightly or pre-release job.
- **Pitfall 18: Using `page.evaluate()` for Things Locators Can Do** -- Use locator methods for all DOM interactions. Reserve `page.evaluate()` for things locators genuinely cannot do (reading computed styles, calling app-specific JS APIs, setting up test hooks).
- **Pitfall 19: Not Using `test.step()` for Complex Flows** -- Wrap logical phases in `test.step()`. Steps appear in traces, reports, and error messages.
- **Pitfall 20: Catching Errors from Assertions (try/catch Around expect)** -- Use `expect.soft()` for non-critical checks, `.not` assertions for absent elements, or restructure the test to avoid conditional logic.

## TypeScript patterns

### Pitfall 1: Using `page.waitForTimeout()` Instead of Assertions

```typescript
import { test, expect } from '@playwright/test';

// BAD
test('bad: arbitrary wait', async ({ page }) => {
  await page.goto('/dashboard');
  await page.getByRole('button', { name: 'Load' }).click();
  await page.waitForTimeout(3000);
  await expect(page.getByTestId('chart')).toBeVisible();
});

// GOOD
test('good: auto-retrying assertion', async ({ page }) => {
  await page.goto('/dashboard');
  await page.getByRole('button', { name: 'Load' }).click();
  await expect(page.getByTestId('chart')).toBeVisible();
});

// GOOD — when you need to wait for a specific network event
test('good: wait for response', async ({ page }) => {
  await page.goto('/dashboard');
  const responsePromise = page.waitForResponse('**/api/chart-data');
  await page.getByRole('button', { name: 'Load' }).click();
  await responsePromise;
  await expect(page.getByTestId('chart')).toBeVisible();
});
```

### Pitfall 2: Not Awaiting Async Operations

```typescript
import { test, expect } from '@playwright/test';

// BAD — missing await on click, assertion runs before navigation
test('bad: missing await', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('password');
  page.getByRole('button', { name: 'Sign in' }).click(); // MISSING AWAIT
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});

// GOOD
test('good: all actions awaited', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Related guides

- [core/locators.md](locators.md) -- locator strategy hierarchy (Pitfalls 3, 7, 18)
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- web-first assertions (Pitfalls 1, 4, 10, 20)
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- fixtures vs hooks (Pitfalls 5, 13, 14)
- [core/configuration.md](configuration.md) -- baseURL, webServer, retries (Pitfalls 6, 9, 16, 17)
- [core/test-organization.md](test-organization.md) -- describe blocks, nesting, tags (Pitfalls 12, 15)
- [core/flaky-tests.md](flaky-tests.md) -- diagnosing and fixing flaky tests (Pitfalls 1, 2, 5)
- [core/debugging.md](debugging.md) -- traces, UI mode, page.pause()
