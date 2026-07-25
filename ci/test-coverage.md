# Test Coverage

> **When to use**: Measure which application code executes during Playwright tests. Coverage is a diagnostic signal, not proof that behavior is correctly asserted.

## Choose an approach

| Approach | Use |
|---|---|
| Chromium V8 coverage | Fast browser-runtime inspection for Chromium |
| Istanbul instrumentation | Cross-browser source-mapped coverage |
| API/unit coverage merge | Combine backend or unit results with E2E output |

## Chromium V8 coverage

```typescript
import { test, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

test('collects application coverage', async ({ page }, testInfo) => {
  await page.coverage.startJSCoverage({ resetOnNavigation: false });
  await page.goto('/');
  await page.getByRole('link', { name: 'Products' }).click();
  await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();

  const entries = await page.coverage.stopJSCoverage();
  const output = testInfo.outputPath('v8-coverage.json');
  await mkdir(testInfo.outputDir, { recursive: true });
  await writeFile(output, JSON.stringify(entries));
});
```

The API is Chromium-only and reports generated runtime code. Convert it with a source-map-aware coverage tool before enforcing source-level thresholds.

## Instrumented application

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import istanbul from 'vite-plugin-istanbul';

export default defineConfig({
  plugins: process.env.COVERAGE === 'true'
    ? [istanbul({
        include: 'src/**/*',
        exclude: ['**/*.spec.ts', '**/*.test.ts'],
        extension: ['.ts', '.tsx'],
        requireEnv: true,
      })]
    : [],
});
```

Enable instrumentation only in a controlled test build.

## Read browser coverage

```typescript
import { test } from '@playwright/test';
import { writeFile } from 'node:fs/promises';

test.afterEach(async ({ page }, testInfo) => {
  const coverage = await page.evaluate(() => {
    return (globalThis as typeof globalThis & {
      __coverage__?: Record<string, unknown>;
    }).__coverage__;
  });

  if (coverage) {
    await writeFile(
      testInfo.outputPath('istanbul-coverage.json'),
      JSON.stringify(coverage),
    );
  }
});
```

Merge per-test or per-shard files after execution; do not let workers overwrite one shared file.

## CI

```yaml
- run: COVERAGE=true npx playwright test
- name: Upload coverage
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@<reviewed-commit-sha>
  with:
    name: coverage-${{ strategy.job-index }}
    path: test-results/**/istanbul-coverage.json
```

Merge first, generate HTML/LCOV/Cobertura output second, then publish or enforce thresholds.

## Interpretation

- Line coverage says code executed, not that outcomes were asserted.
- Branch coverage is usually more useful for validation and error paths.
- Exclude generated files and test-only code explicitly.
- Keep thresholds stable and raise them deliberately.
- Investigate sudden drops before accepting new baselines.
- Avoid optimizing tests solely to increase a percentage.

## Troubleshooting

- Empty coverage: verify the application was instrumented and served the test build.
- Missing source files: verify source maps and URL-to-path mapping.
- Corrupt merged output: write unique files per worker or shard.
- Coverage only in Chromium: use instrumentation for cross-browser collection.
- Slow suite: collect coverage in a dedicated project.

## Related guides

- [Reporting and artifacts](reporting-and-artifacts.md)
- [Projects and dependencies](projects-and-dependencies.md)
- [Performance testing](../core/performance-testing.md)
