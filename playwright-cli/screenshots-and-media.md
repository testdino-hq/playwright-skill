# Screenshots and Media

Use screenshots for state evidence, videos for temporal failures, and PDF for print output. Store artifacts in a deliberate, gitignored location unless they are reviewed baselines.

## CLI quick reference

```bash
playwright-cli screenshot --filename=artifacts/page.png
playwright-cli screenshot e12 --filename=artifacts/card.png
playwright-cli resize 390 844
playwright-cli pdf --filename=artifacts/invoice.pdf
playwright-cli video-start
playwright-cli video-stop artifacts/checkout.webm
```

Use descriptive names containing the scenario, viewport, or browser.

## TypeScript screenshots

```typescript
import { test, expect } from '@playwright/test';

test('captures checkout', async ({ page }) => {
  await page.goto('/checkout');
  await expect(page.getByRole('heading', { name: 'Checkout' })).toBeVisible();

  await page.screenshot({
    path: 'artifacts/checkout-full.png',
    fullPage: true,
    animations: 'disabled',
  });

  await page.getByTestId('order-summary').screenshot({
    path: 'artifacts/order-summary.png',
  });
});
```

Wait for fonts, images, and data before capture. Disable animation or use reduced motion for reproducible output.

## Mask dynamic content

```typescript
await page.screenshot({
  path: 'artifacts/dashboard.png',
  mask: [
    page.getByTestId('current-time'),
    page.getByTestId('account-number'),
  ],
  maskColor: '#000',
});
```

Mask secrets and nondeterministic regions. Do not use masking to hide meaningful regressions.

## Responsive suite

```typescript
const viewports = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
] as const;

for (const viewport of viewports) {
  await page.setViewportSize(viewport);
  await page.goto('/pricing');
  await page.screenshot({
    path: `artifacts/pricing-${viewport.name}.png`,
    fullPage: true,
  });
}
```

For full device behavior, use Playwright device projects instead of only resizing.

## PDF

```typescript
await page.emulateMedia({ media: 'print' });
await page.pdf({
  path: 'artifacts/invoice.pdf',
  format: 'Letter',
  printBackground: true,
  preferCSSPageSize: true,
});
```

PDF generation is Chromium-only. Validate page breaks, print CSS, headers, and redaction of private data.

## Video and screencast

Use context video when every page action must be recorded:

```typescript
const context = await browser.newContext({
  recordVideo: { dir: 'artifacts/video', size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
await page.goto('/checkout');
await context.close();
```

Close the context to finalize the video. Use CLI `video-start`/`video-stop` for an interactive session and tracing for step-level debugging.

## Selection guide

| Need | Artifact |
|---|---|
| Exact visual state | Screenshot |
| Cross-run visual comparison | `expect(page).toHaveScreenshot()` |
| Sequence or animation | Video |
| DOM, network, console, actions | Trace |
| Printable output | PDF |

## Checklist

- Wait for a stable state.
- Keep viewport and theme explicit.
- Mask sensitive or truly dynamic content.
- Finalize video by closing its context.
- Set CI retention limits for large artifacts.
