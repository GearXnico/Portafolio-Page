import { expect, test } from "@playwright/test";

// Walks the full path: form → proxy → API (application programming interface) → database. The
// API responds 201 only after saving the message (test_contact.py checks it against the
// database), so a 201 here means the message was stored in the database.
test("a message sent from the form reaches the API and is saved", async ({ page }) => {
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
