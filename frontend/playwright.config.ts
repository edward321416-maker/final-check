import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const python = path.resolve("..", "backend", ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const externalBaseURL = process.env.FINAL_CHECK_BASE_URL;
export default defineConfig({
  testDir: "./tests", fullyParallel: true, workers: 2, timeout: 45_000,
  expect: { timeout: 10_000 }, retries: 0,
  reporter: [["list"], ["json", { outputFile: "../artifacts/playwright-results.json" }]],
  use: {
    baseURL: externalBaseURL ?? "http://127.0.0.1:3100",
    extraHTTPHeaders: externalBaseURL?.includes("ngrok-free") ? { "ngrok-skip-browser-warning": "1" } : undefined,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
  webServer: externalBaseURL ? undefined : [
    { command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8100`, cwd: "../backend", url: "http://127.0.0.1:8100/api/health", reuseExistingServer: false, timeout: 30_000,
      env: { ...process.env, FINAL_CHECK_AI_PROVIDER: process.env.FINAL_CHECK_AI_PROVIDER ?? "local-fallback" } },
    { command: "npm run start", url: "http://127.0.0.1:3100", reuseExistingServer: false, timeout: 30_000 },
  ],
});
