import { expect, test } from "@playwright/test";

import { contentSecurityPolicy, securityHeaders } from "../security-headers";

test("la página responde con las cabeceras de seguridad", async ({ request }) => {
  const response = await request.get("/");

  expect(response.ok()).toBe(true);
  const headers = response.headers();
  for (const [name, value] of Object.entries(securityHeaders)) {
    expect(headers[name.toLowerCase()], name).toBe(value);
  }
  // La CSP solo va en el build (vite preview y producción); si está, tiene que ser la definida.
  const csp = headers["content-security-policy"];
  if (csp !== undefined) expect(csp).toBe(contentSecurityPolicy);
});

// También detecta lo que la CSP bloquee, porque el navegador lo informa como error en la consola.
test("la página no muestra errores en la consola", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  expect(errors).toEqual([]);
});
