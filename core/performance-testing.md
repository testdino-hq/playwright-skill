# Performance Testing

> **When to use**: Measuring and enforcing Web Vitals, resource loading timing, bundle sizes, and runtime performance. Use Playwright to catch performance regressions in CI before users notice them.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Web Vitals Measurement (LCP, CLS, FID/INP)** -- Enforcing Core Web Vitals thresholds as part of your test suite.
- **Performance API Access** -- Measuring navigation timing, resource loading, or custom performance marks.
- **Resource Loading and Bundle Size Monitoring** -- Enforcing bundle size budgets and catching unexpected large resources.
- **Slow Network Simulation via CDP** -- Testing your app's behavior and performance under constrained network conditions.
- **CPU Throttling via CDP** -- Simulating low-powered devices to test animation smoothness, interaction responsiveness, or heavy computation.
- **Performance Budgets in CI** -- Enforcing hard performance limits that block merges when thresholds are exceeded.

## Decision table

| What to Measure | Technique | When to Use |
|---|---|---|
| LCP, CLS, FID/INP | `PerformanceObserver` via `addInitScript` | Core Web Vitals regression testing |
| TTFB, DOM load times | `performance.getEntriesByType('navigation')` | Server response and page load budgets |
| API call durations | `performance.getEntriesByType('resource')` | Backend performance regression |
| JS/CSS bundle sizes | `page.on('response')` + `content-length` header | Bundle size budgets in CI |
| Slow network behavior | CDP `Network.emulateNetworkConditions` | Testing loading states, lazy loading, offline |
| Low-end device behavior | CDP `Emulation.setCPUThrottlingRate` | Animation smoothness, interaction latency |
| Full Lighthouse audit | `@playwright/test` + Lighthouse CLI via CDP port | Comprehensive performance scoring |
| Runtime performance | `page.evaluate` + `requestAnimationFrame` FPS count | Animation and rendering performance |

## TypeScript patterns

### Quick Reference

```typescript
// Measure Largest Contentful Paint (LCP)
const lcp = await page.evaluate(() => {
  return new Promise<number>((resolve) => {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      resolve(entries[entries.length - 1].startTime);
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  });
});
expect(lcp).toBeLessThan(2500); // Good LCP threshold

// Throttle network to 3G
const client = await page.context().newCDPSession(page);
await client.send('Network.emulateNetworkConditions', {
  offline: false, downloadThroughput: 1.6 * 1024 * 1024 / 8,
  uploadThroughput: 750 * 1024 / 8, latency: 150,
});
```

## Guardrails

- **Web Vitals Measurement (LCP, CLS, FID/INP):** You only need aggregate field data -- use Chrome UX Report or RUM tools instead.
- **Performance API Access:** Web Vitals alone cover your needs.
- **Resource Loading and Bundle Size Monitoring:** Bundle analysis is handled by webpack-bundle-analyzer or similar build tools.
- **Slow Network Simulation via CDP:** Playwright's built-in `offline` option is sufficient for your test.
- **CPU Throttling via CDP:** Network performance is the bottleneck, not CPU.
- **Performance Budgets in CI:** Performance varies too much in CI environment -- use trend-based monitoring instead.

## Related guides

- [core/configuration.md](configuration.md) -- timeout and retry settings for performance-sensitive tests
- [core/network-mocking.md](network-mocking.md) -- mocking slow APIs for performance boundary testing
- [core/browser-apis.md](browser-apis.md) -- using browser APIs for measurement
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI configuration for performance budgets
- [core/clock-and-time-mocking.md](clock-and-time-mocking.md) -- time-related performance testing
