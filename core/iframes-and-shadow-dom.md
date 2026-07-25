# Iframes and Shadow DOM

> **When to use**: When your application embeds content in `<iframe>` elements (payment widgets, third-party embeds, legacy modules) or uses Web Components with Shadow DOM (design systems, custom elements, Salesforce Lightning).
> **Prerequisites**: [core/locators.md](locators.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Basic iframe Interaction with `frameLocator()`** -- You need to interact with content inside an `<iframe>` -- payment forms, embedded editors, captchas, third-party widgets.
- **Selecting the Right iframe** -- Multiple iframes exist on the page or the iframe has no obvious identifier.
- **Nested Iframes** -- An iframe contains another iframe (common in complex widget hierarchies, ad containers, or embedded third-party tools).
- **Cross-Origin Iframes** -- The iframe loads content from a different domain (payment providers, OAuth flows, third-party embeds).
- **Using the Frame API for Advanced Scenarios** -- You need to access the frame's URL, wait for frame navigation, or run `evaluate` inside the frame.
- **Shadow DOM -- Automatic Piercing** -- Your app uses Web Components with open Shadow DOM. This is the default behavior -- no special configuration needed.
- **Closed Shadow DOM Workaround** -- A third-party component uses `attachShadow({ mode: 'closed' })`, which blocks Playwright's auto-piercing.
- **Web Components with Slots and Custom Events** -- Testing web components that use `<slot>` for content projection or dispatch custom events.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Content inside `<iframe>` | `page.frameLocator('selector')` | Returns a scoped locator for the iframe document |
| Multiple iframes on page | Use `title`, `name`, or `src` attribute selectors | More stable than index-based `nth()` |
| Nested iframes | Chain `frameLocator().frameLocator()` | Each call scopes one level deeper |
| Cross-origin iframe | Same as any iframe -- `frameLocator()` | Playwright handles cross-origin transparently |
| URL check or `evaluate` inside frame | `page.frame({ url })` (Frame API) | FrameLocator does not expose URL or evaluate |
| Open Shadow DOM | Standard locators -- no changes needed | Playwright pierces open shadow roots by default |
| Closed Shadow DOM | `addInitScript` to override `attachShadow` | Forces closed roots to open before page loads |
| Slotted content in Web Components | Locate within the custom element tag | Slotted content is light DOM, accessible normally |
| Non-piercing CSS (rare) | `css:light=selector` | Explicitly restricts to light DOM only |

## TypeScript patterns

### Quick Reference

```typescript
// Iframes — use frameLocator to reach inside
const frame = page.frameLocator('iframe[title="Payment"]');
await frame.getByLabel('Card number').fill('4242424242424242');

// Nested iframes — chain frameLocator calls
const inner = page.frameLocator('#outer').frameLocator('#inner');
await inner.getByRole('button', { name: 'Submit' }).click();

// Shadow DOM — Playwright pierces open shadow roots automatically
await page.getByRole('button', { name: 'Toggle' }).click();       // auto-pierces
await page.locator('my-component').getByText('Hello').click();     // auto-pierces
```

### Basic iframe Interaction with `frameLocator()`

```typescript
import { test, expect } from '@playwright/test';

test('complete payment inside Stripe iframe', async ({ page }) => {
  await page.goto('/checkout');

  // Locate the iframe by its title, name, or a CSS selector
  const paymentFrame = page.frameLocator('iframe[title="Secure payment"]');

  // Use normal locators inside the frame
  await paymentFrame.getByLabel('Card number').fill('4242424242424242');
  await paymentFrame.getByLabel('Expiry').fill('12/28');
  await paymentFrame.getByLabel('CVC').fill('123');
  await paymentFrame.getByRole('button', { name: 'Pay' }).click();

  // Assertion on content inside the iframe
  await expect(paymentFrame.getByText('Payment successful')).toBeVisible();

  // Assertion on the parent page (outside the iframe)
  await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
});
```

## Guardrails

- **Basic iframe Interaction with `frameLocator()`:** The content is in the main frame. Never use `frameLocator` for Shadow DOM.
- **Selecting the Right iframe:** There is only one iframe and a simple `page.frameLocator('iframe')` works.
- **Nested Iframes:** There is only one level of iframe nesting.
- **Cross-Origin Iframes:** The iframe is same-origin.
- **Using the Frame API for Advanced Scenarios:** `frameLocator()` covers your needs. It is simpler and auto-waits.
- **Shadow DOM -- Automatic Piercing:** The shadow root is closed (see workaround below).
- **Closed Shadow DOM Workaround:** The shadow root is open (the default). Auto-piercing handles open roots.
- **Web Components with Slots and Custom Events:** The component does not use slots or custom events.

## Related guides

- [core/locators.md](locators.md) -- locator fundamentals including frame and shadow DOM basics
- [core/browser-apis.md](browser-apis.md) -- testing browser APIs that may live inside iframes
- [core/canvas-and-webgl.md](canvas-and-webgl.md) -- canvas elements inside iframes or web components
- [core/debugging.md](debugging.md) -- using Playwright Inspector to identify iframe boundaries and shadow roots
