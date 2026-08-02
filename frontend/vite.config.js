import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to your backend so the frontend never hardcodes
// an origin. Point VITE_API_PROXY at your Django (or FastAPI) gateway.
// In production the app just calls the same-origin /api, so nothing changes.
export default defineConfig(() => {
  const target = process.env.VITE_API_PROXY || "http://localhost:8000";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // Both /api (versioned endpoints) and /health (Render liveness / cold-start probe).
        "/api": { target, changeOrigin: true },
        "/health": { target, changeOrigin: true },
      },
    },
  };
});
