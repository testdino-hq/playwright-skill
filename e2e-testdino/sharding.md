# Sharded e2e Runs as One Run

> **When to use**: The e2e suite is split across CI jobs with `--shard`, or by giving each job its own files, and the team needs one result: one pass or fail, one list of failures, one link. e2e writes a separate `report.json` per job and does not merge them.
> **Prerequisites**: the e2e skill, topic `running` (`--shard`, CI). [results-and-artifacts.md](results-and-artifacts.md) for the reporter. To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

Cutting the suite is e2e's job and its skill covers it. Putting the pieces back together is not something a test runner on one machine can do: each job only knows its own slice. The merge happens where all the jobs report to.

## Quick Reference

```bash
# Every shard: the same run id, its own index
TESTDINO_CI_RUN_ID="$CI_RUN_ID" npx e2e run --shard 1/3
TESTDINO_CI_RUN_ID="$CI_RUN_ID" npx e2e run --shard 2/3
TESTDINO_CI_RUN_ID="$CI_RUN_ID" npx e2e run --shard 3/3
```

| CI | A value that is the same on every job of one pipeline |
|---|---|
| GitHub Actions | `${{ github.run_id }}-${{ github.run_attempt }}` |
| GitLab CI | `$CI_PIPELINE_ID` |
| CircleCI | `$CIRCLE_WORKFLOW_ID` |
| Azure Pipelines | `$(Build.BuildId)` |
| Jenkins | `$BUILD_TAG` |

## Patterns

### Pattern 1: A GitHub Actions Matrix That Reports as One Run

**Use when**: The suite runs as a `--shard` matrix on GitHub Actions.

Take the job from the e2e skill (topic `running`, "Continuous integration") and add the matrix and two variables:

```yaml
jobs:
  e2e:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false                 # one red shard must not cancel the others
      matrix:
        shard: [1, 2, 3]
    steps:
      # ...checkout, install, browser install: as in the e2e skill's workflow
      - run: npx e2e run --shard ${{ matrix.shard }}/3 --reporter list,junit
        env:
          TESTDINO_TOKEN: ${{ secrets.TESTDINO_TOKEN }}
          TESTDINO_CI_RUN_ID: ${{ github.run_id }}-${{ github.run_attempt }}
          # ...the model key and credentials the suite needs
      # The e2e skill's two upload steps, each with the shard in its name, or the uploads collide
      - if: ${{ !cancelled() }}
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: e2e-report-${{ matrix.shard }}
          path: |
            .e2e/report.json
            .e2e/junit.xml
      - if: ${{ !cancelled() }}
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: e2e-artifacts-${{ matrix.shard }}
          path: .e2e/results
          retention-days: 7
```

The three jobs appear as one run with the suite's total, and each test keeps the number of the shard it ran in.

`github.run_attempt` is part of the id on purpose: re-running the workflow is a new attempt and gets its own run, instead of mixing into the first. When the step runs through `testdino-e2e run` ([flaky-or-broken.md](flaky-or-broken.md), Pattern 4), a retried attempt can also run only the tests that failed in that job before, linked to the first run as a re-run. TestDino decides; a job it cannot narrow safely (one passing `--repeat-each`, say) runs in full and prints why. Needs e2e 0.19.0+.

### Pattern 2: GitLab and the Others

**Use when**: Any CI with a parallel or matrix feature.

The rule is the same everywhere: the id must match across the jobs of one pipeline and differ between pipelines.

```yaml
# .gitlab-ci.yml
e2e:
  parallel: 3
  variables:
    TESTDINO_CI_RUN_ID: $CI_PIPELINE_ID
  script:
    # ...
    - npx e2e run --shard $CI_NODE_INDEX/$CI_NODE_TOTAL --reporter list,junit
```

`TESTDINO_TOKEN` comes from the CI's secret store on every job.

### Pattern 3: Split Mode, When Jobs Run Different Files

**Use when**: You decide which files each job runs (by directory, by target, by team) instead of letting `--shard` slice the suite.

`TESTDINO_CI_RUN_ID` is for `--shard`. Jobs that pick their own files use a split position and a split id, and both are required:

```bash
TESTDINO_SPLIT=1/2 TESTDINO_SPLIT_ID="$PIPELINE_ID" npx e2e run tests/checkout
TESTDINO_SPLIT=2/2 TESTDINO_SPLIT_ID="$PIPELINE_ID" npx e2e run tests/account
```

### Pattern 4: Read a Merged Run

