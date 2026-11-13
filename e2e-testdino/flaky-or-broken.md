# Flaky or Broken? Deciding From Run History

> **When to use**: An e2e test failed and the question is one of these: is it flaky or really broken, has it been failing for days, may it stop blocking merges while someone fixes it, and, after a fix, did the fix hold.
> **Prerequisites**: the e2e skill, topic `debugging` ("Flaky tests", "Is it the app?"). [debugging-a-ci-failure.md](debugging-a-ci-failure.md) for finding the test's id. To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

In a Playwright suite, a flaky test wastes time. In an e2e suite it also wastes money: outside strict mode a retry never replays from the cache, so every agent step of a retried test goes to the model again. The only measurement one machine can make is to run the test again and again, and the e2e skill's recipe for that is ten runs with the cache off: ten times the model calls. Run history usually has the answer already, for free.

## Quick Reference

```text
get_flake_verdict   testcase_id [, testrun_id]              → deterministic | flaky | inconclusive
list_test_controls  view: "candidates"                      → flaky tests that failed a build in the last 30 days
quarantine_tests    testcase_ids, reason [, ends_in_days, only_this_error, dry_run]
verify_fix          testcase_id, baseline_run_id            → fixed | not_fixed | changed_failure | still_failing | unstable | no_runs_since_baseline | baseline_not_found
get_rerun_selection runId [, scope]                         → the exact command that re-runs only what failed
```

```bash
# In CI, so quarantine and critical tests decide the exit code
npx -p @testdino/e2e testdino-e2e run -- --reporter list,junit

# Run again only the tests that failed in a TestDino run
npx -p @testdino/e2e testdino-e2e rerun --from-run <testRunId>
```

## Patterns

### Pattern 1: Ask for the Verdict Before Rerunning Anything

**Use when**: A test failed in CI and someone says "probably flaky".

```text
get_flake_verdict  projectId, testcase_id, testrun_id
```

The verdict compares the attempts of one run. It says whether the failure repeats, never why.

| Verdict | What the attempts showed | What it rules out | Next |
|---|---|---|---|
| `deterministic` | Every attempt failed with the same signature | "It's flaky, retry it." The e2e skill calls this a product bug or a changed screen | Fix the app, or the locator and the expectation together: [debugging-a-ci-failure.md](debugging-a-ci-failure.md) |
| `flaky` | An attempt failed and a later one passed | "The assertion is wrong." It passed once on the same code | The causes are listed in the e2e skill, topic `debugging`, "Flaky tests". Read the failing attempt's signature first |
| `inconclusive` | One attempt only, or attempts that failed differently | Nothing yet | Let it run with retries in CI, or measure locally (Pattern 3) |

A verdict needs retries. e2e retries once when `CI` is set, so CI runs usually have two attempts for a failure. A job that passes `--retries 0` produces `inconclusive` every time.

`get_debug_evidence` returns the same verdict together with the error, the artifacts and the run where the test last passed. When debugging, call that one instead and skip this call.

### Pattern 2: Look Across Runs, Not at One

**Use when**: The question is "since when" or "how often".

| Question | Call |
|---|---|
| Is this failure new, or has it been failing for days? | `get_debug_evidence`: `## When it changed` names the last passing and first failing run, or says the test never passed in the history kept |
| How has this test done lately? | `get_testcase_details` with `include_history: true` |
| Which tests are the flakiest in the project? | `get_project_details`: the top flaky, most-failing and chronically broken tests |
| Which flaky tests actually failed a build recently? | `list_test_controls` with `view: "candidates"` |

The last list is the one worth acting on. A test that always passes on retry never fails the build, so quarantining it changes nothing; it still costs a live retry per run, which is a reason to fix it rather than hide it.

### Pattern 3: When Local Repeats Are Still the Right Tool

**Use when**: You have changed the test or the app and want to know, before pushing, that the fix holds.

This is the e2e skill's own recipe, and it is the right one for measuring a fix. It is the wrong one for deciding whether a test is flaky, because history already knows.

```bash
npx e2e run tests/<feature>.e2e.ts:<line> --repeat-each 10 --retries 0 --no-cache
```

`--no-cache` matters for agent steps: without it, runs 2 to 10 replay the first run's recording and prove nothing about the model's path. That makes this ten live runs of every goal in the test. Do it once, on one test, after the fix.

### Pattern 4: Quarantine, So a Known Failure Stops Blocking Merges

**Use when**: The failure is understood, someone owns the fix, and the team should keep merging meanwhile. Only when the user asks for it.

