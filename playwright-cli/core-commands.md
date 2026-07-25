# Core Commands

Use `snapshot` to obtain current element refs before every interaction sequence. Re-snapshot after navigation, modal changes, or major DOM updates because refs can become stale.

## Essential loop

```bash
playwright-cli open http://localhost:3000/login
playwright-cli snapshot
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "$TEST_PASSWORD"
playwright-cli click e3
playwright-cli snapshot
playwright-cli close
```

Do not place real secrets directly in shell history. Use an approved secret source or test-only account.

## Browser and navigation

```bash
playwright-cli open [url]
playwright-cli open --browser=firefox
playwright-cli open --persistent
playwright-cli open --profile=./.profiles/admin
playwright-cli goto http://localhost:3000/settings
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
playwright-cli close
```

Use `--persistent` only when state must survive restarts. Keep profiles outside version control.

## Inspection

```bash
playwright-cli snapshot
playwright-cli snapshot --filename=checkout.yaml
playwright-cli console error
playwright-cli network
```

Snapshot output maps semantic elements to refs such as `e1 [textbox "Email"]`. Prefer the semantic ref over CSS or XPath.

## Element interaction

```bash
playwright-cli click e4
playwright-cli dblclick e5
playwright-cli fill e1 "complete value"
playwright-cli type "keystrokes"
playwright-cli select e7 "CA"
playwright-cli check e8
playwright-cli uncheck e8
playwright-cli hover e9
playwright-cli drag e10 e11
playwright-cli upload e12 ./fixtures/avatar.png
```

`fill` replaces the value. `type` emits individual keyboard events. Use `upload` only with an explicit fixture path.

## Keyboard, mouse, and viewport

```bash
playwright-cli press Enter
playwright-cli press Control+K
playwright-cli keydown Shift
playwright-cli keyup Shift
playwright-cli mousemove 150 300
playwright-cli mousedown
playwright-cli mouseup
playwright-cli mousewheel 0 600
playwright-cli resize 1280 720
```

Coordinate input is fragile; prefer element refs whenever possible.

## Dialogs and tabs

```bash
playwright-cli dialog-accept
playwright-cli dialog-accept "prompt value"
playwright-cli dialog-dismiss
playwright-cli tab-list
playwright-cli tab-new http://localhost:3000/help
playwright-cli tab-select 1
playwright-cli tab-close 1
```

Register the intended dialog action before the operation that opens it when using `run-code`.

## TypeScript equivalent

Use generated TypeScript when the workflow should become a maintained test:

```typescript
import { test, expect } from '@playwright/test';

test('signs in', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard/);
});
```

## Troubleshooting

- Missing ref: snapshot again and verify the element is visible.
- Click intercepted: inspect the snapshot, console, and trace for overlays.
- Navigation race: wait on the resulting URL or visible state in TypeScript.
- Unexpected behavior: capture `console`, `network`, and a trace before retrying.
