# Mobile and Responsive Testing

> **When to use**: Testing how your application behaves on phones, tablets, and across viewport sizes. Covers device emulation, touch interactions, geolocation, orientation changes, and mobile-specific UI patterns.
> **Prerequisites**: [core/configuration.md](configuration.md), [core/locators.md](locators.md)

## Topic map

- **1. Device Emulation** -- Testing your app as it appears on a specific real-world device -- iPhone, Pixel, iPad. Applies the correct viewport, user agent, device scale factor, and touch support in one shot.
- **2. Custom Viewports** -- Testing responsive layouts at specific breakpoints without full device emulation. Ideal for verifying CSS media queries fire at the right widths.
- **3. Touch Events** -- Testing touch-specific interactions -- tap, swipe, pinch. Required for mobile-only gestures that have no mouse equivalent.
- **4. Mobile-Specific UI** -- Testing UI components that only appear on mobile -- hamburger menus, bottom sheets, pull-to-refresh, sticky mobile headers, floating action buttons.
- **5. Geolocation** -- Testing location-dependent features -- store finders, delivery zones, weather widgets, location-based pricing.
- **6. Multi-Project Responsive Testing** -- Running the same tests across desktop and mobile browsers in parallel. The standard approach for responsive apps.
- **7. Responsive Breakpoint Testing** -- Systematically verifying layout behavior at every major CSS breakpoint. Best used alongside visual regression testing.
- **8. Orientation Testing** -- Testing portrait vs landscape layouts. Critical for tablet apps, media players, dashboards, and any app that adapts to orientation.
- **9. Mobile Performance** -- Simulating real-world mobile conditions -- slow 3G networks, underpowered CPUs. Critical for testing loading states, skeleton screens, and timeout handling.
- **10. PWA Mobile Testing** -- Testing Progressive Web App features -- service workers, install prompts, offline mode, push notifications on mobile.
- **`tap()` throws "Page.tap: Not supported" error** -- The browser context was created without `hasTouch: true`. Device profiles set this automatically, but custom viewport configurations do not.
- **`isMobile` is always `false`** -- `isMobile` is set by the device profile's `isMobile` property, not by viewport size. Custom viewports do not set it.
- **Geolocation not working -- location remains default** -- Missing `permissions: ['geolocation']` in context options. The browser silently denies the Geolocation API without this permission.
- **CDP session throws on Firefox/WebKit** -- `page.context().newCDPSession(page)` is Chromium-only. Firefox and WebKit do not support CDP.
- **Viewport change does not trigger CSS media queries** -- `page.setViewportSize()` changes the viewport but does not trigger `resize` or `orientationchange` events in some frameworks that rely on JavaScript-based responsive logic rather than CSS media queries.
- **Service worker not registering in tests** -- Service workers require HTTPS or localhost. Playwright's default `baseURL` of `http://localhost:3000` works, but other HTTP origins do not.

## Decision table

| Question | Answer | Approach |
|---|---|---|
| Need to test how app looks on iPhone 14? | Yes | Use `devices['iPhone 14']` -- gets viewport, UA, touch, scale factor in one shot |
| Need to test a CSS breakpoint at 768px? | Yes | Use `test.use({ viewport: { width: 768, height: 1024 } })` -- simpler, no UA change |
| Need to test both portrait and landscape? | Yes | Use named device + landscape variant: `devices['iPad Pro 11']` and `devices['iPad Pro 11 landscape']` |
| Need realistic mobile performance? | Yes | Use CDP `Network.emulateNetworkConditions` + `Emulation.setCPUThrottlingRate` (Chromium only) |
| Need to test touch gestures? | Yes | Use device profile with `hasTouch: true`, then use `tap()`, mouse gestures for swipe |
| Need to test geolocation? | Yes | Set `geolocation` and `permissions: ['geolocation']` in context options |
| Need pixel-perfect mobile testing? | No -- use real devices | Playwright emulation approximates; font rendering and native UI differ from real hardware |
| Which devices to test by default? | Start with 3 | `Desktop Chrome` + `Pixel 7` (Android) + `iPhone 14` (iOS). Add tablet if your app has a tablet layout. |
| When to add more device projects? | When bugs escape | If users report device-specific bugs, add that device profile permanently |
| Run all devices on every PR? | No | Run desktop + one mobile on PRs. Run all devices on main branch merges. |
| Device emulation vs custom viewport? | Depends on goal | Emulation: testing real-world device behavior. Custom viewport: testing CSS breakpoints. |
| Should I test every screen size? | No | Test your actual CSS breakpoints, plus smallest (320px) and largest (1440px+) supported sizes |

## TypeScript patterns

### Quick Reference

```typescript
import { devices } from '@playwright/test';

// Predefined device profiles (viewport, userAgent, touch, deviceScaleFactor)
devices['iPhone 14']           // 390x844, touch, Safari mobile UA
devices['iPhone 14 Pro Max']   // 430x932, touch, Safari mobile UA
devices['Pixel 7']             // 412x915, touch, Chrome mobile UA
devices['iPad Pro 11']         // 834x1194, touch, Safari tablet UA
devices['Galaxy S9+']          // 320x658, touch, Chrome mobile UA
devices['Desktop Chrome']      // 1280x720, no touch, Chrome desktop UA
devices['Desktop Safari']      // 1280x720, no touch, Safari desktop UA

// Landscape variants
devices['iPhone 14 landscape'] // 844x390, touch, Safari mobile UA
devices['iPad Pro 11 landscape'] // 1194x834, touch, Safari tablet UA
```

### 1. Device Emulation

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  projects: [
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 14'] },
    },
    {
      name: 'Tablet',
      use: { ...devices['iPad Pro 11'] },
    },
  ],
});
```

## Guardrails

- **1. Device Emulation:** You only need to test a specific viewport width (use custom viewports instead). Device emulation is not a substitute for real device testing when pixel-perfect rendering matters.
- **2. Custom Viewports:** You need realistic mobile behavior (touch events, mobile user agent, device scale factor). Use device emulation instead.
- **3. Touch Events:** The feature works identically with mouse clicks. Playwright's `click()` dispatches touch events automatically on touch-enabled device profiles.
- **4. Mobile-Specific UI:** The component renders identically on desktop and mobile.
- **5. Geolocation:** The feature does not use the Geolocation API. If it uses IP-based location, mock the API response instead.
- **6. Multi-Project Responsive Testing:** Your app is desktop-only or mobile-only.
- **7. Responsive Breakpoint Testing:** You only need one or two viewport sizes -- just use `test.use()` overrides instead.
- **8. Orientation Testing:** Your app does not change layout based on orientation (purely responsive to width only -- test with custom viewports instead).

## Related guides

- [core/configuration.md](configuration.md) -- project setup with device profiles and multi-project config
- [core/visual-regression.md](visual-regression.md) -- combine responsive testing with screenshot comparison across viewports
- [core/network-mocking.md](network-mocking.md) -- mock API responses alongside mobile testing
- [core/service-workers-and-pwa.md](service-workers-and-pwa.md) -- in-depth PWA testing beyond mobile context
- [core/performance-testing.md](performance-testing.md) -- comprehensive performance testing including mobile metrics
- [core/browser-apis.md](browser-apis.md) -- geolocation, permissions, and other browser APIs in detail
- [ci/projects-and-dependencies.md](../ci/projects-and-dependencies.md) -- advanced multi-project patterns for responsive testing matrices
