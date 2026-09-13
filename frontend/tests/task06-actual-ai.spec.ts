import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("TASK06 actual local AI two-stage public-announcement flow", async ({ page }, info) => {
  test.skip(process.env.TASK06_ACTUAL_AI !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK06_ACTUAL_AI=1 and the actual local Codex provider.");
  test.setTimeout(600_000);
  const output = path.resolve("../artifacts/task06");
  await fs.mkdir(output, { recursive: true });
  const source = await fs.readFile(path.resolve("../benchmarks/task04/sources/C03.txt"), "utf8");

  await page.goto("/");
  await page.getByLabel("공고문 텍스트", { exact: true }).fill(source);
  await page.getByRole("button", { name: "텍스트 공고로 시작" }).click();
  await expect(page).toHaveURL(/\/announcement$/);
  const extraction = page.waitForResponse(response => response.url().endsWith("/extract") && response.request().method() === "POST", { timeout: 240_000 });
  await page.getByRole("button", { name: "요구사항 추출 실행" }).click();
  const extractionResponse = await extraction;
  expect(extractionResponse.ok()).toBe(true);
  let session = await extractionResponse.json();
  expect(session.generic_profile.pipeline_status).toBe("RUNNING");
  await expect(page.getByText("검토 후보 준비 완료", { exact: false })).toBeVisible({ timeout: 300_000 });
  const completedResponse = await page.request.get(`/api/sessions/${session.id}`);
  expect(completedResponse.ok()).toBe(true);
  session = await completedResponse.json();
  let profile = session.generic_profile;
  expect(profile.stage1.execution_kind).toBe("ACTUAL");
  expect(profile.stage2.execution_kind).toBe("ACTUAL");
  expect(profile.provider).toContain("Codex CLI");
  expect(profile.pipeline_status).toMatch(/COMPLETE|OVERFLOW_REVIEW/);
  expect(profile.failed_batches).toEqual([]);
  expect(profile.raw_candidate_count).toBeGreaterThanOrEqual(profile.gated_candidate_count);
  expect(profile.requirements.length).toBeGreaterThanOrEqual(2);
  await fs.writeFile(path.join(output, "actual-ai-extraction.json"), JSON.stringify(session, null, 2), "utf8");
  await page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
  await expect(page).toHaveURL(/\/requirements$/);

  const editable = profile.requirements.find((item: { issues: string[] }) => item.issues.length === 0) ?? profile.requirements[0];
  const deleteItem = profile.requirements.find((item: { requirement_id: string }) => item.requirement_id !== editable.requirement_id);
  expect(deleteItem).toBeTruthy();
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await page.getByRole("button", { name: `요구사항 ${editable.requirement_id}`, exact: true }).click();
  const editedCondition = `${editable.condition} (사람이 원문 확인)`;
  await inspector.getByLabel("condition").fill(editedCondition);
  await inspector.getByRole("button", { name: "수정 저장" }).click();
  await expect(page.getByRole("article", { name: `요구사항 ${editable.requirement_id}`, exact: true })).toContainText("AI EXTRACTED");
  await page.getByRole("button", { name: `요구사항 ${deleteItem.requirement_id}`, exact: true }).click();
  await inspector.getByRole("button", { name: "항목 삭제" }).click();

  const retained = profile.requirements.filter((item: { requirement_id: string }) => item.requirement_id !== deleteItem.requirement_id);
  for (const item of retained) {
    const card = page.getByRole("article", { name: `요구사항 ${item.requirement_id}`, exact: true });
    await page.getByRole("button", { name: `요구사항 ${item.requirement_id}`, exact: true }).click();
    if (item.issues.length > 0) {
      const simplified = item.rule.split(/이며|이고|하며|하고|그리고|또한|;|,|\s및\s|\n|[.!?]\s+/)[0].trim();
      await inspector.getByLabel("요구사항 문장").fill(simplified || item.evidence.quote);
      await inspector.getByRole("button", { name: "수정 저장" }).click();
    }
    await inspector.getByRole("button", { name: "항목 승인" }).click();
    await expect(card).toContainText("HUMAN CONFIRMED");
  }

  await page.getByText("공고 원문과 provenance", { exact: true }).click();
  await expect(page.getByText("Stage1 prompt:", { exact: false })).toBeVisible();
  await page.getByLabel("공고 원문 전체와 누락 가능성을 직접 검토했습니다.").check();
  await page.getByRole("button", { name: "Profile 확정" }).click();
  await expect(page.getByTestId("profile-status")).toHaveText("CONFIRMED");
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/announcements/submission.pdf"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  const validation = page.waitForResponse(response => response.url().endsWith("/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  const validationResponse = await validation;
  expect(validationResponse.ok()).toBe(true);
  session = await validationResponse.json();
  expect(session.generic_profile.status).toBe("CONFIRMED");
  expect(session.validation_profile).toBe("generic");
  expect(session.validation_complete).toBe(false);
  expect(session.status).toBe("REVIEW_REQUIRED");
  expect(session.results.every((result: { status: string }) => ["REVIEW", "EXTERNAL"].includes(result.status))).toBe(true);
  await fs.writeFile(path.join(output, "actual-ai-confirmed-handoff.json"), JSON.stringify(session, null, 2), "utf8");
  await page.screenshot({ path: path.join(output, "actual-ai-results.png"), fullPage: true });
});
