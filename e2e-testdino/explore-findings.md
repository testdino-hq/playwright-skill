# Explore and Bug Bash Findings: Owners, Tickets, History

> **When to use**: `e2e explore` or a bug bash produced findings, and they need to outlive the terminal: someone to own each bug, a ticket, the evidence attached, and a way to know the bug stays fixed.
> **Prerequisites**: the e2e skill, topics `explore` and `bug-bash`. That skill covers planning charters, running them, triage and verification. To write, run or fix a test on this machine, read it (`npx e2e guide <topic>`); this guide starts where it stops.

A bug bash ends, by the e2e skill's own steps, with a report: confirmed bugs, each with a failing repro test, plus rejected findings and warnings. The report is text in a terminal, and the evidence is in `.e2e/bugbash/`, a folder the same skill says to delete before the next bash. This guide is about what happens to the confirmed bugs after that.

**What is and is not automatic.** The `@testdino/e2e` reporter uploads tests. It does not turn the `run.explore` findings of an exploration into records, and exploratory sessions in TestDino take findings through the UI, not through the MCP server. So the durable record of a finding is two things you create on purpose: the **repro test** (which carries the evidence and proves the fix) and a **ticket** (which carries the owner).

## Quick Reference

```text
verified bug  →  tests/bugbash/<slug>.e2e.ts fails for the reported reason      (e2e skill, topic bug-bash, step 6)
              →  upload that run, tagged                                        (Pattern 2)
              →  one ticket per bug, linked to the failing test                 (Pattern 3)
              →  one session per bash, holding the charters and the tickets     (Pattern 4)
              →  fix lands: the repro goes green and joins the suite            (Pattern 5)
```

```bash
# Every finding of every charter, issues first, most severe first
node scripts/e2e-findings.mjs .e2e/bugbash/*/report.json
```

## Patterns

### Pattern 1: List the Findings From the Reports

**Use when**: The charters have finished and you need one merged list to triage, instead of reading each log.

Each charter's `report.json` holds its findings under `run.explore.findings`. This script prints them in the order the e2e skill reports them:

```js
// scripts/e2e-findings.mjs: the findings of one or more `e2e explore` runs, issues first, most severe first.
// Usage: node scripts/e2e-findings.mjs <report.json> [<report.json> ...]
import { readFileSync } from 'node:fs';

const SEVERITY = { 5: 'critical', 4: 'high', 3: 'medium', 2: 'low', 1: 'trivial' };
const findings = [];
for (const path of process.argv.slice(2)) {
  const explore = JSON.parse(readFileSync(path, 'utf8')).run.explore;
  if (!explore) continue; // not an exploration: a test run's report has no run.explore
  for (const f of explore.findings) findings.push({ ...f, goal: explore.goal, report: path });
}
findings.sort((a, b) => (a.kind === b.kind ? b.severity - a.severity : a.kind === 'issue' ? -1 : 1));

console.log(`${findings.length} findings: ${findings.filter((f) => f.kind === 'issue').length} issues, ${findings.filter((f) => f.kind !== 'issue').length} warnings\n`);
for (const f of findings) {
  console.log(`${SEVERITY[f.severity]} ${f.kind}: ${f.title}${f.path ? ` (${f.path})` : ''}`);
  console.log(`  expected: ${f.expected}`);
  console.log(`  actual:   ${f.actual}`);
  f.reproduction.forEach((step, i) => console.log(`  ${i + 1}. ${step}`));
  console.log(`  charter:  ${f.goal}`);
  console.log(`  report:   ${f.report}\n`);
}
```

These are claims, not bugs. The e2e skill is firm on this: a finding is the model's claim plus evidence, and nothing is reported as a bug until its repro test fails for the reason reported. Merge duplicates and triage with that skill's steps 4 to 6 before going further.

### Pattern 2: Upload the Repro Run

**Use when**: Repro tests exist under `tests/bugbash/`, tagged `bugbash`, and each fails on its defect.

The bug-bash config in the e2e skill sets `reporters: ['list']`. Add the reporter there, with a tag, so the repro run is uploaded and easy to tell from the regular suite:

```ts
// e2e.bugbash.config.ts
import { testdino } from '@testdino/e2e';
// ...
  reporters: ['list', testdino({ tags: ['bugbash'] })],
```

```bash
npx e2e run --tag bugbash --config e2e.bugbash.config.ts --video=retain-on-failure
```

Now each confirmed bug is a failing test in a run that will not be deleted with `.e2e/bugbash/`: its error, its trace page, the screen at failure and the recording are all one link. Exploration runs themselves do not need uploading; their findings are in the list from Pattern 1 and their evidence is superseded by the repro's.

A charter's recording is not masked. Check what the repro run shows before uploading it from an app with real data.

### Pattern 3: One Ticket per Confirmed Bug, Linked to Its Failing Test

**Use when**: The repro run is uploaded and the user wants tickets. Only with their yes.

```text
get_integration_status  projectId, provider: "jira", includeCreateOptions: true   → connected? which fields are required?
list_testcase           by_testrun_id, by_status: "failed"                        → each repro's pw_test_id
create_external_issue   projectId, provider: "jira",
                        source: { type: "test_case", id: "<pw_test_id>", runId: "<testrun_id>" },
                        summary: "<the finding's title>",
                        description: "<expected, actual, steps, path>",
                        preview: true                                             → the draft, nothing created
```

