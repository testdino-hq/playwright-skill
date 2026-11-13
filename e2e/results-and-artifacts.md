# Results and Artifacts From an e2e Run

> **When to use**: An e2e suite runs in CI, and its results, screenshots, videos and trace pages need to outlive the job: a link to share, history across runs, evidence an agent can fetch from another machine. Also for checking or troubleshooting the `@testdino/e2e` reporter.
> **Prerequisites**: the e2e skill, topic `running` (reporters, the output folder, CI). To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

e2e writes everything about a run into `.e2e/` on the machine that ran it. In CI that folder dies with the job unless something carries it out. The built-in reporters cover one run at a time. A results service covers the rest: every run kept, shards merged, links that work for a teammate.

## Quick Reference

```bash
npm install --save-dev @testdino/e2e     # needs e2e >=0.16.0 <1 and Node >=22.12.0; e2e itself may need a newer Node
npm ls e2e @testdino/e2e                 # 1.1.0+ for live results and trace pages

export TESTDINO_TOKEN="<project API key>"
npx e2e run                              # the TestDino line of the summary links the run
```

```ts
// e2e.config.ts
import type { E2EConfig } from 'e2e';
import { testdino } from '@testdino/e2e';

export default {
  targets: [/* your targets */],
  reporters: ['list', testdino()],
} satisfies E2EConfig;
```

## Patterns

### Pattern 1: Add the Reporter Beside the Built-In Ones

**Use when**: The project has an `e2e.config.ts` and no `testdino()` in its `reporters`.

Keep `list`. A config that lists only reporter objects prints nothing in the terminal, and the terminal's failure block is what the e2e skill reads first.

```ts
reporters: ['list', 'junit', testdino()],
```

`--reporter` on the command line replaces only the built-in reporters. Reporter objects in the config still run, so `npx e2e run --reporter list,junit` in CI still uploads.

Without a token the reporter uploads nothing and the tests run as usual. That makes it safe to commit the config line before the CI secret exists.

### Pattern 2: The Token in CI

**Use when**: Wiring the reporter into a pipeline.

Start from the workflow in the e2e skill (topic `running`, "Continuous integration"). The reporter adds one variable to the step that runs the tests:

```yaml
      - run: npx e2e run --reporter list,junit
        env:
          TESTDINO_TOKEN: ${{ secrets.TESTDINO_TOKEN }}
          # ...the model key and credentials the e2e skill's workflow already passes
```

