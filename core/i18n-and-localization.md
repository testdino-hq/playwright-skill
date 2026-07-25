# Internationalization and Localization Testing

> **When to use**: Verifying your application works correctly across locales, languages, text directions, date/number formats, and timezones. Catches layout breaks, missing translations, and format errors before they reach international users.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **Setting Browser Locale** -- Testing locale-dependent rendering -- date formats, number formatting, currency, sorting, and browser-level localization.
- **Multi-Locale Project Configuration** -- Running the full test suite across multiple locales in CI.
- **RTL Layout Testing** -- Your app supports right-to-left languages (Arabic, Hebrew, Persian, Urdu) and you need to verify layout direction, text alignment, and mirrored UI.
- **Date, Number, and Currency Format Verification** -- Your app uses `Intl.DateTimeFormat`, `Intl.NumberFormat`, or similar locale-sensitive APIs.
- **Language Switcher Testing** -- Your app has an in-app language selector that changes the UI language without depending on browser locale.
- **Translation Completeness Checks** -- Verifying that all visible UI strings are translated and no fallback keys leak into the UI.
- **Timezone Testing** -- Your app displays time-sensitive data (event times, deadlines, scheduling) and you need to verify correct timezone rendering.
- **Multi-Language Screenshot Comparison** -- Catching visual layout regressions caused by text expansion, RTL mirroring, or font rendering differences across locales.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Test locale-dependent formatting | Set `locale` in browser context | Playwright sets `navigator.language` and affects `Intl` APIs |
| Test app language switcher | Interact with the switcher UI directly | Tests the actual user workflow, not just browser locale |
| Test timezone rendering | Set `timezoneId` in browser context | Overrides `Date` and `Intl.DateTimeFormat` timezone |
| Catch text overflow from long translations | Visual regression + bounding box checks | German/Finnish text is 30-40% longer than English |
| Verify RTL layout | Set Arabic/Hebrew locale + assert `dir="rtl"` | Tests both browser signal and app response |
| Catch missing translations | Scan page text for key patterns (`{{`, dot notation) | Catches build/deploy issues where translation files are missing |
| Compare layouts across locales | `toHaveScreenshot` per locale with project-based config | Captures visual differences automatically |
| Test DST edge cases | Set specific `timezoneId` + known date boundaries | DST boundaries cause the most timezone bugs |

## TypeScript patterns

### Quick Reference

```typescript
// Set locale and timezone per context
const context = await browser.newContext({
  locale: 'de-DE',
  timezoneId: 'Europe/Berlin',
});

// Or in playwright.config.ts for project-level locale testing
projects: [
  { name: 'english', use: { locale: 'en-US', timezoneId: 'America/New_York' } },
  { name: 'german',  use: { locale: 'de-DE', timezoneId: 'Europe/Berlin' } },
  { name: 'arabic',  use: { locale: 'ar-SA', timezoneId: 'Asia/Riyadh' } },
],
```

### Setting Browser Locale

```typescript
import { test, expect } from '@playwright/test';

test.describe('locale-specific formatting', () => {
  test('US locale formats dates as MM/DD/YYYY', async ({ browser }) => {
    const context = await browser.newContext({ locale: 'en-US' });
    const page = await context.newPage();
    await page.goto('/dashboard');

    // Verify date format matches US convention
    await expect(page.getByTestId('last-updated')).toHaveText(/\d{1,2}\/\d{1,2}\/\d{4}/);
    await context.close();
  });

  test('German locale formats dates as DD.MM.YYYY', async ({ browser }) => {
    const context = await browser.newContext({ locale: 'de-DE' });
    const page = await context.newPage();
    await page.goto('/dashboard');

    await expect(page.getByTestId('last-updated')).toHaveText(/\d{1,2}\.\d{1,2}\.\d{4}/);
    await context.close();
  });

  test('Japanese locale formats numbers with commas', async ({ browser }) => {
    const context = await browser.newContext({ locale: 'ja-JP' });
    const page = await context.newPage();
    await page.goto('/pricing');

    // Japanese yen: no decimal places, uses comma grouping
    await expect(page.getByTestId('price')).toHaveText(/[\d,]+円/);
    await context.close();
  });
});
```

## Guardrails

- **Setting Browser Locale:** Your app does not use the browser locale and instead relies on a user preference stored server-side.
- **Multi-Locale Project Configuration:** You only need to test a single locale or the app does not vary by locale.
- **RTL Layout Testing:** Your app has no RTL support.
- **Date, Number, and Currency Format Verification:** Formats are hardcoded and do not depend on locale.
- **Language Switcher Testing:** Language is determined purely by browser locale with no user override.
- **Translation Completeness Checks:** You have a build-time translation validation step that already catches missing keys.
- **Timezone Testing:** All times are displayed in UTC with no local conversion.
- **Multi-Language Screenshot Comparison:** Visual regression testing is handled separately and locale is not a layout risk.

## Related guides

- [core/locators.md](locators.md) -- locator strategies that work across locales
- [core/configuration.md](configuration.md) -- project-level locale and timezone configuration
- [core/visual-regression.md](visual-regression.md) -- screenshot comparison fundamentals
- [core/clock-and-time-mocking.md](clock-and-time-mocking.md) -- mocking time for date-dependent testing
- [ci/docker-and-containers.md](../ci/docker-and-containers.md) -- consistent font rendering in CI with Docker
