# File Operations

> **When to use**: Testing file uploads, downloads, drag-and-drop file interactions, file type validation, and download verification.
> **Prerequisites**: [core/locators.md](locators.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Single File Upload** -- A form has a standard `<input type="file">` element.
- **Multiple File Upload** -- The file input accepts `multiple` and you need to attach several files at once.
- **File Chooser Dialog** -- The upload is triggered by a button click that opens the native file picker, not by a visible `<input type="file">`. Common with drag-and-drop libraries and custom upload components.
- **Drag-and-Drop File Upload** -- The UI has a drop zone that accepts files via the HTML5 Drag and Drop API and has no `<input type="file">` fallback.
- **File Download — Wait and Verify** -- Testing export buttons, report generation, or any action that triggers a browser download.
- **Configuring Download Paths** -- You need downloads to go to a specific directory, or you need to disable the download dialog prompt.
- **File Type Validation** -- Testing that the application rejects invalid file types and accepts valid ones.
- **Large File Handling** -- Testing uploads or downloads of large files where timeouts and progress indicators matter.
- **"FileChooser event was not emitted"** -- The click did not open a native file picker dialog. The upload component may use a different mechanism.
- **"Download event was not emitted"** -- The link opens in a new tab or navigates to the file URL instead of triggering a download.
- **Upload works locally but fails in CI** -- File paths are wrong in CI, or the fixture files are not included in the repo/build.
- **`setInputFiles` does nothing — no file appears** -- The input element is detached, inside a Shadow DOM, or in an iframe.

## Decision table

| Scenario | Approach | Key API |
|---|---|---|
| Standard `<input type="file">` | `setInputFiles()` on the locator | `locator.setInputFiles(path)` |
| Hidden file input | Find the input even if hidden, call `setInputFiles()` | `page.locator('input[type="file"]').setInputFiles()` |
| Custom button opens file picker | Listen for `filechooser` event before clicking | `page.waitForEvent('filechooser')` |
| Drag-and-drop zone with no input | Dispatch `drop` event with `DataTransfer` | `locator.dispatchEvent('drop', ...)` |
| DnD zone with hidden input fallback | Prefer `setInputFiles()` on the hidden input | Check `input[type="file"]` count first |
| Multiple files at once | Pass array to `setInputFiles()` | `setInputFiles([path1, path2])` |
| In-memory test file (no disk) | Pass object with `name`, `mimeType`, `buffer` | `setInputFiles({ name, mimeType, buffer })` |
| Download — verify filename | `download.suggestedFilename()` | `page.waitForEvent('download')` |
| Download — verify content | `download.saveAs()` then read with `fs` | `fs.readFileSync()` |
| Download — temp file only | `download.path()` returns temp location | Auto-deleted after test |
| Large file upload/download | Use `test.slow()`, increase assertion timeouts | `{ timeout: 120_000 }` |

## TypeScript patterns

### Quick Reference

```typescript
// Upload — single file
await page.getByLabel('Upload').setInputFiles('fixtures/resume.pdf');

// Upload — multiple files
await page.getByLabel('Upload').setInputFiles(['fixtures/a.png', 'fixtures/b.png']);

// Upload — clear selection
await page.getByLabel('Upload').setInputFiles([]);

// Download — wait and save
const download = await page.waitForEvent('download');
await page.getByRole('button', { name: 'Export CSV' }).click();
const path = await download.path();           // temp path
await download.saveAs('test-results/export.csv'); // permanent path

// File chooser dialog — non-input uploads
const fileChooser = await page.waitForEvent('filechooser');
await page.getByRole('button', { name: 'Choose file' }).click();
await fileChooser.setFiles('fixtures/photo.jpg');
```

### Single File Upload

```typescript
import { test, expect } from '@playwright/test';
import path from 'path';

test('upload a single document', async ({ page }) => {
  await page.goto('/settings/profile');

  const filePath = path.join(__dirname, '../fixtures/avatar.png');
  await page.getByLabel('Profile picture').setInputFiles(filePath);

  // Verify the file name appears in the UI
  await expect(page.getByText('avatar.png')).toBeVisible();

  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByText('Profile updated')).toBeVisible();
});
```

## Guardrails

- **Single File Upload:** The upload uses a drag-and-drop zone with no underlying file input.
- **Multiple File Upload:** The UI only allows one file. Use single file upload.
- **File Chooser Dialog:** There is a visible `<input type="file">` — use `setInputFiles` directly.
- **Drag-and-Drop File Upload:** A file input exists — even hidden ones work with `setInputFiles`.
- **File Download — Wait and Verify:** The file is served as a page navigation (opens in a new tab). Use multi-tab patterns instead.
- **Configuring Download Paths:** Default temp paths via `download.path()` or `download.saveAs()` are sufficient.
- **File Type Validation:** The application does no client-side validation and relies entirely on server-side checks (test via API instead).
- **Large File Handling:** Every test. Large file tests are slow. Run them in a separate suite or tag them for nightly runs.

## Related guides

- [core/locators.md](locators.md) -- locator strategies for finding upload/download elements
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- assertion patterns for verifying upload/download results
- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- creating reusable download directory fixtures
- [core/network-mocking.md](network-mocking.md) -- mocking upload endpoints for faster tests
- [core/error-and-edge-cases.md](error-and-edge-cases.md) -- testing upload failure states and error handling
