# Session Management

Use named sessions to isolate cookies, storage, tabs, browsers, and user roles. Keep each session scoped to one purpose and close it when complete.

## Quick reference

```bash
playwright-cli -s=admin open http://localhost:3000
playwright-cli -s=admin snapshot
playwright-cli -s=viewer open http://localhost:3000
playwright-cli list
playwright-cli -s=admin close
playwright-cli close-all
```

Commands without `-s=<name>` use the default session.

## Isolation

```bash
# Admin logs in
playwright-cli -s=admin open http://localhost:3000/login
playwright-cli -s=admin snapshot
playwright-cli -s=admin fill e1 "admin@example.com"

# Viewer has independent state
playwright-cli -s=viewer open http://localhost:3000/login
playwright-cli -s=viewer snapshot
```

Use semantic names such as `admin`, `viewer`, `chromium`, or `staging`. Avoid generic names that obscure ownership.

## Lifecycle

```bash
playwright-cli list
playwright-cli -s=admin close
playwright-cli close
playwright-cli close-all
playwright-cli kill-all
playwright-cli -s=admin delete-data
```

Use `kill-all` only for unresponsive browser processes. Close sessions before deleting their data.

## Persistent profiles

```bash
playwright-cli -s=admin open --persistent http://localhost:3000
playwright-cli -s=admin open --profile=./.profiles/admin http://localhost:3000
```

Persistent profiles retain browser data across restarts. Keep them gitignored, do not share them between concurrent sessions, and delete stale profiles.

## Auth-state sharing

```bash
playwright-cli -s=login state-save .auth/admin.json
playwright-cli -s=admin state-load .auth/admin.json
playwright-cli -s=admin goto http://localhost:3000/dashboard
```

Prefer a saved storage-state file when several clean sessions need the same login. Treat the file as a credential.

## TypeScript multi-user test

```typescript
import { test, expect } from '@playwright/test';

test('admin and viewer see different controls', async ({ browser }) => {
  const admin = await browser.newContext({ storageState: '.auth/admin.json' });
  const viewer = await browser.newContext({ storageState: '.auth/viewer.json' });
  const adminPage = await admin.newPage();
  const viewerPage = await viewer.newPage();

  await Promise.all([
    adminPage.goto('/dashboard'),
    viewerPage.goto('/dashboard'),
  ]);

  await expect(adminPage.getByRole('button', { name: 'Delete' })).toBeVisible();
  await expect(viewerPage.getByRole('button', { name: 'Delete' })).toBeHidden();

  await Promise.all([admin.close(), viewer.close()]);
});
```

## Browser variants

```bash
playwright-cli -s=chromium open --browser=chromium http://localhost:3000
playwright-cli -s=firefox open --browser=firefox http://localhost:3000
playwright-cli -s=webkit open --browser=webkit http://localhost:3000
```

Do not reuse the same session name for different browser configurations.

## Bound browsers

When a Playwright process exposes a bound browser, attach only to the session identifier produced by that authorized process. Use the session dashboard to verify ownership before interacting.

## Checklist

- One role, browser, or task per session.
- Use storage state for reusable authentication.
- Never commit profiles or auth-state files.
- Close contexts even when assertions fail.
- Use `close-all` after parallel CLI workflows.
- Reserve `kill-all` for stuck processes.
