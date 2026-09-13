import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";

type OperationLedger = { EXTRACT: number; PLAN: number; SEMANTIC: number };

function readOperationLedger(sessionId: string): OperationLedger {
  const dataDir = process.env.FINAL_CHECK_DATA_DIR;
  if (!dataDir) throw new Error("FINAL_CHECK_DATA_DIR is required for ACTUAL operation evidence");
  const database = new DatabaseSync(path.join(dataDir, "runtime.sqlite3"), { readOnly: true });
  try {
    const ledger: OperationLedger = { EXTRACT: 0, PLAN: 0, SEMANTIC: 0 };
    const rows = database.prepare(
      "SELECT operation_kind, COUNT(*) AS operation_count FROM ai_operations WHERE session_id = ? GROUP BY operation_kind",
    ).all(sessionId) as Array<{ operation_kind: string; operation_count: number | bigint }>;
    for (const row of rows) {
      if (!Object.hasOwn(ledger, row.operation_kind)) throw new Error(`Unexpected operation kind: ${row.operation_kind}`);
      ledger[row.operation_kind as keyof OperationLedger] = Number(row.operation_count);
    }
    return ledger;
  } finally {
    database.close();
  }
}

test("TASK08 actual public announcement C01 excerpt to planner, broken and fixed verifier flow", async ({ page }, info) => {
  test.skip(process.env.TASK08_ACTUAL_AI !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK08_ACTUAL_AI=1 and the actual local Codex provider.");
  test.setTimeout(900_000);
  const publicAnnouncement = await fs.readFile(path.resolve("../benchmarks/task04/sources/C01.txt"), "utf8");
  const source = publicAnnouncement.split(/\r?\n/).find(line => line.trim().startsWith("-") && line.includes("전체 길이 60초 이내 영상"))?.trim();
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
    await expect.poll(async () => (await getSession()).generic_profile.pipeline_status, { timeout: 600_000 }).not.toBe("RUNNING");
    session = await getSession();
  }
  expect(session.generic_profile.pipeline_status).toBe("COMPLETE");
  const target = session.generic_profile.requirements.find((item: { evidence: { quote: string } }) =>
    item.evidence.quote.includes("60초 이내") && item.evidence.quote.includes("영상"));
  expect(target, "Actual Stage1/Stage2 must retain a source-grounded 60-second video requirement").toBeTruthy();

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
      session = await (await page.request.post(`/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`, {
        data: { expected_version: current.version, action: "APPROVE", requirement },
      })).json();
    } else {
      session = await (await page.request.post(`/api/sessions/${sessionId}/requirements/${item.requirement_id}/review`, {
        data: { expected_version: current.version, action: "DELETE", requirement: null },
      })).json();
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
  expect(session.verification_plan.plans[0].status).toBe("VERIFIED");
  expect(session.verification_plan.plans[0].checker_type).toBe("VIDEO_METADATA");
  const planSetId = session.verification_plan.plan_set_id;

  await page.goto("/requirements");
  await expect(page.getByRole("region", { name: "자동 검사 계획 요약" })).toContainText("자동 검사 가능");
  await page.getByRole("link", { name: "제출파일 선택하기" }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/v15/demo-broken/테스트어린이집_숏폼영상.MP4"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("BLOCKED");
  await expect(page.getByRole("article")).toContainText("BLOCKER");
  const broken = await getSession();
  expect(broken.results[0].announcement_evidence).toBeTruthy();
  expect(broken.results[0].submission_evidence).toBeTruthy();

  const directory = path.resolve("../artifacts/task08/screenshots");
  await fs.mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, "actual-c01-excerpt-broken.png"), fullPage: true });
  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"));
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("READY");
  await expect(page.getByRole("article")).toContainText("PASS");
  const fixed = await getSession();
  expect(fixed.verification_plan.plan_set_id).toBe(planSetId);
  expect(fixed.results[0].submission_evidence).toBeTruthy();
  expect(fixed.results[0].semantic_review).toBeNull();
  const operationLedger = readOperationLedger(sessionId);
  expect(operationLedger).toEqual({ EXTRACT: 1, PLAN: 1, SEMANTIC: 0 });
  await page.screenshot({ path: path.join(directory, "actual-c01-excerpt-fixed.png"), fullPage: true });
  await fs.writeFile(path.resolve("../artifacts/task08/actual-product-e2e.json"), JSON.stringify({
    classification: "ACTUAL",
    session_id: sessionId,
    source: "C01 public announcement exact excerpt from benchmarks/task04/sources/C01.txt",
    media: ["fixtures/v15/demo-broken/테스트어린이집_숏폼영상.MP4", "fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"],
    plan_set_id: planSetId,
    operation_ledger: operationLedger,
    semantic_review: fixed.results[0].semantic_review,
    planner: fixed.verification_plan.planner_provenance,
    extraction: { job: fixed.current_job, stage1: fixed.generic_profile.stage1, stage2: fixed.generic_profile.stage2 },
    broken: { status: broken.status, result: broken.results[0] },
    fixed: { status: fixed.status, result: fixed.results[0] },
  }, null, 2), "utf8");
});
