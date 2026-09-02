import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const python = path.resolve("..", "backend", ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
export default defineConfig({
  testDir: "./tests", fullyParallel: true, workers: 2, timeout: 45_000,
  expect: { timeout: 10_000 }, retries: 0,
  reporter: [["list"], ["json", { outputFile: "../artifacts/playwright-results.json" }]],
  use: { baseURL: "http://127.0.0.1:3100", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
  webServer: [
    { command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8100`, cwd: "../backend", url: "http://127.0.0.1:8100/api/health", reuseExistingServer: false, timeout: 30_000 },
    { command: "npm run start", url: "http://127.0.0.1:3100", reuseExistingServer: false, timeout: 30_000 },
  ],
});
