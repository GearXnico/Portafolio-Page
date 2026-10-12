import { expect, test } from "@playwright/test";

// Recorre el camino completo: formulario → proxy → API → base. La API responde 201 solo
// después de guardar el mensaje (test_contact.py lo comprueba contra la base), así que un 201
// aquí significa que el mensaje quedó en la base.
test("un mensaje enviado desde el formulario llega a la API y se guarda", async ({ page }) => {
  await page.goto("/");

  const form = page.locator("#contact form");
  await form.getByLabel("Nombre").fill("Prueba E2E");
  await form.getByLabel("Correo").fill("e2e@example.com");
  await form.getByLabel("Mensaje").fill(`Mensaje de prueba ${String(Date.now())}`);

  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/contact") && r.request().method() === "POST",
  );
  await form.getByRole("button", { name: "Enviar" }).click();

  expect((await response).status()).toBe(201);
  await expect(form.getByRole("status")).toContainText("Tu mensaje llegó");
  await expect(form.getByLabel("Mensaje")).toHaveValue("");
});
