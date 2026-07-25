# Forms and Validation

> **When to use**: Testing form filling, submission, validation messages, multi-step wizards, dynamic fields, and auto-complete interactions.
> **Prerequisites**: [core/locators.md](locators.md), [core/assertions-and-waiting.md](assertions-and-waiting.md)

## Topic map

- **Filling Basic Form Fields** -- Testing any form with standard HTML inputs — text, email, password, number, textarea, select, checkbox, radio.
- **Date and Time Inputs** -- Testing native `<input type="date">`, `<input type="time">`, `<input type="datetime-local">`, or third-party date pickers.
- **Required Field Validation** -- Testing that the form shows appropriate error messages when required fields are empty.
- **Format Validation and Custom Rules** -- Testing email format, phone number format, password strength, and business-specific validation rules.
- **Multi-Step Forms and Wizards** -- The form spans multiple pages or steps, with next/previous navigation and per-step validation.
- **Auto-Complete and Typeahead Fields** -- Testing search fields, address lookups, mention pickers, or any input that shows suggestions as the user types.
- **Dynamic Forms — Conditional Fields** -- Form fields appear, disappear, or change based on the value of other fields.
- **Form Submission and Response Handling** -- Testing what happens after a form is submitted — success messages, redirects, error responses from the server, and loading states during submission.
- **Form Reset Testing** -- Testing "clear form" or "reset" functionality, verifying that fields return to their default values.
- **`fill()` does nothing or clears but doesn't type** -- The input field uses a contenteditable div (rich text editors), not a real `<input>` or `<textarea>`.
- **Date picker does not accept `fill()` value** -- Third-party date pickers often render custom UI over a hidden input. `fill()` sets the hidden input but the UI does not update.
- **`selectOption()` throws "not a <select> element"** -- The dropdown is a custom component (ARIA listbox), not a native `<select>`.
- **Validation errors do not appear after `fill()` and submit** -- The validation triggers on `blur` (focus leaving the field), but `fill()` does not trigger blur automatically.

## Decision table

| Scenario | Approach | Key API |
|---|---|---|
| Standard text input | `fill()` (clears, then types) | `page.getByLabel('Name').fill('Jane')` |
| Need keystroke events (autocomplete) | `pressSequentially()` with delay | `locator.pressSequentially('text', { delay: 100 })` |
| Native `<select>` dropdown | `selectOption()` by value or label | `locator.selectOption('US')` or `{ label: 'United States' }` |
| Custom dropdown (ARIA listbox) | Click trigger, then select option role | `getByRole('option', { name: '...' }).click()` |
| Checkbox | `check()` / `uncheck()` (idempotent) | `locator.check()` — safe to call even if already checked |
| Radio button | `check()` on the target radio | `page.getByLabel('Express').check()` |
| Date input (native) | `fill()` with ISO format | `locator.fill('2025-03-15')` |
| Date picker (third-party) | Click to open, navigate, select day | `getByRole('gridcell', { name: '15' }).click()` |
| Validation errors | Submit, then assert error text | `expect(page.getByText('Required')).toBeVisible()` |
| Multi-step wizard | `test.step()` per step, assert heading | `await test.step('Step 1', async () => { ... })` |
| Conditional/dynamic fields | Change trigger field, assert new field visibility | `expect(locator).toBeVisible()` / `.not.toBeVisible()` |
| Form submission | `waitForResponse` + click submit | Register response listener before click |
| Auto-complete | `pressSequentially()`, wait for listbox, select option | `getByRole('option', { name }).click()` |
| Form reset | Click reset, assert default values | `expect(locator).toHaveValue('')` |

## TypeScript patterns

### Quick Reference

```typescript
// Text input
await page.getByLabel('Name').fill('Jane Doe');

// Select dropdown
await page.getByLabel('Country').selectOption('US');
await page.getByLabel('Country').selectOption({ label: 'United States' });

// Checkbox and radio
await page.getByLabel('Remember me').check();
await page.getByLabel('Express shipping').click();

// Date input
await page.getByLabel('Start date').fill('2025-03-15');

// Clear a field
await page.getByLabel('Name').clear();

// Submit
await page.getByRole('button', { name: 'Submit' }).click();

// Verify validation error
await expect(page.getByText('Email is required')).toBeVisible();
```

### `fill()` does nothing or clears but doesn't type

```typescript
// Check if it is contenteditable
const isContentEditable = await page.getByTestId('editor').evaluate(
  (el) => el.getAttribute('contenteditable')
);

// For contenteditable, use pressSequentially or type
if (isContentEditable) {
  await page.getByTestId('editor').click();
  await page.getByTestId('editor').pressSequentially('Hello world');
}
```

## Guardrails

- **Filling Basic Form Fields:** Never. This is the foundation pattern.
- **Date and Time Inputs:** The date picker is a simple text field with no special input type. Just use `fill()`.
- **Required Field Validation:** You only care about the happy path. Validation tests should complement, not replace, success path tests.
- **Format Validation and Custom Rules:** The validation is purely server-side with no client-side feedback. Test via API instead.
- **Multi-Step Forms and Wizards:** The form is a single page. Use the basic form filling pattern.
- **Auto-Complete and Typeahead Fields:** The field is a plain text input with no suggestions.
- **Dynamic Forms — Conditional Fields:** All fields are always visible. Use the basic form filling pattern.
- **Form Submission and Response Handling:** You only care about client-side validation. Test submission separately from validation.

## Related guides

- [core/locators.md](locators.md) -- locator strategies for finding form elements
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- assertion patterns for verifying form state
- [core/file-operations.md](file-operations.md) -- file upload fields in forms
- [core/error-and-edge-cases.md](error-and-edge-cases.md) -- testing form error states and edge cases
- [core/accessibility.md](accessibility.md) -- ensuring forms are accessible (label associations, ARIA attributes)
- [core/network-mocking.md](network-mocking.md) -- mocking form submission API responses
