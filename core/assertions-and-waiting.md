# Assertions and Waiting

> **When to use**: Every time you write an `expect()` call, wait for a condition, or wonder why a test is flaky due to timing.
> **Prerequisites**: [core/locators.md](locators.md) for locator strategies used in examples.

## Topic map

- **Web-First Assertions (Auto-Retry)** -- The style you care about lives on a `::before` or `::after` pseudo-element — icon glyphs (`content`), decorative bars, required-field asterisks, tooltips.
- **Non-Retrying Assertions** -- The value is already resolved — a JavaScript variable, an API response body, a page title from `page.title()`, or a URL from `page.url()`.
- **Negative Assertions** -- Verifying something has disappeared, been removed, or is not present.
- **Soft Assertions** -- You want to collect multiple failures in a single test without stopping at the first one. Common for form validation checks, dashboard content audits, or visual checklists.
- **Polling Assertions** -- Waiting for a non-DOM, non-locator async condition: API readiness, database state, file existence, polling a service.
- **Retrying Assertion Blocks with `toPass()`** -- Multiple assertions or actions must pass together as a group, and the whole block should be retried if any part fails. Common for race conditions where data appears incrementally.
- **Custom Matchers** -- Domain-specific assertions you repeat across many tests — valid price format, date range, accessible form, etc.
- **Auto-Waiting (Actionability)** -- You don't need to "use" this — understand it. Every Playwright action (`click`, `fill`, `check`, `selectOption`, etc.) auto-waits for the target element to be actionable before proceeding.
- **Explicit Waits** -- Waiting for navigation, network responses, or page load states that are not tied to a specific locator.
- **Assertion Timeouts** -- A specific assertion needs more or less time than the global default.
- **"Timed out 5000ms waiting for expect(...).toBeVisible()"** -- The element never appeared within the assertion timeout. Common reasons:
- **"expect.soft: Test finished with X failed assertions"** -- Check the HTML report (`npx playwright show-report`). Each soft failure is listed with its locator, expected value, and actual value. Group related soft assertions under `test.step()` for better readability.
- **"Expected '  Dashboard  ' to have text 'Dashboard'"** -- `toHaveText()` performs full text match including normalization, but whitespace mismatch still trips people up when elements have unusual rendering.

## Decision table

| Scenario | Recommended Approach | Why |
|---|---|---|
| Element visible / hidden | `expect(locator).toBeVisible()` / `.not.toBeVisible()` | Auto-retries, handles timing |
| Text content check | `expect(locator).toHaveText()` or `.toContainText()` | Auto-retries; use `toContainText` for substring |
| Element count | `expect(locator).toHaveCount(n)` | Retries until count matches |
| Input value | `expect(locator).toHaveValue('x')` | Auto-retries on the locator |
| Element attribute | `expect(locator).toHaveAttribute('href', '/x')` | Auto-retries |
| CSS property | `expect(locator).toHaveCSS('color', 'rgb(0,0,0)')` | Auto-retries; use computed RGB values. Add `{ pseudo: '::after' }` (1.60+) for pseudo-element styles |
| Element gone from DOM | `expect(locator).not.toBeAttached()` | Distinguishes hidden vs. removed |
| URL changed | `page.waitForURL('/path')` or `expect(page).toHaveURL('/path')` | `toHaveURL` auto-retries; `waitForURL` blocks |
| Page title | `expect(page).toHaveTitle('Title')` | Auto-retries |
| API response status | `expect(response.status()).toBe(200)` | Already resolved — non-retrying |
| Background job / polling | `expect.poll(() => fetchStatus())` | Retries a function, not a locator |
| Multiple assertions as one | `expect(async () => { ... }).toPass()` | Retries the entire block |
| Multiple independent checks | `expect.soft(locator)` | Collects all failures |
| Resolved JS value | `expect(value).toBe(x)` | No retry needed |

## TypeScript patterns

### Quick Reference

```typescript
// Web-first (auto-retry) — ALWAYS prefer these
await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
await expect(page.getByRole('heading')).toHaveText('Dashboard');
await expect(page.getByRole('listitem')).toHaveCount(5);

// Negative — auto-retries until condition is met
await expect(page.getByRole('dialog')).not.toBeVisible();

// Soft — collect failures, don't stop test
await expect.soft(page.getByRole('heading')).toHaveText('Title');

// Polling — non-DOM async conditions
await expect.poll(() => getUserCount()).toBe(10);

// Retry a block — multiple assertions that must pass together
await expect(async () => { /* assertions */ }).toPass();
```

### Web-First Assertions (Auto-Retry)

```typescript
import { test, expect } from '@playwright/test';

test('required field shows a red asterisk via ::after', async ({ page }) => {
  await page.goto('/register');

  const label = page.getByText('Email', { exact: true });

  // Verify the ::after content and color of the "required" marker
  await expect(label).toHaveCSS('content', '"*"', { pseudo: '::after' });
  await expect(label).toHaveCSS('color', 'rgb(220, 38, 38)', { pseudo: '::after' });
});
```

## Guardrails

- **Web-First Assertions (Auto-Retry):** The style is on the element itself; pass no `pseudo` option.
- **Non-Retrying Assertions:** Asserting on anything that might change asynchronously in the DOM. Use web-first assertions instead.
- **Negative Assertions:** Never.
- **Soft Assertions:** Subsequent assertions depend on the result of earlier ones (if the first fails, later assertions may be meaningless).
- **Polling Assertions:** The condition is about a DOM element. Use web-first assertions on locators.
- **Retrying Assertion Blocks with `toPass()`:** A single web-first assertion suffices.
- **Custom Matchers:** The assertion is only used in one test. Inline it.
- **Explicit Waits:** A web-first assertion on a locator would suffice.

## Related guides

- [core/locators.md](locators.md) — locator strategies used in assertion targets
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) — custom fixtures for reusable assertion setup
- [core/debugging.md](debugging.md) — debugging assertion failures with UI mode and traces
- [core/flaky-tests.md](flaky-tests.md) — fixing timing-related flakiness
- [core/error-index.md](error-index.md) — specific error messages and fixes