The source `id` is the repro's `pw_test_id` from the listing, and `runId` is required: together they name the test in that run. The preview shows whether the source resolved.

Show the user the draft, then repeat without `preview`. The ticket links back to the failing test, so whoever picks it up has the evidence without asking.

Write the description from the finding, in user terms, the way [../qa/bug-reports.md](../qa/bug-reports.md) lays it out: the finding's `expected` and `actual`, its `reproduction` steps as numbered steps, the `path`, the severity, and the repro test's path. Supported providers are Jira, Linear, Asana and monday.com. For GitHub Issues, use `gh issue create` with the same text.

### Pattern 4: One Session per Bug Bash

**Use when**: The team tracks exploratory testing, or wants to see later what a bash covered and what it found.

```text
create_session  projectId,
                name: "Bug bash: checkout, 2026-11-13",
                sessionType: "Exploratory",
                mission: "<the charters, as HTML: one line per charter with its slug and persona>",
                tags: ["bugbash", "checkout"],
                linkedIssues: [ { displayId: "SHOP-812", title: "...", url: "..." } ]
```

- `mission` is the place for the charters, and for the last part of the e2e skill's report: the areas no charter reached. That is the part people need next time.
- `tags` is an array of strings here.
- `linkedIssues` ties the session to the tickets from Pattern 3.
- The findings themselves are added in the TestDino UI. Say so rather than implying the session holds them.

### Pattern 5: When the Fix Lands, the Repro Joins the Suite

**Use when**: A confirmed bug is fixed.

The e2e skill ends the story this way: the repro test turning green is the proof, and it stays as the regression test with its `bugbash` tag removed. From then on it runs in the normal suite and is uploaded with it.

```text
verify_fix  projectId, testcase_id: "<the repro's pw_test_id>", baseline_run_id: "<the bugbash run>"
```

A test's identity is its file, its title path, its target and its agent. Tags are not part of it, so removing the tag keeps the history. Three things break it:

- **Renaming the test or moving the file.** A moved repro is a new test with no history, and its recorded agent steps record again. Remove the tag first, verify, and move the file in a later change if at all.
- **A different target name in the bug-bash config.** A target's default name is its platform (`web`). If the project config names its target `chromium` and the bug-bash config names it `web`, the same repro is two tests. Use the project's target names in the bug-bash config.
- **Running the repro as a persona.** Repros run as the `default` agent unless pinned; keep it that way.

### Pattern 6: Keep Failing Repros Out of the Gate, Without Quarantine

**Use when**: Repro tests are committed while their bugs are still open.

A repro test fails until its bug is fixed, by design. The e2e skill keeps such tests out of the gating run with `npx e2e run --exclude-tag bugbash`. That is the right tool. Quarantine is for a test that belongs in the gate and fails for a reason someone is fixing; a repro was never in the gate.

## Decision Guide

| Situation | Do |
|---|---|
| Findings not yet verified | Nothing in this guide. Verify first (e2e skill, topic `bug-bash`) |
| A finding was rejected (artifact, environment, design, fixture) | Keep it in the bash report with the reason. No ticket, no test |
| A confirmed bug | Repro test uploaded (Pattern 2), ticket (Pattern 3) |
| A warning the user wants tracked | A ticket without a repro test, marked as polish |
| The same bash runs every release | One session per bash, same tags, so sessions list side by side |
| An environment finding that is a production risk | The e2e skill reports these as unverified. Ticket it as a risk, not a bug |
| No issue tracker connected | The repro run's link and the list from Pattern 1, in the pull request or handoff |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| File a ticket per finding straight from the explorer's output | Findings are model claims; many are artifacts of the explorer | Verify, then ticket only what a repro confirms |
| Leave confirmed bugs in `.e2e/bugbash/` | The next bash deletes the folder | Upload the repro run |
| Create tickets or sessions without asking | Both land in tools other people watch | Preview, then wait for a yes |
| Paste a finding's screenshot or video into a public tracker | Recordings are not masked | Link the failing test; attach media only to private tickets |
| Quarantine the repro tests | They are expected to fail and are not in the gate | `--exclude-tag bugbash` |
| Rename or move a repro when its bug is fixed | New id, lost history, agent steps record again | Remove the tag only |

## Troubleshooting

### The script prints "0 findings"

The files are not exploration reports. `run.explore` exists only on `e2e explore` runs; the repro run and the regular suite have none.

### `create_external_issue` is refused

The provider is not connected for the project, or a required field is missing. `get_integration_status` with `includeCreateOptions: true` lists the projects, issue types and required fields.

### The repro passes in CI but failed locally

It asserted something another repro changed, or it depended on the seeded account of its charter. Make each repro assert only its own defect, and sign in the way its charter did.

## Related

- [flaky-or-broken.md](flaky-or-broken.md): `verify_fix`, and why quarantine is the wrong tool here
- [feature-map-to-test-cases.md](feature-map-to-test-cases.md): the charters come from the feature map; so can the test cases
- [../qa/bug-reports.md](../qa/bug-reports.md): the shape of a bug report a developer can act on
