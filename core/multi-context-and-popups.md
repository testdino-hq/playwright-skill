# Multi-Context, Popups, and New Windows

> **When to use**: Handling popup windows, new tabs, OAuth authorization flows, payment gateway redirects, multi-tab coordination, and any scenario where your application opens additional browser windows or tabs.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Handling Basic Popups** -- A user action opens a new tab or window and you need to interact with it.
- **OAuth Popup Flows** -- Your app opens a third-party OAuth window (Google, GitHub, Microsoft, etc.) for authentication.
- **Payment Gateway Popups** -- Checkout flows open a payment provider in a new window (PayPal, 3D Secure verification).
- **Multi-Tab Coordination** -- Testing scenarios where multiple tabs share state -- real-time collaboration, shopping cart sync, or session management across tabs.
- **Download Triggers in New Tabs** -- A download is triggered by opening a new tab (e.g., PDF generation that opens in a new window before downloading).
- **Multi-Context for Isolated Sessions** -- Testing interactions between different users (e.g., admin and regular user, two chat participants).
- **Observing New Contexts and Mirrored Events (Playwright 1.60+)** -- You're orchestrating many contexts/pages (multi-user suites, agent-driven sessions) and want a single place to react when a new context is created, or to listen for page lifecycle events at the context level rather th...

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| `target="_blank"` link | `page.waitForEvent('popup')` | Playwright fires `popup` for all new windows/tabs |
| `window.open()` call | `page.waitForEvent('popup')` | Same mechanism regardless of how the window opens |
| OAuth login popup | `waitForEvent('popup')` + interact + wait for close | OAuth providers redirect back and close the popup |
| Payment popup (PayPal) | `waitForEvent('popup')` + complete flow | Same as OAuth but with payment-specific UI |
| Download in new tab | `popup.waitForEvent('download')` | Catch the download event on the popup page |
| Multiple tabs, same user | Open pages in the same `context` | Shared cookies, localStorage, session |
| Multiple users (separate sessions) | Create separate `browser.newContext()` per user | Isolated cookies, storage, auth state |
| Tab sync testing | Multiple `context.newPage()` + assert shared state | Tests real-time state synchronization |
| Popup that may or may not appear | `waitForEvent('popup', { timeout })` with try/catch | Graceful handling of conditional popups |

## TypeScript patterns

### Quick Reference

```typescript
// Catch a popup triggered by a click
const popupPromise = page.waitForEvent('popup');
await page.getByRole('button', { name: 'Open preview' }).click();
const popup = await popupPromise;
await popup.waitForLoadState();
await expect(popup.getByRole('heading')).toContainText('Preview');

// List all open pages in a context
const allPages = context.pages();
console.log(`Open tabs: ${allPages.length}`);
```

### Multi-Context for Isolated Sessions

```typescript
import { test, expect } from '@playwright/test';

test('admin sees user changes in real-time', async ({ browser }) => {
  // Create separate contexts for two users (separate sessions)
  const adminContext = await browser.newContext();
  const userContext = await browser.newContext();

  const adminPage = await adminContext.newPage();
  const userPage = await userContext.newPage();

  // Admin logs in and watches the user list
  await adminPage.goto('/admin/users');

  // User signs up
  await userPage.goto('/register');
  await userPage.getByLabel('Name').fill('New User');
  await userPage.getByLabel('Email').fill('newuser@example.com');
  await userPage.getByLabel('Password').fill('password123');
  await userPage.getByRole('button', { name: 'Register' }).click();

  // Admin should see the new user appear
  await expect(adminPage.getByText('newuser@example.com')).toBeVisible({ timeout: 10000 });

  await adminContext.close();
  await userContext.close();
});
```

## Guardrails

- **Handling Basic Popups:** The "popup" is actually a modal dialog within the same page -- use `getByRole('dialog')` instead.
- **OAuth Popup Flows:** You can bypass OAuth entirely by injecting auth tokens directly -- see [core/authentication.md](authentication.md).
- **Payment Gateway Popups:** The payment gateway loads in an iframe on the same page -- use `frameLocator` instead.
- **Multi-Tab Coordination:** Each tab is independent and can be tested in separate test cases.
- **Download Triggers in New Tabs:** The download starts directly without opening a new tab -- use `page.waitForEvent('download')` directly.
- **Multi-Context for Isolated Sessions:** You only need a single user perspective -- a single context is sufficient.
- **Observing New Contexts and Mirrored Events (Playwright 1.60+):** You have one context and one page — listen on the `page` directly.

## Related guides

- [core/authentication.md](authentication.md) -- bypassing OAuth popups with stored auth state
- [core/multi-user-and-collaboration.md](multi-user-and-collaboration.md) -- multi-user real-time collaboration testing
- [core/file-operations.md](file-operations.md) -- file download handling without popups
- [core/third-party-integrations.md](third-party-integrations.md) -- mocking OAuth providers to avoid real popups
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- fixtures for multi-context setups
