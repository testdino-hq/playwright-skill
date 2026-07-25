# Projects and Dependencies

> **When to use**: Run the same tests with different browsers, devices, roles, environments, or prerequisite setup.

## Browser projects

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
});
```

Keep project names stable because CLI filters and reports depend on them.

## Setup dependency

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'setup',
      testMatch: '**/*.setup.ts',
      teardown: 'cleanup',
    },
    {
      name: 'cleanup',
      testMatch: '**/*.teardown.ts',
    },
    {
      name: 'authenticated',
      dependencies: ['setup'],
      use: { storageState: 'playwright/.auth/user.json' },
    },
  ],
});
```

Dependencies run before the dependent project and appear in reports. Use teardown projects only for resources that are safe and necessary to clean after the run.

## Role projects

```typescript
export default defineConfig({
  projects: [
    {
      name: 'admin',
      testMatch: '**/*.admin.spec.ts',
      use: { storageState: '.auth/admin.json' },
    },
    {
      name: 'viewer',
      testMatch: '**/*.viewer.spec.ts',
      use: { storageState: '.auth/viewer.json' },
    },
  ],
});
```

Use separate state files and test identities for every role.

## Environment projects

```typescript
const environments = {
  local: 'http://127.0.0.1:3000',
  staging: 'https://staging.example.test',
} as const;

export default defineConfig({
  projects: Object.entries(environments).map(([name, baseURL]) => ({
    name,
    use: { baseURL },
  })),
});
```

Do not include production unless the suite is explicitly designed and authorized for safe production checks.

## CLI

```bash
npx playwright test --project=chromium
npx playwright test --project=admin
npx playwright test --project=chromium --no-deps
```

Use `--no-deps` only when prerequisite state already exists and skipping setup is intentional.

## Rules

- Use projects for configuration variants, not arbitrary test grouping.
- Avoid a browser × role × environment explosion; test only valuable combinations.
- Keep setup idempotent and dependency graphs acyclic.
- Do not share mutable auth state across concurrent projects.
- Use `testMatch` and `testIgnore` to make ownership explicit.
- Prefer fixtures for per-test resources.

## Related guides

- [Global setup and teardown](global-setup-teardown.md)
- [Parallel execution and sharding](parallel-and-sharding.md)
- [Authentication](../core/authentication.md)
- [Mobile and responsive testing](../core/mobile-and-responsive.md)
