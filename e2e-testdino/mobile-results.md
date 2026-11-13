# Device Run Results: Recordings and Screens From CI

> **When to use**: e2e tests ran on an iOS simulator, an Android emulator, a connected phone or a hosted device in CI, and you need the recording, the screen at failure, or the results of one device apart from the others.
> **Prerequisites**: the e2e skill, topic `setup` ("Mobile targets") and topic `running` (`--video`, `--trace`). [results-and-artifacts.md](results-and-artifacts.md) for the reporter. To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

A browser failure can often be reproduced on a laptop in a minute. A device failure often cannot: the simulator image, the build and the device cloud session are all in CI. That makes the evidence from the CI run the only evidence there is, and it is worth making sure it arrives.

## Quick Reference

```bash
npx e2e run --video=retain-on-failure      # MP4 on devices, WebM on browsers; only failed attempts keep theirs
```

```text
list_testcase       by_testrun_id, search: "<target name>", by_status: "failed"  → narrowed; keep rows whose platform matches
get_debug_evidence  testcase_id, testrun_id, format: "md"                        → error, trace page, screen at failure
get_testcase_details testcase_id, testrun_id                                     → evidence[]: the recording and screenshots
```

| Limit | Value |
|---|---|
| Largest file uploaded | 50 MB |
| Upload window after the run ends | 40 seconds |
| Recording a hosted device service keeps as a link | Listed as not uploaded; open it at the provider |

## Patterns

### Pattern 1: Name the Targets, Because They Become the Columns

**Use when**: A config has more than one device, or both a browser and a device.

Each e2e target shows as its own project inside a run, and every test row carries the target as `platform`. A target's name defaults to its platform (`ios`, `android`), and two targets on one platform must be named. Name them for the device even when e2e does not force it: `iphone` and `pixel` read better in a list of failures than a platform, and stay stable when a second device is added.

```ts
targets: [
  { name: 'iphone', engine: mobile({ platform: 'ios' }), app: { bundleId: 'com.example.app' } },
  { name: 'pixel', engine: mobile({ platform: 'android' }), app: { bundleId: 'com.example.app' } },
],
```

The same test on two targets is two rows with two ids. That is what lets a verdict, a quarantine or a fix check apply to Android alone when only Android fails. How to declare devices, pools and hosted providers is in the e2e skill, topic `setup`.

### Pattern 2: Get the Recording Under the Limits

**Use when**: A device run finishes and a recording shows as "not uploaded".

Device recordings are MP4 and much larger than browser WebM recordings. Two limits follow from that.

| Limit | What gets dropped | How to stay under it |
|---|---|---|
| 50 MB per file | The recording of a long test | One behavior per test, as the e2e skill requires anyway. Long device tests are the ones that reach it |
| 40 seconds after the run | Recordings of the last tests to finish, still uploading | Record less: `--video=retain-on-failure` or `on-first-retry` instead of `on` |

A test's artifacts upload when that test finishes, so most recordings are safe long before the run ends. The ones at risk belong to the last tests, and to runs where every test records.

Set the mode for the run on the command line, or per test where one flow needs it. A test's own `video` on a target whose engine cannot record fails with `UNSUPPORTED_ARTIFACT`; `--video` on the command line skips such targets with a notice instead.

```ts
test('pays with Apple Pay', { video: 'on' }, async ({ app, agent }) => { /* ... */ });
```

### Pattern 3: Hosted Devices Keep Their Own Video

**Use when**: The target leases devices from a cloud provider.

A hosted device service usually records the whole session itself and returns a link. e2e records that link in the report as the video's `url` instead of a file path. The reporter cannot upload a link, so the test shows the recording as not uploaded.

Nothing is lost: the link is in the run's `report.json` (keep it as a CI artifact) and in the provider's dashboard. The trace page, the screen at failure and screenshots still upload as usual, and they are what an agent reads.

### Pattern 4: For an Agent, the Text Is the Evidence

**Use when**: An agent is asked to debug a device failure from CI.

A recording helps a person. An agent debugs from text, and a device failure has the same text a browser failure has:

```text
get_debug_evidence  projectId, testcase_id, testrun_id, format: "md"
```

- The **trace page** (the `walkthrough` artifact) has every step, what the app logged, the agent's last turns, and the screen at failure one node per line. On a device, where the screen was is the app and the screen title rather than a URL.
- The **screen at failure** (the `log` artifact) holds the names the rest of that screen's test lines need.
- The **failure screenshot** is in `evidence[]` from `get_testcase_details`.

From there, [debugging-a-ci-failure.md](debugging-a-ci-failure.md) applies unchanged. When a screen is missing from the evidence and the device is not available locally, say so and ask for a rerun with `--trace on --video on` rather than guessing at the UI.

