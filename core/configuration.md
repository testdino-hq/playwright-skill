# Configuration

> **When to use**: Setting up a new Playwright project, adjusting timeouts, adding browser targets, configuring CI behavior, or connecting environment-specific settings.

## Topic map

- **Production-Ready Config (Copy-Paste Starter)**
- **TypeScript**
- **Pattern 1: Environment-Specific Configuration** -- Tests run against dev, staging, and production environments.
- **Pattern 2: Multi-Project with Setup Dependencies** -- Tests need shared authentication state or database seeding before running.
- **Pattern 3: `webServer` with Build Step** -- Tests need a running application server. Let Playwright manage the server lifecycle.
- **Pattern 4: `globalSetup` / `globalTeardown`** -- One-time non-browser work: seeding a database, starting a service, setting env vars. Runs once per `npx playwright test` invocation.
- **Pattern 5: `.env` File Setup** -- Managing secrets, URLs, or feature flags without hardcoding.
- **Pattern 6: Trace, Screenshot, and Video Settings** -- Deciding artifact collection strategy for local development vs CI.
- **Which Timeout to Adjust**
- **Server Management**
- **Single vs Multi-Project Config**
- **globalSetup vs Setup Projects vs Fixtures**
- **"baseURL" not working -- tests navigate to full URL** -- Always pass relative paths to `page.goto()`:
- **webServer starts but tests still fail with connection refused** -- Ensure `webServer.url` matches the actual server address. Add a health check route if needed:
- **Tests pass locally but timeout in CI** -- Increase `navigationTimeout` for CI, reduce `workers` to avoid resource contention:
- **"Error: page.goto: Target page, context or browser has been closed"** -- Do not increase the global timeout. Instead, find the slow step using `--trace on` and fix it. Common causes: waiting for a slow API, unresolved network request, or missing `await`.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Starting out, early development | Single project (chromium only) | Faster feedback, simpler config |
| Pre-release cross-browser validation | Multi-project: chromium + firefox + webkit | Catch rendering/API differences |
| Mobile-responsive app | Add mobile projects alongside desktop | Viewport + touch differences matter |
| Authenticated + unauthenticated tests | Setup project + dependent projects | Share auth state without re-login per test |
| CI pipeline with tight time budget | Chromium in PR checks; all browsers on merge to main | Balance speed vs coverage |

## TypeScript patterns

### Pattern 1: Environment-Specific Configuration

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

// Load environment-specific .env file: .env.staging, .env.production, etc.
const ENV = process.env.TEST_ENV || 'local';
dotenv.config({ path: path.resolve(__dirname, `.env.${ENV}`) });

const envConfig: Record<string, { baseURL: string; retries: number }> = {
  local:      { baseURL: 'http://localhost:3000',       retries: 0 },
  staging:    { baseURL: 'https://staging.example.com', retries: 2 },
  production: { baseURL: 'https://www.example.com',     retries: 2 },
};

const env = envConfig[ENV];

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  retries: env.retries,
  use: {
    baseURL: env.baseURL,
  },
});
```

### Pattern 2: Multi-Project with Setup Dependencies

```typescript
// tests/global.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await page.context().storageState({ path: authFile });
});
```

## Guardrails

- **Pattern 1: Environment-Specific Configuration:** Single-environment local-only projects.
- **Pattern 2: Multi-Project with Setup Dependencies:** Tests are fully independent with no shared setup phase.
- **Pattern 3: `webServer` with Build Step:** Testing against an already-deployed environment (staging/prod).
- **Pattern 4: `globalSetup` / `globalTeardown`:** You need browser context (use a setup project instead) or per-test isolation (use fixtures).
- **Pattern 5: `.env` File Setup:** Never commit `.env` files with real secrets. Provide `.env.example` instead.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- custom fixtures that replace `globalSetup` for per-test state
- [core/test-organization.md](test-organization.md) -- file structure, naming conventions, test grouping
- [core/authentication.md](authentication.md) -- setup projects for shared auth state
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI-specific config and caching
- [ci/projects-and-dependencies.md](../ci/projects-and-dependencies.md) -- advanced multi-project patterns
