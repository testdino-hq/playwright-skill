# Browser APIs

> **When to use**: When testing features that depend on browser-native APIs -- geolocation, permissions, clipboard, notifications, camera/microphone, localStorage, sessionStorage, IndexedDB.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Geolocation** -- Your app uses `navigator.geolocation` for maps, store locators, delivery tracking, or location-based features.
- **Permissions** -- Your app requests browser permissions -- notifications, camera, microphone, geolocation, clipboard.
- **Clipboard API** -- Testing copy/paste functionality, "Copy to clipboard" buttons, or paste-from-clipboard features.
- **Camera and Microphone Mocking** -- Testing video calls, QR code scanners, voice recording, or any feature using `getUserMedia`.
- **localStorage and sessionStorage** -- Your app persists state, tokens, preferences, or feature flags in web storage.
- **IndexedDB Testing** -- Your app uses IndexedDB for offline storage, caching, or large datasets (progressive web apps, offline-first apps).
- **Notifications** -- Your app uses the browser Notification API to show desktop notifications.
- **Preserving a Real Browser's Behavior on Attach (`connectOverCDP({ noDefaults })`, Playwright 1.60+)** -- You attach to an existing, user-owned browser over CDP and need it to keep behaving exactly as the user left it — Playwright otherwise overrides the default context's download, focus, and media emulation.

## Decision table

| Browser API | How to Test | Key Configuration |
|---|---|---|
| Geolocation | `geolocation` context option + `permissions: ['geolocation']` | `context.setGeolocation()` for mid-test changes |
| Permissions (any) | `permissions` array in context options | `context.grantPermissions()` / `context.clearPermissions()` |
| Clipboard | Grant `clipboard-read`/`clipboard-write` + `page.evaluate(navigator.clipboard...)` | Requires secure context (HTTPS or localhost) |
| Notifications | Mock `Notification` constructor via `page.evaluate` | Grant `notifications` permission; capture constructor calls |
| Camera / Microphone | Chromium `--use-fake-device-for-media-stream` launch arg | Only works in Chromium; grant `camera`/`microphone` permissions |
| localStorage | `page.evaluate(() => localStorage.getItem/setItem(...))` | Set before navigation or reload to take effect |
| sessionStorage | `page.evaluate(() => sessionStorage.getItem/setItem(...))` | Scoped to the browsing session; cleared on context close |
| IndexedDB | `page.evaluate` with `indexedDB.open()` | Wrap in Promises for async operations |

## TypeScript patterns

### Quick Reference

```typescript
// Geolocation — set via context options
const context = await browser.newContext({
  geolocation: { latitude: 40.7128, longitude: -74.0060 },
  permissions: ['geolocation'],
});

// Permissions — grant at context level
const context = await browser.newContext({
  permissions: ['clipboard-read', 'clipboard-write', 'notifications'],
});

// localStorage / sessionStorage — access via page.evaluate
await page.evaluate(() => localStorage.setItem('theme', 'dark'));
const value = await page.evaluate(() => localStorage.getItem('theme'));

// Clipboard — read/write in page context
await page.evaluate(() => navigator.clipboard.writeText('copied text'));
```

### Geolocation

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    geolocation: { latitude: 51.5074, longitude: -0.1278 }, // London
    permissions: ['geolocation'],
  },
});
```

## Guardrails

- **Geolocation:** Your app never reads the user's location.
- **Permissions:** Your app does not use the Permissions API.
- **Clipboard API:** Your app does not interact with the clipboard.
- **Camera and Microphone Mocking:** Your app does not use camera or microphone.
- **localStorage and sessionStorage:** You can set the state through the UI or API instead. Prefer those approaches for realism.
- **IndexedDB Testing:** Your app only uses localStorage or server-side storage.
- **Notifications:** Notifications are purely server-side (push without Notification API).
- **Preserving a Real Browser's Behavior on Attach (`connectOverCDP({ noDefaults })`, Playwright 1.60+):** You launched the browser for testing. The default overrides give you deterministic downloads and focus/media emulation, which is usually what tests want.

## Related guides

- [core/configuration.md](configuration.md) -- global geolocation/permissions in config
- [core/service-workers-and-pwa.md](service-workers-and-pwa.md) -- offline and cache testing using IndexedDB and service workers
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- wrap browser API setup in reusable fixtures
- [core/debugging.md](debugging.md) -- inspecting storage and permissions in Playwright traces
