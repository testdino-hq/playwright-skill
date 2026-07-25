# Search and Filter Recipes

> **When to use**: You need to test search inputs, filters (category, multi-select, date range), autocomplete suggestions, pagination with filters, or "no results" states.

## Topic map

- **Recipe 1: Search Input with Results**
- **Complete Example**
- **Recipe 2: Search with Debounce (Waiting for Results)**
- **Complete Example**
- **Recipe 3: Filter by Category**
- **Complete Example**
- **Recipe 4: Multi-Select Filter**
- **Complete Example**
- **Recipe 5: Date Range Filter**
- **Complete Example**
- **Recipe 6: Clear All Filters**
- **Complete Example**
- **Recipe 7: Search with Autocomplete / Suggestions**
- **Complete Example**
- **Recipe 8: No Results State**
- **Complete Example**
- **Recipe 9: Pagination with Filters**
- **Complete Example**
- **Variations**
- **Search with Highlight of Matching Terms**
- **Search with URL Query Params for Sharing**
- **Faceted Search with Result Counts**

## TypeScript patterns

### Search with Highlight of Matching Terms

```typescript
test('highlights matching terms in search results', async ({ page }) => {
  await page.goto('/products');

  await page.getByRole('searchbox', { name: /search/i }).fill('wireless');
  await page.getByRole('searchbox', { name: /search/i }).press('Enter');

  await page.waitForResponse('**/api/products?*');

  // Verify matching text is wrapped in a highlight element
  const highlights = page.locator('mark, .highlight, [data-highlight]');
  const count = await highlights.count();
  expect(count).toBeGreaterThan(0);

  // Each highlight should contain the search term
  for (let i = 0; i < count; i++) {
    await expect(highlights.nth(i)).toContainText(/wireless/i);
  }
});
```

### Search with URL Query Params for Sharing

```typescript
test('search results are shareable via URL', async ({ page, context }) => {
  await page.goto('/products');

  await page.getByRole('searchbox', { name: /search/i }).fill('keyboard');
  await page.getByRole('complementary').getByLabel('Electronics').check();
  await page.getByRole('searchbox', { name: /search/i }).press('Enter');

  await page.waitForResponse('**/api/products?*');

  // Get the current URL
  const searchUrl = page.url();

  // Open the same URL in a new page (simulating sharing the link)
  const newPage = await context.newPage();
  await newPage.goto(searchUrl);

  // Verify the same filters and results are shown
  await expect(newPage.getByRole('searchbox', { name: /search/i })).toHaveValue('keyboard');
  await expect(newPage.getByRole('complementary').getByLabel('Electronics')).toBeChecked();

  const rows = newPage.getByRole('row').filter({ hasNot: newPage.getByRole('columnheader') });
  await expect(rows.first()).toBeVisible();

  await newPage.close();
});
```
