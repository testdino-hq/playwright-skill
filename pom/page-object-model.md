# Page Object Model

> **When to use**: Encapsulate repeated interactions with a stable page or reusable UI component. Prefer fixtures or helpers for state setup, data generation, and stateless utilities.

## Design rules

- Model user capabilities, not the DOM tree.
- Keep locators private or read-only unless tests genuinely need them.
- Expose intent-based methods such as `signIn()` or `addProduct()`.
- Keep assertions in tests unless a method represents a reusable business invariant.
- Inject `Page`; do not create browsers or contexts inside a page object.
- Compose component objects instead of building inheritance hierarchies.
- Resolve locators lazily; never cache element handles or mutable page state.

## Basic TypeScript page object

```typescript
import { expect, type Locator, type Page } from '@playwright/test';

export class LoginPage {
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;

  constructor(private readonly page: Page) {
    this.email = page.getByLabel('Email');
    this.password = page.getByLabel('Password');
    this.submit = page.getByRole('button', { name: 'Sign in' });
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async signIn(email: string, password: string): Promise<void> {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
  }

  async expectInvalidCredentials(): Promise<void> {
    await expect(this.page.getByRole('alert')).toContainText('Invalid credentials');
  }
}
```

Keep a small assertion method only when many tests share that exact domain expectation. Otherwise assert directly in the test.

## Use it from a test

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test('user signs in', async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn('user@example.com', process.env.TEST_PASSWORD!);
  await expect(page).toHaveURL(/dashboard/);
});
```

## Component composition

```typescript
import type { Locator, Page } from '@playwright/test';

export class Navbar {
  private readonly root: Locator;

  constructor(page: Page) {
    this.root = page.getByRole('navigation');
  }

  async openAccount(): Promise<void> {
    await this.root.getByRole('link', { name: 'Account' }).click();
  }
}

export class DashboardPage {
  readonly navbar: Navbar;

  constructor(private readonly page: Page) {
    this.navbar = new Navbar(page);
  }

  async goto(): Promise<void> {
    await this.page.goto('/dashboard');
  }
}
```

Use component objects for navigation bars, dialogs, tables, and widgets reused across pages.

## Provide page objects through fixtures

```typescript
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

type AppFixtures = { loginPage: LoginPage };

export const test = base.extend<AppFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
});

export { expect } from '@playwright/test';
```

Fixtures remove repeated construction and provide lifecycle control. Do not hide navigation or authentication in a fixture unless every consuming test requires it.

## Structure

```text
tests/
├── fixtures/app.fixture.ts
├── pages/login.page.ts
├── pages/dashboard.page.ts
├── components/navbar.component.ts
└── auth/login.spec.ts
```

Organize by feature when the suite is small; split `pages/` and `components/` when reuse justifies it.

## Avoid

- A single “god object” containing every page.
- Methods named after clicks instead of outcomes.
- Deep base-page inheritance.
- Constructors that navigate or perform asynchronous work.
- Stored values that can become stale after rerenders.
- Wrapping one-line Playwright calls without adding domain meaning.
- Returning raw element handles.

## Related guides

- [POM vs fixtures vs helpers](pom-vs-fixtures-vs-helpers.md)
- [Locators](../core/locators.md)
- [Fixtures and hooks](../core/fixtures-and-hooks.md)
- [Test organization](../core/test-organization.md)