- The token is a TestDino project API key ([how to create one](https://docs.testdino.com/guides/generate-api-keys)). Pass it as a CI secret, never as a literal in `e2e.config.ts`.
- Commit, branch and author come from the Git checkout. Without one the run still uploads, with those fields empty. On a pull request build (a GitHub Actions `pull_request` event, or the pull request variables of GitLab, Bitbucket, Buildkite and similar CI) the run also carries the pull request number and branches.
- Keep the e2e skill's artifact upload steps for `.e2e/report.json`. The reporter does not replace that file: `--last-failed` reads it, and [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md) needs it.

### Pattern 3: Know What Arrives, and When

**Use when**: Telling a user what they will see, or working out why something is missing.

| When | What appears in TestDino |
|---|---|
| e2e starts the run | The run, marked running, with the number of tests it will run |
| A test starts | That test, listed as running. Tests that have not started are not listed |
| A test finishes | Its attempts (each retry is one), steps with their e2e action and label, errors, console output, screenshots, video |
| e2e finishes | Trace pages, run-level errors, serial-group tests, the final status |

| Recorded per test | Detail |
|---|---|
| Error | Starts with the e2e error code, such as `ASSERTION_FAILED` |
| Failure details | The failing line, the page address at failure (no password, query string or fragment), the screen size, up to 5 elements closest to what a failed locator asked for, and `AI judgment:` when a model checked the step |
| App log | Console, uncaught errors and network warnings, each with its step. The newest 200 lines per attempt |
| Artifacts | PNG, JPEG, WebM, MP4, ZIP, JSON, TXT and Markdown, up to 50 MB per file |
| Trace page | The `trace.md` e2e keeps for a test, as a `walkthrough` attachment on the last attempt. Needs e2e 0.19.0+ |
| Screen at failure | `screen-at-failure.txt`, as a `log` attachment |
| Visual comparison | A failed `toHaveScreenshot` (e2e 0.19.0+) opens with its expected, actual and diff images |

Each e2e target shows as its own project inside the run, so the same test on `desktop-chromium` and on `ios` is two rows.

**Not uploaded**: a file over 50 MB, a file that is missing or of another type, a recording a hosted device service keeps as a link, and anything still uploading 40 seconds after the run finishes. During the run each upload gets 60 seconds. Test console output (stdout and stderr) is capped at 2 MB per run. The cut-off exists so the run always completes. Per-step model, tokens, cost and replay cache decisions are not sent either; they stay in `report.json`.

### Pattern 4: Choose Which Tests Keep a Trace Page

**Use when**: A failure in CI arrives without a `walkthrough`, or a passing test's steps are needed.

The trace page is the most useful single file for a failure, and e2e decides which tests get one, not the reporter. The default `retain-on-failure` covers failed, timed-out, interrupted and flaky tests. For one run that pages every test:

```bash
npx e2e run --trace on
```

Trace pages are written when the run ends, so they upload inside the 40-second window. A run with hundreds of pages and large videos is the case that loses files: keep `--trace on` and `--video on` for runs where you need them. The modes and where to set them per test are in the e2e skill, topics `running` and `writing-tests`.

### Pattern 5: Tags, and Keeping Media Local

**Use when**: Runs need to be told apart (nightly, smoke, a bug bash), or the app shows data that must not leave CI.

```ts
reporters: ['list', testdino({ tags: ['nightly'] })],   // or TESTDINO_TAGS=nightly,smoke
```

```ts
reporters: ['list', testdino({ artifacts: false })],    // results still upload; screenshots, videos, trace pages stay local
```

| Option | Environment variable | Does |
|---|---|---|
| `token` | `TESTDINO_TOKEN` | Project API key. Without it nothing uploads |
| `ciRunId` | `TESTDINO_CI_RUN_ID` | Merges the shards of one pipeline into one run: [sharding.md](sharding.md) |
| `split`, `splitId` | `TESTDINO_SPLIT`, `TESTDINO_SPLIT_ID` | Merges jobs that run different files: [sharding.md](sharding.md) |
| `tags` | `TESTDINO_TAGS` (comma-separated) | Run-level tags |
| `artifacts` | none | `false` keeps screenshots, videos and trace pages on the machine |
| `debug` | `TESTDINO_DEBUG` | `true` or `1` prints what the reporter does to stderr |
| `serverUrl` | `TESTDINO_SERVER_URL` | Another TestDino address. `testdino-e2e run` and `rerun` read only the variable, so set it for them too |
| none | `TESTDINO_SHARD` | `i/n`; overrides the shard read from `--shard` |
| none | `NO_UPDATE_NOTIFIER` | Any value turns off the daily update check against the npm registry |

An option set in the config wins over its environment variable, with two edge cases: `tags: []` still falls back to `TESTDINO_TAGS`, and `token: ''` in the config blocks the variable.

Before turning uploads on for an app with real data, read what e2e masks: screenshots mask secure fields only (e2e skill, topic `writing-tests`), and videos are not masked (topics `mcp` and `bug-bash`).

### Pattern 6: Confirm the Run Landed

**Use when**: After the first CI run with the reporter, or when a user says a run is missing.

The e2e summary ends with a `TestDino` row. On success it holds the link to the run (`uploaded N tests` when no link came back), sometimes followed by a note in parentheses about shards or a split. Any other text is the reason, listed under Troubleshooting below.

Over the TestDino MCP server:

```text
health                                   → projectId
list_testruns  by_commit: "<sha prefix>" → the run, its counts, branch, CI pipeline link
```

## Decision Guide

Each reporter answers a different question. They combine; none replaces another.

| The reader needs | Reporter | Reaches |
|---|---|---|
| What failed, right now, in this terminal | `list` | This machine |
| A test tab in the CI system | `junit` | The CI job |
| A summary to paste into a pull request or handoff | `markdown` | Wherever it is pasted |
| One comment on the pull request, edited on rerun | `github()` from `@e2e-dev/github` | The pull request |
| One page for one run, opened from disk | `htmlReporter()` from `@e2e-dev/html-reporter`. New in November 2026: confirm `npx e2e guide running` lists it for the installed e2e | Whoever has the file or the CI artifact |
| Every run kept, shards merged, a link per failure, history, an agent on another machine | `testdino()` from `@testdino/e2e` | Anyone with project access, and the MCP tools |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| Replace `list` with `testdino()` | No terminal output; the e2e skill's fix workflow starts from the terminal's failure block | Keep both |
| Put the token in `e2e.config.ts` | It is a secret in a committed file | `TESTDINO_TOKEN` from CI secrets |
| Drop the `report.json` artifact upload because results are in TestDino | `--last-failed` and the cost data need the file | Keep both uploads |
| Record video for every test on every run | Device recordings are large; files over 50 MB and late uploads are dropped | `--video=retain-on-failure`, or `on-first-retry` |
| Upload media from an app showing production data | Videos are not masked | Test accounts, or `artifacts: false` |
| Stay on reporter 1.0.x | The run appears only after it finishes, with no trace pages, failure details or re-runs | `npm install --save-dev @testdino/e2e@latest` |

## Troubleshooting

The `TestDino` row of the e2e summary says what happened:

| Message | Fix |
|---|---|
| `skipped (TESTDINO_TOKEN is not set)` | Set the variable where `npx e2e run` runs, or pass `token`. A pull request from a fork prints this too, because CI withholds secrets there |
| `not recorded (the project is over its execution limit)` | The tests ran but the run was not saved. The plan's execution limit is reached |
| `not uploaded (no event channel the server offered could be reached)` | Allow outbound connections from the CI machine to TestDino |
| `upload failed: …` | The text after the colon names the cause. Run again; if it repeats, send that text to TestDino support |
| `Test Controls: rules not loaded (…); failures count as usual` | Only under `testdino-e2e run`: the quarantine and critical rules could not be fetched, so this build's result is e2e's own: [flaky-or-broken.md](flaky-or-broken.md) |
| `@testdino/e2e <version> is available (installed <version>): …` | An update notice, not an error. The check runs at most once a day; `NO_UPDATE_NOTIFIER=1` turns it off |
| `stopped; the test run was ended as interrupted` | The run was stopped (Ctrl-C or a cancelled job) and is saved as interrupted. Trace pages are not uploaded after a forced stop |
| `<link> (shards uploaded as separate runs: set TESTDINO_CI_RUN_ID to merge them)` | Uploaded, but each shard is its own run: [sharding.md](sharding.md) |
| `<link> (split ignored: a split position and TESTDINO_SPLIT_ID are needed together)` | Uploaded without the split. Set both on every job |

### `tsc` reports TS5097 inside `node_modules/@testdino/e2e`

The package ships TypeScript source. e2e compiles it when it loads the config, so test runs are unaffected; only a project-wide `tsc` check that reaches `e2e.config.ts` complains. Set `allowImportingTsExtensions: true` in that `tsconfig.json` (it needs `noEmit: true`, which a test project normally has), or keep `e2e.config.ts` out of the checked files.

### A failed test has no trace page

In order of likelihood: e2e is older than 0.19.0, the reporter is older than 1.1.0, the test or run sets `trace: 'off'`, `artifacts: false` is set, or the page was still uploading 40 seconds after the run ended.

### A device recording is "not uploaded"

It is over 50 MB, or a hosted device service kept it as a link. See [mobile-results.md](mobile-results.md).

### The run shows fewer tests than the suite has

A filtered run (file arguments, `--grep`, tags, a shard, a re-run) counts only the tests it selected. That is correct, not a partial upload.

## Related

- [debugging-a-ci-failure.md](debugging-a-ci-failure.md): using what was uploaded
- [sharding.md](sharding.md): several jobs, one run
- [../ci/reporting-and-artifacts.md](../ci/reporting-and-artifacts.md): the same topic for Playwright
- [`@testdino/e2e` documentation](https://docs.testdino.com/cli/testdino-e2e)
