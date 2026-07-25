# Migrating from Selenium to Playwright

> **When to use**: Convert Selenium/WebDriver suites in any source language to TypeScript Playwright.

## Mindset shifts

- Remove driver installation and WebDriver protocol management.
- Replace implicit and explicit wait mixtures with locator auto-waiting.
- Replace stored element handles with lazy locators.
- Use isolated browser contexts instead of global driver state.
- Use Playwright Test fixtures, retries, projects, traces, and parallelism.
- Assert with awaited web-first expectations.

## API mapping

| Selenium concept | TypeScript Playwright |
|---|---|
| Navigate to URL | `await page.goto(url)` |
| Find by id/CSS/XPath | Prefer `getByRole`, `getByLabel`, or `getByTestId` |
| `click` | `await locator.click()` |
| `sendKeys` | `fill`, `press`, or `pressSequentially` |
| Explicit visibility wait | `await expect(locator).toBeVisible()` |
| Wait for URL | `await page.waitForURL(pattern)` |
| Switch to frame | `page.frameLocator(selector)` |
| Window handle | `page.waitForEvent('popup')` |
| Actions drag-and-drop | `locator.dragTo(target)` |
| New driver session | `browser.newContext()` |
| Cookies/profile reuse | `storageState` |
| Grid parallelism | Playwright workers, projects, and sharding |

## TypeScript page object

```typescript
import { type Locator, type Page } from '@playwright/test';

export class LoginPage {
  private readonly email: Locator;
  private readonly password: Locator;
  private readonly submit: Locator;

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
}
```

Do not reproduce Selenium base-page inheritance or cache elements. Compose focused page and component objects.

## TypeScript test

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';

test('user signs in', async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn('user@example.com', process.env.TEST_PASSWORD!);

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Frames, popups, and drag-and-drop

```typescript
const payment = page.frameLocator('[title="Payment"]');
await payment.getByLabel('Card number').fill('4242424242424242');

const popupPromise = page.waitForEvent('popup');
await page.getByRole('link', { name: 'Open report' }).click();
const popup = await popupPromise;
await expect(popup.getByRole('heading', { name: 'Report' })).toBeVisible();

await page.getByTestId('source').dragTo(page.getByTestId('target'));
```

Start waiting for a popup before the action that opens it.

## Migration sequence

1. Add TypeScript Playwright beside the existing suite.
2. Configure `baseURL`, browsers, retries, traces, and CI.
3. Convert shared page objects without copying inheritance hierarchies.
4. Replace driver setup with fixtures and project configuration.
5. Migrate stable, high-value tests first.
6. Replace explicit waits with web-first assertions.
7. Run both suites until behavior and coverage match.
8. Remove Selenium drivers, grid configuration, and dependencies.

## Common mistakes

- Translating selectors literally instead of adopting semantic locators.
- Calling `locator()` and expecting an immediate not-found error.
- Storing locator-derived state across rerenders.
- Sharing one page or context across parallel tests.
- Adding sleeps to imitate explicit waits.
- Forgetting that `fill()` replaces existing text.
- Omitting `await` from expectations.
- Enabling every browser on every pull request without measuring value.

## Related guides

- [Locators](../core/locators.md)
- [Assertions and waiting](../core/assertions-and-waiting.md)
- [Page Object Model](../pom/page-object-model.md)
- [Parallel execution and sharding](../ci/parallel-and-sharding.md)
- [Debugging](../core/debugging.md)
