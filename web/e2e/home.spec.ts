import { expect, test } from "@playwright/test";

test("la página carga su contenido desde bootstrap", async ({ page }) => {
  // La respuesta de bootstrap prueba el camino completo: página → proxy → API → base.
  const bootstrap = page.waitForResponse("**/api/bootstrap");
  await page.goto("/");

  expect((await bootstrap).ok()).toBe(true);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("en un celular la página no se sale de la pantalla", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);
});
