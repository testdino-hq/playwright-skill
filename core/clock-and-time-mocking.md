# Clock and Time Mocking

> **When to use**: Testing time-dependent features -- countdown timers, scheduled events, expiration dates, age gates, session timeouts, or any UI that behaves differently based on the current time. Playwright's `page.clock` API lets you control time without waiting in real-time.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/configuration.md](configuration.md)

## Topic map

- **Frozen Time with `install()` and `setFixedTime()`** -- Your test needs time to stand still at a specific moment -- verifying what the UI shows at a particular date/time.
- **Fast-Forwarding Time with `fastForward()`** -- Testing timers, countdowns, debounced actions, or any feature that reacts to elapsed time. `fastForward` fires all pending timers up to the specified duration.
- **Resuming Time with `resume()`** -- You need to start with a mocked time, then let time flow normally for interaction-dependent behavior.
- **Testing Date-Dependent UI** -- Features that change based on the current date -- age verification, expiration warnings, seasonal content, date pickers.
- **Timezone-Dependent Features** -- Testing features that combine mocked time with specific timezones.

## Decision table

| Scenario | API | Why |
|---|---|---|
| Check UI at a specific date/time | `clock.install()` + `clock.setFixedTime()` | Time is frozen; no timer ticking |
| Test countdown or timer behavior | `clock.install()` + `clock.fastForward()` | Fires timers as time advances without real waiting |
| Test after a long idle period | `clock.install()` + `clock.fastForward('30:00')` | Simulates 30 minutes without waiting 30 minutes |
| Start mocked, then tick normally | `clock.install()` + `clock.resume()` | Useful when you need real `requestAnimationFrame` after setup |
| Different timezone display | `browser.newContext({ timezoneId })` | Affects `Date` timezone rendering |
| Timezone + mocked time | `newContext({ timezoneId })` + `clock.install()` | Both timezone and absolute time are controlled |
| Test date picker defaults | `clock.install()` with target date | Calendar opens to the mocked "today" |
| Test DST transitions | Set `timezoneId` + `install` at DST boundary | Tests the most common timezone bugs |

## TypeScript patterns

### Quick Reference

```typescript
// Freeze time at a specific moment
await page.clock.install({ time: new Date('2025-03-15T10:00:00Z') });
await page.goto('/dashboard');

// Advance time by 5 minutes
await page.clock.fastForward('05:00');

// Set time to a specific point (jumps, does not tick through)
await page.clock.setFixedTime(new Date('2025-12-31T23:59:59Z'));

// Let time resume ticking from current mocked point
await page.clock.resume();
```

### Resuming Time with `resume()`

```typescript
import { test, expect } from '@playwright/test';

test('notification appears in real-time after scheduled trigger', async ({ page }) => {
  // Start at a known time
  await page.clock.install({ time: new Date('2025-03-15T09:59:55Z') });
  await page.goto('/dashboard');

  // Notification is scheduled for 10:00:00 — advance to 5 seconds before
  await expect(page.getByTestId('notification-bell')).not.toHaveAttribute('data-count');

  // Let real time tick from this point
  await page.clock.resume();

  // The notification should appear within a few seconds
  await expect(page.getByTestId('notification-bell')).toHaveAttribute('data-count', '1', {
    timeout: 10000,
  });
});
```

## Guardrails

- **Frozen Time with `install()` and `setFixedTime()`:** The feature under test depends on timers ticking (use `fastForward` instead).
- **Fast-Forwarding Time with `fastForward()`:** You just need to check a static time-dependent display -- use `setFixedTime` instead.
- **Resuming Time with `resume()`:** The entire test should use mocked time.
- **Testing Date-Dependent UI:** The date is passed from the server and does not depend on client-side `Date`.
- **Timezone-Dependent Features:** The feature uses only UTC and does not render local times.

## Related guides

- [core/i18n-and-localization.md](i18n-and-localization.md) -- timezone and locale testing patterns
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-waiting vs time-based assertions
- [core/error-and-edge-cases.md](error-and-edge-cases.md) -- testing timeout and expiration edge cases
- [core/performance-testing.md](performance-testing.md) -- timing-related performance measurement
- [core/websockets-and-realtime.md](websockets-and-realtime.md) -- real-time features that depend on timing
