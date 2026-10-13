import { expect, test } from "@playwright/test";

// Un enlace con UTM (parámetros de origen del enlace): la página las pasa a `bootstrap`, que
// registra la visita con ellas, y al formulario de contacto, que las guarda con el mensaje.
// Que se guarden en la base lo prueban test_bootstrap.py y test_contact.py; aquí se prueba que
// el navegador las lee de la URL y las manda por el proxy hasta la API.
test("una visita con UTM llega a la API con su origen, también en el contacto", async ({
  page,
}) => {
  const campaign = `e2e-${String(Date.now())}`;
  // Se espera la respuesta y no el pedido: en desarrollo, React monta dos veces y el primer
  // pedido se cancela.
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
  // La API responde 201 solo después de guardar el mensaje (con sus UTM).
  expect(sent.status()).toBe(201);
  expect(sent.request().postDataJSON()).toMatchObject({
    utm_source: "e2e",
    utm_campaign: campaign,
  });
});
