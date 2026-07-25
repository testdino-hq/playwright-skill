# Device and Environment Emulation

Use emulation to test responsive layouts, locale-sensitive behavior, permissions, and accessibility preferences. Prefer a config or new browser context for settings that cannot be changed reliably after launch.

## Quick commands

```bash
playwright-cli resize 390 844
playwright-cli run-code "async page => page.emulateMedia({ colorScheme: 'dark' })"
playwright-cli run-code "async page => page.emulateMedia({ reducedMotion: 'reduce' })"
playwright-cli run-code "async page => page.context().grantPermissions(['geolocation'])"
playwright-cli run-code "async page => page.context().setGeolocation({ latitude: 43.6532, longitude: -79.3832 })"
```

## Viewports

| Target | Width × height |
|---|---:|
| Small mobile | 320 × 568 |
| Mobile | 390 × 844 |
| Tablet portrait | 768 × 1024 |
| Laptop | 1366 × 768 |
| Desktop | 1920 × 1080 |

Test just below, at, and just above application breakpoints. A viewport alone does not emulate touch, user agent, or device scale factor.

## TypeScript device project

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
    {
      name: 'fr-mobile',
      use: {
        ...devices['iPhone 14'],
        locale: 'fr-CA',
        timezoneId: 'America/Toronto',
      },
    },
  ],
});
```

Use Playwright device descriptors instead of manually combining viewport, touch, user agent, and scale factor.

## Geolocation and permissions

```typescript
import { test, expect } from '@playwright/test';

test.use({
  geolocation: { latitude: 43.6532, longitude: -79.3832 },
  permissions: ['geolocation'],
});

test('shows local content', async ({ page, context }) => {
  await page.goto('/nearby');
  await expect(page.getByText('Toronto')).toBeVisible();
  await context.setGeolocation({ latitude: 45.5019, longitude: -73.5674 });
  await page.reload();
  await expect(page.getByText('Montréal')).toBeVisible();
});
```

Grant only required permissions and clear them after ad hoc CLI sessions.

## Locale and timezone

Configure `locale` and `timezoneId` before creating the context. Verify user-facing results rather than implementation details:

```typescript
test.use({ locale: 'de-DE', timezoneId: 'Europe/Berlin' });

test('formats local values', async ({ page }) => {
  await page.goto('/invoice');
  await expect(page.getByTestId('total')).toContainText('1.234,56');
});
```

## Media preferences

```typescript
test('supports accessibility preferences', async ({ page }) => {
  await page.emulateMedia({
    colorScheme: 'dark',
    reducedMotion: 'reduce',
    forcedColors: 'active',
  });
  await page.goto('/');
  await page.screenshot({ path: 'artifacts/a11y-preferences.png' });
});
```

Test light/dark, reduced motion, forced colors, and print only when the application supports them.

## Network conditions

Use CDP network throttling only in Chromium-specific tests. For portable failure testing, prefer request routing to delay or abort selected endpoints.

## Checklist

- Create a fresh context for each device profile.
- Cover application breakpoints, not every device.
- Assert visible behavior after changing location or preferences.
- Label screenshots with device, locale, and theme.
- Do not treat viewport resizing as complete mobile emulation.
