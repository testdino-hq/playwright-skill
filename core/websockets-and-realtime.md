# WebSockets and Real-Time Testing

> **When to use**: When your application uses WebSockets, Server-Sent Events (SSE), or polling for real-time features -- chat, live dashboards, notifications, collaborative editing, stock tickers, live sports scores.
> **Prerequisites**: [core/assertions-and-waiting.md](assertions-and-waiting.md), [core/fixtures-and-hooks.md](fixtures-and-hooks.md)

## Topic map

- **Observing WebSocket Traffic** -- You need to verify that your app sends and receives the correct WebSocket messages without modifying them.
- **Waiting for a Specific WebSocket Message** -- Your test depends on a particular server-pushed message before proceeding.
- **Mocking WebSocket Messages with `routeWebSocket`** -- Your client negotiates a WebSocket subprotocol (e.g. `graphql-transport-ws`, `wamp`, a versioned protocol string) and you want to assert it sent the right one, or branch your mock based on it.
- **Forwarding with Modification (Man-in-the-Middle)** -- You want to connect to the real server but intercept, modify, or inject messages.
- **Server-Sent Events (SSE) Testing** -- Your app uses `EventSource` for server-to-client streaming (live logs, progress updates, news feeds).
- **Polling-Based Real-Time Testing** -- Your app uses HTTP polling (setInterval + fetch) instead of WebSockets or SSE.
- **WebSocket Connection Lifecycle** -- You need to verify that your app handles connection, disconnection, and reconnection properly.

## Decision table

| Scenario | Approach | Why |
|---|---|---|
| Verify app sends correct WS message | `page.on('websocket')` + `ws.on('framesent')` | Observe without intercepting |
| Verify app handles server push | `page.routeWebSocket()` with mock server | Full control over what the "server" sends |
| Test with real server but inject messages | `routeWebSocket` + `connectToServer()` | Man-in-the-middle: forward real traffic plus inject extras |
| Test SSE endpoint | `page.route()` with `text/event-stream` content type | SSE is HTTP -- standard route interception works |
| Test HTTP polling | `page.route()` with changing responses per call | Increment a counter; return different data each call |
| Verify reconnection logic | `routeWebSocket` that closes the first connection | Simulate server failure, verify the app retries |
| Test binary WebSocket data | `ws.on('framereceived')`, check `frame.payload` as Buffer | Binary frames arrive as `Buffer` in Node.js |

## TypeScript patterns

### Quick Reference

```typescript
// Listen for WebSocket connections
page.on('websocket', (ws) => {
  console.log('WebSocket opened:', ws.url());

  ws.on('framesent', (frame) => console.log('Sent:', frame.payload));
  ws.on('framereceived', (frame) => console.log('Received:', frame.payload));
  ws.on('close', () => console.log('WebSocket closed'));
});

// Mock a WebSocket via route (Playwright 1.48+)
await page.routeWebSocket('**/ws', (ws) => {
  ws.onMessage((message) => {
    ws.send(JSON.stringify({ echo: message }));
  });
});
```

### Observing WebSocket Traffic

```typescript
import { test, expect } from '@playwright/test';

test('chat message is sent over WebSocket', async ({ page }) => {
  const messages: { direction: string; payload: string }[] = [];

  page.on('websocket', (ws) => {
    ws.on('framesent', (frame) => {
      messages.push({ direction: 'sent', payload: String(frame.payload) });
    });
    ws.on('framereceived', (frame) => {
      messages.push({ direction: 'received', payload: String(frame.payload) });
    });
  });

  await page.goto('/chat');
  await page.getByRole('textbox', { name: 'Message' }).fill('Hello!');
  await page.getByRole('button', { name: 'Send' }).click();

  // Wait for the message to appear in UI (confirms round-trip)
  await expect(page.getByText('Hello!')).toBeVisible();

  // Verify WebSocket traffic
  const sentMessage = messages.find(
    (m) => m.direction === 'sent' && m.payload.includes('Hello!')
  );
  expect(sentMessage).toBeDefined();
});
```

## Guardrails

- **Observing WebSocket Traffic:** You need to intercept or mock the messages. Use `routeWebSocket` instead.
- **Waiting for a Specific WebSocket Message:** The UI already reflects the message. Assert on the UI instead.
- **Mocking WebSocket Messages with `routeWebSocket`:** Your app doesn't use subprotocols — there's nothing to inspect.
- **Forwarding with Modification (Man-in-the-Middle):** Full mocking (`routeWebSocket` without `connectToServer`) is sufficient.
- **Server-Sent Events (SSE) Testing:** The app uses WebSockets. SSE is HTTP-based and intercepted differently.
- **Polling-Based Real-Time Testing:** The app uses WebSockets or SSE -- use the patterns above.
- **WebSocket Connection Lifecycle:** Connection lifecycle is not user-visible.

## Related guides

- [core/multi-user-and-collaboration.md](multi-user-and-collaboration.md) -- multi-user tests that rely on WebSocket for real-time sync
- [core/assertions-and-waiting.md](assertions-and-waiting.md) -- auto-retrying assertions for async UI updates
- [core/when-to-mock.md](when-to-mock.md) -- deciding when to mock WebSocket vs use real server
- [core/debugging.md](debugging.md) -- tracing WebSocket frames in Playwright traces
