# Debugging an e2e Failure That Happened in CI

> **When to use**: An e2e test failed in CI, on a teammate's machine, or in a cloud session, and the file the e2e skill tells you to read first, `.e2e/results/<test>/trace.md`, is not on this disk.
> **Prerequisites**: the e2e skill: "Workflow: fixing a failed test" in its SKILL.md and topic `debugging`. [results-and-artifacts.md](results-and-artifacts.md) for how the evidence got uploaded. To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

The e2e skill's fix workflow is built on one rule: the run already saw every screen up to the failure, so fix from what it recorded and never walk the flow again. That rule still holds when the run was in CI. The only thing that changes is where the recording is.

## Quick Reference

```text
Is .e2e/results/<test>/trace.md on this disk, written by the run that failed?
├─ yes → the e2e skill, topic `debugging`. This guide adds nothing.
└─ no  → 1. find the failing test and its id        (Pattern 1)
         2. fetch the evidence                      (Pattern 2)
         3. read it the way `debugging` reads it    (Pattern 3)
         4. fix locally, rerun only that test       (Pattern 4)
         5. after the push, check the fix held      (Pattern 5)
```

```text
health                                                         → projectId
list_testcase       by_branch | by_commit, by_status: "failed" → pw_test_id, testrun_id, platform
get_debug_evidence  testcase_id, testrun_id, format: "md"      → error, verdict, when it changed, artifact links
```

## Patterns

### Pattern 1: Find the Failing Test and Its Id

**Use when**: Starting from "the e2e job is red on my branch".

`list_testcase` resolves the runs for a branch, commit or time window itself; there is no need to list runs first. A branch or a time window resolves to the newest 20 runs at most, with a warning when it cuts; for a longer view, narrow the branch or query runs one at a time with `by_testrun_id`.

```text
list_testcase  projectId, by_branch: "<branch>", by_status: "failed", by_time_interval: "1d"
```

Each row carries what the next calls need:

| Field | For an e2e test |
|---|---|
| `pw_test_id` | TestDino's id for this test on this target. The field keeps its Playwright name. Pass it as `testcase_id` |
| `testrun_id` | The run it failed in. Keep it: it is the baseline for Pattern 5 |
| `platform` | The e2e target, such as `desktop-chromium` or `ios`. Pass it to `--target` when reproducing |
| `title_path` | `["", <target>, <file>, <describe…>, <title>]` |
| `attempt_count` | More than 1 means retries ran, and a flake verdict is possible |
| `quarantined` | The failure is already known and, under `testdino-e2e run`, did not fail the build |

The same test on two targets is two rows with two ids. Identifying a test by its title then returns `AMBIGUOUS_IDENTITY` with the candidates; use the id of the target that failed.

For many failures in one run, group them before reading any single one: `get_run_error_clusters` with the `testrun_id` returns the distinct error signatures and the tests under each. Twelve tests failing on one `APP_UNREACHABLE` is one problem.

### Pattern 2: Fetch the Evidence in One Call

**Use when**: You have the id.

```text
get_debug_evidence  projectId, testcase_id, testrun_id, format: "md"
```

It returns the error, a verdict on whether the failure repeats, the boundary between the last passing run and the first failing one, and download links for the stored artifacts. Screenshots and videos are listed by `get_testcase_details` in `evidence[]`.

