# Choosing a Locator Strategy

> **When to use**: When deciding which Playwright locator method to use for an element

## Topic map

- **Quick Answer** -- Use `getByRole()` for everything that has a semantic HTML role (buttons, links, headings, form fields, dialogs). Fall back to `getByLabel()` for form fields, `getByText()` for plain content, and `getByTestId()` only a...
- **Decision Flowchart**
- **Decision Matrix**
- **Detailed Analysis**
- **Tier 1: `getByRole()` -- Use by Default** -- The strongest locator. It mirrors how assistive technology and real users perceive the page.
- **Tier 2: `getByLabel()` -- Form Fields** -- Queries by the associated `<label>` text. This is often the most readable locator for form fields.
- **Tier 3: `getByText()` -- Static Content** -- Finds elements by their visible text content.
- **Tier 4: `getByPlaceholder()` -- Inputs Without Labels** -- Locates by placeholder attribute value.
- **Tier 5: `getByTestId()` -- Last Resort** -- Locates by `data-testid` attribute.
- **Never Use: Raw CSS Selectors or XPath** -- If you are reaching for a CSS selector, stop. Walk back up the flowchart and find a semantic locator. If none exists, add `data-testid`.
- **Real-World Examples**
- **1. Buttons**
- **2. Links**
- **3. Text Inputs**
- **4. Checkboxes and Radios**
- **5. Dropdowns and Selects**
- **6. Headings**
- **7. Navigation Items**
- **8. Table Cells**
- **9. Images**
- **10. Custom Components (No ARIA Role)**
- **11. Dynamic Lists**
- **12. Modals and Dialogs**
- **Anti-Patterns to Avoid**
- **Scoping Strategy: When Multiple Elements Match** -- When a locator matches more than one element, narrow scope rather than using `nth()`:

## Decision table

| Element Type | Recommended Locator | Fallback | Example |
|---|---|---|---|
| Button | `getByRole('button', { name })` | `getByText()` if role missing | `getByRole('button', { name: 'Submit' })` |
| Link | `getByRole('link', { name })` | `getByText()` for anchor text | `getByRole('link', { name: 'Sign up' })` |
| Text input | `getByLabel('...')` | `getByRole('textbox', { name })` | `getByLabel('Email address')` |
| Checkbox | `getByRole('checkbox', { name })` | `getByLabel()` | `getByRole('checkbox', { name: 'Accept terms' })` |
| Radio button | `getByRole('radio', { name })` | `getByLabel()` | `getByRole('radio', { name: 'Express shipping' })` |
| Dropdown / Select | `getByRole('combobox', { name })` | `getByLabel()` | `getByLabel('Country')` |
| Heading | `getByRole('heading', { name, level })` | `getByText()` | `getByRole('heading', { name: 'Dashboard', level: 1 })` |
| Nav link | chain: `getByRole('navigation').getByRole('link', { name })` | scope with `locator('nav')` | see detailed example below |
| Table cell | chain: `getByRole('row').filter().getByRole('cell')` | `locator('td')` scoped | see detailed example below |
| Image | `getByRole('img', { name })` | `getByAltText()` | `getByRole('img', { name: 'Company logo' })` |
| Modal / Dialog | `getByRole('dialog')` then chain within | `locator('[role="dialog"]')` | `getByRole('dialog').getByRole('button', { name: 'Confirm' })` |
| Dynamic list item | `.filter({ hasText })` or `.filter({ has })` | `nth()` as last resort | `getByRole('listitem').filter({ hasText: 'Milk' })` |
| Custom component | `getByTestId('...')` | Add `data-testid` to markup | `getByTestId('color-picker')` |

## TypeScript patterns

### 1. Buttons

```typescript
// TypeScript
// Standard button
await page.getByRole('button', { name: 'Submit' }).click();

// Icon-only button (uses aria-label)
await page.getByRole('button', { name: 'Close' }).click();

// Button inside a specific section
await page.getByRole('region', { name: 'Billing' })
  .getByRole('button', { name: 'Update' }).click();
```

### 2. Links

```typescript
// TypeScript
// Standard link
await page.getByRole('link', { name: 'Sign up' }).click();

// Link inside navigation
await page.getByRole('navigation')
  .getByRole('link', { name: 'Pricing' }).click();

// Link with exact match (avoid partial hits)
await page.getByRole('link', { name: 'Log in', exact: true }).click();
```

## Related guides

- [Playwright Locators documentation](https://playwright.dev/docs/locators)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [ARIA Roles reference (MDN)](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles)
