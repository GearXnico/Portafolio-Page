import { expect, type Page } from "@playwright/test";

// Test admin credentials. In CI each run generates them (ci.yml); locally, it uses the ones in your
// .env. Without them the test fails with this message instead of being skipped.
function adminCredentials(): { email: string; password: string } {
  const email = process.env.E2E_ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD;
  if (!email || !password) {
    throw new Error(
      "E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD are required to log in to the admin panel.",
    );
  }
  return { email, password };
}

/** Logs in to the admin panel as the test admin and waits for the home screen to load. */
export async function loginAsAdmin(page: Page): Promise<void> {
  const { email, password } = adminCredentials();
  await page.goto("/admin/login");
  await page.getByLabel("Correo").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Panel de administración" })).toBeVisible();
}
