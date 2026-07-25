# Fixtures and Hooks

> **When to use**: Whenever tests need shared setup, teardown, reusable resources, or configurable context. Fixtures are Playwright's killer feature — prefer them over hooks in every situation where both could work.

## Topic map

- **1. Custom Test Fixture** -- Tests need a resource with guaranteed setup and teardown.
- **2. Worker-Scoped Fixtures** -- A resource is expensive to create and safe to share across tests in the same worker (database connections, auth tokens, compiled assets).
- **3. Auto Fixtures** -- Something must run for every test without being explicitly requested — blocking analytics, capturing console errors, injecting feature flags.
- **4. Fixture Composition with `mergeTests()`** -- You have multiple fixture files (auth fixtures, API fixtures, UI fixtures) and tests need several of them.
- **5. Parameterized Fixtures (Option Fixtures)** -- A fixture's behavior should be configurable per-project or per-describe block (locale, viewport, user role, feature flags).
- **6. Fixture Dependencies** -- One fixture needs the output of another fixture. Playwright automatically resolves the dependency graph.
- **7. Overriding Built-in Fixtures** -- Every test needs the same modification to `page`, `context`, or `browser` — custom headers, viewport, locale, route blocking.
- **8. beforeEach / afterEach — When Hooks Are Acceptable** -- Simple, stateless setup with no teardown needed. Navigation to a starting URL is the canonical example.
- **9. beforeAll / afterAll — Worker-Level Hooks** -- One-time setup that all tests in a file share and that has no cleanup needs, such as logging a diagnostic or checking a precondition.
- **10. Typed Fixtures in TypeScript** -- Always define an interface for your fixtures. This gives you autocomplete, catches typos at compile time, and documents the fixture contract.
- **11. Aborting a Test From a Fixture or Route (`test.abort()`, Playwright 1.60+)** -- A fixture, hook, or route handler detects an unrecoverable precondition — a required backend is down, a seed step failed, or a route received an unexpected request — and continuing would only produce a confusing downs...
- **1. Global Mutable State in `beforeAll`**
- **2. Cleanup in `afterEach` Instead of Fixture Teardown**
- **3. Fixtures That Do Too Many Things**
- **4. Over-Abstracting Fixtures**
- **5. Not Typing Fixtures in TypeScript**

## Decision table

| Mechanism | Scope | Cleanup guaranteed? | Parallelism-safe? | Use for |
|---|---|---|---|---|
| `test.extend()` fixture | per-test | Yes (via `use()` callback) | Yes | Most setup/teardown needs |
| Worker-scoped fixture | per-worker | Yes | Yes (isolated per worker) | Expensive resources: DB connections, auth state |
| Auto fixture | per-test or per-worker | Yes | Yes | Side effects that must always run: blocking analytics, logging |
| `beforeEach` / `afterEach` | per-test | No (`afterEach` skipped on crash) | Yes | Simple, one-off setup that doesn't need cleanup |
| `beforeAll` / `afterAll` | per-worker | No (`afterAll` skipped on crash) | Dangerous if mutating shared state | One-time worker setup with no cleanup needs |

## TypeScript patterns

### 1. Custom Test Fixture

```typescript
// todos.spec.ts
import { test, expect } from './fixtures';

test('add a todo item', async ({ todoPage, page }) => {
  await todoPage.addTodo('Buy milk');
  await expect(await todoPage.todos()).toHaveCount(1);
});
```

### 4. Fixture Composition with `mergeTests()`

```typescript
// fixtures/auth.ts
import { test as base } from '@playwright/test';

type AuthFixtures = {
  authenticatedPage: import('@playwright/test').Page;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('/dashboard');
    await use(page);
  },
});
```

## Guardrails

- **1. Custom Test Fixture:** The setup is a single line with no teardown — a `beforeEach` is fine.
- **2. Worker-Scoped Fixtures:** Tests mutate the resource — each test must get its own copy.
- **3. Auto Fixtures:** Tests need to opt out. Auto fixtures always run; there is no per-test escape hatch.
- **4. Fixture Composition with `mergeTests()`:** You only have one fixture file. Don't over-engineer.
- **5. Parameterized Fixtures (Option Fixtures):** The value never changes — just hardcode it in the fixture.
- **6. Fixture Dependencies:** You are tempted to nest fixtures more than 3 levels deep — flatten the design instead.
- **7. Overriding Built-in Fixtures:** Only some tests need the override. Use a new named fixture instead to keep the default `page` available.
- **8. beforeEach / afterEach — When Hooks Are Acceptable:** The setup creates something that must be cleaned up. Use a fixture instead.

## Related guides

- [pom/page-object-model.md](../pom/page-object-model.md) — Page objects are typically consumed via fixtures
- [core/test-organization.md](test-organization.md) — Where to put fixture files in the project tree
- [core/configuration.md](configuration.md) — Option fixtures are configured in `playwright.config`
- [core/authentication.md](authentication.md) — Auth state is the most common worker-scoped fixture
- [ci/global-setup-teardown.md](../ci/global-setup-teardown.md) — For truly global (all-workers) setup, not per-worker
- [pom/pom-vs-fixtures-vs-helpers.md](../pom/pom-vs-fixtures-vs-helpers.md) — When to use each abstraction
