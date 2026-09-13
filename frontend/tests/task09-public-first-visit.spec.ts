import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("TASK09 public first visit crosses the ngrok notice without a bypass header", async ({ browser }, info) => {
  const publicUrl = process.env.FINAL_CHECK_BASE_URL;
  test.skip(process.env.TASK09_FIRST_VISIT !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK09_FIRST_VISIT=1 against the public ngrok URL.");
  expect(publicUrl).toBeTruthy();

  const context = await browser.newContext({
    storageState: { cookies: [], origins: [] },
    extraHTTPHeaders: {},
  });
  const emptyState = await context.storageState();
  expect(emptyState.cookies).toHaveLength(0);
  expect(emptyState.origins).toHaveLength(0);

  const page = await context.newPage();
  let initialNavigationHeaders: Record<string, string> = {};
  page.on("request", request => {
    if (!Object.keys(initialNavigationHeaders).length
        && request.isNavigationRequest()
        && request.frame() === page.mainFrame()) {
      initialNavigationHeaders = request.headers();
    }
  });

  const response = await page.goto(publicUrl!, { waitUntil: "domcontentloaded" });
  expect(response?.ok()).toBe(true);
  expect(initialNavigationHeaders["ngrok-skip-browser-warning"]).toBeUndefined();

  const visitSite = page.getByText("Visit Site", { exact: true });
  await expect(visitSite).toBeVisible();
  await page.waitForTimeout(250);
  const screenshots = path.resolve("../artifacts/task09/screenshots");
  await fs.mkdir(screenshots, { recursive: true });
  await page.screenshot({ path: path.join(screenshots, "public-first-visit.png"), fullPage: true });

  const firstTitle = await page.title();
  expect(firstTitle).toContain("ERR_NGROK_6024");
  await visitSite.click();
  await expect(page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." })).toBeVisible();
  await page.screenshot({ path: path.join(screenshots, "public-after-interstitial.png"), fullPage: true });

  const finalState = await context.storageState();
  await fs.writeFile(path.resolve("../artifacts/task09/public-first-visit.json"), JSON.stringify({
    classification: "ACTUAL",
    test_kind: "JUDGE_FIRST_VISIT",
    public_url: publicUrl,
    fresh_browser_context: true,
    initial_cookie_count: emptyState.cookies.length,
    initial_storage_origin_count: emptyState.origins.length,
    ngrok_skip_browser_warning_header_used: false,
    initial_response_status: response?.status(),
    initial_error_code: "ERR_NGROK_6024",
    interstitial_shown: true,
    visit_site_visible: true,
    visit_site_clicked: true,
    final_check_landing_visible: true,
    final_url: page.url(),
    post_click_cookie_count: finalState.cookies.length,
    screenshots: [
      "screenshots/public-first-visit.png",
      "screenshots/public-after-interstitial.png"
    ],
    application_e2e_evidence: "public-e2e.json",
    other_network_browser: "NOT_TESTED"
  }, null, 2), "utf8");
  await context.close();
});
