import { expect, test } from "@playwright/test";

test.describe("con el navegador en inglés", () => {
  test.use({ locale: "en-US" });

  test("la página sale en inglés", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Product" })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });

  test("el selector cambia el idioma y se recuerda al recargar", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Product" })).toBeVisible();

    await page.getByRole("button", { name: "Español" }).click();
    await expect(page.getByRole("heading", { name: "Producto" })).toBeVisible();

    await page.reload();
    await expect(page.getByRole("heading", { name: "Producto" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Español" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});

test.describe("con el navegador en español", () => {
  test.use({ locale: "es-CL" });

  test("la página sale en español", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Producto" })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
  });
});
