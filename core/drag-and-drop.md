# Drag and Drop Recipes

> **When to use**: You need to test drag-and-drop interactions -- sortable lists, kanban boards, file drop zones, or any element that can be repositioned by dragging.

## Topic map

- **Recipe 1: Native HTML5 Drag and Drop**
- **Complete Example**
- **Recipe 2: Sortable Lists (Reordering Items)**
- **Complete Example**
- **Recipe 3: Kanban Board (Moving Between Columns)**
- **Complete Example**
- **Recipe 4: File Drop Zone**
- **Recommended: `locator.drop()` (Playwright 1.60+)** -- The drop zone is driven by `drop`/`dragover` DOM events (most modern uploaders, editors that accept dropped images, or zones with no `input[type=file]` fallback).
- **Legacy / fallback: file input + dispatched events**
- **Recipe 5: Drag with Custom Preview / Ghost Image**
- **Complete Example**
- **Recipe 6: Testing Drag Position and Coordinates**
- **Complete Example**
- **Variations**
- **Drag and Drop with Keyboard Accessibility**
- **Drag and Drop Between iframes**
- **Touch-Based Drag on Mobile**

## TypeScript patterns

### Drag and Drop with Keyboard Accessibility

```typescript
test('reorders items using keyboard', async ({ page }) => {
  await page.goto('/tasks');

  const list = page.getByRole('list', { name: 'Task list' });
  const taskC = list.getByRole('listitem').filter({ hasText: 'Task C' });

  // Focus the item
  await taskC.focus();

  // Use keyboard shortcut to pick up the item
  await page.keyboard.press('Space');

  // Move up twice
  await page.keyboard.press('ArrowUp');
  await page.keyboard.press('ArrowUp');

  // Drop the item
  await page.keyboard.press('Space');

  const items = await list.getByRole('listitem').allTextContents();
  expect(items[0]).toContain('Task C');
});
```

### Drag and Drop Between iframes

```typescript
test('drags between main page and iframe', async ({ page }) => {
  await page.goto('/editor');

  const sourceItem = page.getByText('Widget A');
  const iframe = page.frameLocator('#preview-frame');
  const dropTarget = iframe.locator('#content-area');

  // Cross-frame drag requires coordinates since dragTo does not work across frames
  const sourceBox = await sourceItem.boundingBox();
  const iframeElement = page.locator('#preview-frame');
  const iframeBox = await iframeElement.boundingBox();

  // Calculate target position within the iframe
  const targetX = iframeBox!.x + 100;
  const targetY = iframeBox!.y + 100;

  await sourceItem.hover();
  await page.mouse.down();
  await page.mouse.move(targetX, targetY, { steps: 20 });
  await page.mouse.up();

  await expect(iframe.getByText('Widget A')).toBeVisible();
});
```

## Guardrails

- **Recommended: `locator.drop()` (Playwright 1.60+):** You're on Playwright < 1.60 — use the `setInputFiles` approach instead.

## Related guides

- [Playwright Drag and Drop Docs](https://playwright.dev/docs/input#drag-and-drop)
