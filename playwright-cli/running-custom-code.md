# Running Custom Playwright Code

Use `run-code` only when no focused CLI command covers the operation. Keep snippets small, explicit, and limited to the authorized page.

## CLI form

```bash
playwright-cli run-code "async page => page.waitForLoadState('networkidle')"
playwright-cli run-code "async page => page.context().grantPermissions(['clipboard-read'])"
playwright-cli run-code "async page => page.emulateMedia({ colorScheme: 'dark' })"
```

Do not interpolate untrusted page text, URLs, selectors, or shell input into the code string.

## Prefer maintained TypeScript

Move reusable or multi-step logic into a Playwright test:

```typescript
import { test, expect } from '@playwright/test';

test('loads account data', async ({ page }) => {
  const responsePromise = page.waitForResponse(
    response => response.url().endsWith('/api/account') && response.ok(),
  );
  await page.goto('/account');
  await responsePromise;
  await expect(page.getByRole('heading', { name: 'Account' })).toBeVisible();
});
```

## Reliable waits

```typescript
await page.waitForLoadState('domcontentloaded');
await page.waitForURL(/dashboard/);
await page.getByTestId('spinner').waitFor({ state: 'hidden' });
await page.getByRole('heading', { name: 'Results' }).waitFor();
```

Prefer locators, URLs, responses, and visible states. Avoid `waitForTimeout()` except for diagnosing timing behavior.

## Frames

```typescript
const paymentFrame = page.frameLocator('[title="Payment"]');
await paymentFrame.getByLabel('Card number').fill('4242424242424242');
await paymentFrame.getByRole('button', { name: 'Pay' }).click();
```

Use `frameLocator` when the iframe is represented in the DOM. Re-resolve nested frames after navigation.

## Downloads

```typescript
const downloadPromise = page.waitForEvent('download');
await page.getByRole('link', { name: 'Export CSV' }).click();
const download = await downloadPromise;
await download.saveAs(`artifacts/${download.suggestedFilename()}`);
```

Start waiting before the triggering action. Save only to an approved workspace path.

## Clipboard and page information

```typescript
await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
await page.evaluate(text => navigator.clipboard.writeText(text), 'test value');
const copied = await page.evaluate(() => navigator.clipboard.readText());
expect(copied).toBe('test value');

const details = {
  title: await page.title(),
  url: page.url(),
  viewport: page.viewportSize(),
};
```

## Error handling

```typescript
async function clickOptionalBanner(page: import('@playwright/test').Page) {
  const close = page.getByRole('button', { name: 'Close banner' });
  if (await close.isVisible()) await close.click();
}
```

Catch only expected, recoverable conditions. Let unexpected failures surface with a trace.

## Multi-page extraction

```typescript
type Item = { name: string; price: string };
const items: Item[] = [];

for (let pageNumber = 1; pageNumber <= 3; pageNumber++) {
  await page.goto(`/catalog?page=${pageNumber}`);
  const rows = page.getByTestId('product');
  for (let index = 0; index < await rows.count(); index++) {
    items.push({
      name: await rows.nth(index).getByTestId('name').innerText(),
      price: await rows.nth(index).getByTestId('price').innerText(),
    });
  }
}
```

Respect authorization, rate limits, and data-handling rules. Prefer API access when UI rendering is not under test.

## Checklist

- Prefer built-in commands first.
- Keep `run-code` single-purpose.
- Convert reusable work to TypeScript.
- Wait on observable state.
- Capture a trace before debugging retries.
