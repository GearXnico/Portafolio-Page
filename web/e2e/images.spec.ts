import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// PNG de 1×1 px: la API lo vuelve a codificar como WebP.
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64",
);

// Criterio de la tarea 4.3: una captura subida desde el formulario se ve en la página pública.
test("una captura subida en el panel se ve en la página pública", async ({ page }) => {
  const id = String(Date.now());
  await loginAsAdmin(page);
  // El proyecto se crea por la API (la 4.2 ya prueba el formulario); la sesión va en las cookies.
  const created = await page.request.post("/api/admin/projects", {
    data: {
      slug: `e2e-captura-${id}`,
      title_es: `Captura E2E ${id}`,
      title_en: `Screenshot E2E ${id}`,
      summary_es: "Proyecto de la prueba de capturas",
      summary_en: "Screenshot test project",
      visible: true,
    },
  });
  expect(created.status()).toBe(201);
  const { id: projectId } = (await created.json()) as { id: number };

  try {
    await page.goto(`/admin/projects/${String(projectId)}`);
    const section = page.getByRole("region", { name: "Capturas" });
    await section.getByLabel(/^Imagen/).setInputFiles({
      name: "captura.png",
      mimeType: "image/png",
      buffer: PNG,
    });
    await section.getByLabel("Texto alternativo en español").fill("Captura de prueba");
    await section.getByLabel("Texto alternativo en inglés").fill("Test screenshot");
    await section.getByRole("button", { name: "Subir captura" }).click();
    await expect(section.getByRole("img", { name: "Captura de prueba" })).toBeVisible();

    await page.goto("/");
    const card = page.locator("#projects article", { hasText: `E2E ${id}` });
    const image = card.getByRole("img", { name: /Captura de prueba|Test screenshot/ });
    await expect(image).toHaveAttribute("src", /^\/media\/projects\/.+\.webp$/);

    // Vite (desarrollo) no sirve /media; Caddy sí, y ahí se comprueba que el archivo existe y es
    // WebP. El job "Despliegue" del CI corre estos E2E contra Caddy.
    const file = await page.request.get((await image.getAttribute("src")) ?? "");
    if (!file.headers()["content-type"]?.startsWith("text/html")) {
      expect(file.status()).toBe(200);
      expect(file.headers()["content-type"]).toBe("image/webp");
    }
  } finally {
    expect((await page.request.delete(`/api/admin/projects/${String(projectId)}`)).status()).toBe(
      204,
    );
  }
});