A quarantined test still runs and still reports. Its failures stop failing the build until the quarantine's end date.

**The build result changes only under the wrapper.** A reporter cannot change e2e's exit code, so CI has to run e2e through `testdino-e2e run`, with e2e's own options after `--`:

```yaml
      - run: npx -p @testdino/e2e testdino-e2e run -- --reporter list,junit
        env:
          TESTDINO_TOKEN: ${{ secrets.TESTDINO_TOKEN }}
```

| Run result | Exit code under `testdino-e2e run` |
|---|---|
| The only failures are quarantined, or match a known error, and the run had no run-level error or failed serial-group hook | 0 |
| A test marked critical passed only on retry | 1 |
| Any other failure | 1, as e2e reports it |
| e2e exited 2, 3, 4 or 130 (config, environment, internal, interrupted) | Unchanged. Quarantine never hides a run that could not run |

Then quarantine through the MCP server. Preview first:

```text
quarantine_tests  projectId,
                  testcase_ids: ["<pw_test_id>"],
                  reason: "Remaining count races the save request; fix tracked in SHOP-812",
                  ends_in_days: 7,
                  dry_run: true
```

- **`reason` is required**, and it is what the next person reads. Name the cause and the ticket.
- **Give it an end date.** A quarantine cannot be deleted, only released, and one without an end in mind is how a suite fills with tests nobody trusts.
- **`only_this_error`** (one test at a time) covers only failures with that error line, such as `ASSERTION_FAILED: expect.toHaveText failed`. Any other failure of the same test still fails the build. Use the error of the final attempt.
- **One id per target.** The same test on `desktop-chromium` and `mobile-webkit` is two ids. Quarantine the target that fails, not both by reflex.
- A quarantined test cannot also be marked critical. The two are opposite decisions about the same test.

### Pattern 5: Quarantine, `test.fail`, or a Tag?

**Use when**: Choosing how to keep a known failure from blocking.

| Situation | Use | Why |
|---|---|---|
| A known app bug with a ticket, failing every run | `test.fail` in the test (e2e skill, topic `writing-tests`; not allowed inside a serial group) | The test still runs, and a pass fails it with `UNEXPECTED_PASS`, so the suite tells you when the bug is fixed. Lives in code review |
| Flaky, cause not yet found, blocking merges today | Quarantine with an end date | No code change, takes effect on the next run, releases itself |
| Fails only with one specific error you understand | Quarantine with `only_this_error` | A new kind of failure still blocks |
| Bug bash repro tests that fail until the bug is fixed | `--exclude-tag bugbash` on the gating run (e2e skill, topic `bug-bash`) | They were never part of the gate |
| The test cannot run in this environment | `test.skip` with a reason | Not a failure at all |

### Pattern 6: After the Fix, Verify Against the Run You Saw Fail

**Use when**: A fix is merged and at least one new run has finished.

```text
verify_fix  projectId, testcase_id, baseline_run_id: "<the run you diagnosed>"
```

| Result | Read it as |
|---|---|
| `fixed` | Passing with no retries since the baseline. Release the quarantine if there is one (`release_quarantine`, when the user asks) |
| `unstable` | Passing only after retries. Not fixed: each of those retries ran the agent steps live |
| `not_fixed` | The same error. The fix missed; this is not flakiness |
| `changed_failure` | A different error. A new investigation |
| `still_failing` | Still failing, and the errors cannot be compared |
| `no_runs_since_baseline` | Nothing ran yet. Wait for CI |
| `baseline_not_found` | The baseline is not a run this test ran in: Troubleshooting below |

### Pattern 7: Re-Run Only What Failed

**Use when**: A run failed and you want the failures again, on any machine or in CI, without the previous `report.json` on disk.

`--last-failed` is e2e's tool for this and needs the last run's report in the same output folder (a later CI job can download it there first). From a TestDino run it works anywhere:

```bash
npx -p @testdino/e2e testdino-e2e rerun --from-run <testRunId>                  # the failed tests
npx -p @testdino/e2e testdino-e2e rerun --from-run <testRunId> --scope flaky    # or: failed-and-flaky
npx -p @testdino/e2e testdino-e2e rerun --from-run <testRunId> -- --workers 2   # e2e options after --
```

