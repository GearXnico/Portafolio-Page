import { expect, test } from "@playwright/test";

// A link with UTM: the page passes them to `bootstrap`, which records the visit with them, and to
// the contact form, which saves them with the message. test_bootstrap.py and test_contact.py prove
// they are saved in the database; this test proves the browser reads them from the URL and sends
// them through the proxy to the API.
test("a visit with UTM reaches the API with its source, also in the contact form", async ({
  page,
}) => {
  const campaign = `e2e-${String(Date.now())}`;
  // Waits for the response, not the request: in development, React mounts twice and the first
  // request is cancelled.
  const bootstrap = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/bootstrap");
  await page.goto(`/?utm_source=e2e&utm_medium=test&utm_campaign=${campaign}`);

  const visit = await bootstrap;
  expect(visit.status()).toBe(200);
  expect(Object.fromEntries(new URL(visit.url()).searchParams)).toMatchObject({
    utm_source: "e2e",
    utm_medium: "test",
    utm_campaign: campaign,
  });

  const form = page.locator("#contact form");
  await form.getByLabel("Nombre").fill("Prueba UTM");
  await form.getByLabel("Correo").fill("e2e@example.com");
  await form.getByLabel("Mensaje").fill(`Mensaje con UTM ${campaign}`);
  const contact = page.waitForResponse(
    (r) => r.url().endsWith("/api/contact") && r.request().method() === "POST",
  );
  await form.getByRole("button", { name: "Enviar" }).click();

  const sent = await contact;
  // The API responds 201 only after saving the message (with its UTM parameters).
  expect(sent.status()).toBe(201);
  expect(sent.request().postDataJSON()).toMatchObject({
    utm_source: "e2e",
    utm_campaign: campaign,
  });
});
