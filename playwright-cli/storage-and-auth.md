# Storage and Authentication

Treat cookies, local storage, session storage, profiles, and storage-state files as credentials. Use only test accounts and keep saved state out of version control.

## Save and restore

```bash
playwright-cli state-save .auth/admin.json
playwright-cli -s=admin state-load .auth/admin.json
playwright-cli -s=admin goto http://localhost:3000/dashboard
```

Load state before navigation when the destination requires authentication. Refresh saved state when tokens expire.

## Recommended login flow

```bash
playwright-cli -s=login open http://localhost:3000/login
playwright-cli -s=login snapshot
playwright-cli -s=login fill e1 "admin@example.com"
playwright-cli -s=login fill e2 "$TEST_PASSWORD"
playwright-cli -s=login click e3
playwright-cli -s=login state-save .auth/admin.json
playwright-cli -s=login close
```

Never place real passwords or tokens directly in commands or committed files.

## TypeScript setup project

```typescript
import { test as setup, expect } from '@playwright/test';

const authFile = '.auth/admin.json';

setup('authenticate admin', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.context().storageState({ path: authFile });
});
```

Use one state file per role. Add `.auth/` to `.gitignore`.

## Cookies

```bash
playwright-cli cookie-list
playwright-cli cookie-get session
playwright-cli cookie-set feature_flag enabled
playwright-cli cookie-delete feature_flag
playwright-cli cookie-clear
```

Set domain, path, expiry, `secure`, `httpOnly`, and `sameSite` deliberately when testing cookie behavior.

## Local and session storage

```bash
playwright-cli localstorage-list
playwright-cli localstorage-get theme
playwright-cli localstorage-set theme dark
playwright-cli localstorage-delete theme
playwright-cli localstorage-clear

playwright-cli sessionstorage-list
playwright-cli sessionstorage-get wizard-step
playwright-cli sessionstorage-set wizard-step 2
playwright-cli sessionstorage-delete wizard-step
playwright-cli sessionstorage-clear
```

Local storage survives reloads; session storage is scoped to a tab. Reload after changing values that the app reads only during startup.

## Typed storage helpers

```typescript
type Flags = { newCheckout: boolean };

await page.evaluate((flags: Flags) => {
  localStorage.setItem('feature-flags', JSON.stringify(flags));
}, { newCheckout: true });

await page.reload();
await expect(page.getByTestId('new-checkout')).toBeVisible();
```

Use JSON serialization for structured values and validate the application-visible outcome.

## Token refresh testing

Set a test token with a short controlled expiry, trigger a request, and assert that the application refreshes or signs out. Do not copy production tokens into fixtures.

## OAuth and SSO

Authenticate interactively only in an authorized environment. Prefer provider test tenants or API-issued test state. Never automate MFA bypasses, CAPTCHAs, or real user accounts.

## IndexedDB

Use small TypeScript helpers through `page.evaluate()` for IndexedDB inspection or deletion. Prefer public application behavior over direct database manipulation unless storage itself is under test.

## Cleanup

```bash
playwright-cli cookie-clear
playwright-cli localstorage-clear
playwright-cli sessionstorage-clear
playwright-cli close-all
```

Also delete obsolete `.auth` files and persistent profiles using a reviewed, explicit path.

## Checklist

- Use test-only identities.
- Save state after confirming login success.
- Keep one file per role and environment.
- Gitignore all auth artifacts.
- Rotate or delete expired state.
- Assert behavior after storage changes.
