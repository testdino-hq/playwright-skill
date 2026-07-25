# Electron Testing

> **When to use**: When your application is an Electron desktop app and you need end-to-end tests covering the renderer process, main process, IPC communication, native dialogs, system tray, and multi-window workflows.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Basic Electron App Setup** -- Starting to test an Electron app with Playwright for the first time.
- **Electron App Fixture (Recommended)** -- You want isolated, reusable Electron app instances across test files.
- **Accessing the Main Process** -- You need to read Electron app state, check paths, get app version, or verify main process behavior.
- **Testing IPC Communication** -- Your app uses `ipcMain` / `ipcRenderer` for communication between the main and renderer processes.
- **File System Dialogs** -- Your app uses Electron's `dialog.showOpenDialog`, `dialog.showSaveDialog`, or similar native file dialogs.
- **System Tray Testing** -- Your app has a system tray icon with context menus or status indicators.
- **Multiple Windows** -- Your Electron app opens multiple windows (preferences, about, detached panels).
- **Testing Packaged/Built Apps** -- You want to test the production build of your Electron app (after `electron-builder`, `electron-forge`, etc.).

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Launch Electron app for testing | `_electron.launch({ args: ['./main.js'] })` | Playwright's built-in Electron support |
| Get the main window | `app.firstWindow()` | Returns the first `BrowserWindow` as a Playwright `Page` |
| Read main process state | `app.evaluate(({ app }) => ...)` | Runs code in the main process with Electron APIs |
| Test IPC round-trips | `window.evaluate` (renderer) + `app.evaluate` (main) | Cover both sides of the IPC bridge |
| Mock native file dialogs | Override `dialog.showOpenDialog` via `app.evaluate` | Native dialogs cannot be automated directly |
| Test system tray | `app.evaluate` to invoke tray callbacks | Tray icons are OS-native; not clickable via Playwright |
| Multiple windows | `app.waitForEvent('window')` | Captures new `BrowserWindow` instances as they open |
| Test packaged builds | `electron.launch({ executablePath })` | Points to the built binary instead of source |

## TypeScript patterns

### Quick Reference

```typescript
import { _electron as electron } from 'playwright';

// Launch the Electron app
const app = await electron.launch({ args: ['./main.js'] });

// Get the first window (renderer process)
const window = await app.firstWindow();

// Access the main process for evaluation
const appPath = await app.evaluate(async ({ app }) => {
  return app.getPath('userData');
});

// Close the app
await app.close();
```

### Electron App Fixture (Recommended)

```typescript
// fixtures.ts
import { test as base, expect, _electron as electron, ElectronApplication, Page } from '@playwright/test';

type ElectronFixtures = {
  electronApp: ElectronApplication;
  window: Page;
};

export const test = base.extend<ElectronFixtures>({
  electronApp: async ({}, use) => {
    const app = await electron.launch({
      args: ['./dist/main.js'],
      env: { ...process.env, NODE_ENV: 'test' },
    });
    await use(app);
    await app.close();
  },

  window: async ({ electronApp }, use) => {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await use(window);
  },
});

export { expect };
```

## Guardrails

- **Basic Electron App Setup:** Your app is a web app, not an Electron app.
- **Electron App Fixture (Recommended):** All tests can share a single app instance (rare in practice).
- **Accessing the Main Process:** Everything you need is in the renderer (UI). Prefer testing through the UI.
- **Testing IPC Communication:** IPC is an implementation detail and the behavior is fully testable through the UI.
- **File System Dialogs:** File selection is handled by a web input (`<input type="file">`). Use standard Playwright file chooser for that.
- **System Tray Testing:** Your app has no tray functionality.
- **Multiple Windows:** Your app uses a single window.
- **Testing Packaged/Built Apps:** Development mode testing is sufficient for your CI pipeline.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- wrapping Electron app launch in fixtures
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- all standard assertions work on Electron windows
- [core/iframes-and-shadow-dom.md](iframes-and-shadow-dom.md) -- Electron apps often embed web components or iframes
- [core/browser-apis.md](browser-apis.md) -- localStorage, IndexedDB, and other APIs work the same in Electron
