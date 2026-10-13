import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// Criterio de la tarea 4.5: un mensaje y los conteos de una visita de prueba con UTM se ven en
// el panel. La visita y el mensaje van directo a la API (por el mismo proxy que usa la página),
// con UTM únicos por corrida para no confundirse con datos de otros tests.
test("el panel muestra un mensaje y la visita de un enlace con UTM", async ({ page }) => {
  const run = String(Date.now());
  const source = `e2e-${run}`;
  const campaign = `prueba-${run}`;
  const text = `Mensaje de prueba ${run}`;

  const visit = await page.request.get(
    `/api/bootstrap?utm_source=${source}&utm_campaign=${campaign}`,
  );
  expect(visit.status()).toBe(200);
  const contact = await page.request.post("/api/contact", {
    data: {
      name: "Prueba E2E",
      email: "e2e@example.com",
      message: text,
      lang: "es",
      utm_source: source,
      utm_campaign: campaign,
      website: "",
    },
  });
  expect(contact.status()).toBe(201);

  await loginAsAdmin(page);

  await page.getByRole("link", { name: "Visitas por enlace" }).click();
  await expect(page.getByRole("row", { name: `${source} ${campaign} 1 1` })).toBeVisible();

  await page.getByRole("link", { name: "Volver al panel" }).click();
  await page.getByRole("link", { name: "Mensajes" }).click();
  const message = page.locator("article", { hasText: text });
  await expect(message).toContainText(`${source} / ${campaign} · Nuevo`);
  await message.getByRole("button", { name: "Marcar como leído" }).click();
  await expect(message).toContainText("· Leído");
});
