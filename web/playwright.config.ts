import { defineConfig, devices } from "@playwright/test";

// E2E (prueba de punta a punta): abre la página en un navegador real.
// Usa el servidor que ya esté corriendo (por ejemplo, el del compose) o levanta `npm run dev`.
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  // Navegador en español por defecto; los tests de idioma cambian el locale.
  use: { baseURL, locale: "es-CL", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: baseURL,
    reuseExistingServer: true,
  },
});
