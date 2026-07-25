# File Upload and Download Recipes

> **When to use**: You need to test file uploads (single, multiple, drag-and-drop), file downloads (verify content, filename, type), upload progress, or file type restrictions.

## Topic map

- **Recipe 1: Single File Upload via Input**
- **Complete Example**
- **Recipe 2: Multiple File Upload**
- **Complete Example**
- **Recipe 3: Drag-and-Drop File Upload**
- **Complete Example**
- **Recipe 4: Download and Verify File Content**
- **Complete Example**
- **Recipe 5: Download and Verify Filename**
- **Complete Example**
- **Recipe 6: Large File Upload with Progress**
- **Complete Example**
- **Recipe 7: Testing File Type Restrictions**
- **Complete Example**
- **Variations**
- **Upload via File Chooser Dialog**
- **Upload with Image Preview**
- **Download with Authentication**

## TypeScript patterns

### Upload via File Chooser Dialog

```typescript
test('uploads via the native file chooser dialog', async ({ page }) => {
  await page.goto('/documents');

  // Listen for the file chooser event before clicking the trigger
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Choose file' }).click();

  const fileChooser = await fileChooserPromise;

  // Verify it accepts only certain types
  expect(fileChooser.isMultiple()).toBe(false);

  await fileChooser.setFiles({
    name: 'chosen-file.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('pdf-content'),
  });

  await expect(page.getByText('chosen-file.pdf')).toBeVisible();
});
```

### Upload with Image Preview

```typescript
test('shows image preview after selecting a file', async ({ page }) => {
  await page.goto('/settings/profile');

  const fileInput = page.locator('input[type="file"]');

  await fileInput.setInputFiles(path.resolve(__dirname, '../fixtures/avatar.jpg'));

  // Verify the image preview is displayed
  const preview = page.getByRole('img', { name: /preview|avatar/i });
  await expect(preview).toBeVisible();

  // Verify the preview src is a blob or data URL
  const src = await preview.getAttribute('src');
  expect(src).toMatch(/^(blob:|data:image)/);
});
```

## Related guides

- [Playwright Upload Docs](https://playwright.dev/docs/input#upload-files)
- [Playwright Download Docs](https://playwright.dev/docs/downloads)
