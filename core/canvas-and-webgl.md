# Canvas and WebGL Testing

> **When to use**: When your application renders content on `<canvas>` elements -- charts (Chart.js, D3), maps (Mapbox, Leaflet), games, image editors, WebGL visualizations, drawing tools, signature pads.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/locators.md](locators.md)

## Topic map

- **Screenshot Comparison (Visual Regression)** -- Verifying the visual output of canvas-rendered content -- charts, graphs, maps, drawings. This is the most reliable approach because canvas pixels are not queryable via DOM.
- **Interacting with Canvas via Coordinates** -- Testing user interactions on canvas -- clicking chart data points, dragging on a drawing tool, selecting map regions.
- **Canvas API Testing via `page.evaluate()`** -- You need to inspect canvas pixel data, read the rendering context state, or verify programmatic canvas operations.
- **WebGL Rendering Verification** -- Your app uses WebGL for 3D visualizations, data plots, or games.
- **Chart Library Testing Strategies** -- Testing Chart.js, D3, Recharts, Highcharts, or similar chart libraries.

## Decision table

| Scenario | Best Approach | Why |
|---|---|---|
| Verify chart looks correct | `toHaveScreenshot()` on canvas element | Canvas pixels are not DOM; screenshot is the source of truth |
| Click a data point on chart | `canvas.click({ position: { x, y } })` | Canvas does not have clickable child elements |
| Verify canvas is not blank | `page.evaluate` + `getImageData` or `toDataURL` | Quick programmatic check without baseline image |
| Test SVG-based chart (D3) | Standard locators (`svg rect`, `svg path`) | SVG elements are in the DOM; use locator queries |
| Read specific pixel color | `page.evaluate` + `getImageData` | Direct access to pixel data |
| Test WebGL rendering | `toHaveScreenshot()` with higher `maxDiffPixelRatio` | WebGL has rendering variance; pixel assertions are unreliable |
| Test canvas drag/draw | `mouse.down()` + `mouse.move()` + `mouse.up()` | Simulates real drawing interactions |
| Chart tooltip after hover | `canvas.hover({ position })` then assert tooltip DOM | Tooltips are usually HTML overlays |

## TypeScript patterns

### Quick Reference

```typescript
// Screenshot comparison — the primary strategy for canvas
await expect(page.locator('canvas#chart')).toHaveScreenshot('revenue-chart.png');

// Click at specific coordinates on canvas
await page.locator('canvas').click({ position: { x: 200, y: 150 } });

// Read canvas state via page.evaluate
const pixelColor = await page.evaluate(() => {
  const canvas = document.querySelector('canvas') as HTMLCanvasElement;
  const ctx = canvas.getContext('2d')!;
  const pixel = ctx.getImageData(100, 100, 1, 1).data;
  return { r: pixel[0], g: pixel[1], b: pixel[2], a: pixel[3] };
});
```

### Screenshot Comparison (Visual Regression)

```typescript
import { test, expect } from '@playwright/test';

test('revenue chart renders correctly', async ({ page }) => {
  await page.goto('/dashboard');

  // Wait for the chart to finish rendering
  await expect(page.locator('canvas#revenue-chart')).toBeVisible();

  // Optionally wait for a loading indicator to disappear
  await expect(page.getByTestId('chart-loading')).toBeHidden();

  // Screenshot comparison against a baseline
  await expect(page.locator('canvas#revenue-chart')).toHaveScreenshot('revenue-chart.png', {
    maxDiffPixelRatio: 0.01,  // Allow 1% pixel difference for anti-aliasing
  });
});

test('chart updates after date range change', async ({ page }) => {
  await page.goto('/dashboard');

  // Change date range
  await page.getByRole('combobox', { name: 'Date range' }).selectOption('Last 30 days');

  // Wait for chart to re-render
  await expect(page.getByTestId('chart-loading')).toBeHidden();

  // Compare against a different baseline
  await expect(page.locator('canvas#revenue-chart')).toHaveScreenshot('revenue-chart-30d.png', {
    maxDiffPixelRatio: 0.01,
  });
});

test('mask dynamic areas in canvas screenshot', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page.locator('canvas#chart')).toHaveScreenshot('chart-stable.png', {
    // Mask the timestamp area that changes every render
    mask: [page.locator('.chart-timestamp')],
    maxDiffPixelRatio: 0.02,
  });
});
```

## Guardrails

- **Screenshot Comparison (Visual Regression):** The canvas content is dynamic on every render (animations, timestamps). Use threshold or mask options.
- **Interacting with Canvas via Coordinates:** The element has an accessible DOM overlay (many chart libraries render tooltips as HTML). Interact with the overlay instead.
- **Canvas API Testing via `page.evaluate()`:** A screenshot comparison is sufficient. Pixel-level assertions are brittle.
- **WebGL Rendering Verification:** The canvas uses 2D context only.
- **Chart Library Testing Strategies:** Charts have full HTML/SVG DOM output (D3 with SVG). Use standard locators for SVG elements.

## Related guides

- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-retrying assertions and visual comparison options
- [core/configuration.md](configuration.md) -- configure screenshot thresholds and update baselines
- [core/iframes-and-shadow-dom.md](iframes-and-shadow-dom.md) -- canvas elements inside iframes
- [core/debugging.md](debugging.md) -- debugging visual regression failures with trace viewer
