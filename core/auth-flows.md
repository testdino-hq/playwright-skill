# Authentication Flow Recipes

> **When to use**: You need to test login, signup, logout, session management, or any authentication-related user flow.

## Topic map

- **Recipe 1: Basic Login**
- **Complete Example**
- **Recipe 2: Login with "Remember Me"**
- **Complete Example**
- **Recipe 3: Signup with Email Verification (Mocked)**
- **Complete Example**
- **Recipe 4: Password Reset Flow**
- **Complete Example**
- **Recipe 5: OAuth Login (Mocked Callback)**
- **Complete Example**
- **Recipe 6: Role-Based Access Testing**
- **Complete Example**
- **Recipe 7: Session Timeout Handling**
- **Complete Example**
- **Recipe 8: Logout**
- **Complete Example**
- **Variations**
- **Login via API for Speed** -- Skip the UI for login when testing non-auth features. Use `request` context to get tokens faster.
- **Multi-Factor Authentication**
- **Passkeys / WebAuthn (Playwright 1.61+)** -- Playwright 1.61 ships a virtual WebAuthn authenticator scoped to the browser context: `context.credentials`. Tests can register passkeys and answer `navigator.credentials.create()` / `navigator.credentials.get()` cere...
- **Testing Auth with Different Browser Contexts**

## TypeScript patterns

### Login via API for Speed

```typescript
import { test as setup } from '@playwright/test';

setup('authenticate via API', async ({ request }) => {
  const response = await request.post('/api/auth/login', {
    data: {
      email: 'user@example.com',
      password: 'SecurePass123!',
    },
  });

  expect(response.ok()).toBeTruthy();

  // Save the auth state
  await request.storageState({ path: '.auth/user.json' });
});
```

### Multi-Factor Authentication

```typescript
test('logs in with MFA (TOTP)', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('mfa-user@example.com');
  await page.getByLabel('Password').fill('SecurePass123!');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // MFA challenge screen appears
  await expect(page.getByText('Enter verification code')).toBeVisible();

  // In test environments, use a predictable TOTP code or mock the verification
  await page.route('**/api/auth/verify-mfa', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, token: 'jwt-token' }),
    });
  });

  await page.getByLabel('Verification code').fill('123456');
  await page.getByRole('button', { name: 'Verify' }).click();

  await expect(page).toHaveURL('/dashboard');
});
```

## Related guides

- [Playwright Authentication Docs](https://playwright.dev/docs/auth)