- Run it from the folder with `e2e.config.ts`, with `TESTDINO_TOKEN` set. Needs e2e 0.19.0+.
- The selection is checked against the checkout first. Tests no longer in it are skipped and named.
- Each test runs on the target it failed on. A setup test cannot run alone, so the tests that use it run too.
- Results go to `.e2e/testdino-picked`, so the last local report stays untouched.
- `--grep`, `--grep-invert`, `--last-failed`, `--changed-since` and `--shard` are refused: the selection already decides what runs.
- When nothing in scope failed, it says so and exits 0.
- `--test-ids a,b` runs those ids instead of the scope, `--exclude-ids a,b` leaves ids out, and `--rerun-tags a,b` (or `TESTDINO_RERUN_TAGS`) tags the new run. The new run shows in TestDino as a re-run of the original, and quarantine and critical rules decide its exit code as under `testdino-e2e run`.
- It does not read `e2e.config.ts`: when the reporter sets `serverUrl`, set `TESTDINO_SERVER_URL` for the re-run.
- A selection picked in TestDino runs with `testdino-e2e run --selection <id>`; options after `--` may then change only how tests run, never which.

An agent gets the same command from `get_rerun_selection` (read-only). Starting the re-run in CI is `rerun_test`, which costs CI minutes and model calls, so it needs the user's explicit yes and a choice of `mode`: `same-commit` answers "is it the test?", `latest` answers "did the fix land?".

## Decision Guide

| The question | Answer from |
|---|---|
| Flaky or broken? | `get_flake_verdict`, or `## Verdict` in `get_debug_evidence` |
| New, or failing for days? | `## When it changed` in `get_debug_evidence` |
| Can we merge with this failing? | Is it quarantined (`list_test_controls`)? If not, should it be (Pattern 5) |
| Did my fix work? | `verify_fix` with the baseline run |
| Does the fix hold before I push? | Local `--repeat-each` (Pattern 3) |
| Run just the failures again | `testdino-e2e rerun --from-run` |
| Why is it flaky? | The e2e skill, topic `debugging`; for causes common to any UI test, [../core/flaky-tests.md](../core/flaky-tests.md) |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| Run `--repeat-each 10 --no-cache` to learn whether a CI failure is flaky | Ten live runs of every agent step to learn what the recorded attempts already show | Pattern 1 |
| Raise `retries` until the suite is green | Each retry runs the agent steps live, and the flake is still there | Find the cause; quarantine meanwhile |
| Quarantine with no reason or "flaky" as the reason | Nobody can tell later whether it may be released | Cause and ticket in `reason` |
| Quarantine every id of a test when one target fails | Hides a regression on the targets that were fine | The failing target's id |
| Quarantine, then keep plain `npx e2e run` in CI | The build still fails; the quarantine does nothing | `testdino-e2e run` |
| Call a fix done because the next run was green | One green run of a flaky test proves little | `verify_fix`; `unstable` is not fixed |
| Quarantine or re-run in CI without asking | Both change what the team's pipeline does | Show the dry run or the selection, wait for a yes |

## Troubleshooting

### A quarantined test still fails the build

CI runs plain `npx e2e run`, the reporter is older than 1.1.0, the rules did not load (the `TestDino` rows say `Test Controls: rules not loaded (…)`), the failure is a different error than `only_this_error` covers, the quarantine is on another target's id, another failure in the run is not quarantined, or the run also had a run-level error or a failed serial-group hook. `list_test_controls` shows what is active; `list_testruns` shows, per run, whether quarantine was applied and how many failures it excluded.

### The build fails though every test passed

A test marked critical passed only on retry. That is what critical means. `list_test_controls` with `view: "critical"` lists them.

### `inconclusive` on every verdict

The job runs with `--retries 0`, or the test fails differently on each attempt. For the second case, read both attempts' signatures: two different errors are two problems.

### `baseline_not_found`

A `verify_fix` result, not an error. The run id is not one this test ran in: another project, another target's id, or a run filtered to other tests.

### `testdino-e2e rerun` exits 1 and runs nothing

TestDino could not say which tests failed (the run is still in progress, or was uploaded by a reporter older than 1.1.0), `e2e list` could not check the selection, or none of the selected tests exist on this checkout. The message names which.

## Related

- [debugging-a-ci-failure.md](debugging-a-ci-failure.md): finding the id and reading the evidence
- [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md): what retries and stale recordings cost
- [sharding.md](sharding.md): the wrapper in a shard matrix
- [../core/flaky-tests.md](../core/flaky-tests.md), [../core/dynamic-test-selection.md](../core/dynamic-test-selection.md): flakiness and quarantine in Playwright suites
- [TestDino Test Controls](https://docs.testdino.com/guides/test-controls)
