# Test Organization

> **When to use**: Structuring test files, naming tests, grouping with `describe`, tagging, filtering, and deciding parallel vs serial execution.
> **Prerequisites**: [core/configuration.md](configuration.md)

## Topic map

- **Pattern 1: Feature-Based File Structure** -- Any project — this is the default layout.
- **Pattern 2: Naming Conventions** -- Writing any test or file.
- **Pattern 3: `test.describe()` Grouping** -- A file has multiple related tests that share context or setup.
- **Pattern 4: Tags and Annotations** -- You need to categorize tests for selective runs (smoke suites, CI pipelines, skip known issues).
- **Pattern 5: Test Filtering** -- Running a subset of tests from the CLI or CI.
- **Pattern 6: Parallel vs Serial Execution** -- Deciding how tests run relative to each other.
- **Pattern 7: Monorepo Testing** -- A single repository contains multiple apps or packages that each need E2E tests.
- **One giant test file** -- **Fix:** Split by feature — one file per feature area, 5–15 tests per file.
- **Meaningless test names** -- **Fix:** Describe behavior. When a test fails, the name should tell you what broke.
- **Deep describe nesting** -- **Fix:** Max 2 levels. Split deeper nesting into separate files.
- **Using `test.describe.serial()` as the default** -- **Fix:** Each test should be independent. Use `beforeEach` or fixtures to set up state.
- **Relying on test execution order** -- **Fix:** Each test creates its own data via API calls or fixtures.

## Decision table

| Concept | Rule |
|---|---|
| File suffix | `.spec.ts` — always |
| Grouping | By feature/domain, not by page or URL |
| Test names | `test('should ...')` or `test('user can ...')` — describe behavior |
| Nesting | Max 2 levels of `test.describe()` |
| Default execution | `fullyParallel: true` — tests run in parallel by default |
| Serial tests | Almost never use `test.describe.serial()` |
| Test dependencies | Avoid — each test sets up its own state |
| Tags | `@smoke`, `@regression`, `@slow` — filter with `--grep` |

## TypeScript patterns

### Pattern 2: Naming Conventions

```typescript
// tests/checkout/cart.spec.ts
import { test, expect } from '@playwright/test';

// Good: group by feature, describe behavior
test.describe('Shopping Cart', () => {
  test('should add item to empty cart', async ({ page }) => {
    await page.goto('/products/widget-a');
    await page.getByRole('button', { name: 'Add to cart' }).click();
    await expect(page.getByTestId('cart-count')).toHaveText('1');
  });

  test('should update quantity when same item added twice', async ({ page }) => {
    await page.goto('/products/widget-a');
    await page.getByRole('button', { name: 'Add to cart' }).click();
    await page.getByRole('button', { name: 'Add to cart' }).click();
    await expect(page.getByTestId('cart-count')).toHaveText('2');
  });

  test('user can remove item from cart', async ({ page }) => {
    await page.goto('/cart');
    // ... setup item in cart via API or fixture
    await page.getByRole('button', { name: 'Remove' }).first().click();
    await expect(page.getByText('Your cart is empty')).toBeVisible();
  });
});
```

### Pattern 5: Test Filtering

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'smoke',
      testMatch: '**/*.spec.ts',
      grep: /@smoke/,
    },
    {
      name: 'regression',
      testMatch: '**/*.spec.ts',
      grep: /@regression/,
    },
    {
      name: 'all',
      testMatch: '**/*.spec.ts',
      grepInvert: /@slow/,
    },
  ],
});
```

## Guardrails

- **Pattern 1: Feature-Based File Structure:** Never. This is always correct.
- **Pattern 2: Naming Conventions:** Never.
- **Pattern 3: `test.describe()` Grouping:** A file has only 1–3 tests with no shared setup — skip the `describe` wrapper.
- **Pattern 4: Tags and Annotations:** All tests always run together and you have < 20 tests.
- **Pattern 5: Test Filtering:** Never — know these commands.
- **Pattern 6: Parallel vs Serial Execution:** You have < 5 tests (parallelism doesn't matter).
- **Pattern 7: Monorepo Testing:** Single app repo.

## Related guides

- [core/configuration.md](configuration.md) — `testMatch`, `testDir`, `fullyParallel`, `workers`
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) — shared setup via fixtures instead of `beforeAll`
- [core/test-architecture.md](test-architecture.md) — when to write E2E vs API vs component tests
- [ci/parallel-and-sharding.md](../ci/parallel-and-sharding.md) — CI sharding for large suites
- [ci/projects-and-dependencies.md](../ci/projects-and-dependencies.md) — multi-project config
