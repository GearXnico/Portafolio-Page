import { expect, test } from "@playwright/test";

// The title depends on the content loaded in the database, so the test checks the page language
// and the switcher, which don't change with the content.
test.describe("with the browser in English", () => {
  test.use({ locale: "en-US" });

  test("the page renders in English", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    // Ends the same with or without a loaded profile ("<headline> · Portfolio" or "Portfolio").
    await expect(page).toHaveTitle(/Portfolio$/);
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /^Portfolio/);
  });

  test("the switcher changes the language and it is remembered on reload", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");

    await page.getByRole("button", { name: "Español" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
    await expect(page).toHaveTitle(/Portafolio$/);

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
    await expect(page.getByRole("button", { name: "Español" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});

test.describe("with the browser in Spanish", () => {
  test.use({ locale: "es-CL" });

  test("the page renders in Spanish", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("button", { name: "Español" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("html")).toHaveAttribute("lang", "es");
  });
});
