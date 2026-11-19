import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api calls are proxied to the FastAPI backend, so no CORS trouble in development.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
});
