# GitHub Actions

> **When to use**: Run Playwright tests on pull requests, protected branches, or schedules with reproducible dependencies and retained diagnostics.

## Baseline workflow

Pin third-party actions to reviewed commit SHAs. Replace placeholders during implementation.

```yaml
name: Playwright
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    env:
      CI: true
      BASE_URL: http://127.0.0.1:3000
      TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
    steps:
      - uses: actions/checkout@<reviewed-commit-sha>
      - uses: actions/setup-node@<reviewed-commit-sha>
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npm run start &
      - run: npx wait-on http://127.0.0.1:3000
      - run: npx playwright test
      - name: Upload report
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@<reviewed-commit-sha>
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
      - name: Upload traces
        if: ${{ failure() }}
        uses: actions/upload-artifact@<reviewed-commit-sha>
        with:
          name: test-results
          path: test-results/
          retention-days: 7
```

Prefer Playwright `webServer` configuration over shell backgrounding when the test runner can own the server lifecycle.

## TypeScript CI configuration

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? '50%' : undefined,
  reporter: process.env.CI
    ? [['blob'], ['github']]
    : [['html', { open: 'on-failure' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Sharding

Use a matrix only when runtime justifies artifact-merging complexity:

```yaml
strategy:
  fail-fast: false
  matrix:
    shard: [1/4, 2/4, 3/4, 4/4]
steps:
  - run: npx playwright test --shard=${{ matrix.shard }}
```

Give each shard a unique blob-report artifact, download all blobs in a dependent job, then run `npx playwright merge-reports`.

## Security and reliability

- Use minimal `permissions`; do not grant write access to untrusted pull requests.
- Store credentials in GitHub secrets or an approved identity provider.
- Never expose secrets to workflows from forks.
- Pin actions by commit SHA and review dependency updates.
- Use `npm ci` with a committed lockfile.
- Match installed Playwright packages and browser binaries.
- Upload traces on failure and reports when the job is not cancelled.
- Set timeouts and artifact retention explicitly.

## Related guides

- [Parallel execution and sharding](parallel-and-sharding.md)
- [Reporting and artifacts](reporting-and-artifacts.md)
- [Docker and containers](docker-and-containers.md)
- [Global setup and teardown](global-setup-teardown.md)
