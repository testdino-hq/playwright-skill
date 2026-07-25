# Testing React Apps with Playwright

> **When to use**: Testing React applications built with Create React App (CRA), Vite, or custom bundlers. Covers E2E testing, experimental component testing, React Router navigation, form libraries, portals, error boundaries, and context/state verification through the UI.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **Setup**
- **Playwright Config for React (Vite)**
- **Component Testing Config** -- Component testing mounts individual React components in a real browser without a full dev server. This is experimental but useful for testing complex components in isolation.
- **Component Testing with `@playwright/experimental-ct-react`** -- Testing complex interactive components in isolation -- data tables, form wizards, rich text editors, dropdowns with keyboard navigation. The component needs a real browser (not jsdom) but not a full application.
- **Testing Hooks Indirectly Through the UI** -- Verifying that custom hooks produce the correct UI behavior. Playwright cannot call hooks directly -- test them through the components that consume them.
- **Testing Context and State Changes Through User Interactions** -- Verifying that React context (theme, auth, locale) and state management (Redux, Zustand, Jotai) produce correct UI changes.
- **Testing React Router Navigation** -- Testing client-side routing with React Router v6+. Verify route transitions, URL parameters, protected routes, and browser history behavior.
- **Testing Form Libraries (React Hook Form, Formik)** -- Testing forms built with react-hook-form, Formik, or similar libraries. Playwright interacts with the DOM, so the form library is transparent -- test the user experience, not the library internals.
- **Testing React Portals (Modals, Tooltips, Dropdowns)** -- Testing components rendered via `ReactDOM.createPortal()` -- modals, dialogs, tooltips, dropdown menus, toast notifications. These render outside the parent DOM hierarchy, but Playwright sees the full document.
- **Testing Error Boundaries** -- Verifying that React error boundaries catch rendering errors gracefully and show fallback UI instead of a white screen.
- **Framework-Specific Tips**
- **CRA vs Vite: Key Differences** -- Adjust your `webServer.command` and `baseURL` accordingly.
- **React Strict Mode and Double Effects** -- React Strict Mode in development runs effects twice. This can cause unexpected behavior in tests (e.g., double API calls). Your tests should be resilient to this:
- **Testing Suspense and Lazy Components**
- **Component Testing: When to Use It vs E2E**
- **Detecting Memory Leaks in Long-Running Tests** -- If your React app has unmounted component state updates (the "Can't perform a React state update on an unmounted component" warning), catch them:

## Decision table

| Don't Do This | Problem | Do This Instead |
|---|---|---|
| `page.evaluate(() => store.getState())` to assert Redux state | Couples tests to implementation; state shape changes break tests | Assert on the UI that the state produces: `expect(cartBadge).toHaveText('3')` |
| Import React components in E2E test files | E2E tests run in Node.js, not the browser; component imports fail | Use `@playwright/experimental-ct-react` for component testing, E2E for full-app tests |
| `page.waitForTimeout(500)` after React state changes | React batches updates; timing varies across machines | Use `expect(locator).toHaveText('new value')` which auto-retries |
| Test internal component state with `page.evaluate` | Fragile; breaks on refactors; tests implementation, not behavior | Interact through the UI and assert on visible output |
| Mock `useState` or `useEffect` in Playwright tests | Playwright runs in the browser context, not the React component tree | Let hooks run naturally; control inputs (API responses, props via component testing) |
| Use `page.locator('.MuiButton-root')` for Material UI | Class names change between MUI versions and are generated dynamically | `page.getByRole('button', { name: 'Submit' })` works regardless of the component library |
| Test every component with `@playwright/experimental-ct-react` | Overhead of browser mounting for simple components; duplicates unit tests | Use component testing for complex interactive widgets; unit tests for pure logic; E2E for flows |
| Skip testing keyboard navigation on custom components | Accessibility regressions are common in custom dropdowns, modals, tabs | Test `Tab`, `Enter`, `Escape`, `ArrowDown` interactions in component tests |
| Assert on React DevTools or `__REACT_FIBER__` internals | Internal React properties are not stable across versions | Only interact with and assert on the rendered DOM |

## TypeScript patterns

### Component Testing Config

```typescript
// playwright-ct.config.ts
import { defineConfig, devices } from '@playwright/experimental-ct-react';

export default defineConfig({
  testDir: './tests/components',
  testMatch: '**/*.ct.ts',

  use: {
    trace: 'on-first-retry',
    ctPort: 3100,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

### Testing Suspense and Lazy Components

```typescript
// React.lazy() components show a fallback while loading
test('lazy-loaded route shows spinner then content', async ({ page }) => {
  await page.goto('/');

  // Navigate to a lazy route
  await page.getByRole('link', { name: 'Reports' }).click();

  // The reports module loads lazily -- you may briefly see a spinner
  // Playwright auto-waits for the final content
  await expect(page.getByRole('heading', { name: 'Reports' })).toBeVisible();
});
```

## Guardrails

- **Component Testing with `@playwright/experimental-ct-react`:** The component behavior depends heavily on backend data or routing context. Use E2E tests instead.
- **Testing Hooks Indirectly Through the UI:** The hook logic is pure computation with no UI side effects -- use a unit testing framework for that.
- **Testing Context and State Changes Through User Interactions:** You want to assert on the raw state object -- Playwright tests the UI, not internal state. If the UI is correct, the state is correct.
- **Testing React Router Navigation:** Your app uses server-side routing only (Next.js App Router handles this differently -- see [core/nextjs.md](nextjs.md)).
- **Testing Form Libraries (React Hook Form, Formik):** Testing the form library itself. You are testing YOUR form behavior.
- **Testing React Portals (Modals, Tooltips, Dropdowns):** The component is not a portal -- it renders inline.
- **Testing Error Boundaries:** You are testing error handling in event handlers or async code -- error boundaries only catch rendering errors.

## Related guides

- [core/locators.md](locators.md) -- locator strategies that work with any React component library
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-waiting assertions for React state changes
- [core/forms-and-validation.md](forms-and-validation.md) -- form testing patterns applicable to react-hook-form and Formik
- [core/component-testing.md](component-testing.md) -- in-depth component testing guide
- [core/accessibility.md](accessibility.md) -- testing ARIA patterns in React component libraries
- [core/test-architecture.md](test-architecture.md) -- when to use E2E vs component vs unit tests
- [core/nextjs.md](nextjs.md) -- Next.js-specific patterns for React apps with SSR
