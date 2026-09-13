import { test, expect, type Page, type TestInfo } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

class GenericFlow {
  constructor(readonly page: Page, readonly info: TestInfo) {}
  card(id: string) { return this.page.getByRole("article", { name: `요구사항 ${id}`, exact: true }); }
  inspector() { return this.page.getByRole("region", { name: "요구사항 Inspector" }); }
  async select(id: string) {
    await this.page.getByRole("button", { name: `요구사항 ${id}`, exact: true }).click();
    return this.inspector();
  }
  async capture(name: string) {
    const directory = path.resolve("../artifacts/task03/screenshots");
    await fs.mkdir(directory, { recursive: true });
    await this.page.screenshot({ path: path.join(directory, `${this.info.project.name}-${name}.png`), fullPage: true });
    expect(await this.page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  }
  async textInput() {
    await this.page.goto("/");
    await this.page.getByLabel("공고문 텍스트", { exact: true }).fill(await fs.readFile(path.resolve("../fixtures/announcements/submission.txt"), "utf8"));
    await this.page.getByRole("button", { name: "텍스트 공고로 시작" }).click();
    await expect(this.page).toHaveURL(/\/announcement$/);
    await expect(this.page.getByTestId("profile-status")).toHaveText("DRAFT");
    const response = this.page.waitForResponse(r => r.url().endsWith("/extract") && r.request().method() === "POST");
    await this.page.getByRole("button", { name: "요구사항 추출 실행" }).click();
    const data = await (await response).json();
    expect(data.generic_profile.execution_kind).toBe("SIMULATED");
    expect(data.validation_profile).toBeNull();
    await expect(this.page.getByRole("article")).toHaveCount(5);
    await expect(this.page.getByRole("button", { name: "Profile 확정" })).toHaveCount(0);
    await this.page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
    await expect(this.page).toHaveURL(/\/requirements$/);
    await expect(this.page.getByRole("region", { name: "요구사항 Inspector" })).toBeVisible();
  }
}

test("generic text, evidence, human edit/delete/approve, confirmation and real handoff", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  const flow = new GenericFlow(page, info);
  await flow.textInput();
  let inspector = await flow.select("G001");
  await expect(flow.card("G001")).toContainText("AI EXTRACTED");
  await expect(inspector.locator("blockquote")).toHaveText("제안서는 PDF 형식으로 제출해야 한다.");
  await expect(page.getByRole("button", { name: "Profile 확정" })).toBeDisabled();
  await flow.capture("01-extracted");
  await inspector.getByLabel("요구사항 문장").fill("제안서는 PDF 형식으로 제출해야 한다");
  await expect(page.getByRole("button", { name: "요구사항 G002", exact: true })).toBeDisabled();
  await inspector.getByRole("button", { name: "수정 저장" }).click();
  await expect(flow.card("G001")).toContainText("AI EXTRACTED");
  inspector = flow.inspector();
  await inspector.getByRole("button", { name: "검토 필요로 유지" }).click();
  await expect(inspector.getByRole("button", { name: "항목 승인" })).toBeEnabled();
  inspector = await flow.select("G004");
  await inspector.getByRole("button", { name: "항목 삭제" }).click();
  await expect(flow.card("G004")).toHaveCount(0);
  for (const id of ["G001", "G002", "G003", "G005"]) {
    inspector = await flow.select(id);
    await inspector.getByRole("button", { name: "항목 승인" }).click();
    await expect(flow.card(id)).toContainText("HUMAN CONFIRMED");
  }
  await page.getByText("공고 원문과 provenance", { exact: true }).click();
  await expect(page.getByText("Source SHA-256:", { exact: false })).toBeVisible();
  await page.getByLabel("공고 원문 전체와 누락 가능성을 직접 검토했습니다.").check();
  await page.getByRole("button", { name: "Profile 확정" }).click();
  await expect(page.getByTestId("profile-status")).toHaveText("CONFIRMED");
  await page.reload();
  await expect(page.getByTestId("profile-status")).toHaveText("CONFIRMED");
  inspector = await flow.select("G001");
  await expect(inspector.getByLabel("요구사항 문장")).toHaveValue("제안서는 PDF 형식으로 제출해야 한다");
  await flow.capture("02-confirmed");
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await expect(page).toHaveURL(/\/upload$/);
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/announcements/submission.pdf"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  const response = page.waitForResponse(r => r.url().endsWith("/validate") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  const data = await (await response).json();
  expect(data.validation_profile).toBe("generic");
  expect(data.generic_profile.status).toBe("CONFIRMED");
  expect(data.engine_sha256).toBeNull();
  expect(data.validation_complete).toBe(false);
  expect(data.results).toHaveLength(4);
  expect(data.results.every((r: { status: string; source_mode: string }) => ["REVIEW", "EXTERNAL"].includes(r.status) && r.source_mode === "generic_review")).toBe(true);
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("REVIEW_REQUIRED");
  await expect(page.getByRole("article")).toHaveCount(4);
  await flow.capture("03-handoff");
  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("REVIEW_REQUIRED");
  expect(errors).toEqual([]);
});

for (const scanned of [false, true]) {
  test(`actual ${scanned ? "scanned" : "text"} PDF announcement path`, async ({ page }, info) => {
    const flow = new GenericFlow(page, info);
    await page.goto("/");
    await page.getByLabel("공고문 파일").setInputFiles(path.resolve(`../fixtures/announcements/${scanned ? "scanned" : "submission"}.pdf`));
    await page.getByRole("button", { name: "파일 정보 확인" }).click();
    await expect(page).toHaveURL(/\/announcement$/);
    if (scanned) {
      await expect(page.getByText("요구사항 0개 · VISION_REQUIRED", { exact: false })).toBeVisible();
      await expect(page.getByRole("article")).toHaveCount(0);
      await expect(page.getByRole("button", { name: "요구사항 추출 실행" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Profile 확정" })).toHaveCount(0);
    } else {
      await page.getByRole("button", { name: "요구사항 추출 실행" }).click();
      await expect(page.getByRole("article")).toHaveCount(5);
      await page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
      await expect(page).toHaveURL(/\/requirements$/);
      const inspector = await flow.select("G001");
      await expect(inspector.locator("blockquote")).toHaveText("제안서는 PDF 형식으로 제출해야 한다.");
    }
    await flow.capture(scanned ? "04-scan-review" : "05-pdf-extracted");
  });
}
