import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The app only ever calls same-origin relative "/api/..." paths. The dev server
// forwards them to the local FastAPI fixture backend, so no browser request is
// ever made to an external host and no CORS preflight is involved.
const LOCAL_FIXTURE_API = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: LOCAL_FIXTURE_API,
        changeOrigin: false
      }
    }
  }
});
