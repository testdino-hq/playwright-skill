# Agent Cost and Replay Cache Health Across Runs

> **When to use**: Agent steps cost more than expected, CI got slower or more expensive without an obvious reason, you need to know which recordings stopped replaying, what a pull request's run cost against main, or whether the suite is ready for `--strict-cache`.
> **Prerequisites**: the e2e skill, topic `agent` ("The replay cache", "Budgets and cost") and topic `running` ("Output"). To write, run or fix a test on this machine, read that skill (`npx e2e guide <topic>`); this guide starts where it stops.

An `agent.act` step that replays from the cache makes no model call. One that hands off or misses pays for the model, on every run, until someone records it again. e2e reports this per run: the terminal's `AI` and `Cache` rows, `--debug`, the trace page. What no single run can tell you is that a step replayed last week and has paid on every run since.

**Where this data lives today**: in each run's `report.json`. TestDino shows the tests, steps and failures of an e2e run, but not yet the model, tokens, cost or cache decision of a step. So this guide works on the report files, and the first pattern is about keeping them.

## Quick Reference

| Question | In `report.json` |
|---|---|
| What did the run cost? | `run.usage.estimatedCostUsd`. Absent when no provider reported a price |
| How many tokens? | `run.usage.modelTokens`. `modelCachedTokens` is the provider's prompt cache, not the replay cache |
| What did one step cost? | `step.model`: `calls`, `inputTokens`, `outputTokens`, `estimatedCostUsd`, `provider`, `model` |
| Did it replay? | `step.cache.mode`: `self-finalized` (replayed), `agent-concluded` (handed off), `missed` |
| Why not? | `step.cache.reason`, and `step.cache.detail` for where the replay stopped |
| What became of the recording? | `step.cache.write`: `saved`, `kept`, `unconfirmed`, `evicted`, `no-change`, `not-written`. Set only by a run whose cache is read-write, which is the local default. A CI run reads the cache without writing it, so its report has no `write` |
| Which model recorded it? | `step.cache.recordedBy` |

Steps are at `run.results[].attempts[].steps[]`. A serial group's steps are at `run.serialGroups[].attempts[].members[].steps[]`.

```bash
node scripts/e2e-cost.mjs .e2e/report.json                          # one run
node scripts/e2e-cost.mjs .e2e/report.json base-report/report.json  # against main
```

## Patterns

### Pattern 1: Keep Every Run's Report

**Use when**: Always, before any question in this guide can be answered.

`report.json` is overwritten by the next run on the same disk and deleted with the CI job. The workflow in the e2e skill already uploads it as a CI artifact named `e2e-report`; keep that step, and give the artifact a retention long enough to compare against (the default on GitHub Actions is 90 days).

To compare a pull request with main, fetch main's latest report into a folder beside the checkout:

```bash
base=$(gh run list --branch main --workflow e2e.yml --status success --limit 1 --json databaseId --jq '.[0].databaseId')
gh run download "$base" -n e2e-report -D base-report
# sharded (artifacts named e2e-report-<shard>, as in sharding.md): one folder per shard
gh run download "$base" -p 'e2e-report-*' -D base-report
```

In a workflow this needs `GH_TOKEN` in the step's env and `actions: read` in `permissions`. A sharded suite has one report per shard, under `base-report/e2e-report-<shard>/`. Pass every shard's report on each side, comma-separated (`head-1/report.json,head-2/report.json base-report/e2e-report-1/report.json,base-report/e2e-report-2/report.json`). Do not pair shard 1 with shard 1: adding one test moves others to another shard.

Compare runs that selected the same tests. A pull request run filtered with `--changed-since` or `--last-failed`, against a full run of main, compares two different suites, and its `Change` line reads as a saving.

### Pattern 2: A Script That Reads One Report, or Two

**Use when**: You want the cost per test and the list of steps that did not replay.

No dependencies; any Node that runs e2e runs it. Ask before adding the file to the user's repository.

