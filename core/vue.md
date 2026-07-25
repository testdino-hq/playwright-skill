# Testing Vue Apps with Playwright

> **When to use**: Testing Vue 3 applications, including composition API components, Pinia stores, Vue Router navigation, Nuxt.js apps, Teleport portals, and transitions. Covers E2E testing and experimental component testing with `@playwright/experimental-ct-vue`.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **Setup**
- **Playwright Config for Vue (Vite)**
- **Component Testing Config**
- **Nuxt.js Setup** -- Nuxt requires a build step before testing and uses port 3000 by default.
- **Component Testing with `@playwright/experimental-ct-vue`** -- Testing complex interactive Vue components in isolation -- data tables, form components, custom select dropdowns, rich editors. The component needs a real browser but not a full application.
- **Testing Pinia Stores Through the UI** -- Verifying that Pinia stores produce the correct UI behavior. Playwright tests the rendered output, not the store directly. If the UI is correct, the store is correct.
- **Testing Vue Router Navigation** -- Testing client-side routing with Vue Router. Verify route transitions, navigation guards, URL parameters, and browser history behavior.
- **Testing Teleport (Portals)** -- Testing components rendered via Vue's `<Teleport>` -- modals, notifications, overlay menus. Teleport moves DOM elements to a different location (often `body`), but Playwright sees the entire document.
- **Testing Transitions and Animations** -- Verifying that Vue `<Transition>` and `<TransitionGroup>` components work correctly -- elements appear, disappear, and reorder with expected behavior. Focus on the end state, not the animation itself.
- **Testing Composition API Components** -- Testing components built with the Vue 3 Composition API (`<script setup>`, `setup()` function). From Playwright's perspective, Composition API and Options API components are identical -- you test the rendered output.
- **Testing Nuxt.js Specific Patterns** -- Testing Nuxt 3 applications with server-side rendering, auto-imports, server routes (`/server/api/`), and middleware.
- **Framework-Specific Tips**
- **Vue DevTools and Playwright** -- Vue DevTools is a browser extension. It does not interfere with Playwright tests since Playwright launches its own browser profile without extensions. Do not rely on Vue DevTools for debugging in CI -- use Playwright...
- **Testing `v-model` Two-Way Binding** -- `v-model` on form inputs works through standard HTML events. Playwright's `fill()`, `check()`, `selectOption()` methods trigger the correct events automatically. No special handling is needed.
- **Vue vs Nuxt: Configuration Differences**
- **Component Testing: Providing Pinia and Router** -- When using `@playwright/experimental-ct-vue`, components that depend on Pinia or Vue Router need these dependencies provided. Configure the test wrapper:
- **Handling Vue Warnings in Tests** -- Vue emits runtime warnings (prop validation, missing components, etc.) that can indicate real issues:

## Decision table

| Don't Do This | Problem | Do This Instead |
|---|---|---|
| `page.evaluate(() => app.__vue_app__.config.globalProperties.$store)` | Accesses Vue internals; breaks on upgrades; tests implementation | Assert on the UI that state produces |
| `page.locator('[data-v-abc123]')` (scoped style hash) | Vue generates random scoped attribute hashes; changes on every build | Use `getByRole`, `getByText`, `getByTestId` |
| Import `.vue` files in E2E tests | E2E tests run in Node.js; `.vue` files need Vite/Webpack compilation | Use `@playwright/experimental-ct-vue` for component tests |
| `page.waitForTimeout(300)` to wait for transition to finish | Transition durations vary; arbitrary waits are fragile | `await expect(locator).toBeVisible()` auto-waits through transitions |
| Mock Pinia stores by patching `window.__pinia` | Fragile; depends on Pinia internals; may not trigger reactivity | Control state through UI interactions or mock the API responses the store consumes |
| Test composables by calling them via `page.evaluate` | Composables rely on Vue's setup context; calling them outside a component fails | Test composables through the components that use them, or unit test with Vitest |
| Use `page.locator('.v-btn')` for Vuetify components | Vuetify class names are internal and change between versions | `page.getByRole('button', { name: 'Submit' })` works regardless of the component library |
| Skip testing keyboard navigation for custom components | Vue component libraries often have incomplete keyboard support | Test `Tab`, `Enter`, `Escape`, `ArrowDown/Up` on dropdowns, modals, tabs |
| Run Nuxt dev server in CI | Dev mode includes hot reload overhead, slower builds, development warnings | Use `npx nuxi build && npx nuxi preview` in CI |

## TypeScript patterns

### Component Testing Config

```typescript
// playwright-ct.config.ts
import { defineConfig, devices } from '@playwright/experimental-ct-vue';

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

### Component Testing: Providing Pinia and Router

```typescript
// playwright/index.ts (component testing setup)
import { beforeMount } from '@playwright/experimental-ct-vue/hooks';
import { createPinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';

beforeMount(async ({ app, hooksConfig }) => {
  // Install Pinia for all component tests
  const pinia = createPinia();
  app.use(pinia);

  // Install a minimal router if the component uses <RouterLink> or useRoute()
  if (hooksConfig?.routes) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: hooksConfig.routes,
    });
    app.use(router);
  }
});
```

## Guardrails

- **Component Testing with `@playwright/experimental-ct-vue`:** The component depends heavily on Pinia stores, Vue Router, or backend data. Use E2E tests instead, or provide the dependencies in your component test setup.
- **Testing Pinia Stores Through the UI:** Testing pure store logic (getters, actions with no UI side effect) -- use unit tests with Vitest for that.
- **Testing Vue Router Navigation:** Testing Nuxt.js file-based routing -- the patterns are similar but Nuxt has additional server-side concerns.
- **Testing Teleport (Portals):** The component is not teleported -- it renders inline in its parent.
- **Testing Transitions and Animations:** Testing the exact CSS animation keyframes -- visual regression testing is better for pixel-level validation.
- **Testing Composition API Components:** You want to test composable functions in isolation -- use Vitest for that.
- **Testing Nuxt.js Specific Patterns:** Testing a plain Vue SPA without Nuxt.

## Related guides

- [core/locators.md](locators.md) -- locator strategies for any Vue component library (Vuetify, PrimeVue, Quasar)
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-waiting assertions for Vue reactivity
- [core/component-testing.md](component-testing.md) -- in-depth component testing patterns
- [core/forms-and-validation.md](forms-and-validation.md) -- form testing patterns for VeeValidate and FormKit
- [core/accessibility.md](accessibility.md) -- accessibility testing for Vue component libraries
- [core/test-architecture.md](test-architecture.md) -- when to use E2E vs component vs unit tests
- [core/nextjs.md](nextjs.md) -- comparison: Nuxt vs Next.js testing patterns
