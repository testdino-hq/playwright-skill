# Locators

> **When to use**: Every time you need to find an element on the page. Start here before reaching for CSS or XPath.
> **Prerequisites**: [core/configuration.md](configuration.md)

## Topic map

- **Recent Locator Helpers (Playwright 1.59+)** -- Playwright 1.59 added two useful locator-discovery helpers:
- **`page.pickLocator()` For Interactive Discovery** -- You are exploring a page, debugging a selector, or migrating a legacy suite and want Playwright to suggest a locator for the element under your cursor.
- **`locator.normalize()` For Refactors** -- You inherit brittle CSS/XPath-heavy locators and want Playwright to suggest a more idiomatic form during cleanup work.
- **Role-Based Locators (Default Choice)** -- Always. This is your starting point for every element.
- **Label-Based Locators** -- Targeting form fields that have associated `<label>` elements or `aria-label`.
- **Text-Based Locators** -- Targeting non-interactive content — status messages, paragraphs, banners, labels outside forms.
- **Test ID Locators** -- No semantic locator works — the element has no accessible role, label, or stable text. Common with custom canvas-rendered components, complex data grids, or third-party widgets.
- **CSS/XPath — Last Resort** -- You have zero control over the markup, no test IDs, no accessible names, and no way to add them. Legacy apps with generated class names and no semantic HTML.
- **Locator Chaining and Filtering** -- A single locator matches multiple elements and you need to narrow down by context, content, or position.
- **Frame Locators** -- Interacting with content inside `<iframe>` or `<frame>` elements — payment widgets, embedded editors, third-party widgets.
- **Shadow DOM Piercing** -- Targeting elements inside web components that use Shadow DOM (custom elements, design system components, Salesforce Lightning).
- **Dynamic Content — Waiting for Elements** -- Elements appear after API calls, animations, lazy loading, or route transitions.
- **"strict mode violation" — locator matches multiple elements** -- Your locator is not specific enough and Playwright refuses to pick one for you.
- **Element exists but locator times out** -- The element is inside an iframe, Shadow DOM, or is obscured/hidden.
- **`getByRole` doesn't find the element** -- The element's implicit ARIA role doesn't match what you expect, or it has no role.

## Decision table

| Don't Do This | Problem | Do This Instead |
|---|---|---|
| `page.locator('.btn-primary')` | Breaks when CSS classes change (renames, CSS modules, Tailwind) | `page.getByRole('button', { name: 'Save' })` |
| `page.locator('#submit-btn')` | IDs are implementation details; often auto-generated | `page.getByRole('button', { name: 'Submit' })` |
| `page.locator('div > span:nth-child(3)')` | Breaks on any DOM restructure | `page.getByText('Expected content')` or `getByTestId()` |
| `page.locator('xpath=//div[@class="form"]//input[2]')` | Fragile, unreadable, position-dependent | `page.getByLabel('Last name')` |
| `page.getByText('Submit')` for a button | Text locators don't assert the element is interactive | `page.getByRole('button', { name: 'Submit' })` |
| `page.locator('.item').nth(0)` on dynamic lists | Index changes when items are added/removed/reordered | `.filter({ hasText: 'Specific item' })` |
| `page.getByText('Aceptar')` hardcoded i18n text | Fails when locale changes | `page.getByRole('button', { name: /accept/i })` or `getByTestId('confirm-btn')` |
| `await page.waitForTimeout(3000)` | Arbitrary delay; too slow in fast environments, too short in slow ones | `await expect(locator).toBeVisible()` |
| `page.locator('.card').locator('.card-title').locator('a')` | Deep CSS chaining breaks on any structural change | `page.getByRole('link', { name: 'Card title text' })` |
| `page.$('selector')` (ElementHandle API) | Returns a snapshot, not auto-waiting; deprecated pattern | `page.locator('selector')` — locators are lazy and auto-wait |
| `page.locator('text=Click here')` | Legacy text selector syntax | `page.getByText('Click here')` or `getByRole` with name |
| Multiple locators for one element in sequence | Each `locator()` call in a chain restarts the search | Store as variable: `const btn = page.getByRole('button', { name: 'Save' })` |

## TypeScript patterns

### Quick Reference

```typescript
// Priority order — use the first one that works:
page.getByRole('button', { name: 'Submit' })        // 1. Role (default)
page.getByLabel('Email address')                     // 2. Label (form fields)
page.getByText('Welcome back')                       // 3. Text (non-interactive)
page.getByPlaceholder('Search...')                    // 4. Placeholder
page.getByAltText('Company logo')                    // 5. Alt text (images)
page.getByTitle('Close dialog')                      // 6. Title attribute
page.getByTestId('checkout-summary')                 // 7. Test ID (last semantic option)
page.locator('css=.legacy-widget >> internal:role=button') // 8. CSS/XPath (last resort)
```

### `page.pickLocator()` For Interactive Discovery

```typescript
import { test } from '@playwright/test';

test('pick a locator during debugging', async ({ page }) => {
  await page.goto('/checkout');

  const picked = await page.pickLocator();
  console.log(picked);

  await page.cancelPickLocator();
});
```

## Guardrails

- **`page.pickLocator()` For Interactive Discovery:** Writing final production tests without review. Treat the picked locator as a starting point, not the final answer.
- **`locator.normalize()` For Refactors:** You have not yet thought through the element's semantics. A normalized locator can still be less clear than a hand-written role or label locator.
- **Role-Based Locators (Default Choice):** The element has no ARIA role and adding one is outside your control.
- **Label-Based Locators:** The element is not a form control. Use `getByRole` with the accessible name instead — it covers labels too.
- **Text-Based Locators:** The element is a button, link, heading, or form field. Use `getByRole` instead.
- **Test ID Locators:** Any semantic locator (`getByRole`, `getByLabel`, `getByText`) can identify the element. Test IDs are invisible to users and assistive technology.
- **CSS/XPath — Last Resort:** Any other locator type works. Always.
- **Locator Chaining and Filtering:** A direct `getByRole` with `name` already uniquely identifies the element.

## Related guides

- [core/locator-strategy.md](locator-strategy.md) — deep-dive decision framework for choosing locator strategies at the project level
- [core/assertions-and-waiting.md](assertions-and-waiting.md) — pair locators with web-first assertions
- [pom/page-object-model.md](../pom/page-object-model.md) — encapsulate locators in page objects
- [core/iframes-and-shadow-dom.md](iframes-and-shadow-dom.md) — advanced iframe and Shadow DOM patterns
- [core/i18n-and-localization.md](i18n-and-localization.md) — locator strategies for internationalized apps