```js
// scripts/e2e-cost.mjs: what the agent steps of an e2e run cost, and which ones did not replay.
// Usage: node scripts/e2e-cost.mjs <report.json>[,<shard report.json>...] [<base report.json>[,...]]
import { readFileSync } from 'node:fs';

const CACHE = { 'self-finalized': 'replayed', 'agent-concluded': 'handed off', missed: 'missed' };
const usd = (n) => `$${n.toFixed(4)}`;

function load(path) {
  const { run } = JSON.parse(readFileSync(path, 'utf8'));
  const key = (testId, x) => `${testId}|${x.targetId}|${x.agent ?? 'default'}|${x.repeat ?? 0}`; // agent and repeat are optional
  const byTestId = new Map(run.results.map((r) => [key(r.testId, r), r]));
  const name = (r) =>
    `${r.file} › ${r.titlePath.join(' › ')} [${r.targetId}${(r.agent ?? 'default') === 'default' ? '' : ` as ${r.agent}`}${r.repeat ? ` #${r.repeat}` : ''}]`;
  const steps = [];
  const add = (test, attempt, list) => {
    const seen = new Map();
    for (const s of list.filter((x) => x.api?.startsWith('agent.'))) {
      const id = `${s.api} ${s.label}`;
      const nth = (seen.get(id) ?? 0) + 1;
      seen.set(id, nth);
      steps.push({
        test, attempt,
        key: `${test} | ${id} | ${nth}`,
        where: `${s.source?.file ?? '?'}:${s.source?.line ?? '?'}`,
        what: `${s.api} ${JSON.stringify(s.label)}`,
        // agent.assert, agent.waitFor and agent.extract are never cached; an act with no record ran with the cache off (config, flag or a custom executor).
        cache: s.cache ? CACHE[s.cache.mode] : s.api === 'agent.act' ? 'cache off' : 'never cached',
        reason: s.cache?.reason, write: s.cache?.write, detail: s.cache?.detail,
        calls: s.model?.calls ?? 0,
        tokens: (s.model?.inputTokens ?? 0) + (s.model?.outputTokens ?? 0),
        cost: s.model?.estimatedCostUsd ?? 0,
      });
    }
  };
  for (const r of run.results) for (const a of r.attempts) add(name(r), a.index, a.steps);
  // A serial group's steps live on the group, one member per test.
  for (const g of run.serialGroups ?? [])
    for (const a of g.attempts)
      for (const m of a.members) {
        const r = byTestId.get(key(m.testId, g));
        add(r ? name(r) : `${g.file} › ${m.testId} [${g.targetId}]`, a.index, m.steps);
      }
  return { run, steps };
}

// A sharded run: every shard's report on one side, so tests that moved between shards still match.
function loadAll(paths) {
  const parts = paths.split(',').map(load);
  const status = parts.find((p) => p.run.status !== 'passed')?.run.status ?? 'passed';
  return { run: { ...parts[0].run, status }, steps: parts.flatMap((p) => p.steps) };
}

const sum = (list, field) => list.reduce((total, s) => total + s[field], 0);
const count = (list, cache) => list.filter((s) => s.cache === cache).length;
const totals = (steps) =>
  `${steps.length} agent steps · ${count(steps, 'replayed')} replayed · ${count(steps, 'handed off')} handed off · ` +
  `${count(steps, 'missed')} missed · ${count(steps, 'never cached')} never cached · ` +
  (count(steps, 'cache off') ? `${count(steps, 'cache off')} cache off · ` : '') +
  `${sum(steps, 'calls')} model calls · ${sum(steps, 'tokens')} tokens · ${usd(sum(steps, 'cost'))}`;

const [headPath, basePath] = process.argv.slice(2);
if (!headPath) {
  console.error('Usage: node scripts/e2e-cost.mjs <report.json>[,<shard report.json>...] [<base report.json>[,...]]');
  process.exit(2);
}
const head = loadAll(headPath);
const { run } = head;
console.log(`Run ${run.status} · e2e ${run.runner.version}${run.vcs?.commit ? ` · ${String(run.vcs.commit).slice(0, 7)}` : ''}`);
console.log(totals(head.steps));
const retries = head.steps.filter((s) => s.attempt > 0);
if (retries.length) console.log(`  on retries: ${retries.length} of those steps · ${usd(sum(retries, 'cost'))}`);

console.log('\nCost per test, highest first');
const perTest = new Map();
for (const s of head.steps) perTest.set(s.test, [...(perTest.get(s.test) ?? []), s]);
for (const [test, list] of [...perTest].sort((a, b) => sum(b[1], 'cost') - sum(a[1], 'cost') || sum(b[1], 'calls') - sum(a[1], 'calls')))
  console.log(`  ${usd(sum(list, 'cost'))}  ${String(sum(list, 'calls')).padStart(3)} calls  ${test}`);

const live = head.steps.filter((s) => ['handed off', 'missed', 'cache off'].includes(s.cache));
console.log(`\nagent.act steps that did not replay (${live.length})`);
for (const s of live)
  console.log(`  ${s.cache}${s.reason ? ` · ${s.reason}` : ''}${s.write ? ` · recording ${s.write}` : ''}  ${s.where}  ${s.what}${s.attempt ? `  (retry ${s.attempt})` : ''}${s.detail ? `\n      ${s.detail}` : ''}`);

if (basePath) {
  const base = loadAll(basePath);
  console.log(`\nBase: ${totals(base.steps)}`);
  const delta = sum(head.steps, 'cost') - sum(base.steps, 'cost');
  const calls = sum(head.steps, 'calls') - sum(base.steps, 'calls');
  console.log(`Change: ${delta >= 0 ? '+' : '-'}${usd(Math.abs(delta))} · ${calls >= 0 ? '+' : ''}${calls} model calls`);
  // First attempts only: a retry never replays outside strict mode, so it would always look like a regression.
  const first = (steps) => new Map(steps.filter((s) => s.attempt === 0).map((s) => [s.key, s]));
  const before = first(base.steps);
  const now = first(head.steps);
  const stale = [...now.values()].filter((s) => before.get(s.key)?.cache === 'replayed' && s.cache !== 'replayed');
  console.log(`\nReplayed in the base run, ran live here (${stale.length})`);
  for (const s of stale) console.log(`  ${s.cache}${s.reason ? ` · ${s.reason}` : ''}  ${s.where}  ${s.what}`);
  const added = [...now.values()].filter((s) => !before.has(s.key));
  console.log(`\nNot in the base run: new, renamed or reworded (${added.length})`);
  for (const s of added) console.log(`  ${s.cache}  ${s.where}  ${s.what}`);
}
```

