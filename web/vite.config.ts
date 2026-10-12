import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { productionHeaders, securityHeaders } from "./security-headers";

const apiProxy = { "/api": process.env.API_URL ?? "http://localhost:8000" };

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    headers: securityHeaders,
    // En local, /api se pasa a la API del compose, igual que hará Caddy en producción.
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    headers: productionHeaders,
    proxy: apiProxy,
  },
  build: {
    // Sin source maps en el build: no se publica el código fuente original.
    sourcemap: false,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    coverage: {
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"],
      thresholds: { lines: 60 },
    },
  },
});
