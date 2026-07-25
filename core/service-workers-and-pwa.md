# Service Workers and PWA Testing

> **When to use**: When your application is a Progressive Web App (PWA) or uses service workers for offline support, caching, push notifications, or background sync.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Service Worker Registration** -- You need to verify that your service worker registers successfully, activates, and controls the page.
- **Offline Mode Testing** -- Your PWA should work offline -- serving cached pages, showing offline indicators, queuing data for sync.
- **Cache Verification** -- You need to confirm that specific resources are cached by the service worker.
- **PWA Install Prompt** -- You need to test the "Add to Home Screen" / PWA install flow.
- **Push Notification Testing** -- Your PWA uses the Push API to receive push notifications from a server.
- **Background Sync Testing** -- Your app uses the Background Sync API to defer network requests until the user has connectivity.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Verify SW registers | `context.waitForEvent('serviceworker')` | Confirms the SW file was fetched and registered |
| Test offline page serving | `context.setOffline(true)` + reload | Simulates network loss at the browser level |
| Verify specific assets are cached | `page.evaluate(() => caches.keys())` | Directly queries the Cache API |
| Test install prompt | `addInitScript` to mock `beforeinstallprompt` | Browser does not fire this event in automation |
| Validate web manifest | `page.request.get(manifestUrl)` | Fetch and parse the JSON manifest |
| Test push notifications | `sw.evaluate()` to dispatch PushEvent | Simulates a push message inside the SW |
| Test background sync | Go offline, perform action, come back online | Verifies the sync queue processes correctly |
| Test SW update flow | `registration.update()` via `page.evaluate` | Triggers a manual SW update check |

## TypeScript patterns

### Quick Reference

```typescript
// Service workers require a persistent context — use launchPersistentContext
const context = await chromium.launchPersistentContext(userDataDir, {
  baseURL: 'https://localhost:3000',
});

// Enable/disable offline mode
await context.setOffline(true);   // Go offline
await context.setOffline(false);  // Come back online

// Wait for service worker to register
const sw = await context.waitForEvent('serviceworker');
console.log('SW URL:', sw.url());
```

### Background Sync Testing

```typescript
import { test, expect } from '@playwright/test';

test('background sync retries failed requests when online', async ({ swContext }) => {
  const page = await swContext.newPage();
  await page.goto('/tasks');

  // Ensure SW is active
  await page.evaluate(() => navigator.serviceWorker.ready);

  // Go offline
  await swContext.setOffline(true);

  // Create a task (will fail to sync)
  await page.getByLabel('New task').fill('Buy groceries');
  await page.getByRole('button', { name: 'Add' }).click();

  // Task shows as "pending sync"
  await expect(page.getByText('Buy groceries')).toBeVisible();
  await expect(page.getByTestId('sync-status')).toHaveText('Pending');

  // Come back online — background sync should fire
  await swContext.setOffline(false);

  // Wait for sync to complete
  await expect(page.getByTestId('sync-status')).toHaveText('Synced', { timeout: 15000 });
});
```

## Guardrails

- **Service Worker Registration:** Your app does not use service workers.
- **Offline Mode Testing:** Your app has no offline support.
- **Cache Verification:** You trust the framework's caching strategy and only need to verify the offline UX (test offline mode instead).
- **PWA Install Prompt:** Your app is not a PWA or does not handle the `beforeinstallprompt` event.
- **Push Notification Testing:** Notifications are handled entirely client-side without the Push API.
- **Background Sync Testing:** Your app does not use background sync.

## Related guides

- [core/browser-apis.md](browser-apis.md) -- IndexedDB and localStorage used alongside service workers
- [core/configuration.md](configuration.md) -- project-level config for PWA testing
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- wrapping persistent context in fixtures
- [core/websockets-and-realtime.md](websockets-and-realtime.md) -- real-time features that interact with offline/online state
