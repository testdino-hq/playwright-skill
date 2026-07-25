# Playwright Error Index

Quick-reference for specific Playwright error messages. Find your error, understand the cause, apply the fix.
> **How to use**: Search this file for the exact error text you see in your terminal or test report. Each entry gives you the cause and a working fix.

## Topic map

- **Locator & Element Errors**
- **"locator.click: Target closed"** -- Wait for navigation to complete before performing the next action, or use `Promise.all` to coordinate the click and navigation together.
- **"waiting for locator('...') to be visible"** -- First confirm the locator matches what you expect using the Playwright Inspector. Then ensure the precondition for the element to appear is met.
- **"locator.click: Error: strict mode violation"** -- Make the locator more specific so it resolves to exactly one element.
- **"Error: expect(locator).toBeVisible() — locator resolved to X elements"** -- Narrow the locator to a single element (see strict mode violation fix above). Alternatively, if you intentionally want to check all matches:
- **"locator.fill: Error: Element is not an <input>, <textarea> or [contenteditable] element"** -- Target the actual input element.
- **"Error: elementHandle.click: Node is not an Element"** -- Switch from ElementHandle to Locator. Locators re-query the DOM on every action and never go stale.
- **"Error: locator.click: Timeout 30000ms exceeded"** -- Identify what is blocking the action using traces, then address it.
- **Navigation & Page Errors**
- **"page.goto: net::ERR_CONNECTION_REFUSED"** -- Use the `webServer` config option to let Playwright start and manage the dev server automatically.
- **"page.goto: Timeout 30000ms exceeded"** -- Use a more appropriate `waitUntil` option or increase the navigation timeout.
- **"Error: page.goto: Navigation failed because page was closed!"** -- Ensure cleanup only runs after all page operations complete. Use fixtures for lifecycle management instead of manual `afterEach`.
- **"page.waitForNavigation: Timeout 30000ms exceeded"** -- Replace `waitForNavigation()` with `waitForURL()` which works with both SPAs and traditional page loads.
- **"Error: frame.goto: Frame was detached"** -- Re-acquire the frame reference after the parent page updates.
- **Test Framework Errors**
- **"Error: Test timeout of 30000ms exceeded"** -- Identify the slow step using `test.step()` and traces, then either fix the root cause or adjust the timeout.
- **"Error: expect(received).toMatchSnapshot()"** -- Update the snapshot if the change is intentional, or mask/hide dynamic areas.
- **"Error: browserType.launch: Executable doesn't exist"** -- Install the browsers.
- **"Error: Cannot use import statement outside a module"** -- Ensure TypeScript is configured correctly and always run tests through the Playwright CLI.
- **"Error: fixture \"xxx\" has already been registered"** -- Ensure each fixture name is unique across your merged fixture chain. Use a single fixture file that combines all extensions.
- **Network & API Errors**
- **"page.route: Pattern should start with..."** -- Use the correct pattern format.
- **"Error: apiRequestContext.get: connect ECONNREFUSED"** -- Ensure the API server is running. Use `webServer` config to auto-start it, or add a health check.
- **"Request was not handled: GET https://..."** -- Ensure your route handler covers all expected requests, or let unhandled requests pass through.
- **Authentication & State Errors**
- **"Error: browserContext.storageState: No such file"** -- Ensure the auth setup runs first and the file path is consistent.
- **"Error: Target page, context or browser has been closed"** -- Never store page/context references in shared mutable state. Use Playwright fixtures for lifecycle management.
- **CI-Specific Errors**
- **"Error: browserType.launch: Browser closed unexpectedly"** -- Install OS-level dependencies and configure the environment.
- **"Error: Playwright Test needs to be invoked via 'npx playwright test'"** -- Always use the Playwright CLI to run tests.
- **Additional Common Errors**
- **"Error: page.evaluate: Execution context was destroyed"** -- Ensure the page is stable before evaluating.
- **"Error: page.screenshot: Cannot take a screenshot larger than..."** -- Clip the screenshot to a specific region or limit the viewport.
- **"Error: waiting for locator('...').toBeAttached()"** -- Verify the precondition for the element to render.
- **"Error: protocol error: Target.createTarget: Failed to create target"** -- Reduce parallelism, close unused contexts, or use fewer workers.
- **"Error: expect(locator).toHaveText() — expected string but received array"** -- Either narrow the locator to one element or use the array form of `toHaveText()`.
- **"Error: page.waitForSelector: Timeout 30000ms exceeded (deprecated)"** -- Replace `waitForSelector()` with locator-based assertions.
- **"Error: Test was expected to have a title matching /.../"** -- Ensure the page is fully loaded and use the correct expected value.
- **"Error: page.type: Element is not focusable"** -- Use `fill()` instead of `type()`. Only use `type()` when you specifically need to simulate individual keystrokes.
- **"Error: page.setInputFiles: Non-multiple file input can only accept single file"** -- Upload one file at a time, or ensure the input supports multiple files.
- **"Error: browser.newContext: Could not parse content-type application/json"** -- Delete the storage state file and regenerate it.
- **Quick Diagnostic Checklist** -- When you hit an error not listed above, run through this checklist:

## TypeScript patterns

### "locator.click: Target closed"

```typescript
// TypeScript — handle popup that closes itself
const popupPromise = page.waitForEvent('popup');
await page.getByRole('button', { name: 'Open popup' }).click();
const popup = await popupPromise;
await popup.waitForLoadState();
// interact with popup before it closes
await popup.getByRole('button', { name: 'Confirm' }).click();
```

### "waiting for locator('...') to be visible"

```typescript
// TypeScript — debug: check what the locator resolves to
console.log(await page.getByRole('button', { name: 'Submit' }).count());
// If 0, the element is not in the DOM — check your selector or page state

// Correct approach: wait for the data to load first
await page.waitForResponse(resp =>
  resp.url().includes('/api/data') && resp.status() === 200
);
await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
```
