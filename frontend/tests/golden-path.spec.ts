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
    await expect(this.page.getByRole("heading", { level: 1 })).toContainText("마지막 한 번");
    await this.capture("01-home");
    await this.page.getByRole("button", { name: "demo 검사 시작하기" }).click();
    await expect(this.page).toHaveURL(/\/announcement$/);
    await expect(this.page.getByRole("heading", { name: "추출된 요구사항" })).toBeVisible();
    await expect(this.page.getByText("5개 항목")).toBeVisible();
    await this.capture("02-announcement");
    await this.page.getByRole("link", { name: "제출파일 선택하기" }).click();
    await expect(this.page).toHaveURL(/\/upload$/);
  }
}

test("five-screen golden path, evidence, filter, reload and recheck", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  const flow = new GoldenPath(page, info);
  await flow.start();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
  await page.getByRole("button", { name: "문제 있는 demo 불러오기" }).click();
  await expect(page.getByText("proposal.pdf", { exact: true })).toBeVisible();
  await flow.capture("03-upload");
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("BLOCKED");
  const blockers = page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) });
  await expect(blockers).toHaveCount(2);
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
  await page.getByRole("button", { name: "전체 5", exact: true }).click();
  await page.reload();
  await expect(page.getByRole("article")).toHaveCount(5);
  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await expect(page).toHaveURL(/\/recheck$/);
  await page.getByRole("button", { name: "수정한 demo 불러오기" }).click();
  await expect(page.getByText("consent.pdf", { exact: true })).toBeVisible();
  await flow.capture("05-recheck");
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("NEEDS_REVIEW");
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).not.toContainText("READY");
  await expect(page.getByRole("region", { name: "재검사 비교" })).toContainText("2개 판정 변경");
  await expect(page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) })).toHaveCount(0);
  await expect(page.getByRole("article", { name: "R19 사진만으로 구성된 영상 확인" })).toContainText("REVIEW");
  await flow.capture("06-results-fixed");
  expect(errors).toEqual([]);
});

test("deep link without a session has a recovery path", async ({ page }) => {
  await page.goto("/results");
  await expect(page.getByRole("heading", { name: "먼저 검사를 시작해 주세요" })).toBeVisible();
  await page.getByRole("link", { name: "홈으로 돌아가기" }).click();
  await expect(page).toHaveURL("/");
});

test("custom file upload never receives mocked findings", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("공고문 파일").setInputFiles(path.resolve("../fixtures/demo-announcement.txt"));
  await page.getByRole("button", { name: "파일 정보 확인" }).click();
  await expect(page).toHaveURL(/\/announcement$/);
  await expect(page.getByText("실제 공고 분석은 아직 연결되지 않았습니다")).toBeVisible();
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/demo-fixed/proposal.pdf"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page.getByRole("alert", { name: "작업 오류" })).toContainText("실제 분석 엔진이 아직 연결되지 않았습니다");
  await expect(page).toHaveURL(/\/upload$/);
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
