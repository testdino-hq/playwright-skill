# Docker and Containers

> **When to use**: Run Playwright in a reproducible Linux environment locally or in CI.

## Rules

- Match the container's Playwright version to `@playwright/test`.
- Pin production images by digest.
- Run tests as a non-root user where practical.
- Use `--init` so browser child processes are reaped.
- Provide adequate `/dev/shm`; avoid unexplained browser crashes.
- Mount only required directories and never bake secrets into images.

## Dockerfile

```dockerfile
FROM mcr.microsoft.com/playwright:<matching-version>@sha256:<reviewed-digest>

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY playwright.config.ts ./
COPY tests ./tests

ENV CI=true
CMD ["npx", "playwright", "test"]
```

Use a `.dockerignore` for `.git`, `node_modules`, reports, traces, auth state, and local secrets.

## Build and run

```bash
docker build -t app-e2e .
docker run --rm --init --shm-size=2gb \
  -e BASE_URL=http://host.docker.internal:3000 \
  -v "$PWD/artifacts:/app/artifacts" \
  app-e2e
```

On Linux, use an explicit host mapping or a Docker network instead of assuming `host.docker.internal`.

## Docker Compose

```yaml
services:
  app:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 5s
      timeout: 2s
      retries: 20

  e2e:
    image: mcr.microsoft.com/playwright:<matching-version>@sha256:<reviewed-digest>
    init: true
    shm_size: 2gb
    working_dir: /work
    volumes:
      - .:/work
    environment:
      CI: "true"
      BASE_URL: http://app:3000
    depends_on:
      app:
        condition: service_healthy
    command: ["npx", "playwright", "test"]
```

Use Compose service names such as `app`, not `localhost`.

## TypeScript configuration

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  workers: process.env.CI ? '50%' : undefined,
  use: {
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  outputDir: 'artifacts/test-results',
  reporter: [['html', { outputFolder: 'artifacts/report', open: 'never' }]],
});
```

## Security

- Pass secrets at runtime through the CI secret store.
- Treat reports, screenshots, videos, and traces as sensitive.
- Avoid privileged containers and host socket mounts.
- Scan and update base images through a reviewed process.
- Do not publish images containing storage state or test-user data.

## Troubleshooting

| Symptom | Action |
|---|---|
| Browser executable missing | Align package and image versions |
| Browser closes unexpectedly | Increase shared memory and reduce workers |
| App unavailable | Check binding, network, health, and service hostname |
| Files owned by root | Run with a mapped user or correct output ownership |
| No artifacts | Mount the configured output directory |

## Related guides

- [GitHub Actions](ci-github-actions.md)
- [GitLab CI](ci-gitlab.md)
- [Other CI providers](ci-other.md)
- [Reporting and artifacts](reporting-and-artifacts.md)
