import { defineConfig } from "vite";

// En local, /api se pasa a la API del compose, igual que hará Caddy en producción.
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.API_URL ?? "http://localhost:8000",
    },
  },
});
