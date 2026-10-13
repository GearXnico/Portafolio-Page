import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// Criterio de la tarea 4.2: un proyecto creado desde el panel se ve en la página pública.
test("un proyecto creado en el panel se ve en la página pública", async ({ page }) => {
  // Slug y título únicos, para poder correr el test varias veces sobre la misma base.
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

  // Limpieza aunque falle una aserción: la sesión del panel sigue en las cookies del navegador.
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