Output for a pull request's CI run against main's, where one recording went stale, one goal was reworded and one test retried:

```text
Run passed · e2e 0.23.0 · 0123456
6 agent steps · 1 replayed · 1 handed off · 2 missed · 2 never cached · 18 model calls · 44448 tokens · $0.0230
  on retries: 1 of those steps · $0.0069

Cost per test, highest first
  $0.0145   11 calls  tests/checkout.e2e.ts › checkout › pays with a saved card [web]
  $0.0063    5 calls  tests/checkout.e2e.ts › checkout › applies a coupon [web]
  $0.0022    2 calls  tests/checkout.e2e.ts › orders › lists the new order [web]

agent.act steps that did not replay (3)
  handed off · target-not-found  tests/checkout.e2e.ts:9  agent.act "apply the coupon {code}"
      at action 2 of 3, tap button "Apply": no control named "Apply" appeared
  missed · no-entry  tests/checkout.e2e.ts:16  agent.act "pay with the saved card"
  missed · retry  tests/checkout.e2e.ts:16  agent.act "pay with the saved card"  (retry 1)

Base: 4 agent steps · 3 replayed · 0 handed off · 0 missed · 1 never cached · 1 model calls · 2160 tokens · $0.0011
Change: +$0.0219 · +17 model calls

Replayed in the base run, ran live here (1)
  handed off · target-not-found  tests/checkout.e2e.ts:9  agent.act "apply the coupon {code}"

Not in the base run: new, renamed or reworded (2)
  missed  tests/checkout.e2e.ts:16  agent.act "pay with the saved card"
  never cached  tests/checkout.e2e.ts:33  agent.extract "the order number"
```

A CI report cannot say what became of a recording, because CI does not write the cache. Run the same test on a developer machine, where the cache is read-write by default, and the line gains that detail:

```text
agent.act steps that did not replay (1)
  missed · no-entry · recording unconfirmed  tests/checkout.e2e.ts:16  agent.act "pay with the saved card"
```

