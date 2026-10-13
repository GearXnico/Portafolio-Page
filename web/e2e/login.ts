import { expect, type Page } from "@playwright/test";

// Credenciales del admin de prueba. En el CI las genera cada corrida (ci.yml); en local, usa
// las de tu .env. Sin ellas el test falla con este mensaje en vez de saltarse.
function adminCredentials(): { email: string; password: string } {
  const email = process.env.E2E_ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD;
  if (!email || !password) {
    throw new Error("Faltan E2E_ADMIN_EMAIL y E2E_ADMIN_PASSWORD para entrar al panel.");
  }
  return { email, password };
}

/** Entra al panel con el admin de prueba y espera a que cargue el inicio. */
export async function loginAsAdmin(page: Page): Promise<void> {
  const { email, password } = adminCredentials();
  await page.goto("/admin/login");
  await page.getByLabel("Correo").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Panel de administración" })).toBeVisible();
}
