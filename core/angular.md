# Testing Angular Apps with Playwright

> **When to use**: Testing Angular applications -- reactive forms, Angular Material components, Angular Router navigation, lazy-loaded modules, signals, observables, and Zone.js-driven change detection. This guide covers E2E testing patterns specific to Angular behavior.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **Setup**
- **Playwright Config for Angular**
- **Angular CLI Integration** -- Angular projects that previously used Protractor can adopt Playwright as a direct replacement. The test directory conventionally lives at `e2e/` in Angular projects.
- **Environment Configuration** -- Angular uses `environment.ts` and `environment.prod.ts` for build-time configuration. For test-specific settings, use environment variables passed through the Playwright config.
- **Angular-Specific Locator Strategies** -- Targeting elements in Angular templates. Angular generates specific attribute patterns (`_ngcontent-*`, `_nghost-*`, `ng-reflect-*`) that you must avoid in locators. Always use semantic locators.
- **Testing Reactive Forms** -- Testing Angular reactive forms (`FormGroup`, `FormControl`, `FormArray`). Playwright interacts with the rendered DOM, so reactive forms are transparent -- test the user experience.
- **Testing Angular Material Components** -- Testing apps using Angular Material (mat-button, mat-input, mat-select, mat-dialog, mat-table, etc.). Angular Material components use proper ARIA attributes, making them accessible to role-based locators.
- **Testing Angular Router Navigation** -- Testing Angular Router navigation, lazy-loaded routes, route guards, and URL parameter handling.
- **Testing Lazy-Loaded Modules** -- Verifying that Angular lazy-loaded feature modules load correctly when the user navigates to their routes. Lazy-loaded modules introduce network requests for JavaScript chunks.
- **Testing Signals and Observables Indirectly** -- Verifying that Angular signals (`signal()`, `computed()`, `effect()`) and RxJS observables produce correct UI updates. Playwright cannot subscribe to observables or read signals directly -- test through the rendered o...
- **Framework-Specific Tips**
- **Zone.js Considerations** -- Angular uses Zone.js to detect async operations and trigger change detection. Playwright does not depend on Zone.js -- it interacts with the DOM directly. However, Zone.js can affect test behavior:
- **Protractor to Playwright Migration Checklist**
- **Angular Build Configurations** -- The `-s` flag on `http-server` enables SPA fallback (sends `index.html` for all routes), which is essential for Angular Router to work correctly.
- **CDK Overlay Container** -- Angular Material and Angular CDK render overlays (dialogs, menus, selects, autocompletes) in a special container outside the component tree. Playwright sees these overlays in the document -- no special handling is nee...
- **Testing with Angular SSR (Universal)** -- If your Angular app uses server-side rendering:

## Decision table

| Don't Do This | Problem | Do This Instead |
|---|---|---|
| `page.locator('[_ngcontent-abc123]')` | Angular scoped style attributes are random and change every build | Use `getByRole`, `getByLabel`, `getByText`, `getByTestId` |
| `page.locator('[ng-reflect-model="value"]')` | `ng-reflect-*` attributes only exist in dev mode; stripped in production | Test the rendered value: `expect(input).toHaveValue('value')` |
| `page.locator('app-my-component')` | Angular component selectors are implementation details | Target the content the component renders using semantic locators |
| `page.locator('.mat-mdc-button')` | Angular Material class names change between versions (MDC migration) | `page.getByRole('button', { name: 'Submit' })` |
| `page.evaluate(() => (window as any).ng)` to access Angular internals | Depends on debug mode; not available in production builds | Test through the DOM; never access the Angular runtime |
| `await page.waitForTimeout(500)` after clicking a button | Zone.js change detection timing varies; arbitrary waits are fragile | `await expect(locator).toHaveText('expected value')` auto-retries |
| `browser.waitForAngular()` (Protractor pattern) | Does not exist in Playwright; not needed -- Playwright auto-waits | Remove entirely; use web-first assertions |
| Test Angular services by injecting them via `page.evaluate` | Services are not accessible from the browser console in production | Test services indirectly through the UI they power; unit test with TestBed |
| Use `ng serve` in CI | Development server is slower, includes debug code, may hide production-only bugs | Use `ng build && http-server` in CI |
| Skip testing CDK overlay components (dialogs, selects, menus) | These are the most interactive parts of the app; bugs here are highly visible | Test overlays with role-based locators; they render in the regular DOM |

## TypeScript patterns

### Environment Configuration

```typescript
// playwright.config.ts (excerpt)
webServer: {
  command: process.env.CI
    ? 'npx ng build --configuration=production && npx http-server dist/your-app/browser -p 4200 -s'
    : 'npx ng serve --configuration=development',
  url: 'http://localhost:4200',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
  env: {
    NG_APP_API_URL: 'http://localhost:4200/api',
  },
},
```

### Testing with Angular SSR (Universal)

```typescript
// playwright.config.ts (SSR-specific)
webServer: {
  command: process.env.CI
    ? 'npx ng build --ssr && node dist/your-app/server/server.mjs'
    : 'npx ng serve --ssr',
  url: 'http://localhost:4200',
  reuseExistingServer: !process.env.CI,
  timeout: 180_000, // SSR builds are slower
},
```

## Guardrails

- **Angular-Specific Locator Strategies:** You are tempted to use `[_ngcontent-abc123]` or `[ng-reflect-model]` attributes -- they are internal and change on every build.
- **Testing Reactive Forms:** Testing form validation logic in isolation -- use Angular TestBed unit tests for that.
- **Testing Angular Material Components:** Using CSS class selectors like `.mat-mdc-button` or `.mat-option` -- these change between Material versions.
- **Testing Angular Router Navigation:** Testing router configuration in isolation -- use Angular TestBed for that.
- **Testing Lazy-Loaded Modules:** The module is eagerly loaded -- no separate chunk to load.
- **Testing Signals and Observables Indirectly:** Testing observable transformation logic in isolation -- use Jasmine/Jest with Angular TestBed for that.

## Related guides

- [core/locators.md](locators.md) -- locator strategies for Angular Material and CDK components
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-waiting assertions that replace Protractor's waitForAngular
- [core/forms-and-validation.md](forms-and-validation.md) -- form testing patterns for reactive and template-driven forms
- [core/accessibility.md](accessibility.md) -- accessibility testing for Angular Material components
- [core/authentication.md](authentication.md) -- authentication with Angular route guards
- [migration/from-selenium.md](../migration/from-selenium.md) -- migration patterns applicable to Protractor (Protractor is built on Selenium)
- [core/test-architecture.md](test-architecture.md) -- when to use E2E vs unit tests with Angular TestBed
- [ci/ci-github-actions.md](../ci/ci-github-actions.md) -- CI setup with Angular build caching
