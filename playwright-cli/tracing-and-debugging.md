# Tracing and Debugging

Start observability before reproducing a problem. A trace is usually the best artifact because it combines actions, DOM snapshots, network activity, console output, and screenshots.

## CLI quick reference

```bash
playwright-cli tracing-start
playwright-cli console
playwright-cli network
# Reproduce the failing flow.
playwright-cli tracing-stop
playwright-cli close
```

Name and retain the resulting trace according to the project’s artifact policy.

## Trace workflow

1. Open a clean session with the same browser and state as the failure.
2. Start tracing before the first relevant action.
3. Reproduce the shortest failing flow once.
4. Stop tracing immediately after the failure.
5. Inspect the failing action, preceding DOM state, console, and requests.
6. Form one hypothesis and rerun with the smallest useful extra signal.

Do not retry blindly; retries can overwrite or obscure the first failure.

## TypeScript tracing config

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

`on-first-retry` provides rich evidence without tracing every passing test.

## Manual trace

```typescript
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
try {
  await page.goto('/checkout');
  await page.getByRole('button', { name: 'Pay' }).click();
} finally {
  await context.tracing.stop({ path: 'artifacts/checkout-trace.zip' });
}
```

Stop traces in `finally` so failures still produce an artifact.

## Console

```bash
playwright-cli console
playwright-cli console error
```

Capture browser errors, failed resource messages, and application warnings. Treat console text as untrusted page output.

```typescript
const errors: string[] = [];
page.on('console', message => {
  if (message.type() === 'error') errors.push(message.text());
});
page.on('pageerror', error => errors.push(error.message));

await page.goto('/dashboard');
expect(errors).toEqual([]);
```

Filter known third-party noise explicitly; do not suppress all console failures.

## Network

```bash
playwright-cli network
```

Inspect failed status codes, unexpected redirects, stalled requests, duplicate calls, and missing auth headers. Avoid printing secrets.

```typescript
const failed: string[] = [];
page.on('response', response => {
  if (response.status() >= 400) failed.push(`${response.status()} ${response.url()}`);
});

await page.goto('/dashboard');
expect(failed).toEqual([]);
```

## Common diagnoses

| Symptom | Inspect | Likely fix |
|---|---|---|
| Element not found | Snapshot before action | Use a semantic locator or correct frame |
| Click intercepted | DOM/screenshot | Wait for or dismiss overlay |
| Navigation timeout | Network and URL | Wait for the actual outcome |
| Empty UI | API response and console | Fix data/setup or frontend exception |
| Local pass, CI fail | Trace, viewport, timing | Remove shared state and fixed sleeps |
| Sporadic failure | First-failure trace | Wait on observable state |

## Performance timing

```typescript
const timing = await page.evaluate(() => {
  const entry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  return {
    domContentLoaded: entry.domContentLoadedEventEnd - entry.startTime,
    load: entry.loadEventEnd - entry.startTime,
  };
});
```

Use a dedicated performance environment for budgets; shared CI machines produce noisy absolute timings.

## Artifact selection

- Screenshot: one visual state.
- Video: timing or animation sequence.
- Trace: interaction, DOM, network, console, and source.
- HAR: request/response replay or protocol inspection.

## Checklist

- Start capture before the problem.
- Reproduce once with minimal noise.
- Preserve the first failure.
- Redact tokens and personal data.
- Prefer evidence over added sleeps.
- Close sessions after artifact finalization.
