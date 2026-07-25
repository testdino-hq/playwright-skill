# Accessibility Testing

> **When to use**: Every project. Accessibility is not a feature — it is a quality baseline. Integrate automated checks (axe-core) into every test suite and supplement with manual keyboard/screen-reader verification for critical flows.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **ARIA Snapshots For Structure Checks** -- You want to verify the accessibility tree shape of a page, region, dialog, or widget in addition to running axe.
- **Page-Level Aria Snapshot Assertions (Playwright 1.60+)** -- You want to assert the whole page's accessibility tree against a stored snapshot, or you need element bounding boxes alongside the tree (useful for AI/agent consumption and layout-aware checks).
- **axe-core/playwright Integration** -- You want automated WCAG violation detection on any page or component. This is your first line of defense and should run in every test suite.
- **Scanning Specific Regions** -- You want to focus axe-core on a specific component (new feature, redesigned section) or exclude areas you do not control (third-party widgets, ads, embedded iframes).
- **WCAG Compliance Levels** -- Your project targets a specific WCAG compliance level (most target AA). Use tags to limit axe-core to the rules that matter for your compliance requirement.
- **Disabling Specific Rules** -- Migrating a legacy app to accessibility compliance incrementally. You have known violations documented in a tracking system and want the test suite to catch new regressions without failing on existing known issues.
- **Keyboard Navigation Testing** -- Verifying that all interactive elements are reachable and operable via keyboard alone. This is critical for motor-impaired users and power users who navigate without a mouse.
- **Screen Reader Testing Patterns** -- Verifying that ARIA attributes, live regions, and roles produce the correct accessible experience. You cannot run a real screen reader in CI, but you can verify the semantic structure that screen readers depend on.
- **Color Contrast Verification** -- Ensuring text and UI components meet WCAG contrast ratio requirements. axe-core checks contrast automatically, but you may need explicit checks for dynamic themes, dark mode, or brand color changes.
- **Focus Trap Testing** -- Testing modals, dialogs, dropdown menus, slide-over panels, and any overlay that must trap focus within itself to prevent users from accidentally interacting with background content.
- **Accessible Forms** -- Testing that forms are usable by assistive technology. Every form field must have an associated label, error messages must be programmatically linked, and required fields must be announced.
- **Accessibility in CI** -- You want accessibility violations to fail builds, preventing regressions from reaching production. Every team should gate their CI pipeline on accessibility.
- **axe-core reports no violations but screen reader experience is poor** -- Audit your most critical flows with a real screen reader (VoiceOver on macOS: Cmd+F5; NVDA on Windows: free download). Listen to the announcements and ask: would a user who cannot see the screen understand what to do?
- **"color-contrast" violation on elements that look fine** -- axe-core computes contrast against the actual background, which may involve overlapping elements, gradients, or background images. The computed background may differ from what you see.
- **Focus is lost after a dynamic content change** -- When an element is removed from the DOM (closing a modal, deleting a list item, navigating a SPA), focus falls back to `<body>`, leaving keyboard users stranded.
- **axe-core scan returns incomplete results (not violations)** -- `results.incomplete` contains checks axe could not determine automatically. These are not failures — they are items that need manual review. Common for color contrast on complex backgrounds.
- **Tab order test fails intermittently** -- Focus behavior depends on the page being fully loaded and interactive. Animations, lazy-loaded content, or auto-focus scripts can interfere.

## Decision table

