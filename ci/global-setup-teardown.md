# Global Setup and Teardown

> **When to use**: Prepare or clean resources once per test run. Prefer project dependencies or fixtures when setup should be visible in reports, retried, or isolated.

## Choose the mechanism

| Need | Use |
|---|---|
| Authenticate once and reuse state | Setup project |
| Create/clean a resource per test | Test-scoped fixture |
| Create/clean once per worker | Worker-scoped fixture |
| Run a simple process-wide hook | `globalSetup` / `globalTeardown` |

## Setup project

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.context().storageState({ path: authFile });
});
```

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'setup', testMatch: '**/*.setup.ts' },
    {
      name: 'chromium',
      dependencies: ['setup'],
      use: { storageState: 'playwright/.auth/user.json' },
    },
  ],
});
```

Setup projects use normal fixtures, traces, reporters, and retries. Keep auth files gitignored.

## Global hooks

```typescript
// tests/global-setup.ts
import type { FullConfig } from '@playwright/test';

export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0]?.use.baseURL;
  if (!baseURL) throw new Error('baseURL is required');
  await seedDatabase();
}

async function seedDatabase(): Promise<void> {
  // Call an approved test-only seeding API or library.
}
```

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  globalSetup: './tests/global-setup.ts',
  globalTeardown: './tests/global-teardown.ts',
});
```

Global hooks do not receive `page`, `request`, or test fixtures. Import only deterministic setup code.

## Fixture lifecycle

```typescript
import { test as base } from '@playwright/test';

type Fixtures = { projectId: string };

export const test = base.extend<Fixtures>({
  projectId: async ({ request }, use) => {
    const response = await request.post('/api/test/projects');
    const project = await response.json() as { id: string };
    await use(project.id);
    await request.delete(`/api/test/projects/${project.id}`);
  },
});
```

Place cleanup after `use()` so it runs even when the test fails.

## Rules

- Make setup idempotent and safe to rerun.
- Verify authentication before saving storage state.
- Keep per-test data out of global setup.
- Use unique data for parallel workers.
- Never clean production resources.
- Preserve the original test failure if cleanup also fails.
- Use explicit environment checks before destructive teardown.

## Related guides

- [Projects and dependencies](projects-and-dependencies.md)
- [Core fixtures and hooks](../core/fixtures-and-hooks.md)
- [Authentication](../core/authentication.md)
- [Test data management](../core/test-data-management.md)
