import { expect, test } from "@playwright/test";

test("la página abre y la API responde ok", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Producto" })).toBeVisible();
  // "ok" prueba el camino completo: página → proxy → API → base.
  await expect(page.getByTestId("api-status")).toHaveText("ok");
});
