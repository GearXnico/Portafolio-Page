import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// A profile change made in the admin panel shows up on the public page.
test("a profile change in the admin panel shows up on the page", async ({ page }) => {
  const headline = `Titular de prueba ${String(Date.now())}`;
  await loginAsAdmin(page);

  await page.getByRole("link", { name: "Perfil" }).click();
  await page.getByLabel("Titular · Español").fill(headline);
  await page.getByLabel("Titular · English").fill("Test headline");
  await page.getByLabel("Presentación · Español").fill("Presentación de prueba.");
  await page.getByLabel("Presentación · English").fill("Test about.");
  await page.getByLabel("Correo de contacto (no se muestra en la página)").fill("e2e@example.com");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("status")).toBeVisible();

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: headline })).toBeVisible();
});
