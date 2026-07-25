# Test Data Management

> **When to use**: Every test that interacts with data — user accounts, form inputs, entities, or any state that must exist before assertions run.

## Topic map

- **Inline Test Data** -- The data is simple, unique to one test, and essential for understanding the assertion.
- **Factory Functions** -- Multiple tests need the same data shape with different values, or you need guaranteed uniqueness.
- **Faker / Random Data** -- You need realistic-looking data (names, addresses, phone numbers) or want to discover edge cases through randomness.
- **Builder Pattern** -- Objects have many optional fields, conditional logic, or multiple valid configurations. Common for product listings, user profiles, or form payloads with nested data.
- **API Seeding** -- Tests need entities to already exist (users, products, orders) and the app exposes APIs to create them. This is the default strategy for test data setup.
- **Database Seeding** -- No API exists for the data you need, you need bulk data, or you need to set up complex relational state that is cumbersome via API calls.
- **Storage State** -- Multiple tests need an authenticated session and you want to avoid logging in via the UI in every test.
- **Test Data Cleanup** -- Always. Every test that creates data must clean it up.
- **Environment-Specific Data** -- Tests run against multiple environments (dev, staging, production-mirror) with different base URLs, credentials, or data constraints.
- **Fixtures for Test Data** -- Test data setup and teardown should be encapsulated, reusable, and guaranteed to clean up. This is the recommended pattern for all non-trivial test data.
- **Speed ranking (fastest to slowest)** -- 1. Inline data / factories / faker — no I/O, instant
- **Isolation ranking (most to least isolated)** -- 1. Test-scoped fixtures with API teardown — each test gets fresh data, cleaned up after
- **Shared mutable data across tests** -- Fix: Use test-scoped fixtures. Each test gets its own instance.
- **Hardcoded IDs** -- Fix: Create the product in a fixture and use the returned ID.
- **No cleanup** -- Fix: Always pair creation with deletion in a fixture teardown.
- **Relying on pre-existing database state** -- Fix: Seed the plan via API or database fixture before the test.
- **Using production data in tests** -- Fix: Create synthetic test data. Never point test suites at production databases or use real customer identifiers.
- **Over-engineering data setup** -- Fix: A factory function and a fixture cover 95% of cases. Add complexity only when you have a proven need.
- **Making cleanup resilient**

## Decision table

| Strategy | Speed | Isolation | Complexity | Best For |
|---|---|---|---|---|
| Inline data | Instant | Perfect | None | Simple value checks, form inputs |
| Factory functions | Instant | Perfect | Low | Unique identifiers, consistent shapes |
| Faker/random data | Instant | Perfect | Low | Realistic fields, edge-case discovery |
| Builder pattern | Instant | Perfect | Medium | Complex objects with many optional fields |
| API seeding | Fast | Perfect | Medium | Creating entities the app depends on |
| Database seeding | Fast | Good | High | Complex relational data, bulk setup |
| Storage state | Fast | Good | Low | Reusing authenticated sessions |
| Fixture-based setup | Fast | Perfect | Medium | Encapsulating setup + guaranteed teardown |

## TypeScript patterns

### Inline Test Data

```typescript
// tests/contact-form.spec.ts
import { test, expect } from '@playwright/test';

test('submits contact form with valid data', async ({ page }) => {
  const name = 'Ada Lovelace';
  const email = `ada-${Date.now()}@example.com`;
  const message = 'Inquiry about analytics engine';

  await page.goto('/contact');
  await page.getByLabel('Name').fill(name);
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Message').fill(message);
  await page.getByRole('button', { name: 'Send' }).click();

  await expect(page.getByText('Thank you, Ada Lovelace')).toBeVisible();
});
```

### Factory Functions

```typescript
// tests/factories/user.factory.ts
export interface UserData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

let counter = 0;

export function createUserData(overrides: Partial<UserData> = {}): UserData {
  counter++;
  const id = `${Date.now()}-${counter}`;
  return {
    firstName: `Test`,
    lastName: `User${id}`,
    email: `testuser-${id}@example.com`,
    password: 'SecureP@ss123!',
    ...overrides,
  };
}
```

## Guardrails

- **Inline Test Data:** The same data shape repeats across many tests — extract a factory instead.
- **Factory Functions:** The data is trivial and only used once — inline it instead.
- **Faker / Random Data:** Debugging a failure — use a fixed seed to make it reproducible.
- **Builder Pattern:** The object has fewer than 5 fields — a factory with overrides is simpler.
- **API Seeding:** No API exists for the entity, or the API itself is what you are testing (use the UI or database instead).
- **Database Seeding:** An API exists — API seeding is more maintainable and exercises real application logic. Database seeding couples tests to schema details.
- **Storage State:** The test is specifically testing the login flow itself.
- **Test Data Cleanup:** Never. Skipping cleanup causes cascading failures in subsequent runs.

## Related guides

- [core/fixtures-and-hooks.md](fixtures-and-hooks.md) — fixture mechanics, scoping, composition
- [core/authentication.md](authentication.md) — storage state setup, multi-role auth patterns
- [core/api-testing.md](api-testing.md) — API request context, response validation
- [ci/global-setup-teardown.md](../ci/global-setup-teardown.md) — global setup/teardown for batch operations
- [pom/pom-vs-fixtures-vs-helpers.md](../pom/pom-vs-fixtures-vs-helpers.md) — when to use fixtures vs page objects vs helpers
