# Browser Extensions

> **When to use**: Testing Chrome extensions — popups, content scripts, background service workers, or extension-injected UI. Requires Chromium and a persistent browser context.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Loading an Extension** -- You need to test any Chrome extension functionality.
- **Testing Extension Popups** -- Your extension has a browser action popup (the UI that appears when clicking the extension icon).
- **Testing Content Scripts** -- Your extension injects scripts or UI into web pages.
- **Testing Background Service Workers** -- Your extension uses Manifest V3 service workers for background processing, alarms, or message passing.
- **Testing Extension Options Page** -- Your extension has a dedicated options/settings page.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Test popup UI | Navigate to `chrome-extension://<id>/popup.html` | Direct access without needing to click the extension icon |
| Test content script effects | Load a real or test page, assert injected elements | Content scripts run automatically on matching URLs |
| Test background logic | Trigger via popup/content script, verify side effects | Cannot directly call service worker functions from Playwright |
| Test extension storage | Use popup to set values, reload, verify persistence | `chrome.storage` is only accessible from extension pages |
| Test options page | Navigate to `chrome-extension://<id>/options.html` | Same approach as popup testing |
| Test cross-page behavior | Open multiple pages in the same context | Persistent context shares extension state across tabs |
| Run in CI (headless) | Use `--headless=new` Chromium flag | New headless mode supports extensions unlike old headless |
| Test with multiple extensions | Add multiple paths to `--load-extension` | Comma-separate paths in the flag value |

## TypeScript patterns

### Quick Reference

```typescript
// Load an unpacked extension with a persistent context (Chromium only)
const context = await chromium.launchPersistentContext(userDataDir, {
  headless: false, // Extensions require headed mode
  args: [
    `--disable-extensions-except=${pathToExtension}`,
    `--load-extension=${pathToExtension}`,
  ],
});
```

### Testing Extension Popups

```typescript
import { test, expect } from './extension-fixture';

test('extension popup displays saved bookmarks', async ({ page, extensionId }) => {
  // Navigate directly to the popup HTML
  await page.goto(`chrome-extension://${extensionId}/popup.html`);

  // Interact with popup UI using standard locators
  await expect(page.getByRole('heading', { name: 'My Bookmarks' })).toBeVisible();
  await page.getByRole('button', { name: 'Add current page' }).click();
  await expect(page.getByRole('listitem')).toHaveCount(1);
});

test('extension popup settings toggle works', async ({ page, extensionId }) => {
  await page.goto(`chrome-extension://${extensionId}/popup.html`);

  await page.getByRole('checkbox', { name: 'Enable notifications' }).check();
  await expect(page.getByText('Notifications enabled')).toBeVisible();
});
```

## Guardrails

- **Loading an Extension:** You only need to test the web app that an extension interacts with — mock the extension's effects instead.
- **Testing Extension Popups:** The popup is trivial — test the content script or background logic instead.
- **Testing Content Scripts:** The content script only modifies data without visible effects — test via the background worker or storage.
- **Testing Background Service Workers:** The background logic is simple and already covered by popup or content script tests.
- **Testing Extension Options Page:** Settings are fully covered by popup tests.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- building custom fixtures for extension contexts
- [core/service-workers-and-pwa.md](service-workers-and-pwa.md) -- service worker testing patterns (non-extension)
- [core/iframes-and-shadow-dom.md](iframes-and-shadow-dom.md) -- content scripts often inject Shadow DOM elements
- [core/configuration.md](configuration.md) -- project configuration for Chromium-only test suites
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI setup for headed/extension tests