### Pattern 3: Read the "Did Not Replay" List in This Order

**Use when**: The script lists steps that ran live.

Sort by who has to act, cheapest fix first. The full table of reasons is in e2e's docs (`node_modules/e2e/docs/cache.mdx`, "Why a step was not replayed"); the e2e skill's topic `agent` covers the rules behind them.

| What the line says | What is happening | Fix |
|---|---|---|
| `missed · retry` | A retry. Outside strict mode retries never replay | The cost of a flaky test: [flaky-or-broken.md](flaky-or-broken.md) |
| `handed off` with `target-not-found`, `end-mismatch` or `wrong-context`, the same step in run after run | A stale recording. The UI changed under it, and CI cannot re-record | Run the test locally, commit the changed entry |
| `handed off · gap` | An action that cannot be replayed, such as a value read off the screen | Put stable values in `params`, per topic `agent` |
| `target-ambiguous` | The number of matching controls changed | Distinct names for repeated controls, or unique test data |
| `viewport-changed` | A tap, hover or drag was recorded on a screen of another size | Keep the viewport fixed; compare the CI target's size with yours |
| `action-failed`, `action-uncertain` | The app rejected a replayed action | Check the app first: it may be the bug |
| `invalid-entry` | The recording file is unreadable, over 1 MiB, or from another schema version | `npx e2e cache clear`, then re-record |
| `truncated` | The recording hit a limit | Split the step, or pass the secret as a `Secret` |
| `missed · no-entry` on every CI run | CI has no recording for the step. Three possible causes, below | Run that one test locally and read the `recording …` detail |
| `cache off` | The run used `--no-cache`, the config turns the cache off, or a custom step executor did | Keep `--no-cache` for single diagnostic runs |

