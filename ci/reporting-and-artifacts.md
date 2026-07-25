# Reporting and Artifacts

> **When to use**: Configure useful local output, machine-readable CI results, merged shard reports, and diagnostic retention.

## Reporter selection

| Need | Reporter |
|---|---|
| Local terminal feedback | `list`, `line`, or `dot` |
| Interactive investigation | `html` |
| CI test annotations | `github` |
| CI test-result ingestion | `junit` |
| Merge sharded runs | `blob` |
| Custom integration | Typed custom reporter |

## TypeScript configuration

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  reporter: process.env.CI
    ? [
        ['blob'],
        ['junit', { outputFile: 'artifacts/junit.xml' }],
      ]
    : [['html', { outputFolder: 'artifacts/html', open: 'on-failure' }]],
  outputDir: 'artifacts/test-results',
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

Keep every reporter's output path unique.

## Custom TypeScript reporter

```typescript
import type {
  FullResult,
  Reporter,
  TestCase,
  TestResult,
} from '@playwright/test/reporter';

export default class SummaryReporter implements Reporter {
  onTestEnd(test: TestCase, result: TestResult): void {
    console.log(`${result.status}: ${test.title}`);
  }

  onEnd(result: FullResult): void {
    console.log(`suite: ${result.status}`);
  }
}
```

Custom reporters must not print secrets, request bodies, or sensitive attachment content.

## Merge shard reports

Each shard should emit a uniquely named blob artifact. After downloading all artifacts:

```bash
npx playwright merge-reports --reporter=html ./all-blob-reports
```

All shards must use compatible Playwright versions and report configuration.

## CI artifact upload

```yaml
- name: Upload Playwright artifacts
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@<reviewed-commit-sha>
  with:
    name: playwright-${{ github.run_id }}
    path: |
      artifacts/html/
      artifacts/junit.xml
      artifacts/test-results/
    retention-days: 7
```

Use the provider's equivalent always-run condition so failed tests still publish evidence.

## Retention policy

| Artifact | Suggested policy |
|---|---|
| HTML/JUnit summary | Keep for the investigation window |
| Failure screenshots | Keep with failed run |
| Traces and videos | Short retention; potentially sensitive and large |
| Passing-run media | Usually disable |
| Approved visual baselines | Version control with review |

Choose retention according to organizational policy rather than treating these values as universal.

## Security

- Assume traces and videos contain credentials or personal data.
- Restrict artifact access to authorized users.
- Redact logs and custom reporter output.
- Never upload storage-state files.
- Use explicit artifact paths; avoid archiving the whole workspace.
- Delete obsolete artifacts through the provider's retention controls.

## Troubleshooting

- Empty HTML report: verify tests ran and output paths match.
- Shard merge fails: verify all blob directories and Playwright versions.
- JUnit not discovered: publish the exact configured XML path.
- Missing trace: ensure the retry or failure mode actually triggered capture.
- Huge uploads: disable passing-run video and narrow retained paths.

## Related guides

- [GitHub Actions](ci-github-actions.md)
- [GitLab CI](ci-gitlab.md)
- [Parallel execution and sharding](parallel-and-sharding.md)
- [Visual regression](../core/visual-regression.md)
