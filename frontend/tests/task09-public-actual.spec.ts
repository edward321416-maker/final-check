import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("TASK09 public ngrok Codex flow reuses one plan for 61s BLOCKED and 45s READY", async ({ page }, info) => {
  test.skip(process.env.TASK09_ACTUAL_AI !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK09_ACTUAL_AI=1 against the public ngrok URL.");
  test.setTimeout(900_000);

  const healthResponse = await page.request.get("/api/health");
  expect(healthResponse.ok()).toBe(true);
  const health = await healthResponse.json();
  expect(health.status).toBe("ok");
  expect(health.ai).toMatchObject({
    provider: "Codex CLI",
    configured: true,
    model: "gpt-5.6-sol",
    reasoning: "high",
  });
  expect(health.ffprobe.status).toBe("available");

  const publicAnnouncement = await fs.readFile(path.resolve("../benchmarks/task04/sources/C01.txt"), "utf8");
  const source = publicAnnouncement.split(/\r?\n/).find(line =>
    line.trim().startsWith("-") && line.includes("전체 길이 60초 이내 영상"))?.trim();
  expect(source).toBeTruthy();

  await page.goto("/");
  await page.getByLabel("공고문 텍스트", { exact: true }).fill(source!);
  const startedResponse = page.waitForResponse(response => response.url().endsWith("/announcement-text"));
  await page.getByRole("button", { name: "텍스트 공고로 시작" }).click();
  const sessionId = (await (await startedResponse).json()).id as string;
  const getSession = async () => (await page.request.get(`/api/sessions/${sessionId}`)).json();

  let session = await getSession();
  for (let attempt = 0; attempt < 3 && session.generic_profile.pipeline_status !== "COMPLETE"; attempt += 1) {
    const started = await page.request.post(`/api/sessions/${sessionId}/extract`, {
      data: { expected_version: session.generic_profile.version },
    });
    expect(started.ok()).toBe(true);
    await expect.poll(async () => (await getSession()).generic_profile.pipeline_status,
      { timeout: 600_000 }).not.toBe("RUNNING");
    session = await getSession();
  }
  expect(session.generic_profile.pipeline_status).toBe("COMPLETE");
  const target = session.generic_profile.requirements.find((item: { evidence: { quote: string } }) =>
    item.evidence.quote.includes("60초 이내") && item.evidence.quote.includes("영상"));
  expect(target, "Codex Stage1/Stage2 must retain the source-grounded 60-second rule").toBeTruthy();

  for (const item of [...session.generic_profile.requirements]) {
    const current = session.generic_profile;
    if (item.requirement_id === target.requirement_id) {
      const requirement = {
        requirement_id: item.requirement_id,
        rule: "영상 전체 길이는 60초 이내여야 합니다.",
        modality: "MUST",
        severity: "BLOCKER",
        verifier: "DETERMINISTIC",
        condition: "always",
        evidence: item.evidence,
        confidence: item.confidence,
      };
      session = await (await page.request.post(
        `/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`,
        { data: { expected_version: current.version, action: "APPROVE", requirement } },
      )).json();
    } else {
      session = await (await page.request.post(
        `/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`,
        { data: { expected_version: current.version, action: "DELETE", requirement: null } },
      )).json();
    }
  }
  expect(session.generic_profile.requirements).toHaveLength(1);
  session = await (await page.request.post(`/api/sessions/${sessionId}/profile/confirm`, {
    data: { expected_version: session.generic_profile.version, reviewed_full_source: true },
  })).json();
  expect(session.generic_profile.status).toBe("CONFIRMED");

  session = await (await page.request.post(`/api/sessions/${sessionId}/verification-plan/compile`, {
    data: { expected_version: session.generic_profile.version },
  })).json();
  expect(session.verification_plan_state).toBe("READY");
  expect(session.verification_plan.plans).toHaveLength(1);
  expect(session.verification_plan.plans[0]).toMatchObject({ status: "VERIFIED", checker_type: "VIDEO_METADATA" });
  const planSetId = session.verification_plan.plan_set_id;

  await page.reload();
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(
    path.resolve("../fixtures/v15/demo-broken/테스트어린이집_숏폼영상.MP4"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("BLOCKED");
  const broken = await getSession();
  expect(broken.results[0].status).toBe("BLOCKER");
  expect(broken.results[0].announcement_evidence).toBeTruthy();
  expect(broken.results[0].submission_evidence).toBeTruthy();

  const screenshots = path.resolve("../artifacts/task09/screenshots");
  await fs.mkdir(screenshots, { recursive: true });
  await page.screenshot({ path: path.join(screenshots, "public-61s-blocked.png"), fullPage: true });
  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(
    path.resolve("../fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("READY");
  const fixed = await getSession();
  expect(fixed.results[0].status).toBe("PASS");
  expect(fixed.verification_plan.plan_set_id).toBe(planSetId);
  await page.screenshot({ path: path.join(screenshots, "public-45s-ready.png"), fullPage: true });

  await fs.writeFile(path.resolve("../artifacts/task09/public-e2e.json"), JSON.stringify({
    classification: "ACTUAL",
    public_url: process.env.FINAL_CHECK_BASE_URL,
    session_id: sessionId,
    source: "C01 public announcement exact excerpt from benchmarks/task04/sources/C01.txt",
    provider: health.ai,
    ffprobe: health.ffprobe,
    plan_set_id: planSetId,
    planner: fixed.verification_plan.planner_provenance,
    extraction: { job: fixed.current_job, stage1: fixed.generic_profile.stage1, stage2: fixed.generic_profile.stage2 },
    broken: { status: broken.status, result: broken.results[0] },
    fixed: { status: fixed.status, result: fixed.results[0] },
    same_plan_set: fixed.verification_plan.plan_set_id === planSetId,
  }, null, 2), "utf8");
});
