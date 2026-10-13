import { defineConfig, devices } from "@playwright/test";

// E2E (end-to-end tests): opens the page in a real browser.
// Uses the server that is already running (for example, the compose one) or starts `npm run dev`.
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  // Spanish browser by default; the language tests change the locale.
  use: { baseURL, locale: "es-CL", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: baseURL,
    reuseExistingServer: true,
  },
});
