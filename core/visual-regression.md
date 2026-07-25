# Visual Regression Testing

> **When to use**: Catching unintended visual changes -- layout shifts, style regressions, broken responsive designs, theme corruption -- that functional assertions miss. Visual tests answer "does it still look right?" after code changes.
> **Prerequisites**: [core/configuration.md](configuration.md) for project setup, [core/assertions-and-waiting.md](assertions-and-waiting.md) for assertion basics.

## Topic map

- **1. Screenshot Comparison Basics** -- Verifying that a page or component renders correctly after code changes. Best for pages with stable layouts -- landing pages, dashboards, settings panels.
- **2. Configuring Thresholds** -- Your UI has minor rendering differences between runs -- anti-aliasing, font hinting, sub-pixel rendering. Thresholds prevent false failures from pixel-level noise.
- **3. Full Page vs Element Screenshots** -- Deciding scope. Full page catches layout shifts and spacing regressions. Element screenshots isolate components and are more stable.
- **4. Masking Dynamic Content** -- The page contains content that changes between test runs -- timestamps, user avatars, ad slots, relative dates ("3 minutes ago"), random hero images, A/B test variants.
- **5. Animations Handling** -- Always. CSS animations and transitions are the number one cause of flaky visual diffs. A screenshot captured mid-animation will never match the baseline.
- **6. Updating Snapshots** -- You have intentionally changed the UI and need to update the baselines. A design refresh, rebrand, new feature, or layout change.
- **7. Cross-Browser Visual Testing** -- Your users span Chrome, Firefox, and Safari and you need to verify rendering consistency per browser.
- **8. Responsive Visual Testing** -- Your application has responsive breakpoints and you need to verify layouts at different viewport sizes.
- **9. CI Setup for Visual Tests** -- Running visual regression tests in CI. The critical requirement is consistent rendering -- the same test must produce the same screenshot every time.
- **10. Component Visual Testing** -- Testing individual UI components in isolation -- buttons, cards, forms, modals. Faster than full-page screenshots, more stable, and easier to maintain.
- **11. Asserting Pseudo-Element Styles Instead of a Screenshot (Playwright 1.60+)** -- You only care about one or two computed styles on a `::before` / `::after` pseudo-element (an icon glyph, a required asterisk, a status dot color). A targeted CSS assertion is faster and far less brittle than a pixel...
- **"Screenshot comparison failed" on first CI run after local development** -- Generate snapshots using Docker locally so they match CI:
- **"Expected screenshot to match but X pixels differ"** -- Add a small tolerance:
- **Visual tests pass locally but fail in CI (even with Docker)** -- Ensure the Playwright version in `package.json` matches the Docker image tag:
- **Animations cause random diff failures** -- Set `animations: 'disabled'` globally:
- **Snapshot file names conflict between tests** -- Playwright includes the test file name in the snapshot path by default. If you still have conflicts, use explicit unique names:
- **Too many snapshot files to maintain** -- Be selective. Visual test only pages where visual regressions are high-risk:

## Decision table

| Scenario | Recommended Approach | Why |
|---|---|---|
| Key landing pages, marketing site | Full page screenshot, `fullPage: true` | Catches layout shifts, spacing, and overall visual harmony |
| Individual UI components (buttons, cards, modals) | Element screenshot on the component | Isolated, fast, stable -- immune to unrelated page changes |
| Page with dynamic content (timestamps, live data) | Full page + `mask` on dynamic elements | Covers layout while ignoring volatile content |
| Design system component library | Element screenshot per variant, zero threshold | Pixel-perfect enforcement for shared components |
| Responsive layout verification | Screenshot per viewport (loop or projects) | Catches breakpoint bugs at mobile/tablet/desktop |
| Cross-browser rendering consistency | Separate snapshots per browser project | Browsers render fonts and shadows differently |
| CI pipeline | Docker container (Playwright image), Linux-only snapshots | Consistent rendering, no OS-dependent diffs |
| Pixel threshold: design system | `threshold: 0`, `maxDiffPixels: 0` | Zero tolerance for component library |
| Pixel threshold: content pages | `maxDiffPixelRatio: 0.01`, `threshold: 0.2` | Allows minor anti-aliasing variance |
| Pixel threshold: charts and graphs | `maxDiffPixels: 200`, `threshold: 0.3` | Anti-aliasing on curves varies across runs |
| Visual tests add value | Stable pages, design systems, post-refactor verification | Clear baseline, predictable content |
| Visual tests are noise | Highly dynamic pages, real-time dashboards, A/B test pages | Content changes on every load, diffs are meaningless |

## TypeScript patterns

### Quick Reference

```typescript
// Page screenshot -- compare entire viewport
await expect(page).toHaveScreenshot();

// Element screenshot -- compare a specific component
await expect(page.getByTestId('pricing-card')).toHaveScreenshot();

// Named snapshot -- explicit file name
await expect(page).toHaveScreenshot('homepage-hero.png');

// With threshold -- allow minor pixel differences
await expect(page).toHaveScreenshot({ maxDiffPixelRatio: 0.01 });

// Mask dynamic content -- hide timestamps, avatars, ads
await expect(page).toHaveScreenshot({
  mask: [page.getByTestId('timestamp'), page.getByRole('img', { name: 'Avatar' })],
});

// Disable animations -- prevent flaky diffs from CSS transitions
await expect(page).toHaveScreenshot({ animations: 'disabled' });

// Update baselines (CLI)
npx playwright test --update-snapshots
```

### 1. Screenshot Comparison Basics

```typescript
import { test, expect } from '@playwright/test';

test('homepage renders correctly', async ({ page }) => {
  await page.goto('/');

  // Full page screenshot comparison
  await expect(page).toHaveScreenshot('homepage.png');
});

test('pricing card matches design', async ({ page }) => {
  await page.goto('/pricing');

  // Element-level screenshot -- scoped to a single component
  const card = page.getByTestId('pro-plan-card');
  await expect(card).toHaveScreenshot('pro-plan-card.png');
});
```

## Guardrails

- **1. Screenshot Comparison Basics:** The page is highly dynamic with real-time data, live feeds, or content that changes on every load. Use functional assertions instead.
- **2. Configuring Thresholds:** You want pixel-perfect comparisons (design-system component libraries, icon rendering). Keep thresholds at zero.
- **3. Full Page vs Element Screenshots:** Neither -- use both strategically.
- **4. Masking Dynamic Content:** All content is deterministic. Masking adds maintenance overhead.
- **5. Animations Handling:** You are explicitly testing the animation itself (rare).
- **6. Updating Snapshots:** The diff is unexpected -- investigate the cause before blindly updating.
- **7. Cross-Browser Visual Testing:** Early stage projects targeting a single browser -- visual tests across three browsers triple the maintenance burden.
- **8. Responsive Visual Testing:** The page has a single fixed-width layout.

## Related guides

- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- `toHaveScreenshot()` is a web-first assertion and follows the same retry semantics
- [core/configuration.md](configuration.md) -- global screenshot config, project setup, `snapshotPathTemplate`
- [core/mobile-and-responsive.md](mobile-and-responsive.md) -- responsive viewport testing patterns
- [ci/docker-and-containers.md](../ci/docker-and-containers.md) -- Docker setup for consistent rendering
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI pipeline configuration for visual tests
