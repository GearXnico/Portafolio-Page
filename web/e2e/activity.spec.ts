import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// Task 4.5 criterion: a message and the counts of a test visit with UTM (Urchin Tracking Module)
// parameters show up in the admin panel. The visit and the message go straight to the API
// (application programming interface) (through the same proxy the page uses), with UTM values
// unique per run so they aren't confused with data from other tests.
test("the admin panel shows a message and the visit from a UTM link", async ({ page }) => {
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
