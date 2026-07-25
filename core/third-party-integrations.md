# Third-Party Integrations

> **When to use**: Testing your application's interaction with external services -- OAuth providers, payment gateways, analytics, chat widgets, maps, social login, and CAPTCHAs. The core principle: mock the third-party boundary, not your own application code.
> **Prerequisites**: [core/network-mocking.md](network-mocking.md), [core/when-to-mock.md](when-to-mock.md), [core/authentication.md](authentication.md)

## Topic map

- **Mocking OAuth Providers (Google, GitHub, etc.)** -- Testing the full login flow without depending on real OAuth provider availability, rate limits, or test accounts.
- **Payment Gateway Testing (Stripe Elements)** -- Testing checkout flows that use Stripe Elements, PayPal buttons, or similar embedded payment UIs.
- **Analytics Blocking** -- Preventing analytics scripts from executing during tests to improve speed, avoid polluting analytics data, and eliminate flakiness from third-party script failures.
- **Chat Widget Testing (Intercom, Drift, etc.)** -- Your app embeds a third-party chat widget and you need to test the interaction or verify it does not break your UI.
- **Map Integration Testing (Google Maps)** -- Your app embeds Google Maps or a similar map provider and you need to verify map-related interactions.
- **reCAPTCHA Bypass for Testing** -- Your app uses reCAPTCHA or hCaptcha and you need tests to proceed without solving challenges.
- **Social Login Mocking** -- Your app offers multiple social login options and you need to test the login flow without real provider accounts.

## Decision table

| Integration | Mock Strategy | When to Use Real | When to Mock |
|---|---|---|---|
| OAuth (Google, GitHub, etc.) | Route intercept on provider URL + mock callback | Dedicated integration test with test accounts | All E2E feature tests that require login |
| Stripe/payment gateway | Use Stripe test mode with test cards OR mock API | Checkout flow integration tests | All non-payment E2E tests |
| Google Analytics / Segment | `route.abort()` to block entirely | Dedicated analytics verification tests | Every other test (block for speed) |
| Chat widgets (Intercom, Drift) | `route.abort()` to block, or interact via iframe | Tests specifically about chat functionality | Every other test (block for speed/stability) |
| Google Maps | Mock geocoding/places API responses | Tests verifying real map rendering | Tests that only need location data |
| reCAPTCHA | Google test keys (preferred) or mock `grecaptcha` | Never in automated tests | Always -- CAPTCHA cannot be solved by automation |
| Social login | Reusable OAuth mock fixture per provider | Periodic integration check | All E2E tests requiring auth |
| Email services (SendGrid, SES) | Mock API endpoints, verify calls were made | End-to-end email delivery tests (separate suite) | All tests that trigger emails |

## TypeScript patterns

### Quick Reference

```typescript
// Mock an OAuth callback to bypass the real provider
await page.route('**/auth/callback*', (route) => {
  route.fulfill({
    status: 302,
    headers: { Location: '/dashboard?token=mock-jwt-token' },
  });
});

// Block analytics scripts from loading
await page.route('**/*.google-analytics.com/**', (route) => route.abort());
await page.route('**/segment.io/**', (route) => route.abort());

// Mock a third-party widget endpoint
await page.route('**/api.stripe.com/**', (route) => {
  route.fulfill({ status: 200, contentType: 'application/json', body: '{"id":"pi_mock"}' });
});
```

### Analytics Blocking

```typescript
import { test, expect } from '@playwright/test';

// Block analytics in a fixture for all tests
import { test as base } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    // Block common analytics and tracking scripts
    await page.route(/(google-analytics|googletagmanager|segment\.io|hotjar|mixpanel|amplitude)/, (route) =>
      route.abort()
    );
    await page.route('**/collect?**', (route) => route.abort()); // GA beacon
    await page.route('**/analytics/**', (route) => route.abort());
    await use(page);
  },
});

export { expect };
```

## Guardrails

- **Mocking OAuth Providers (Google, GitHub, etc.):** You need to verify the actual OAuth integration works end-to-end (use a dedicated integration test for that).
- **Payment Gateway Testing (Stripe Elements):** Stripe provides test mode with test card numbers and you want full integration coverage.
- **Analytics Blocking:** You specifically need to test that analytics events are fired correctly.
- **Chat Widget Testing (Intercom, Drift, etc.):** The chat widget is cosmetic and not part of critical user flows.
- **Map Integration Testing (Google Maps):** The map is decorative and not part of a user workflow.
- **reCAPTCHA Bypass for Testing:** You can disable CAPTCHA in your test environment through a server-side flag (preferred approach).
- **Social Login Mocking:** You have a backend bypass that sets auth state directly.

## Related guides

- [core/network-mocking.md](network-mocking.md) -- foundational route interception patterns
- [core/authentication.md](authentication.md) -- auth state management and login bypasses
- [core/when-to-mock.md](when-to-mock.md) -- decision framework for mocking vs real services
- [core/multi-context-and-popups.md](multi-context-and-popups.md) -- handling OAuth popup windows
- [core/security-testing.md](security-testing.md) -- testing auth security aspects
- [core/iframes-and-shadow-dom.md](iframes-and-shadow-dom.md) -- interacting with payment widget iframes
