import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

const announcementPath = path.resolve("../fixtures/task10/announcement.txt");
const positivePath = path.resolve("../fixtures/task10/submission-with-effect.pdf");
const missingPath = path.resolve("../fixtures/task10/submission-without-effect.pdf");
const expectedEffectQuote = "기대효과: 참여자의 접근성을 높이고 지역 협력의 지속성을 강화합니다.";

test("TASK10 actual semantic review grounds controlled positive evidence and keeps absence review-only", async ({ page }, info) => {
  test.skip(process.env.TASK10_ACTUAL_AI !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK10_ACTUAL_AI=1 and FINAL_CHECK_AI_PROVIDER=codex.");
  test.setTimeout(900_000);
  const output = path.resolve("../artifacts/task10");
  const screenshots = path.join(output, "screenshots");
  await fs.mkdir(screenshots, { recursive: true });

  await page.goto("/");
  await page.getByLabel("공고문 텍스트", { exact: true }).fill(await fs.readFile(announcementPath, "utf8"));
  const startedResponse = page.waitForResponse(response => response.url().endsWith("/announcement-text"));
  await page.getByRole("button", { name: "텍스트 공고로 시작" }).click();
  const sessionId = (await (await startedResponse).json()).id as string;
  const getSession = async () => (await page.request.get(`/api/sessions/${sessionId}`)).json();
  let session = await getSession();

  for (let attempt = 0; attempt < 3 && session.generic_profile.pipeline_status !== "COMPLETE"; attempt += 1) {
    const started = await page.request.post(`/api/sessions/${sessionId}/extract`, {
      data: { expected_version: session.generic_profile.version },
    });
    expect(started.ok(), "ACTUAL Stage1/Stage2 request must start").toBe(true);
    await expect.poll(async () => (await getSession()).generic_profile.pipeline_status, { timeout: 600_000 }).not.toBe("RUNNING");
    session = await getSession();
  }
  expect(session.generic_profile.pipeline_status).toBe("COMPLETE");
  expect(session.generic_profile.stage1.execution_kind).toBe("ACTUAL");
  expect(session.generic_profile.stage2.execution_kind).toBe("ACTUAL");
  expect(session.generic_profile.provider).toContain("Codex CLI");

  const retained = session.generic_profile.requirements.find((item: { evidence: { quote: string } }) =>
    item.evidence.quote.includes("기대효과")) ?? session.generic_profile.requirements[0];
  expect(retained, "ACTUAL extraction must produce a candidate to human-review").toBeTruthy();
  for (const item of [...session.generic_profile.requirements]) {
    const current = session.generic_profile;
    if (item.requirement_id === retained.requirement_id) {
      const requirement = {
        requirement_id: item.requirement_id,
        rule: "제안서 PDF에는 사업 추진 배경과 기대효과를 포함해야 합니다.",
        modality: "MUST",
        severity: "REVIEW",
        verifier: "SEMANTIC",
        condition: "always",
        evidence: item.evidence,
        confidence: item.confidence,
      };
      session = await (await page.request.post(`/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`, {
        data: { expected_version: current.version, action: "APPROVE", requirement },
      })).json();
    } else {
      session = await (await page.request.post(`/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`, {
        data: { expected_version: current.version, action: "DELETE", requirement: null },
      })).json();
    }
  }
  session = await (await page.request.post(`/api/sessions/${sessionId}/profile/confirm`, {
    data: { expected_version: session.generic_profile.version, reviewed_full_source: true },
  })).json();
  expect(session.generic_profile.status).toBe("CONFIRMED");

  await page.reload();
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(positivePath);
  const uploadedPositive = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedPositive).ok()).toBe(true);
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
  const readiness = await page.request.get(`/api/sessions/${sessionId}/semantic-readiness`);
  expect(readiness.ok()).toBe(true);
  expect((await readiness.json()).ack_required).toBe(true);
  await page.getByRole("checkbox", { name: "PDF에서 추출된 전체 텍스트가 AI 내용 검토에 사용되는 것을 확인했습니다." }).check();
  const firstRun = page.waitForResponse(response => response.url().endsWith("/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  const firstResponse = await firstRun;
  expect(firstResponse.ok()).toBe(true);
  const firstStarted = await firstResponse.json();
  expect(["RUNNING", "COMPLETE"], "background semantic run may finish before this response is read").toContain(firstStarted.run_state);
  await expect.poll(async () => (await getSession()).run_state, { timeout: 600_000 }).toMatch(/COMPLETE|FAILED/);
  const positive = await getSession();
  expect(positive.run_state).toBe("COMPLETE");
  const positiveResult = positive.results.find((result: { requirement_id: string }) => result.requirement_id === retained.requirement_id);
  expect(positiveResult.status).toBe("REVIEW");
  expect(positiveResult.source_mode).toBe("generic_review");
  expect(positiveResult.semantic_review.assessment).toBe("RELATED_EVIDENCE_FOUND");
  expect(positiveResult.submission_evidence.excerpt).toContain(expectedEffectQuote);
  await page.screenshot({ path: path.join(screenshots, "actual-semantic-positive.png"), fullPage: true });

  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(missingPath);
  const uploadedMissing = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedMissing).ok()).toBe(true);
  await expect(page.getByRole("button", { name: "재검사 실행하기" })).toBeEnabled();
  await page.getByRole("checkbox", { name: "PDF에서 추출된 전체 텍스트가 AI 내용 검토에 사용되는 것을 확인했습니다." }).check();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect.poll(async () => (await getSession()).run_state, { timeout: 600_000 }).toMatch(/COMPLETE|FAILED/);
  const missing = await getSession();
  expect(missing.run_state).toBe("COMPLETE");
  const missingResult = missing.results.find((result: { requirement_id: string }) => result.requirement_id === retained.requirement_id);
  expect(missingResult.status).toBe("REVIEW");
  expect(missingResult.status).not.toBe("BLOCKER");
  expect(missingResult.semantic_review.coverage).toBe("FULL");
  expect(missingResult.semantic_review.assessment).toBe("NO_CLEAR_EVIDENCE");
  await page.screenshot({ path: path.join(screenshots, "actual-semantic-missing.png"), fullPage: true });

  await fs.writeFile(path.join(output, "actual-semantic-e2e.json"), JSON.stringify({
    classification: "ACTUAL",
    baseline: "d90f53ae8e20b8a51b3a4559a3e7e5651dd204a0",
    provider: positiveResult.semantic_review.provider,
    prompt: { version: "task10-semantic-review-v1", sha256: positiveResult.semantic_review.provider.prompt_sha256 },
    profile_id: positive.generic_profile.profile_id,
    fixture_sha256: {
      positive: crypto.createHash("sha256").update(await fs.readFile(positivePath)).digest("hex"),
      missing: crypto.createHash("sha256").update(await fs.readFile(missingPath)).digest("hex"),
    },
    positive: { status: positiveResult.status, assessment: positiveResult.semantic_review.assessment, accepted_evidence: positiveResult.semantic_review.evidence },
    missing: { status: missingResult.status, assessment: missingResult.semantic_review.assessment },
    semantic_pass_or_blocker_observed: false,
  }, null, 2), "utf8");
});
