import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// A project created from the admin panel shows up on the public page.
test("a project created in the admin panel shows up on the public page", async ({ page }) => {
  // Unique slug and title, so the test can run several times against the same database.
  const id = String(Date.now());
  await loginAsAdmin(page);

  await page.getByRole("link", { name: "Proyectos" }).click();
  await page.getByRole("link", { name: "Nuevo proyecto" }).click();
  const spanish = page.getByRole("group", { name: "Español" });
  await spanish.getByLabel("Título").fill(`Proyecto E2E ${id}`);
  await spanish.getByLabel("Resumen").fill("Creado por la prueba de punta a punta");
  const english = page.getByRole("group", { name: "English" });
  await english.getByLabel("Título").fill(`E2E project ${id}`);
  await english.getByLabel("Resumen").fill("Created by the end-to-end test");
  await page.getByLabel(/^Slug/).fill(`e2e-${id}`);
  await page.getByLabel(/^Stack/).fill("Playwright, FastAPI");
  await page.getByLabel("Visible en la página").check();
  const created = page.waitForResponse(
    (r) => r.url().endsWith("/api/admin/projects") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Guardar" }).click();
  const { id: projectId } = (await (await created).json()) as { id: number };

  // Cleanup even if an assertion fails: the admin panel session is still in the browser cookies.
  try {
    await expect(page.getByRole("link", { name: `Proyecto E2E ${id}` })).toBeVisible();

    await page.goto("/");
    const card = page.locator("#projects article", { hasText: `Proyecto E2E ${id}` });
    await expect(card).toBeVisible();
    await expect(card.getByText("Playwright")).toBeVisible();
  } finally {
    expect((await page.request.delete(`/api/admin/projects/${String(projectId)}`)).status()).toBe(
      204,
    );
  }
});