The links expire within minutes. Download the files as soon as you have the links, into a scratch folder outside `.e2e/` (that folder is the runner's output, read-only for you):

```bash
d=/tmp/e2e-ci/<testrun_id>/<pw_test_id>   # one folder per run and test; stay in the repository
mkdir -p "$d"
curl -fsS -o "$d/trace.md" "<walkthrough link>"     # -f: an expired link fails instead of saving an error page
curl -fsS -o "$d/screen-at-failure.txt" "<log link>"
```

An expired link is not a missing artifact: `curl -f` exits 22, and the fix is to call the tool again for fresh links.

### Pattern 3: Read It the Way the e2e Skill Reads a Failure

**Use when**: The evidence is downloaded.

Everything the e2e skill's `debugging` topic reads locally has a counterpart:

| Locally, per the e2e skill | From CI |
|---|---|
| The terminal's failure block: code, message, `expected` and `observed` | `## Error` in the evidence. It starts with the e2e error code |
| `❯ at`, where the screen was | `Page at failure:` in the failure details (address without query string, and the screen size) |
| `❯ on screen`, the nodes nearest a failed locator | `Closest matches on screen:`, up to 5 |
| `.e2e/results/<test>/trace.md` | The `walkthrough` artifact: the same file |
| `screen-at-failure.txt` | The `log` artifact |
| The failure screenshot, the `--video` recording | `evidence[]` from `get_testcase_details` |
| `❯ app 2 errors` and the page's `## App log` | The test's console output, newest 200 lines per attempt, each with its step |
| "whether every attempt failed alike" | `## Verdict: <value>`, one of `deterministic`, `flaky`, or `inconclusive` |
| Nothing: one disk holds one run | `## When it changed`: the last run this test passed in and the first it failed in |

Now apply topic `debugging`, "Read the failure" to the downloaded trace page, and look the error code up in its "Error codes" table for the fix. Do not paraphrase that table from memory: it changes with e2e releases, and `npx e2e guide debugging` prints the one that matches the installed version.

Two things in a CI trace page deserve a second look because they rarely show up locally:

- **The cache's decision on an agent step.** Each agent step has a `cache:` line. `cache: replayed 1 of 3 recorded actions, then the agent took over: …` on a step that replays fine on your machine means the recording CI has is stale. `cache: no replay: nothing recorded for this step yet` (reason `no-entry` in `report.json`) usually means `.e2e/cache/` is not committed. Search the page for `then the agent took over` and `no replay:`. Either is a cost problem as well as a clue: [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md).
- **The first attempt of a retried test.** In CI e2e retries once by default, and outside strict mode the retry runs every agent step live. The walkthrough is from the last attempt; `get_flake_verdict` lists each attempt's signature.

### Pattern 4: Let the Boundary Narrow the Question, Then Fix Locally

**Use when**: The evidence shows what failed and you need why.

`## When it changed` turns "why does this fail" into "what changed between these two runs":

```bash
git log --oneline <last passing commit>..<first failing commit>
git diff <last passing commit>..<first failing commit> -- src/ tests/
```

A state of `never_passed` means no passing run is left in history, so there is no range to read; say so instead of guessing one.

Then reproduce only that test, on the target that failed, the way CI ran it:

```bash
CI=1 npx e2e run tests/<feature>.e2e.ts:<line> --target <platform> --retries 0
```

From here it is the e2e skill again: "Rerunning a test while you fix it" for the flags, and the same rule against sleeps and fixed delays. Fix every line the evidence covers, not only the one that failed.

### Pattern 5: After the Push, Check the Fix Held

**Use when**: A fix is pushed and a new CI run has finished.

```text
verify_fix  projectId, testcase_id, baseline_run_id: "<the testrun_id from Pattern 1>"
```

| Result | Meaning | Next |
|---|---|---|
| `fixed` | Passing with no retries since the baseline | Done |
| `not_fixed` | Still failing with the same error | The fix missed. This is not flakiness |
| `changed_failure` | Still failing, with a different error | A new investigation; start at Pattern 2 with the new run |
| `still_failing` | Still failing, and the errors cannot be compared | Read the new run's evidence before calling it the same failure |
| `unstable` | Passing only after retries | Not fixed: [flaky-or-broken.md](flaky-or-broken.md) |
| `no_runs_since_baseline` | Nothing has run since | Wait for CI |
| `baseline_not_found` | The baseline is not a run this test ran in | Take the `testrun_id` from the row of the target that failed |

### Pattern 6: Without the MCP Server

**Use when**: No TestDino MCP server is connected, or the reporter is not installed.

- The CI log's `TestDino` row links the run. A person can open the failing test there and download the walkthrough.
- No reporter at all: the workflow in the e2e skill uploads `.e2e/results` as a CI artifact that expires after 7 days. Download it into a scratch folder. The artifact holds the contents of `results/`, so each test's folder is at its top level:

  ```bash
  gh run download <run id> -n e2e-artifacts -D /tmp/e2e-ci/<run id>
  # sharded (e2e-artifacts-<shard>, as in sharding.md): gh run download <run id> -p 'e2e-artifacts-*' -D /tmp/e2e-ci/<run id>
  ls /tmp/e2e-ci/<run id>        # one folder per test; read <test>/trace.md
  ```

  Then suggest [results-and-artifacts.md](results-and-artifacts.md), so the next failure has a link instead of a zip.

## Decision Guide

| Situation | Do |
|---|---|
| The failing run is on this machine | The e2e skill, topic `debugging` |
| Failed in CI, reporter installed, MCP connected | Patterns 1 to 5 |
| Failed in CI, reporter installed, no MCP | Open the run from the `TestDino` row of the CI log |
| Failed in CI, no reporter | Download the CI artifact (Pattern 6) |
| Many tests failed in one run | `get_run_error_clusters` first, then one test per cluster |
| The evidence leaves a screen out | Look live over `e2e mcp`, as the e2e skill's topic `mcp` describes: go straight to that screen, do not replay the flow |
| The error is `APP_UNREACHABLE` or `ENVIRONMENT_UNAVAILABLE` | The environment, not the test. These exit 3, so one job-level retry can help (e2e skill, topic `running`, exit codes). TestDino puts them in the `setup` error category |
| The error is `MODEL_UNAVAILABLE` | Configuration: the model key, the gateway or the model name. It exits 2, so retrying never helps. Also in the `setup` category |
| You have a Playwright `trace.zip` (a Playwright suite, or e2e 0.18 and older) | [../core/trace-analysis.md](../core/trace-analysis.md). It does not apply to e2e 0.19.0+, which writes a Markdown trace page instead |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| Walk the flow again over `e2e mcp` to see the failing screen | The run recorded it; a replay costs model calls and may not fail the same way | Download the walkthrough and the screen at failure |
| Re-run the whole CI job "to see if it passes" | Pays for every agent step again and answers nothing a verdict does not | `get_debug_evidence` reads the attempts that already ran |
| Read only the error line | The trace page holds what the app logged, where the page went and what the cache did | Read the walkthrough before forming a hypothesis |
| Treat an expired link as "no trace was uploaded" | Links last minutes by design | Call the tool again |
| Run `npx playwright trace` on an e2e failure | It reads Playwright `trace.zip` files; e2e 0.19.0+ does not write one | Read the `walkthrough`. `get_trace_analysis` returns its link and a runbook for e2e, with no AI analysis |
| Paste a signed artifact link into an issue or pull request | Anyone with the link can read the file until it expires | Quote the relevant lines, redacted |
| Add a sleep because "CI is slower" | The e2e skill forbids it for a reason: too short on a slow run, wasted on a fast one | `agent.waitFor` or a matcher on the state you need |

## Troubleshooting

### `AMBIGUOUS_IDENTITY` (409)

The title matches the test on more than one target, or in more than one file. Use the `pw_test_id` of the row whose `platform` failed.

### The evidence has no `walkthrough`

The test's trace mode kept no page, the reporter is older than 1.1.0, e2e is older than 0.19.0, `artifacts: false` is set, or the upload missed the 40-second window. See [results-and-artifacts.md](results-and-artifacts.md), Pattern 4. The error, the failure details and the console output are still there.

### The verdict is `inconclusive`

Only one attempt ran, so nothing says whether the failure repeats. e2e retries once when `CI` is set; a job passing `--retries 0` gives single attempts. Most failures can still be diagnosed from one attempt.

### The local run passes

Compare what differs: `CI=1` changes the defaults (one worker, one retry, a read-only cache), the target may differ, and CI may replay a recording your machine does not have. `--no-cache` for one run rules a stale replay in or out.

## Related

- [flaky-or-broken.md](flaky-or-broken.md): when the verdict is `flaky`, and quarantine
- [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md): when the trace page shows a replay that handed off
- [../qa/bug-reports.md](../qa/bug-reports.md): writing the report when the app is at fault
- [../core/trace-analysis.md](../core/trace-analysis.md): the Playwright `trace.zip` counterpart of this guide
