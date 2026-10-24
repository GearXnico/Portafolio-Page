import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { productionHeaders, securityHeaders } from "./security-headers";

const apiProxy = { "/api": process.env.API_URL ?? "http://localhost:8000" };

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    headers: securityHeaders,
    // Locally, /api is forwarded to the compose API, just as Caddy will do in production.
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    headers: productionHeaders,
    proxy: apiProxy,
  },
  build: {
    // No source maps in the build: the original source code isn't published.
    sourcemap: false,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    coverage: {
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"],
      thresholds: { lines: 80 },
    },
  },
});
