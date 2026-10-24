import { expect, test } from "@playwright/test";

test("the page loads its content from bootstrap", async ({ page }) => {
  // The bootstrap response proves the full path: page → proxy → API → database.
  const bootstrap = page.waitForResponse("**/api/bootstrap");
  await page.goto("/");

  expect((await bootstrap).ok()).toBe(true);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("on a phone the page doesn't overflow the screen", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);
});

test("the page follows the device's light or dark theme", async ({ page }) => {
  const background = () =>
    page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);

  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(await background()).toBe("rgb(255, 255, 255)");

  await page.emulateMedia({ colorScheme: "dark" });
  expect(await background()).toBe("rgb(22, 23, 26)");
});
