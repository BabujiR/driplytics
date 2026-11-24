/**
 * End-to-end tests (P0-20) against the running Docker stack: sign in with Keycloak, upload an export,
 * read the import report, and run axe accessibility checks on the main pages.
 *
 *   .\tasks.ps1 e2e          (stack running: .\tasks.ps1 up)
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /.*\.e2e\.ts$/, // not *.test.ts, so vitest leaves these alone
  timeout: 180_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