Under `--strict-cache`, `invalid-entry`, `wrong-context`, `target-not-found`, `target-ambiguous`, `viewport-changed`, `action-failed`, `action-uncertain` and `end-mismatch` fail the step with `REPLAY_STALE`; `gap` and `truncated` still run live (e2e's `cache.mdx`, "Fail on a stale recording").

`missed · no-entry` in CI looks the same for three different problems. A local run of the test tells them apart:

| The local line ends in | Cause | Fix |
|---|---|---|
| `recording saved`, and the next local run replays | The recording exists on your machine only. `e2e init` gitignores `.e2e/cache/` | Remove that gitignore line and commit the entries |
| `recording unconfirmed` | No check passes after the step, so e2e never saves it. It pays on every run, everywhere | End the test with a verifying check, as the e2e skill requires |
| `recording no-change` | The step changes nothing on screen or in the route, so there is nothing to record | By design. Ask whether the step needs to be an `act` at all |

One stale step in one run is noise: leftover data or a banner can cause an `end-mismatch` once. The same step in run after run is a recording to redo.

### Pattern 4: Explain a Pull Request's Cost Before Merging

**Use when**: The script shows a pull request costs more than main.

The last two sections of the comparison separate the causes:

- **Replayed in the base run, ran live here.** The pull request changed the UI under a recorded step. Expected when the change is intentional; the recording needs redoing and committing in the same pull request, or every CI run after the merge pays.
- **Not in the base run.** Either new agent steps, which is fine, or existing steps under a new key. A recording's key includes the test file, the title path, the target, the instruction and its params, the agent and its `context`, the engine, the project id and the app's identity (full list: e2e's `cache.mdx`). Renaming a test, its `describe` or its file, or rewording a goal, records every goal it touches again. If a refactor only moved or renamed tests, this list is the bill for it.

A step that appears in neither list but costs more is an `agent.assert`, `agent.waitFor` or `agent.extract`. They are never cached, so they cost on every run by design.

### Pattern 5: Cut What Is Never Cached

**Use when**: "never cached" steps dominate the per-test cost.

- Replace an `agent.assert` with a locator matcher where the outcome is an exact value on screen. A matcher is free and also confirms the `act` steps before it.
- A long `agent.waitFor` on a screen that keeps changing judges again on every change, up to the agent's `maxModelCalls`. Raise its `interval`.
- Give judgments a cheaper model: an agents entry takes `judge` beside `model`.

The rules are in the e2e skill, topic `agent`. This guide only tells you which steps to apply them to.

### Pattern 6: Decide When to Turn On `--strict-cache`

**Use when**: Recordings are committed and the team wants CI to stop paying silently.

Without strict mode, a recording that no longer replays quietly hands the step to the agent. With `--strict-cache` the same step fails with `REPLAY_STALE`, so a stale recording is caught in the pull request that caused it.

The suite is ready when, across the last several runs on main, the script's "did not replay" list holds nothing but steps a local run reports as `no-change`, and hand-offs with reason `gap` or `truncated`. Those run live under strict mode too. Then:

```bash
npx e2e run --strict-cache      # in CI; e2e's docs prefer the flag over cache.strict in the config
```

Until then strict mode turns every stale recording into a red build at once. Work the list down first. One more case fails under strict: `missed · no-entry` when the cache holds a recording of the same step under another key, after an e2e upgrade that changed the keys or a change to the project id, the app's identity or the agent's context. Re-record those before switching.

## Decision Guide

| Situation | Do |
|---|---|
| One run, on this machine, right now | The terminal's `AI` and `Cache` rows, or `--debug` for a per-step table. No script needed |
| One run, to share | e2e's `markdown` reporter (counts and spend). `htmlReporter()` from `@e2e-dev/html-reporter` is newer than 0.23.0: confirm `npx e2e guide running` lists it for the installed e2e |
| Which test costs the most | Pattern 2 |
| Cost went up between two runs | Pattern 2 with a base report, then Pattern 4 |
| The same step runs live in run after run | Pattern 3, then re-record and commit |
| A retried test is expensive | It is flaky first, expensive second: [flaky-or-broken.md](flaky-or-broken.md) |
| What the model saw and decided | `--ai-trace` and `npx unbox-ai`, per the e2e skill. Never read `ai-trace.json` directly |
| Choosing a cheaper model | Not with Pattern 2's cache sections: the agent is part of the cache key, so a run as another agent misses every recording and matches no step of the base. e2e's docs (`cache.mdx`) evaluate a model with `--no-cache`: run once per agent with `--no-cache --agent <name>` and compare the totals and the cost per test |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| `--no-cache` in the CI command | Every goal goes to the model on every run | One `--no-cache` run when a test first passes, as the e2e skill says |
| Leave `.e2e/cache/` gitignored and wonder why CI is slow | CI reads the cache and never writes it, so it has nothing to replay | Commit the entries |
| Rename tests and files in a refactor without re-recording | Every goal under a renamed test records again, and CI cannot record | Re-record locally and commit in the same pull request |
| Read `modelCachedTokens` as the replay rate | It is the provider's prompt cache: cheaper calls, not skipped calls | `step.cache.mode` |
| Compare totals of a run with retries against one without | Retries run live and inflate the total | The script compares first attempts and reports retries separately |
| Quote a dollar figure as exact | `estimatedCostUsd` is an estimate, and absent for providers that report no price | Compare runs against each other; use model calls when cost is absent |
| Delete `report.json` after the upload to a dashboard | It is the only place the cost and cache data are | Keep the artifact |

## Troubleshooting

### Every cost is `$0.0000` but the model was called

The provider reported no price (a local model, some gateways, a subscription login). Compare model calls and tokens instead.

### The script lists no agent steps

The run had none, the report is from a `--last-failed` rerun that selected other tests, or the file is a shard's report and the agent tests ran in another shard.

### A step shows `replayed` locally and `missed · no-entry` in CI

The recording is on your machine and not in the repository. See Pattern 3.

### No line ends in `recording …`

The report is from a run with a read-only cache, which is what CI uses unless the config sets `cache: 'read-write'`. Only a read-write run decides what happens to a recording.

### `handed off` with `recordedBy` naming another model

The recording was made by a different model than the one configured now. That alone does not make it stale; use `--no-cache` once to see how the current model does the step.

## Related

- [flaky-or-broken.md](flaky-or-broken.md): retries are the other way agent steps get expensive
- [debugging-a-ci-failure.md](debugging-a-ci-failure.md): the trace page shows the same cache decision per step
- [results-and-artifacts.md](results-and-artifacts.md): keeping `report.json` beside the uploaded results
