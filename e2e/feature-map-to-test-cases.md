# From the Feature Map to Linked Test Cases

> **When to use**: The project has a feature map (the one e2e's `create-verification-skill` writes under `.agents/skills/verify-<app>/features/`, or any list of features) and the team wants its coverage somewhere shared: which feature has an e2e test, whether that test passed in the last run, and which features have none.
> **Prerequisites**: e2e's `create-verification-skill`, section 3 ("Seed the feature map"). `e2e init` does not install it: `npx skills add e2e-inc/e2e --skill create-verification-skill`. [../qa/manual-to-automated.md](../qa/manual-to-automated.md) for the idea of case-ID traceability. To write, run or fix a test on this machine, read the e2e skill (`npx e2e guide <topic>`); this guide starts where it stops.

The feature map is a good idea with one limit: it is Markdown in one repository. Its `tested` or `untested` column says a test file exists, not that the test passed yesterday. Nobody outside the repository reads it, and a product manager asking "is checkout covered" will not open `.agents/skills/`. Linking each feature to a test case, and each test case to its e2e tests, puts the same map where results arrive on their own.

## Quick Reference

```text
feature file (Markdown)                    test case (shared)                   e2e test (results every run)
features/todos.md, "Sub-features"   →      TC-101 "Adds a todo"          ←→     tests/todos.e2e.ts > todos > adds todos and tracks the remaining count
```

```text
list_manual_test_suites   projectId                                  → exact suite names
create_manual_test_case   projectId, title, suiteName, steps         → the case (TC-…)
list_automated_tests      projectId, search, linkStatus: "unlinked"  → pwTestId + fullTitle
link_automated_test       projectId, caseId, pwTestId, fullTitle     → linked; the case becomes Automated
get_test_case_links       projectId, caseId                          → the linked tests with recent results
```

Creating cases and links changes shared data. Show the user the plan (which cases, which links) and wait for a yes. Linking needs the plan's automation linking feature; without it the link calls return 403.

## Patterns

### Pattern 1: Decide What a Test Case Is

**Use when**: Before creating anything.

The feature map has three levels, and only one maps well to a test case:

| In the map | Example | Make it a |
|---|---|---|
| A feature file | `todos.md` | Test suite (a folder of cases) |
| A line under `## Sub-features` | "Complete with the checkbox labelled by the todo's title" | Test case |
| A charter under `## Charters` | `todos-input\|web\|fuzzer\|…` | Nothing here: charters drive bug bashes ([explore-findings.md](explore-findings.md)) |

One case per sub-feature matches how e2e tests are written: one behavior per test, titled with the outcome it verifies. Most cases end up linked to exactly one e2e test, which is the point.

### Pattern 2: Draft the Case From the Feature File and the Test

**Use when**: A sub-feature has no test case yet.

Everything a case needs is already written down. Do not invent steps.

| Case field | Take it from |
|---|---|
| `title` | The e2e test's title, or the sub-feature line reworded as an outcome |
| `preconditions` | `## How to get to it (user POV)`: route, navigation, the account it needs |
| `steps` | The test's `agent.act` goals. They are plain-language user steps already. For `screen` lines, write what the user does, not the locator |
| Each step's `expectedResult` | The test's assertions, and `## Proof` |
| `suiteName` | The feature's name. Call `list_manual_test_suites` first: the name must match exactly |
| `layer`, `type` | `E2E`, and whatever the project uses for regression |

```text
create_manual_test_case
  projectId, suiteName: "Todos",
  title: "Completing a todo lowers the remaining count",
  preconditions: "Open /todos. No account needed.",
  steps: [
    { action: "Add a todo named \"Buy milk\"",          expectedResult: "The list shows \"Buy milk\"; Remaining reads \"1 remaining\"" },
    { action: "Tick the checkbox labelled \"Buy milk\"", expectedResult: "Remaining reads \"0 remaining\"" }
  ],
  layer: "E2E"
```

Never put a credential in a case. Name the account, as the feature map does.

### Pattern 3: Link the Case to Its e2e Test

**Use when**: The case exists and the test has run at least once with the reporter (an id exists only after a run).

```text
list_automated_tests  projectId, search: "completing a todo", linkStatus: "unlinked"
```

Each entry has the two values a link needs:

| Field | For an e2e test |
|---|---|
| `pwTestId` | TestDino's id for the test. The field keeps its Playwright name |
| `fullTitle` | `<file> > <describe…> > <title>`, for example `tests/todos.e2e.ts > todos > completing a todo lowers the remaining count`. Copy it from the listing; a hand-built one is rejected |
| `platforms` | The targets the test ran on |
| `isLinked` | Whether a case already links to it |

The listing has one entry per file and title, with every target under `platforms`. That differs from run results, where each target's row has its own id. Link the entry the listing gives you; `fullTitle` carries no target.

```text
link_automated_test  projectId, caseId: "TC-102", pwTestId: "<from the listing>", fullTitle: "<from the listing>"
```

For a whole feature map, collect the pairs and send them in one `bulk_link_automated_tests` call (up to 500). It takes the case's internal id, not the `TC-` key, and returns a result per pair: check each one, since a bad pair does not fail the batch.

### Pattern 4: Write the Link Back Into the Repository

**Use when**: Cases are linked, so the map and the test both say which case they belong to.

Two small edits keep the three places in step. Ask before making them.

A column in the feature map index:

```markdown
| Feature | Route | Test | Status | Cases |
| --- | --- | --- | --- | --- |
| [Todos](todos.md) | `/todos` | `tests/todos.e2e.ts` | tested | TC-101, TC-102, TC-103 |
```

And the case id as a tag on the test. e2e tags are uploaded with results, so the id is searchable on both sides:

```ts
test('completing a todo lowers the remaining count', { tags: ['TC-102'] }, async ({ app, screen }) => {
  // ...
});
```

```text
list_testcase  projectId, by_branch: "main", by_time_interval: "weekly", by_tag: "TC-102"
```

Adding a tag does not change a test's identity, so its history and its recorded agent steps are kept.

### Pattern 5: Answer the Coverage Questions

**Use when**: Someone asks what is covered.

| Question | Call |
|---|---|
| Which e2e tests does no case cover? | `list_automated_tests` with `linkStatus: "unlinked"` |
| Which features have no automated test? | `list_manual_test_cases` with `automationStatus: "Manual"`. These are the map's `untested` rows |
| Is this feature passing? | `get_test_case_links` for its cases: each linked test with its recent success rate and last run |
| Which features did last night's failures touch? | `list_testcase` with `by_status: "failed"`, then the `TC-` tags on the failing rows |

The first two lists are also the honest input for the feature map's `Status` column, instead of whether a file exists.

### Pattern 6: Keep the Link Alive Through Refactors

**Use when**: Tests are renamed, moved, or split.

A test's identity is its file, its title path, its target and its agent. Change any of them and TestDino sees a new test: the old one stops receiving results and the link points at it.

- After renaming or moving tests, run `list_automated_tests` with `linkStatus: "unlinked"`: the renamed tests show up there. Link them and unlink the old identities (`unlink_automated_test`).
- The same rename also makes every `agent.act` goal in the test record again, because the cache key holds the file and title path. A rename costs twice; do it deliberately. [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md) shows the bill.
- `create-verification-skill`'s own rule for the map applies here too: when a route or label changes and a test fails, the feature file changes in the same commit. Add the case to that list.

## Decision Guide

| Situation | Do |
|---|---|
| No feature map yet | e2e's `create-verification-skill` writes one. Then this guide |
| A map, no test cases | Patterns 1 to 3, top three to five features first, as the map itself was seeded |
| Test cases exist already (imported from a spreadsheet or another tool) | Skip Pattern 2. Search the existing cases and link |
| The same test runs on several targets | One case and one link: the listing shows the test once, with its targets under `platforms`, and the link carries every target's run history. `get_test_case_links` shows the success rate and `platforms` of the most recently seen target only; read the full target list from `list_automated_tests` |
| A feature marked `untested` | Create the case anyway and leave it Manual. It is now a visible gap instead of a line in a file |
| A Playwright suite beside the e2e one | The same linking tools take Playwright tests: [../qa/manual-to-automated.md](../qa/manual-to-automated.md) |

## Anti-Patterns

| Don't | Why | Do instead |
|---|---|---|
| One case per feature file | A feature has several behaviors; one red test makes the whole feature read as failing | One case per sub-feature |
| Type a `fullTitle` by hand | It is a server-built key; a near match is rejected | Copy it from `list_automated_tests` |
| Create cases and links in bulk without showing the plan | Shared data other people rely on | List what will be created, wait for a yes |
| Write locators into case steps | Cases are read by people who do not read tests | The user action, in the words on screen |
| Rename tests freely after linking | Breaks the link and re-records the agent steps | Pattern 6 |
| Treat `tested` in the map as "passing" | It means a test file exists | `get_test_case_links` for the last result |

## Troubleshooting

### `list_automated_tests` does not show a test

It has never run with the reporter, or it ran before the reporter was added. Run it once in CI.

### `link_automated_test` returns 400

The identity is unknown to the project (a hand-built `fullTitle`, or an id from another project), the test is already linked to that case, or the case already has 50 links.

### `link_automated_test` returns 403

No write permission, or the plan does not include automation linking.

### `create_manual_test_case` is refused

`suiteName` does not match an existing suite exactly, or a required custom field is missing; the error names it.

## Related

- [explore-findings.md](explore-findings.md): the map's charters, and where their findings go
- [agent-cost-and-cache-health.md](agent-cost-and-cache-health.md): what a rename costs
- [../qa/manual-to-automated.md](../qa/manual-to-automated.md), [../qa/test-design.md](../qa/test-design.md): the Playwright side of test case work
