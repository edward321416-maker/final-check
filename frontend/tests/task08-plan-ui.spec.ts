import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("TASK08 plan summary labels verified and review-only plans without granting AI verdict authority", async ({ page }, info) => {
  await page.goto("/");
  await page.getByLabel("공고문 텍스트", { exact: true }).fill(await fs.readFile(path.resolve("../fixtures/announcements/submission.txt"), "utf8"));
  await page.getByRole("button", { name: "텍스트 공고로 시작" }).click();
  await page.getByRole("button", { name: "요구사항 추출 실행" }).click();
  await expect(page.getByRole("article")).toHaveCount(5);
  await page.getByRole("article", { name: "요구사항 G004", exact: true }).getByRole("button", { name: "항목 삭제" }).click();
  for (const id of ["G001", "G002", "G003", "G005"]) {
    await page.getByRole("article", { name: `요구사항 ${id}`, exact: true }).getByRole("button", { name: "항목 승인" }).click();
  }
  await page.getByLabel("공고 원문 전체와 누락 가능성을 직접 검토했습니다.").check();
  const confirmedResponse = page.waitForResponse(response => response.url().endsWith("/profile/confirm"));
  await page.getByRole("button", { name: "Profile 확정" }).click();
  const confirmed = await (await confirmedResponse).json();
  const requirement = confirmed.generic_profile.requirements[0];
  await page.route("**/api/sessions/*/verification-plan/compile", route => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      ...confirmed,
      source_mode: "generic_verifier",
      verification_plan_state: "READY",
      verification_plan_error: null,
      verification_plan: {
        plan_set_id: "simulated-plan-set",
        profile_id: confirmed.generic_profile.profile_id,
        profile_version: confirmed.generic_profile.version,
        announcement_sha256: confirmed.generic_profile.announcement.sha256,
        announcement_text_sha256: confirmed.generic_profile.announcement.text_sha256,
        confirmed_requirements_sha256: "a".repeat(64),
        planner_provenance: { provider: "SIMULATED browser fixture", model: "fixture", prompt_version: "task08-planner-v1", prompt_sha256: "b".repeat(64), execution_kind: "SIMULATED" },
        plan_schema_version: "task08-verification-plan-v1",
        created_at: new Date().toISOString(),
        plans: [{
          plan_id: "simulated-plan",
          requirement_id: requirement.requirement_id,
          planner_disposition: "CANDIDATE",
          checker_type: "FILE_TYPE",
          target_selector: { kind: "UNIQUE_EXTENSION", value: ".pdf" },
          constraint: { field: "TYPE", operator: "EQ", value: "PDF", unit: "NONE" },
          parameter_provenance: { evidence_quote: requirement.evidence.quote, evidence_start: requirement.evidence_start, evidence_end: requirement.evidence_end, source_substring: "PDF", normalized_value: "PDF", operator: "EQ" },
          planner_reason: "SIMULATED UI fixture",
          planner_provenance: { provider: "SIMULATED browser fixture", model: "fixture", prompt_version: "task08-planner-v1", prompt_sha256: "b".repeat(64), execution_kind: "SIMULATED" },
          status: "VERIFIED",
          gate_reasons: [],
        }],
      },
    }),
  }));
  await page.getByRole("button", { name: "자동 검사 계획 생성" }).click();
  const summary = page.getByRole("region", { name: "자동 검사 계획 요약" });
  await expect(summary).toContainText("자동 검사 가능");
  await expect(summary).toContainText("FILE_TYPE");
  await expect(page.getByText("게이트를 통과한 계획만 코드로 검사합니다.", { exact: false })).toBeVisible();
  await expect(page.getByText("AI는 계획만 제안하며 판정 권한이 없습니다.", { exact: false })).toBeVisible();
  const directory = path.resolve("../artifacts/task08/screenshots");
  await fs.mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, `${info.project.name}-plan-summary.png`), fullPage: true });
});
