import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://localhost:5173",
    browserName: "chromium",
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  },
  // Предусловие: запущены API (localhost:8000 + seeded DB) и `npm run dev`.
  // Локально: make dev в другом терминале. В CI — см. .github/workflows/ci.yml.
});
