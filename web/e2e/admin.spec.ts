import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// Task 4.1 criterion: without a session, /admin leads to the login. The API (application
// programming interface) still rejects any /api/admin/* route without a cookie with 401 (the API
// tests cover that).
test("without a session, /admin redirects to the login", async ({ page }) => {
  await page.goto("/admin");

  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toHaveAttribute("type", "password");
});

test("with a session it enters the admin panel, and logging out goes back to the login", async ({
  page,
}) => {
  await loginAsAdmin(page);
  await expect(page).toHaveURL(/\/admin$/);

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/admin\/login$/);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/admin\/login$/);
});
