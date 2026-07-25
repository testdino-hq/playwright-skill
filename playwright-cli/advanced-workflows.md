# Advanced Workflows

Compose advanced flows from small, observable steps. Use focused CLI commands for exploration and move reusable logic into TypeScript.

## Popup handling

```typescript
const popupPromise = page.waitForEvent('popup');
await page.getByRole('link', { name: 'Open report' }).click();
const popup = await popupPromise;
await popup.waitForLoadState();
await expect(popup.getByRole('heading', { name: 'Report' })).toBeVisible();
await popup.close();
```

Start waiting before the action that opens the popup. Use a fresh context for OAuth test tenants; never automate real-user MFA or CAPTCHA bypasses.

## Paginated extraction

```typescript
type Product = { name: string; price: string };
const products: Product[] = [];

while (true) {
  const rows = page.getByTestId('product');
  for (let index = 0; index < await rows.count(); index++) {
    products.push({
      name: await rows.nth(index).getByTestId('name').innerText(),
      price: await rows.nth(index).getByTestId('price').innerText(),
    });
  }

  const next = page.getByRole('button', { name: 'Next' });
  if (await next.isDisabled()) break;
  await next.click();
  await expect(rows.first()).toBeVisible();
}
```

Only extract data the user is authorized to access. Respect rate limits and prefer APIs when rendering is not under test.

## Downloads and uploads

```typescript
const downloadPromise = page.waitForEvent('download');
await page.getByRole('button', { name: 'Export' }).click();
const download = await downloadPromise;
await download.saveAs(`artifacts/${download.suggestedFilename()}`);

await page.getByLabel('Upload document').setInputFiles('fixtures/document.pdf');
await expect(page.getByText('Upload complete')).toBeVisible();
```

Use explicit workspace paths, safe fixture files, and size limits. Do not open untrusted downloads automatically.

## Accessibility checks

```typescript
import AxeBuilder from '@axe-core/playwright';

const results = await new AxeBuilder({ page })
  .exclude('[data-testid="known-third-party-widget"]')
  .analyze();

expect(results.violations).toEqual([]);
```

Automated scans supplement, but do not replace, keyboard navigation, focus order, readable labels, and screen-reader review.

## Multi-step forms

```typescript
await page.getByLabel('Full name').fill('Test User');
await page.getByRole('button', { name: 'Next' }).click();
await expect(page.getByRole('heading', { name: 'Address' })).toBeVisible();

await page.getByLabel('City').fill('Toronto');
await page.getByRole('button', { name: 'Review' }).click();
await expect(page.getByText('Test User')).toBeVisible();
await page.getByRole('button', { name: 'Submit' }).click();
await expect(page.getByRole('heading', { name: 'Complete' })).toBeVisible();
```

Assert each transition so failures identify the broken step.

## Multi-user flow

```typescript
const owner = await browser.newContext({ storageState: '.auth/owner.json' });
const reviewer = await browser.newContext({ storageState: '.auth/reviewer.json' });
const ownerPage = await owner.newPage();
const reviewerPage = await reviewer.newPage();

await ownerPage.goto('/documents/42');
await ownerPage.getByRole('button', { name: 'Request review' }).click();

await reviewerPage.goto('/reviews');
await expect(reviewerPage.getByText('Document 42')).toBeVisible();

await Promise.all([owner.close(), reviewer.close()]);
```

Keep each role in a separate context and close all contexts in teardown.

## Recovery

Catch only known, recoverable UI conditions:

```typescript
const consent = page.getByRole('button', { name: 'Accept cookies' });
if (await consent.isVisible()) await consent.click();

await expect(async () => {
  await page.getByRole('button', { name: 'Refresh status' }).click();
  await expect(page.getByTestId('status')).toHaveText('Ready');
}).toPass({ timeout: 10_000 });
```

Do not wrap entire tests in generic retries. Capture a trace and fix the missing synchronization.

## CLI composition

```bash
playwright-cli -s=flow open http://localhost:3000
playwright-cli -s=flow tracing-start
playwright-cli -s=flow snapshot
# Perform the authorized flow with explicit commands.
playwright-cli -s=flow screenshot --filename=artifacts/final-state.png
playwright-cli -s=flow tracing-stop
playwright-cli -s=flow close
```

## Checklist

- Wait before popup/download triggers.
- Assert every major transition.
- Use separate contexts for separate users.
- Keep extraction bounded and authorized.
- Save artifacts to explicit paths.
- Replace broad retries with observable waits.