### Pattern 5: Tell a Broken Device From a Broken Test

**Use when**: A device job is red and many tests failed at once.

Simulators that never boot, an app that failed to install and a device cloud that timed out all fail tests without saying anything about the app. Group the run's failures first:

```text
get_run_error_clusters  projectId, testrun_id
```

| What the cluster shows | Meaning | Next |
|---|---|---|
| Many tests, all `APP_UNREACHABLE` or `ENVIRONMENT_UNAVAILABLE` | The device, the build or the environment, not the tests. TestDino puts these in the `setup` error category | The e2e skill, topic `debugging` (the `APP_UNREACHABLE` row and "Is it the app?"). These exit 3, which is worth one job-level retry |
| Many tests, all `TEST_SETUP_FAILED` or `SEED_DATA_MISSING` | Test prerequisites, also in the `setup` category. These exit 2 | Fix the setup. Retrying the job cannot help |
| Failures on one target only | Something that target does differently: a permission dialog, a keyboard, a slower launch | Compare the trace page with the passing target's |
| The same assertion failing on every target | The app or the test | [debugging-a-ci-failure.md](debugging-a-ci-failure.md) |
| `AUTOMATION_UNSUPPORTED`, `UNSUPPORTED_CAPABILITY` on a device | The step needs something the device engine lacks | The e2e skill's error table says what to use instead |

Do not quarantine setup issues. A quarantine hides one test's failures; a device that does not boot fails all of them, and the run's exit code (2 or 3) is never changed by quarantine anyway.

### Pattern 6: One Device's Results

**Use when**: "How is Android doing?" or "show me only the iPhone failures".

```text
list_testcase  projectId, by_branch: "main", by_time_interval: "weekly", search: "pixel", by_status: "failed"
```

`search` matches every segment of a test's title path. The target name is one of them, but so are the file, the `describe` blocks and the title: `ios` also matches `tests/iosettings.e2e.ts`. Use it to narrow the list, then keep only the rows whose `platform` is the device. A branch or a time window resolves to the newest 20 runs at most, with a warning when it cuts; for a longer view, narrow the branch or query runs one at a time with `by_testrun_id`. Combine it with `by_status: "flaky"` to see whether flakiness is a property of the test or of one device.

## Decision Guide

| Situation | Do |
|---|---|
| Recording missing, test was long | Shorter tests; 50 MB is the limit per file |
| Recording missing, test was among the last | `--video=retain-on-failure`; the 40-second window |
| Recording missing, hosted device | It is a link at the provider (Pattern 3) |
| Target's engine cannot record video | With `--video`, e2e skips that target with a notice. Do not set `video` on the test or target there. Rely on the trace page and screenshots |
| Suite too slow on one device | One worker per device is e2e's rule. Add devices or shard: [sharding.md](sharding.md) |
| Flaky on one device only | Verdict and quarantine on that target's id: [flaky-or-broken.md](flaky-or-broken.md) |
| Screenshots or recordings may show real user data | Test accounts, or `artifacts: false`: [results-and-artifacts.md](results-and-artifacts.md) |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| `--video on` for every device test on every run | A large MP4 per test, against a 50 MB and 40-second limit | `retain-on-failure` |
| Leave device targets on their default names | They show as `ios` and `android`, which says nothing once a second device joins, and renaming later starts a new history for every test | A device `name` on each target from the start |
| Treat "not uploaded" as a failed upload and rerun the job | It is a size limit or a provider link | Patterns 2 and 3 |
| Quarantine every test after a simulator failed to boot | Hides nothing useful and the run still exits 3 | Fix the environment; retry the job once |
| Ask an agent to "watch the video" | It reads text | The trace page and the screen at failure |
| One long test that walks the whole app | Its recording is over the limit, and its failure says little | One behavior per test |

## Troubleshooting

### The recording is listed as not uploaded

Over 50 MB, kept as a link by a hosted device service, or still uploading when the 40-second window closed. The test's other artifacts tell you which: a present trace page with a missing recording points at size.

### Every test on one device shows the same error

Read one trace page before anything else. A failed iOS automation runner or an app that never launched shows there, and the e2e skill's error table has the recovery steps.

### Device failures have no trace page

The same causes as on the web: [results-and-artifacts.md](results-and-artifacts.md), "A failed test has no trace page".

## Related

- [results-and-artifacts.md](results-and-artifacts.md): what uploads, the limits, `artifacts: false`
- [debugging-a-ci-failure.md](debugging-a-ci-failure.md): the debugging flow, which is the same on a device
- [sharding.md](sharding.md): scaling device suites across jobs
- [../core/mobile-and-responsive.md](../core/mobile-and-responsive.md): mobile emulation in Playwright, which is a browser viewport and not a native app
