import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// Criterio de la tarea 4.1: sin sesión, /admin lleva al login. La API igual rechaza con 401
// cualquier ruta de /api/admin/* sin cookie (lo prueban los tests de la API).
test("sin sesión, /admin redirige al login", async ({ page }) => {
  await page.goto("/admin");

  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toHaveAttribute("type", "password");
});

test("con sesión se entra al panel, y al cerrarla vuelve al login", async ({ page }) => {
  await loginAsAdmin(page);
  await expect(page).toHaveURL(/\/admin$/);

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/admin\/login$/);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/admin\/login$/);
});
