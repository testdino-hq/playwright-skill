# Debugging Playwright Tests

> **When to use**: A test is failing and you need to understand why — wrong selectors, timing issues, network failures, or unexpected application state.

## Topic map

- **Systematic Debugging Workflow** -- Follow this order. Do not skip to step 5 — most issues resolve by step 2.
- **Pattern 1: UI Mode for Interactive Debugging** -- Developing new tests, investigating failures locally, exploring application behavior.
- **Pattern 2: Playwright Inspector with PWDEBUG** -- You need to step through actions one at a time, test selectors interactively, or see the exact state before and after each action.
- **Pattern 3: Trace Viewer for CI Failure Analysis** -- A test fails in CI and you need to understand what happened without re-running locally.
- **Pattern 3b: CLI Debugger for Agent Workflows** -- You are debugging from a terminal, remote machine, or coding-agent workflow where opening the full inspector is awkward.
- **Pattern 3c: Terminal Trace Analysis** -- You have a trace archive but need fast answers from a shell, CI worker, or remote box.
- **Pattern 4: Headed Mode with Slow Motion** -- You want to watch the browser during execution without the full Inspector overhead.
- **Pattern 5: VS Code Integration** -- You prefer IDE-based debugging with breakpoints, variable inspection, and integrated test running.
- **Pattern 6: Capturing Browser Console Logs** -- Suspecting JavaScript errors, failed client-side API calls, or application-level logging that explains the failure.
- **Pattern 7: Screenshots on Failure** -- You need a visual snapshot at the exact moment of failure.
- **Pattern 8: Network Debugging** -- Suspecting API failures, wrong request payloads, missing auth headers, or slow responses causing timeouts.
- **Pattern 9: Verbose API Logs** -- You need to see every single Playwright API call with timing to identify where the test is spending time or getting stuck.
- **Pattern 10: `page.pause()` — Inline Breakpoints** -- You need to pause execution at a precise point to inspect the live DOM, try locators, or check application state.
- **Pattern 11: Styled Highlights and `errorContext` (Playwright 1.60+)** -- You're visually debugging which element a locator resolves to (especially in headed mode or while recording a video), or you want richer diagnostics attached to assertion failures.
- **Adding `waitForTimeout` to fix timing issues** -- If the default timeout is insufficient, investigate *why* the operation is slow, then either:
- **Commenting out tests to isolate a failure**
- **Not reading the full error message** -- Playwright error messages include:
- **Debugging in CI without traces**
- **Using `console.log` instead of proper debugging tools**
- **Leaving `page.pause()` or `test.only()` in committed code**

## Decision table

| Failure Type | First Tool | Why |
|---|---|---|
| **Element not found** (selector wrong) | UI Mode (`--ui`) | See the DOM at the moment of failure, try selectors in Pick Locator |
| **Element not found** (timing issue) | Trace Viewer — Actions tab | Compare before/after screenshots to see if element appeared after timeout |
| **Wrong text / value** | Trace Viewer — Actions tab | Inspect the actual DOM content at each action step |
| **Test hangs / times out** | `DEBUG=pw:api` | See which API call is waiting and never resolving |
| **Network / API failure** | Trace Viewer — Network tab | See request/response status codes, payloads, timing |
| **Auth / session issues** | Network debugging (`page.on('response')`) | Check for 401/403 responses, missing cookies/tokens |
| **Visual rendering wrong** | `--headed --slow-mo=500` | Watch the actual rendering in the browser |
| **JavaScript error in app** | Console logging (`page.on('console')`) | Catch uncaught exceptions and error logs |
| **CI-only failure** | Trace Viewer (from CI artifact) | Reproduce the exact CI state without running locally |
| **Flaky / intermittent** | Trace on every run (`trace: 'on'`) + retries | Compare passing and failing traces side by side |
| **State pollution** | Run single test with `test.only()` | Isolate from other tests; if it passes alone, state leaks from another test |

## TypeScript patterns

### Pattern 1: UI Mode for Interactive Debugging

```typescript
// Launch UI Mode from terminal:
// npx playwright test --ui

// Run a specific test file in UI Mode:
// npx playwright test tests/checkout.spec.ts --ui

// playwright.config.ts — configure for UI Mode convenience
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    // Traces are always available in UI Mode regardless of this setting,
    // but this ensures traces are captured for CI failures too
    trace: 'on-first-retry',
  },
});
```

### Pattern 2: Playwright Inspector with PWDEBUG

```typescript
// Launch Inspector from terminal:
// PWDEBUG=1 npx playwright test tests/login.spec.ts

// On Windows PowerShell:
// $env:PWDEBUG=1; npx playwright test tests/login.spec.ts

// On Windows CMD:
// set PWDEBUG=1 && npx playwright test tests/login.spec.ts

// Inspector opens automatically. Use these controls:
// - "Step over" button: execute one action at a time
// - "Pick locator" button: hover elements to see the best locator
// - "Resume" button: run to the next page.pause() or end

import { test, expect } from '@playwright/test';

test('debug login flow', async ({ page }) => {
  await page.goto('/login');

  // Inspector pauses before each action when PWDEBUG=1
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Guardrails

- **Pattern 1: UI Mode for Interactive Debugging:** CI environments (use traces instead).
- **Pattern 2: Playwright Inspector with PWDEBUG:** The failure is visible from the error message or trace alone.
- **Pattern 3: Trace Viewer for CI Failure Analysis:** You can reproduce the failure locally (use UI Mode or Inspector instead).
- **Pattern 3b: CLI Debugger for Agent Workflows:** You want the richest interactive UI locally; use UI Mode or Inspector for that.
- **Pattern 3c: Terminal Trace Analysis:** You need the full visual timeline; use Trace Viewer for that.
- **Pattern 4: Headed Mode with Slow Motion:** The test runs too fast to follow even with slow-mo (use Inspector instead).
- **Pattern 5: VS Code Integration:** You are debugging CI-only failures that do not reproduce locally.
- **Pattern 6: Capturing Browser Console Logs:** The issue is clearly a selector or timing problem visible in the trace.

## Related guides

- [core/error-index.md](error-index.md) — look up specific error messages
- [core/flaky-tests.md](flaky-tests.md) — intermittent failure patterns and fixes
- [core/common-pitfalls.md](common-pitfalls.md) — common beginner mistakes
- [core/assertions-and-waiting.md](assertions-and-waiting.md) — web-first assertions and auto-waiting
- [core/configuration.md](configuration.md) — trace, screenshot, and retry configuration
- [ci/reporting-and-artifacts.md](../ci/reporting-and-artifacts.md) — CI artifact collection for traces and screenshots
