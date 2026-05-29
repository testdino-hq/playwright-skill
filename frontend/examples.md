# Framework Patterns for `data-testid`

Copy-paste patterns for placing valid, unique, stable `data-testid` attributes. Follow the naming and stability rules in [data-testid-conventions.md](data-testid-conventions.md).

---

## React / JSX

```jsx
// Semantic markup FIRST (getByRole works), test IDs for durable handles.
function LoginForm({ onSubmit }) {
  return (
    <form data-testid="login-form" onSubmit={onSubmit}>
      <label htmlFor="email">Email</label>
      <input id="email" type="email" data-testid="login-form-email-input" />
      <p role="alert" data-testid="login-form-email-error" />

      <label htmlFor="password">Password</label>
      <input id="password" type="password" data-testid="login-form-password-input" />

      <button type="submit" data-testid="login-form-submit-button">
        Sign in
      </button>
    </form>
  );
}
```

Lists — stable entity key, never the index:

```jsx
function UserTable({ users }) {
  return (
    <table data-testid="users-table">
      <tbody>
        {users.map((user) => (
          <tr key={user.id} data-testid={`user-row-${user.id}`}>
            <td data-testid={`user-row-${user.id}-name`}>{user.name}</td>
            <td>
              <button data-testid={`user-row-${user.id}-delete-button`}>
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

Custom no-role widget — add ARIA *and* a test ID:

```jsx
function ColorSwatch({ color, selected, onSelect }) {
  return (
    <div
      role="button"
      aria-pressed={selected}
      aria-label={`Select ${color}`}
      tabIndex={0}
      data-testid={`color-swatch-${color}`}
      onClick={onSelect}
    />
  );
}
```

---

## Vue 3 (SFC)

```vue
<template>
  <form data-testid="login-form" @submit.prevent="onSubmit">
    <label for="email">Email</label>
    <input id="email" v-model="email" data-testid="login-form-email-input" />

    <button type="submit" data-testid="login-form-submit-button">Sign in</button>
  </form>

  <ul data-testid="users-list">
    <li
      v-for="user in users"
      :key="user.id"
      :data-testid="`user-row-${user.id}`"
    >
      {{ user.name }}
      <button :data-testid="`user-row-${user.id}-delete-button`">Delete</button>
    </li>
  </ul>
</template>
```

> Note: static IDs use `data-testid="..."`, dynamic ones use the bound form `:data-testid="..."`.

---

## Angular

```html
<form data-testid="login-form" (ngSubmit)="onSubmit()">
  <label for="email">Email</label>
  <input id="email" [(ngModel)]="email" data-testid="login-form-email-input" />

  <button type="submit" data-testid="login-form-submit-button">Sign in</button>
</form>

<ul data-testid="users-list">
  <li *ngFor="let user of users; trackBy: trackById"
      [attr.data-testid]="'user-row-' + user.id">
    {{ user.name }}
    <button [attr.data-testid]="'user-row-' + user.id + '-delete-button'">
      Delete
    </button>
  </li>
</ul>
```

> Use `[attr.data-testid]="..."` for dynamic values (Angular needs `attr.` to bind to a real DOM attribute). Static values can stay as plain `data-testid="..."`. Pair `*ngFor` with a `trackBy` keyed on the same entity id.

---

## Svelte

```svelte
<form data-testid="login-form" on:submit|preventDefault={onSubmit}>
  <label for="email">Email</label>
  <input id="email" bind:value={email} data-testid="login-form-email-input" />

  <button type="submit" data-testid="login-form-submit-button">Sign in</button>
</form>

<ul data-testid="users-list">
  {#each users as user (user.id)}
    <li data-testid={`user-row-${user.id}`}>
      {user.name}
      <button data-testid={`user-row-${user.id}-delete-button`}>Delete</button>
    </li>
  {/each}
</ul>
```

---

## Centralizing test IDs

Share one source of truth between the app and the test suite so renames are a single edit and typos are caught by the compiler.

```ts
// testIds.ts (imported by both components and tests)
export const testIds = {
  loginForm: {
    root: 'login-form',
    email: 'login-form-email-input',
    password: 'login-form-password-input',
    submit: 'login-form-submit-button',
  },
  userRow: (id: string | number) => `user-row-${id}`,
  userRowDelete: (id: string | number) => `user-row-${id}-delete-button`,
} as const;
```

```jsx
import { testIds } from './testIds';

<button data-testid={testIds.loginForm.submit}>Sign in</button>
{users.map((u) => (
  <tr data-testid={testIds.userRow(u.id)} key={u.id}>
    <button data-testid={testIds.userRowDelete(u.id)}>Delete</button>
  </tr>
))}
```

```ts
// In the test — same constants, no magic strings.
import { testIds } from '../src/testIds';
await page.getByTestId(testIds.loginForm.submit).click();
await page.getByTestId(testIds.userRowDelete(42)).click();
```

---

## Production stripping (optional)

Only if your team decides test IDs shouldn't ship to real production. **Keep them in dev, CI, and staging** — those are the environments tests and agents run against.

React (Babel) — `.babelrc` for production builds only:

```json
{
  "env": {
    "production": {
      "plugins": [
        ["react-remove-properties", { "properties": ["data-testid"] }]
      ]
    }
  }
}
```

Next.js — `next.config.js`:

```js
module.exports = {
  compiler: {
    // Strips in production builds; leaves dev/test untouched.
    reactRemoveProperties: process.env.NODE_ENV === 'production',
  },
};
```

Vue/Vite — strip via a build-time transform (e.g. a custom plugin or `@vue/compiler-sfc` node transform) gated on `mode === 'production'`. Verify your staging/CI build does **not** strip, or your suite will lose every locator.

> Decision guide: stripping reduces payload and hides internals, but adds build complexity and a foot-gun (stripping the wrong env breaks all tests). Many teams simply ship `data-testid` — it's a few bytes and harmless. Strip only when there's a concrete reason.