**Use when**: Triaging a sharded run with an agent.

```text
list_testruns  by_branch: "<branch>"                       → the run, with is_sharded: true
list_testcase  by_testrun_id, by_status: "failed"          → failures across every shard
list_testcase  by_testrun_id, by_shard: 2                  → only what shard 2 ran
```

Each test row has `shard_index`. A failure that only ever appears on one shard index across runs points at what that slice shares (a setup test, seeded data, a slow first route), not at the test.

### Pattern 5: What Each Shard Still Does on Its Own

**Use when**: Reviewing a sharded workflow.

Merging the results does not merge the jobs. Three things stay per shard, each covered by the e2e skill or docs:

- **Setup tests.** Each shard brings its own, so a sign-in setup runs once per shard.
- **The pull request comment.** `github()` from `@e2e-dev/github` needs a different `key` on each matrix job, or the jobs share one comment and the last to finish wins. Pass the index in the step's env (`SHARD: ${{ matrix.shard }}`) and use `` github({ key: `shard-${process.env.SHARD}` }) ``.
- **`--last-failed`.** It reads the `report.json` of the previous run from the output folder, and a new job has none unless it downloads that shard's report there first (e2e's docs, `ci.mdx`, "Rerunning failures"). To run only what failed across all shards, use the merged run:

  ```bash
  npx -p @testdino/e2e testdino-e2e rerun --from-run <testRunId>
  ```

  [flaky-or-broken.md](flaky-or-broken.md) covers that command.

A shard that selects no test fails with `NO_TESTS`. When a matrix can have more shards than tests, add `--pass-with-no-tests`.

## Decision Guide

| Situation | Use |
|---|---|
| One machine is fast enough | No shards. `--workers` first; CI defaults to one worker |
| The suite is too slow for one job | `--shard i/n` in a matrix, plus `TESTDINO_CI_RUN_ID` |
| Jobs are split by hand (per directory, per target) | `TESTDINO_SPLIT` and `TESTDINO_SPLIT_ID` |
| Device targets | One worker per device is e2e's rule, so shards or separate jobs are how device suites scale: [mobile-results.md](mobile-results.md) |
| Only JUnit is needed, on GitLab | GitLab already merges the shards' JUnit files in the merge request widget. The reporter adds history, evidence and one run |
| Build should pass when the only failures are quarantined | Run each shard through `npx -p @testdino/e2e testdino-e2e run -- --shard …`: [flaky-or-broken.md](flaky-or-broken.md) |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| Build the run id from the matrix index or the job id | Every shard gets a different id and uploads as its own run | A pipeline-level value (Quick Reference) |
| Use a fixed string such as `nightly` | The id no longer differs between pipelines | A value the CI generates per pipeline |
| Leave `fail-fast` on | The first red shard cancels the rest, and the merged run is missing their tests | `fail-fast: false` |
| Upload every shard's `report.json` or `.e2e/results` under one artifact name | The uploads overwrite or reject each other | A name with the shard index on both artifacts |
| Download three `report.json` files and merge them by hand to find the failures | e2e has no merge command, and a merged report needs its summary, serial groups and artifact paths recomputed | Read the merged run |
| Shard a suite that takes two minutes | Every shard pays app start and setup tests again | Shard when one job is the bottleneck |

## Troubleshooting

### `shards uploaded as separate runs: set TESTDINO_CI_RUN_ID to merge them`

The `TestDino` row of a shard's summary adds this, in parentheses after the run link, when the variable is missing. Set the same value on every shard. A value set at the job level of a matrix reaches all its jobs.

### The merged run is missing a shard's tests

That job never reported: it was cancelled (`fail-fast`), it had no token, or it stopped before its tests started (exit code 2 or 3). Open that job's log and read its `TestDino` row.

### `split ignored: a split position and TESTDINO_SPLIT_ID are needed together`

One of the two variables is missing on that job.

### The run total is lower than the suite

`--shard` is applied after every other filter. A matrix that also passes `--tag` or `--changed-since` merges only the selected tests, which is correct.

## Related

- [results-and-artifacts.md](results-and-artifacts.md): the reporter and its options
- [flaky-or-broken.md](flaky-or-broken.md): re-running only failures, quarantine
- [../ci/parallel-and-sharding.md](../ci/parallel-and-sharding.md): Playwright sharding and `merge-reports`
- [../ci/ci-github-actions.md](../ci/ci-github-actions.md): matrix workflows, pinning actions to commit SHAs
