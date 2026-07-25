# Security Testing

> **When to use**: Validating your application's defenses against common web vulnerabilities — XSS, CSRF, insecure cookies, missing headers, authentication bypass, and sensitive data exposure. Playwright is not a replacement for dedicated security scanners, but it catches the most common issues as part of your E2E suite.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/authentication.md](authentication.md)

## Topic map

- **XSS Injection Testing** -- Verifying that user inputs are properly sanitized and rendered as text, not HTML.
- **CSRF Token Verification** -- Ensuring state-changing requests include valid CSRF tokens and the server rejects requests without them.
- **CSP Header Validation** -- Verifying Content Security Policy headers are present and correctly configured.
- **Cookie Security Flags** -- Verifying session cookies and auth cookies have proper security attributes.
- **Authentication Bypass Testing** -- Ensuring protected routes redirect unauthenticated users and that session invalidation works.
- **HTTPS Redirect and Sensitive Data Exposure** -- Verifying that HTTP requests are redirected to HTTPS and that sensitive data is not leaked in URLs, headers, or client-side storage.
- **Session Fixation Prevention** -- Ensuring the session ID changes after authentication to prevent session fixation attacks.

## Decision table

| Vulnerability | Playwright Test Approach | Confidence Level |
|---|---|---|
| Reflected XSS | Inject payloads in inputs and URL params, assert no script execution | Medium -- covers common cases, not exhaustive |
| Stored XSS | Inject payload, reload page, assert sanitized output | Medium -- catches rendering-level issues |
| CSRF | Verify token presence, test rejection without token | High -- directly tests the mechanism |
| Insecure cookies | Assert `httpOnly`, `secure`, `sameSite` flags | High -- deterministic check |
| Missing security headers | Assert header presence and values | High -- deterministic check |
| Auth bypass | Navigate to protected routes without auth | High -- tests the redirect/block mechanism |
| Session fixation | Compare session IDs before and after login | High -- directly verifiable |
| Sensitive data exposure | Check URLs, localStorage, response bodies for secrets | Medium -- catches obvious leaks |
| HTTPS enforcement | Verify redirect and HSTS header | High -- deterministic check |

## TypeScript patterns

### Quick Reference

```typescript
// Check security headers on every navigation
const response = await page.goto('/dashboard');
expect(response.headers()['content-security-policy']).toBeDefined();
expect(response.headers()['x-frame-options']).toBe('DENY');

// Verify cookie security flags
const cookies = await context.cookies();
const sessionCookie = cookies.find(c => c.name === 'session');
expect(sessionCookie.httpOnly).toBe(true);
expect(sessionCookie.secure).toBe(true);
expect(sessionCookie.sameSite).toBe('Strict');
```

### CSP Header Validation

```typescript
import { test, expect } from '@playwright/test';

test('CSP headers are properly configured', async ({ page }) => {
  const response = await page.goto('/');
  const csp = response!.headers()['content-security-policy'];

  expect(csp).toBeDefined();
  expect(csp).toContain("default-src 'self'");
  expect(csp).not.toContain("'unsafe-inline'"); // Disallow inline scripts
  expect(csp).not.toContain("'unsafe-eval'");   // Disallow eval()
  expect(csp).toContain('script-src');
});

test('security headers are present on all pages', async ({ page }) => {
  const pagesToCheck = ['/', '/login', '/dashboard', '/api/health'];

  for (const url of pagesToCheck) {
    const response = await page.goto(url);
    const headers = response!.headers();

    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-frame-options']).toMatch(/DENY|SAMEORIGIN/);
    expect(headers['strict-transport-security']).toBeDefined();
    expect(headers['referrer-policy']).toBeDefined();
    expect(headers['x-xss-protection']).toBeUndefined(); // Deprecated, should not be set
  }
});
```

## Guardrails

- **XSS Injection Testing:** You need comprehensive XSS scanning — use a dedicated tool like OWASP ZAP alongside Playwright.
- **CSRF Token Verification:** Your API uses token-based auth (JWT) with no cookie-based sessions — CSRF is not applicable.
- **CSP Header Validation:** CSP is managed by infrastructure (CDN/WAF) tested separately.
- **Cookie Security Flags:** Your app is fully stateless with no cookies.
- **Authentication Bypass Testing:** Auth is tested through dedicated API tests that cover these cases already.
- **HTTPS Redirect and Sensitive Data Exposure:** Running against `localhost` where HTTPS is not configured.
- **Session Fixation Prevention:** Using stateless token auth (JWT) with no server-side sessions.

## Related guides

- [core/authentication.md](authentication.md) -- login flows and auth state management
- [core/network-mocking.md](network-mocking.md) -- intercepting requests for security testing
- [core/configuration.md](configuration.md) -- `ignoreHTTPSErrors` and base URL configuration
- [core/third-party-integrations.md](third-party-integrations.md) -- testing OAuth and third-party auth providers
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- running security tests in CI pipelines
