# CRUD Testing Recipes

> **When to use**: You need to test create, read, update, or delete operations on any resource -- forms, tables, lists, cards, inline edits, or bulk actions.

## Topic map

- **Recipe 1: Creating a Resource (Fill Form, Submit, Verify)**
- **Complete Example**
- **Recipe 2: Reading / Listing Resources (Table, Cards, Pagination)**
- **Complete Example**
- **Recipe 3: Updating a Resource (Edit Form, Save, Verify Changes)**
- **Complete Example**
- **Recipe 4: Deleting a Resource (Delete, Confirm Dialog, Verify Removal)**
- **Complete Example**
- **Recipe 5: Inline Editing**
- **Complete Example**
- **Recipe 6: Bulk Operations**
- **Complete Example**
- **Variations**
- **Create with Multi-Step Wizard**
- **CRUD with API Verification**
- **Optimistic UI Updates**

## TypeScript patterns

### Create with Multi-Step Wizard

```typescript
test('creates a resource through a multi-step wizard', async ({ page }) => {
  await page.goto('/products');
  await page.getByRole('button', { name: 'Add product' }).click();

  // Step 1: Basic info
  await expect(page.getByText('Step 1 of 3')).toBeVisible();
  await page.getByLabel('Product name').fill('Wireless Keyboard');
  await page.getByLabel('Category').selectOption('Electronics');
  await page.getByRole('button', { name: 'Next' }).click();

  // Step 2: Pricing
  await expect(page.getByText('Step 2 of 3')).toBeVisible();
  await page.getByLabel('Price').fill('79.99');
  await page.getByLabel('Tax rate').selectOption('Standard (20%)');
  await page.getByRole('button', { name: 'Next' }).click();

  // Step 3: Review and confirm
  await expect(page.getByText('Step 3 of 3')).toBeVisible();
  await expect(page.getByText('Wireless Keyboard')).toBeVisible();
  await expect(page.getByText('$79.99')).toBeVisible();
  await page.getByRole('button', { name: 'Create product' }).click();

  await expect(page.getByRole('alert')).toContainText('Product created');
});
```

### CRUD with API Verification

```typescript
test('create and verify via API', async ({ page, request }) => {
  await page.goto('/products');
  await page.getByRole('button', { name: 'Add product' }).click();

  await page.getByLabel('Product name').fill('API Verified Product');
  await page.getByLabel('Price').fill('49.99');
  await page.getByRole('button', { name: 'Save product' }).click();

  await expect(page.getByRole('alert')).toContainText('Product created');

  // Also verify via API that the data was persisted correctly
  const response = await request.get('/api/products?search=API+Verified+Product');
  const data = await response.json();

  expect(data.products).toHaveLength(1);
  expect(data.products[0].name).toBe('API Verified Product');
  expect(data.products[0].price).toBe(49.99);
});
```
