# Flaky Tests

> **When to use**: A test passes sometimes and fails other times. You need to diagnose the root cause, fix it, and prevent it from happening again.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Flakiness Taxonomy** -- Every flaky test falls into one of four categories. Identify the category first, then apply the matching fix.
- **Diagnosis Flowchart** -- Follow this decision tree to identify which category your flaky test belongs to.
- **Playwright 1.59 Trace Retention Strategy** -- For flaky tests on Playwright 1.59+, prefer `trace: 'retain-on-failure-and-retries'` over `trace: 'on'` when you are comparing failed attempts with passing retries. It keeps the runs that matter without storing every...
- **Capture `errorContext` for Intermittent Assertion Failures (Playwright 1.60+)** -- When a flaky test fails only sometimes on an `expect()` matcher, the bare error message rarely explains *why*. Playwright 1.60 attaches `errorContext` to each `testInfo` error — including the aria snapshot of the elem...
- **Use UI Mode and Trace Viewer Filters** -- When debugging a noisy trace or a long UI Mode run, use the newer filtering options to focus on the failing test, relevant actions, or a specific assertion sequence instead of scanning the full event stream manually.
- **Fix: Timing and Async Issues** -- The test fails locally with `--repeat-each=20`, or you see `waitForTimeout`, missing `await`, or race conditions.
- **Fix: Test Isolation Issues** -- The test passes when run alone (`--grep "test name"`) but fails when run with other tests, or fails only in parallel mode.
- **Fix: Environment Issues** -- The test passes locally but fails in CI, or fails on certain operating systems, viewports, or machines.
- **Detection Strategies** -- You suspect flakiness but the test does not fail consistently, or you want to validate a fix actually eliminated the flakiness.
- **Quarantine Strategy** -- A test is known-flaky and you cannot fix it immediately. Quarantine it so it does not block CI, but track it so it does not rot.
- **Prevention Checklist** -- Apply these rules from the start to prevent flakiness from entering your test suite.

## Decision table

|   |
|   +-- npx playwright test --grep "exact test name" --workers=1
|   +-- Passes alone? --> ISOLATION issue. Fix with unique data + fixtures.
|   +-- Fails alone? --> Continue to Step 3.
|

## TypeScript patterns

### Playwright 1.59 Trace Retention Strategy

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  use: {
    trace: process.env.CI
      ? 'retain-on-failure-and-retries'
      : 'on-first-retry',
  },
});
```

### Capture `errorContext` for Intermittent Assertion Failures (Playwright 1.60+)

```typescript
import { test } from '@playwright/test';

test.afterEach(async ({}, testInfo) => {
  if (testInfo.status !== testInfo.expectedStatus) {
    for (const err of testInfo.errors) {
      if (err.errorContext) {
        await testInfo.attach('failure-context', {
          body: err.errorContext,
          contentType: 'text/plain',
        });
      }
    }
  }
});
```

## Related guides

- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-retrying assertions and explicit waits
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- fixture teardown for test isolation
- [core/test-data-management.md](test-data-management.md) -- unique data per test, factory functions
- [core/configuration.md](configuration.md) -- retry, timeout, and trace configuration
- [core/debugging.md](debugging.md) -- trace viewer, UI mode, and Inspector for diagnosing failures
- [core/common-pitfalls.md](common-pitfalls.md) -- common mistakes that cause flakiness
