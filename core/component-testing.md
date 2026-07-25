# Component Testing

> **When to use**: When you need to test UI components in isolation — verifying rendering, interactions, and behavior without spinning up your full application. Ideal for design systems, shared component libraries, and complex interactive widgets.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **1. Setup and Configuration** -- Starting component testing in an existing Playwright project.
- **2. Mounting Components** -- You need to render a component in a real browser with full DOM, CSS, and event handling.
- **3. Testing Interactions** -- The component has clickable elements, form inputs, keyboard handling, or hover states.
- **4. Testing Props** -- You need to verify a component renders correctly with different prop combinations — states, variants, edge cases.
- **5. Testing Events** -- A component emits events or calls callback props — form submissions, toggle changes, custom events.
- **6. Testing Slots and Children** -- Your component accepts children, named slots (Vue), or render props — layout components, wrappers, modals.
- **7. Providing Context (Wrappers and Providers)** -- Your components depend on React context, Vue provide/inject, or global state (theme, auth, i18n, store).
- **8. Mocking Imports** -- A component imports modules that should not run in tests — API clients, analytics, heavy third-party libraries.
- **9. Visual Component Testing** -- You need pixel-level verification of component appearance — design system components, theme variants, responsive states.
- **10. Component Test vs E2E Test** -- Deciding whether to write a component test, an E2E test, or both for a piece of UI.

## Decision table

| UI Element | Component Test | E2E Test | Unit Test |
|---|---|---|---|
| **Button** (variants, states, loading) | Yes — test all visual variants, disabled state, loading state, click handlers | Only as part of a larger flow | No — needs real DOM for styling and accessibility |
| **Form field** (validation, masking) | Yes — test validation messages, input masking, error states in isolation | Yes — test the full form submission flow with backend | Validate-only logic (regex, format functions) |
| **Modal/Dialog** (open, close, content) | Yes — test open/close behavior, focus trap, content rendering | Yes — test the trigger flow that opens the modal | No — needs real DOM |
| **Data table** (sorting, filtering, pagination) | Yes — test sort, filter, pagination with mock data | Yes — test with real API data and URL sync | Pure sort/filter logic on arrays |
| **Navigation/Menu** | Partially — test dropdown behavior, active states | Yes — test actual route changes and page loads | No |
| **Full page** (dashboard, settings) | No — too much context required; defeats isolation purpose | Yes — this is what E2E tests are for | No |
| **Layout** (sidebar, header, grid) | Yes — test responsive behavior, slot rendering | Only if layout affects user flows (e.g., mobile nav) | No |
| **Chart/Graph** | Yes — visual regression of rendered output | Only if charts are part of a critical flow | Data transformation logic only |
| **Toast/Notification** | Yes — test appearance, auto-dismiss, action buttons | Yes — test that real actions trigger correct toasts | No |
| **Design system primitives** | Yes — this is the primary use case for component testing | No — not needed for primitives | No |

## TypeScript patterns

### Quick Reference

```typescript
// Install for your framework:
// npm init playwright@latest -- --ct          (interactive)
// npm install -D @playwright/experimental-ct-react
// npm install -D @playwright/experimental-ct-vue
// npm install -D @playwright/experimental-ct-svelte

// Mount a component, interact, assert:
import { test, expect } from '@playwright/experimental-ct-react';
import { Button } from './Button';

test('button renders and responds to click', async ({ mount }) => {
  let clicked = false;
  const component = await mount(
    <Button label="Save" onClick={() => { clicked = true; }} />
  );
  await expect(component).toContainText('Save');
  await component.click();
  expect(clicked).toBe(true);
});
```

### 6. Testing Slots and Children

```typescript
import { test, expect } from '@playwright/experimental-ct-vue';
import Card from './Card.vue';

test('vue named slots', async ({ mount }) => {
  const component = await mount(Card, {
    props: { title: 'My Card' },
    slots: {
      default: '<p>Card body content</p>',
      footer: '<button>Save</button>',
    },
  });

  await expect(component.getByText('Card body content')).toBeVisible();
  await expect(component.getByRole('button', { name: 'Save' })).toBeVisible();
});
```

## Guardrails

- **1. Setup and Configuration:** You only need full E2E tests against a running application — component testing adds build complexity that is not justified for pure integration tests.
- **2. Mounting Components:** The component is trivial (a pure function that returns a string) — use a unit test instead.
- **3. Testing Interactions:** You are testing browser-level behavior (navigation, cookies) — use E2E tests for that.
- **4. Testing Props:** The prop differences are purely visual with no DOM change — use visual regression instead.
- **5. Testing Events:** You only care that something renders — use a prop/snapshot test instead.
- **6. Testing Slots and Children:** The component has no slot/children API.
- **7. Providing Context (Wrappers and Providers):** The component has no context dependencies — do not wrap unnecessarily.
- **8. Mocking Imports:** You can provide the dependency via props or context instead — explicit injection is always better than import mocking.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) — fixtures work inside component tests the same way
- [core/visual-regression.md](visual-regression.md) — screenshot comparison patterns applicable to component tests
- [core/network-mocking.md](network-mocking.md) — `page.route()` works inside component tests for mocking API calls
- [core/test-architecture.md](test-architecture.md) — when to use component vs E2E vs API tests
- [core/react.md](react.md) — React-specific component testing setup
- [core/vue.md](vue.md) — Vue-specific component testing with slots and provide/inject
