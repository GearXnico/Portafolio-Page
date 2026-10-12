import { expect, test } from "@playwright/test";

// El título depende del contenido cargado en la base, así que se revisa el idioma de la página
// y el selector, que no cambian con el contenido.
test.describe("con el navegador en inglés", () => {
  test.use({ locale: "en-US" });

  test("la página sale en inglés", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });

  test("el selector cambia el idioma y se recuerda al recargar", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");

    await page.getByRole("button", { name: "Español" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "es");

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
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

    await expect(page.getByRole("button", { name: "Español" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
  });
});
