import { test, expect, type Page, type TestInfo } from "@playwright/test";
import path from "node:path";
import fs from "node:fs/promises";

class GoldenPath {
  constructor(readonly page: Page, readonly info: TestInfo) {}
  async capture(name: string) {
    const directory = path.resolve("../artifacts/screenshots");
    await fs.mkdir(directory, { recursive: true });
    await this.page.screenshot({ path: path.join(directory, `${this.info.project.name}-${name}.png`), fullPage: true });
    const overflow = await this.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow, `horizontal overflow on ${name}`).toBe(false);
  }
  async start() {
    await this.page.goto("/");
    await expect(this.page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." })).toBeVisible();
    await this.capture("01-home");
    await this.page.getByRole("button", { name: "demo 검사 시작하기" }).click();
    await expect(this.page).toHaveURL(/\/announcement$/);
    await expect(this.page.getByRole("heading", { name: "동결 공고 요구사항" })).toBeVisible();
    await expect(this.page.getByText("16개 항목")).toBeVisible();
    await this.capture("02-announcement");
    await this.page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
    await expect(this.page).toHaveURL(/\/requirements$/);
    await expect(this.page.getByRole("heading", { name: "동결 공고 요구사항 · 읽기 전용" })).toBeVisible();
    await expect(this.page.getByText("실시간 AI 추출 결과가 아닙니다.")).toBeVisible();
    await expect(this.page.getByText("AI EXTRACTED", { exact: true })).toHaveCount(0);
    await this.page.getByRole("link", { name: "제출파일 선택하기" }).click();
    await expect(this.page).toHaveURL(/\/upload$/);
  }
}

test("five-screen golden path, evidence, filter, reload and recheck", async ({ page }, info) => {
  const errors: string[] = [];
  const uploads: string[] = [];
  page.on("request", request => {
    if (request.method() === "POST" && /\/sessions\/[^/]+\/files$/.test(new URL(request.url()).pathname)) {
      uploads.push(request.headers()["content-type"] ?? "");
    }
  });
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  const flow = new GoldenPath(page, info);
  await flow.start();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
  await page.getByRole("button", { name: "문제 있는 demo 불러오기" }).click();
  await expect(page.getByText("테스트어린이집_숏폼공모서류.pdf", { exact: true })).toBeVisible();
  const packagePane = page.getByRole("region", { name: "제출 패키지" });
  await expect(packagePane).toContainText("application/pdf");
  await expect(packagePane).not.toContainText("61.0s");
  await expect(packagePane).not.toContainText("페이지 수:");
  await expect(page.getByRole("region", { name: "이번 검사" })).toContainText("16개 동결 Validator 항목");
  await flow.capture("03-upload");
  const brokenRun = page.waitForResponse(response => response.url().endsWith("/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  const brokenBody = await (await brokenRun).json();
  expect(brokenBody.source_mode).toBe("validator");
  expect(brokenBody.engine_sha256).toBe("4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11");
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("BLOCKED");
  const blockers = page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) });
  await expect(blockers).toHaveCount(2);
  await expect(page.getByRole("article", { name: "R09 참가 신청서 및 개인정보 동의서" })).toContainText("BLOCKER");
  await expect(page.getByRole("article", { name: "R13 영상 길이 30~60초" })).toContainText("BLOCKER");
  for (const blocker of await blockers.all()) {
    await expect(blocker.getByText("공고문 근거", { exact: true })).toBeVisible();
    await expect(blocker.getByText("제출파일 근거", { exact: true })).toBeVisible();
    await expect(blocker.locator("blockquote")).toHaveCount(2);
  }
  const r19 = page.getByRole("article", { name: "R19 사진만으로 구성된 영상 확인" });
  await expect(r19.getByText("REVIEW", { exact: true })).toBeVisible();
  await flow.capture("04-results-broken");
  await page.getByRole("button", { name: "BLOCKER 2", exact: true }).click();
  await expect(page.getByRole("article")).toHaveCount(2);
  await page.getByRole("button", { name: "전체 16", exact: true }).click();
  await page.reload();
  await expect(page.getByRole("article")).toHaveCount(16);
  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await expect(page).toHaveURL(/\/recheck$/);
  await page.getByRole("button", { name: "수정한 demo 불러오기" }).click();
  await expect(page.getByText("테스트어린이집_숏폼공모서류.pdf", { exact: true })).toBeVisible();
  await flow.capture("05-recheck");
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("REVIEW_REQUIRED");
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).not.toContainText("READY");
  await expect(page.getByRole("region", { name: "재검사 비교" })).toContainText("2개 판정 변경");
  await expect(page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) })).toHaveCount(0);
  await expect(page.getByRole("article", { name: "R19 사진만으로 구성된 영상 확인" })).toContainText("REVIEW");
  await expect(page.getByRole("article", { name: "R09 참가 신청서 및 개인정보 동의서" })).toContainText("PASS");
  await expect(page.getByRole("article", { name: "R13 영상 길이 30~60초" })).toContainText("PASS");
  expect(uploads).toHaveLength(2);
  expect(uploads.every(value => value.includes("multipart/form-data"))).toBe(true);
  await flow.capture("06-results-fixed");
  expect(errors).toEqual([]);
});

test("deep link without a session has a recovery path", async ({ page }) => {
  await page.goto("/results");
  await expect(page.getByRole("heading", { name: "이 단계를 아직 진행할 수 없습니다" })).toBeVisible();
  await page.getByRole("link", { name: "홈으로 돌아가기" }).click();
  await expect(page).toHaveURL("/");
});

test("unconfirmed custom profile cannot reach submission validation", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("공고문 파일").setInputFiles(path.resolve("../fixtures/demo-announcement.txt"));
  await page.getByRole("button", { name: "파일 정보 확인" }).click();
  await expect(page).toHaveURL(/\/announcement$/);
  await expect(page.getByRole("heading", { name: "요구사항 검토" })).toBeVisible();
  await expect(page.getByTestId("profile-status")).toHaveText("DRAFT");
  await expect(page.getByRole("article")).toHaveCount(0);
  await page.goto("/upload");
  await expect(page.getByRole("link", { name: "요구사항 검토로 돌아가기" })).toHaveAttribute("href", "/requirements");
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toHaveCount(0);
  await expect(page.getByRole("article")).toHaveCount(0);
});

test("backend failure is recoverable and does not advance", async ({ page }) => {
  await page.route("**/api/sessions", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"test service unavailable"}' }));
  await page.goto("/");
  await page.getByRole("button", { name: "demo 검사 시작하기" }).click();
  await expect(page.getByRole("alert", { name: "작업 오류" })).toBeVisible();
  await expect(page).toHaveURL("/");
  await expect(page.getByRole("button", { name: "demo 검사 시작하기" })).toBeEnabled();
});
