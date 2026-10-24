import { expect, test } from "@playwright/test";

import { loginAsAdmin } from "./login";

// 1×1 px PNG: the API re-encodes it as WebP.
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64",
);

// A screenshot uploaded from the form shows up on the public page.
test("a screenshot uploaded in the admin panel shows up on the public page", async ({ page }) => {
  const id = String(Date.now());
  await loginAsAdmin(page);
  // The project is created through the API (projects.spec.ts tests the form); the session is in the
  // cookies.
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

    // Vite (development) doesn't serve /media; Caddy does, and there it checks that the file exists
    // and is WebP. The CI "Deployment" job runs these E2E tests against Caddy.
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
