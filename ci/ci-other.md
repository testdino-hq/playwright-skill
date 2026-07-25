# Other CI Providers

> **When to use**: Configure Playwright on CircleCI, Azure Pipelines, Jenkins, or another runner using the same reproducible CI contract.

## Provider-neutral contract

Every pipeline should:

1. Check out a trusted revision.
2. Install the locked Node version and run `npm ci`.
3. Install matching Playwright browsers and OS dependencies.
4. Start or address the application under test.
5. Run TypeScript Playwright tests with CI settings.
6. Publish reports and failure artifacts even when tests fail.

## CircleCI

```yaml
version: 2.1
jobs:
  test:
    docker:
      - image: mcr.microsoft.com/playwright:<matching-version>
    steps:
      - checkout
      - run: npm ci
      - run: npx playwright test
      - store_artifacts:
          path: playwright-report
      - store_test_results:
          path: test-results
workflows:
  test:
    jobs: [test]
```

Pin the image by digest and use workspaces only for artifacts needed by downstream jobs.

## Azure Pipelines

```yaml
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: "22.x"
  - script: npm ci
  - script: npx playwright install --with-deps
  - script: npx playwright test
    env:
      CI: "true"
      TEST_PASSWORD: $(TEST_PASSWORD)
  - task: PublishTestResults@2
    condition: succeededOrFailed()
    inputs:
      testResultsFiles: test-results/junit.xml
  - task: PublishPipelineArtifact@1
    condition: succeededOrFailed()
    inputs:
      targetPath: playwright-report
      artifact: playwright-report
```

Pin marketplace tasks where the platform supports immutable references.

## Jenkins

```groovy
pipeline {
  agent { docker { image 'mcr.microsoft.com/playwright:<matching-version>' } }
  stages {
    stage('Install') {
      steps { sh 'npm ci' }
    }
    stage('Test') {
      steps {
        withCredentials([string(credentialsId: 'test-password', variable: 'TEST_PASSWORD')]) {
          sh 'npx playwright test'
        }
      }
    }
  }
  post {
    always {
      junit 'test-results/junit.xml'
      archiveArtifacts artifacts: 'playwright-report/**,test-results/**'
    }
  }
}
```

Do not echo credential variables. Restrict archived artifacts because traces may contain secrets.

## TypeScript CI settings

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['html', { open: 'never' }],
  ],
  use: { trace: 'on-first-retry' },
});
```

## Troubleshooting

- Browser missing: install matching browsers or use the official image.
- Server unreachable: bind to `0.0.0.0` and use the service hostname.
- Out-of-memory browser crash: reduce workers and increase shared memory.
- Missing report after failure: use an always/succeeded-or-failed post step.
- Local pass but CI failure: compare Node, browser, timezone, locale, and environment variables.

## Related guides

- [Docker and containers](docker-and-containers.md)
- [Reporting and artifacts](reporting-and-artifacts.md)
- [Parallel execution and sharding](parallel-and-sharding.md)
