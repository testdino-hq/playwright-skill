# GitLab CI

> **When to use**: Run Playwright in GitLab pipelines with caching, artifacts, services, and optional parallel jobs.

## Baseline pipeline

Use an image whose Playwright version matches the lockfile. Pin the image by digest in production.

```yaml
stages: [test]

playwright:
  stage: test
  image: mcr.microsoft.com/playwright:<matching-version>@sha256:<reviewed-digest>
  timeout: 30m
  variables:
    CI: "true"
    BASE_URL: "http://app:3000"
  before_script:
    - npm ci
  script:
    - npx playwright test
  artifacts:
    when: always
    expire_in: 7 days
    paths:
      - playwright-report/
      - test-results/
    reports:
      junit: test-results/junit.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

If the image already includes browsers and OS dependencies, do not reinstall them.

## TypeScript configuration

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? '50%' : undefined,
  reporter: [
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['html', { open: 'never' }],
  ],
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

## Services

```yaml
playwright:
  services:
    - name: postgres:<reviewed-version>
      alias: db
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: $TEST_DB_PASSWORD
    DATABASE_URL: postgresql://test:$TEST_DB_PASSWORD@db:5432/test
```

Use service aliases such as `db`, not `localhost`. Wait for service health before testing.

## Parallel jobs

```yaml
playwright:
  parallel: 4
  script:
    - npx playwright test --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  artifacts:
    name: "blob-$CI_NODE_INDEX"
    paths: [blob-report/]
```

Merge blob reports in a dependent job when a single HTML report is required.

## Rules

- Protect masked variables and limit them to trusted branches.
- Pin container images by digest.
- Use a committed lockfile and `npm ci`.
- Cache package downloads, not `node_modules`.
- Keep reports on every completed job and traces on failures.
- Use resource groups only for tests that truly require serialized access.

## Related guides

- [Parallel execution and sharding](parallel-and-sharding.md)
- [Reporting and artifacts](reporting-and-artifacts.md)
- [Docker and containers](docker-and-containers.md)
