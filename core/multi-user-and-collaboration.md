# Multi-User and Collaboration Testing

> **When to use**: When your application involves real-time collaboration, multi-user workflows, or any scenario where two or more users interact with the same resource simultaneously -- chat apps, shared documents, multiplayer features, admin-and-user flows.
> **Prerequisites**: [core/fixtures-and-hooks.md](fixtures-and-hooks.md), [core/configuration.md](configuration.md)

## Topic map

- **Two Users in One Test via Browser Contexts** -- You need to verify that actions by one user are visible to another in real time.
- **Multi-User Fixture for Reusability** -- Multiple tests need two-user setups. Wrap context creation in a fixture to avoid boilerplate.
- **Collaborative Editing with Conflict Detection** -- Testing real-time collaborative editors (Google Docs-style) where both users edit the same content.
- **Shared State Verification (Presence, Cursors, Indicators)** -- Verifying that one user's presence or activity is reflected in the other user's UI -- online indicators, typing indicators, cursor positions.
- **Race Condition Testing Between Users** -- You need to verify that simultaneous actions (two users clicking "buy" on the last item, or two users editing the same field) are handled correctly.
- **N Users with Dynamic Context Creation** -- You need more than two users, or the number of users is variable (load-like collaboration tests).

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Two users interact in real time | Two `browser.newContext()` in one test | Fully isolated sessions, same test timeline |
| Same multi-user setup across many tests | Custom fixture per user context | Eliminates boilerplate, guarantees cleanup |
| Testing presence/typing indicators | Sequential actions, assert on other page | Order matters -- act on one, assert on the other |
| Race condition (simultaneous clicks) | `Promise.all([action1, action2])` | Fires both as close to simultaneously as possible |
| Admin performs action, user sees result | Two contexts with different `storageState` | Different auth roles, same browser instance |
| 3+ users in one test | Loop with `browser.newContext()` per user | Each context is cheap; browser is shared |
| Cross-browser multi-user (Chrome + Firefox) | Separate browser launches in `beforeAll` | Rarely needed; contexts within one browser suffice |

## TypeScript patterns

### Quick Reference

```typescript
// Two independent browser contexts in one test = two users
const alice = await browser.newContext({ storageState: 'auth/alice.json' });
const bob = await browser.newContext({ storageState: 'auth/bob.json' });
const alicePage = await alice.newPage();
const bobPage = await bob.newPage();

// Each operates independently — different cookies, sessions, localStorage
await alicePage.goto('/chat/room-1');
await bobPage.goto('/chat/room-1');
```

### Two Users in One Test via Browser Contexts

```typescript
import { test, expect } from '@playwright/test';

test('alice sends a message and bob sees it', async ({ browser }) => {
  // Create two isolated contexts
  const aliceContext = await browser.newContext({ storageState: 'auth/alice.json' });
  const bobContext = await browser.newContext({ storageState: 'auth/bob.json' });

  const alicePage = await aliceContext.newPage();
  const bobPage = await bobContext.newPage();

  // Both navigate to the same chat room
  await alicePage.goto('/chat/general');
  await bobPage.goto('/chat/general');

  // Alice sends a message
  await alicePage.getByRole('textbox', { name: 'Message' }).fill('Hello Bob!');
  await alicePage.getByRole('button', { name: 'Send' }).click();

  // Bob sees it in real time
  await expect(bobPage.getByText('Hello Bob!')).toBeVisible();

  // Alice also sees her own message
  await expect(alicePage.getByText('Hello Bob!')).toBeVisible();

  // Cleanup
  await aliceContext.close();
  await bobContext.close();
});
```

## Guardrails

- **Two Users in One Test via Browser Contexts:** You only need to test a single user's flow. One context per test is the default.
- **Multi-User Fixture for Reusability:** Only one test needs multi-user logic.
- **Collaborative Editing with Conflict Detection:** Your app does not support concurrent editing.
- **Shared State Verification (Presence, Cursors, Indicators):** Presence is not a feature of your app.
- **Race Condition Testing Between Users:** Your app has no shared mutable resources.
- **N Users with Dynamic Context Creation:** Two users suffice. Keep it simple.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) -- wrap multi-user contexts in fixtures
- [core/websockets-and-realtime.md](websockets-and-realtime.md) -- test the transport layer beneath collaboration features
- [core/test-data-management.md](test-data-management.md) -- set up shared resources (rooms, documents) before multi-user tests
- [core/configuration.md](configuration.md) -- configure `storageState` per project for different user roles
