import { defineConfig, devices } from "@playwright/test";

/**
 * Runs against a dedicated API (8010) and web (5174) instance, never the ports
 * a developer's own `npm run dev` uses on 8000/5173. The approval store has no
 * reset endpoint and now persists to a real SQLite file by default
 * (APPROVALS_DB_PATH below overrides that to ":memory:"), so every test run
 * needs its own fresh, non-persistent FastAPI process — sharing the dev
 * server's process (or its approvals.db) would let one run's approve/reject
 * calls leak into the next.
 */
const API_PORT = 8010;
const WEB_PORT = 5174;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
    trace: "retain-on-failure"
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT}`,
      cwd: "../api",
      env: { APPROVALS_DB_PATH: ":memory:" },
      port: API_PORT,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000
    },
    {
      command: `npm run dev -- --port ${WEB_PORT}`,
      cwd: ".",
      env: { VITE_API_PORT: String(API_PORT), VITE_PORT: String(WEB_PORT) },
      port: WEB_PORT,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000
    }
  ]
});