| What to Check | Automated (axe-core) | Manual (Keyboard/Screen Reader) | Why |
|---|---|---|---|
| Missing alt text | Yes | No | axe-core detects this reliably |
| Color contrast ratios | Yes | No | Computed automatically from CSS |
| Missing form labels | Yes | No | Detects missing `<label>` and aria associations |
| Invalid ARIA attributes | Yes | No | Validates against WAI-ARIA spec |
| Duplicate IDs | Yes | No | DOM analysis |
| Tab order / logical flow | No | Yes | Requires understanding of page layout and user intent |
| Focus management in modals | Partial (axe checks `aria-hidden`) | Yes | Focus trapping behavior requires behavioral testing |
| Screen reader UX quality | No | Yes | Whether announcements are helpful is subjective |
| Cognitive load / readability | No | Yes | Cannot be automated — requires human judgment |
| Touch target size (mobile) | Yes (WCAG 2.2) | Yes | axe checks minimum size; real-device feel needs manual testing |
| Dynamic content announcements | No | Yes | Live region behavior depends on timing and screen reader |
| Keyboard shortcut conflicts | No | Yes | Requires knowing OS/browser/AT shortcuts |
| Reading order vs visual order | No | Yes | CSS reordering (flexbox `order`, grid) can break this |
| Error recovery flow | No | Yes | Whether error guidance is understandable requires human judgment |
| Video captions / audio descriptions | Partial (checks `<track>`) | Yes | Quality of captions must be verified manually |

## TypeScript patterns

### Quick Reference

```typescript
// Install: npm install -D @axe-core/playwright
import AxeBuilder from '@axe-core/playwright';

// Full page scan
const results = await new AxeBuilder({ page }).analyze();
expect(results.violations).toEqual([]);

// Scoped scan — only the main content area
const results = await new AxeBuilder({ page }).include('#main-content').analyze();

// WCAG AA only
const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();

// Exclude known issues during migration
const results = await new AxeBuilder({ page }).disableRules(['color-contrast']).analyze();

// Playwright 1.59+: capture the accessibility tree for the whole page
const pageTree = await page.ariaSnapshot();

// Or scope it to one region
const dialogTree = await page.getByRole('dialog', { name: 'Checkout' }).ariaSnapshot();

// Playwright 1.60+: assert the whole page's aria tree, and capture bounding boxes
await expect(page).toMatchAriaSnapshot();
const treeWithBoxes = await page.ariaSnapshot({ boxes: true });
```

### ARIA Snapshots For Structure Checks

```typescript
import { test, expect } from '@playwright/test';

test('checkout dialog exposes the expected accessibility structure', async ({ page }) => {
  await page.goto('/checkout');
  await page.getByRole('button', { name: 'Open checkout' }).click();

  const dialogTree = await page
    .getByRole('dialog', { name: 'Checkout' })
    .ariaSnapshot();

  expect(dialogTree).toContain('heading "Checkout"');
  expect(dialogTree).toContain('button "Apply coupon"');
});
```

## Guardrails

- **ARIA Snapshots For Structure Checks:** You only need rule-based WCAG checks. Start with axe for broad coverage, then use ARIA snapshots for high-value structure assertions.
- **Page-Level Aria Snapshot Assertions (Playwright 1.60+):** A scoped locator assertion is enough — whole-page snapshots are broad and change often. Prefer asserting a stable region.
- **axe-core/playwright Integration:** You need to verify subjective UX quality (reading order, cognitive load, plain language). axe-core catches structural violations, not usability problems.
- **Scanning Specific Regions:** You want a full-page baseline. Scan everything first, then narrow down.
- **WCAG Compliance Levels:** You want the broadest possible scan. Omitting `withTags()` runs all rules, including best practices beyond WCAG.
- **Disabling Specific Rules:** Hiding violations you do not intend to fix. Every disabled rule should have a tracking ticket.
- **Keyboard Navigation Testing:** Never skip this. Automated tools cannot fully verify keyboard navigation — this requires behavioral tests.
- **Screen Reader Testing Patterns:** You want to test actual screen reader output (use manual testing with NVDA/VoiceOver for that).

## Related guides

- [core/locators.md](locators.md) — role-based locators align with accessibility best practices
- [core/forms-and-validation.md](forms-and-validation.md) — form interaction patterns including accessible error handling
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) — CI setup for running accessibility tests
- [core/i18n-and-localization.md](i18n-and-localization.md) — accessibility considerations for multilingual apps
- [core/component-testing.md](component-testing.md) — test individual component accessibility in isolation
