# Parallel Execution and Sharding

> **When to use**: Reduce suite runtime while preserving isolation across workers, files, projects, or CI machines.

## Concepts

| Mechanism | Scope |
|---|---|
| Workers | Parallel OS processes on one machine |
| Fully parallel | Tests within files may run concurrently |
| Shards | Split the suite across machines |
| Projects | Run different configurations or dependency graphs |

## TypeScript configuration

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  fullyParallel: true,
  workers: process.env.CI ? '50%' : undefined,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'blob' : 'html',
});
```

Start with fewer workers than available CPUs when the application or database is the bottleneck.

## Isolation pattern

```typescript
import { test as base } from '@playwright/test';

type Fixtures = { uniqueUser: string };

export const test = base.extend<Fixtures>({
  uniqueUser: async ({}, use, testInfo) => {
    const value = `user-${testInfo.workerIndex}-${testInfo.testId}@example.test`;
    await use(value);
  },
});
```

Never depend on file order, shared mutable variables, or one test cleaning data for another.

## CLI sharding

```bash
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

Use the same commit, dependencies, environment, and test inventory on every shard.

## CI matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    shard: [1/4, 2/4, 3/4, 4/4]
steps:
  - run: npx playwright test --shard=${{ matrix.shard }}
  - name: Upload blob report
    if: ${{ !cancelled() }}
    uses: actions/upload-artifact@<reviewed-commit-sha>
    with:
      name: blob-${{ strategy.job-index }}
      path: blob-report/
```

Merge downloaded blob reports with:

```bash
npx playwright merge-reports --reporter=html ./all-blob-reports
```

## Choosing concurrency

1. Measure the serial baseline.
2. Increase workers until runtime stops improving.
3. Watch CPU, memory, database connections, and server latency.
4. Shard only after one machine is efficiently utilized.
5. Rebalance when suite composition changes.

## Common failures

- Duplicate records: generate worker/test-specific data.
- Port conflicts: allocate ports per worker or use one shared read-only server.
- Rate limits: reduce concurrency or use test doubles for external services.
- Empty shards: reduce shard count or rebalance by duration.
- Missing merged report: use blob reporters and unique artifact names.
- Flakes only in parallel: remove shared state before adding retries.

## Related guides

- [Projects and dependencies](projects-and-dependencies.md)
- [Reporting and artifacts](reporting-and-artifacts.md)
- [Test organization](../core/test-organization.md)
- [Flaky tests](../core/flaky-tests.md)
