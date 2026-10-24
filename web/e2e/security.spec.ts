import { expect, test } from "@playwright/test";

import { contentSecurityPolicy, securityHeaders } from "../security-headers";

test("the page responds with the security headers", async ({ request }) => {
  const response = await request.get("/");

  expect(response.ok()).toBe(true);
  const headers = response.headers();
  for (const [name, value] of Object.entries(securityHeaders)) {
    expect(headers[name.toLowerCase()], name).toBe(value);
  }
  // The CSP is only sent in the build (vite preview and production); if present, it must be the
  // defined one.
  const csp = headers["content-security-policy"];
  if (csp !== undefined) expect(csp).toBe(contentSecurityPolicy);
});

// It also catches anything the CSP blocks, because the browser reports it as a console error.
test("the page shows no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  expect(errors).toEqual([]);
});
