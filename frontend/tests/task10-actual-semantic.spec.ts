import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
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

const announcementPath = path.resolve("../fixtures/task10/announcement.txt");
const positivePath = path.resolve("../fixtures/task10/submission-with-effect.pdf");
const missingPath = path.resolve("../fixtures/task10/submission-without-effect.pdf");
const injectionPath = path.resolve("../fixtures/task10/submission-prompt-injection.pdf");
const positiveEffectPage = "기대효과\n기대효과: 참여자의 접근성을 높이고 지역 협력의 지속성을 강화합니다.\n";

test("TASK10 actual semantic review grounds evidence, keeps absence review-only, and contains prompt injection", async ({ page }, info) => {
  test.skip(process.env.TASK10_ACTUAL_AI !== "1" || info.project.name !== "desktop",
    "Run explicitly with TASK10_ACTUAL_AI=1 and FINAL_CHECK_AI_PROVIDER=codex.");
  test.setTimeout(900_000);
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
        rule: "제안서 PDF에는 기대효과를 포함해야 합니다.",
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

  await page.goto("/upload");
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(positivePath);
  const uploadedPositive = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedPositive).ok()).toBe(true);
  const acknowledgement = page.getByRole("checkbox", { name: "PDF에서 추출된 전체 텍스트가 AI 내용 검토에 사용되는 것을 확인했습니다." });
  await expect(acknowledgement).toBeVisible();
  const readiness = await page.request.get(`/api/sessions/${sessionId}/semantic-readiness`);
  expect(readiness.ok()).toBe(true);
  expect((await readiness.json()).ack_required).toBe(true);
  await acknowledgement.check();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
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
  const semanticProvider = positiveResult.semantic_review.provider;
  expect(semanticProvider.execution_kind).toBe("ACTUAL");
  expect(semanticProvider.provider).toContain("ChatGPT-authenticated Codex CLI");
  expect(semanticProvider.prompt_version).toBe("task10-semantic-review-v1");
  const acceptedPositiveEvidence = positiveResult.semantic_review.evidence.find(
    (evidence: { excerpt?: unknown }) => typeof evidence.excerpt === "string" && evidence.excerpt.trim().length > 0,
  );
  expect(acceptedPositiveEvidence, "Semantic acceptance must retain a non-empty locally grounded excerpt").toBeTruthy();
  expect(positiveEffectPage).toContain(acceptedPositiveEvidence.excerpt);

  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(missingPath);
  const uploadedMissing = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedMissing).ok()).toBe(true);
  await expect(acknowledgement).toBeVisible();
  await acknowledgement.check();
  await expect(page.getByRole("button", { name: "재검사 실행하기" })).toBeEnabled();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect.poll(async () => (await getSession()).run_state, { timeout: 600_000 }).toMatch(/COMPLETE|FAILED/);
  const missing = await getSession();
  expect(missing.run_state).toBe("COMPLETE");
  const missingResult = missing.results.find((result: { requirement_id: string }) => result.requirement_id === retained.requirement_id);
  expect(missingResult.status).toBe("REVIEW");
  expect(missingResult.status).not.toBe("BLOCKER");
  expect(missingResult.semantic_review.coverage).toBe("FULL");
  expect(missingResult.semantic_review.assessment).toBe("NO_CLEAR_EVIDENCE");
  const missingFingerprint = missingResult.semantic_review.evidence_fingerprint;
  expect(missingFingerprint).not.toBe(positiveResult.semantic_review.evidence_fingerprint);
  await page.goto("/results");
  await expect(page.getByRole("region", { name: "재검사 비교" })).toContainText("내용 근거 상태가 변경되었습니다.");
  const missingScreenshot = await page.screenshot({ fullPage: true });

  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(positivePath);
  const uploadedPositiveRecheck = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedPositiveRecheck).ok()).toBe(true);
  await expect(acknowledgement).toBeVisible();
  await acknowledgement.check();
  await expect(page.getByRole("button", { name: "재검사 실행하기" })).toBeEnabled();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect.poll(async () => (await getSession()).run_state, { timeout: 600_000 }).toMatch(/COMPLETE|FAILED/);
  const rechecked = await getSession();
  expect(rechecked.run_state).toBe("COMPLETE");
  const recheckedResult = rechecked.results.find((result: { requirement_id: string }) => result.requirement_id === retained.requirement_id);
  expect(recheckedResult.status).toBe("REVIEW");
  expect(recheckedResult.semantic_review.assessment).toBe("RELATED_EVIDENCE_FOUND");
  expect(recheckedResult.semantic_review.evidence_fingerprint).not.toBe(missingFingerprint);
  await page.goto("/results");
  const comparison = page.getByRole("region", { name: "재검사 비교" });
  await expect(comparison).toContainText("내용 근거 상태가 변경되었습니다.");
  await expect(comparison).toContainText("이전: 명확한 근거 후보 미발견");
  const recheckedScreenshot = await page.screenshot({ fullPage: true });

  await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  await page.getByLabel("제출파일", { exact: true }).setInputFiles(injectionPath);
  const uploadedInjection = page.waitForResponse(response => response.url().endsWith("/files") && response.request().method() === "POST");
  await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  expect((await uploadedInjection).ok()).toBe(true);
  await expect(acknowledgement).toBeVisible();
  await acknowledgement.check();
  await expect(page.getByRole("button", { name: "재검사 실행하기" })).toBeEnabled();
  await page.getByRole("button", { name: "재검사 실행하기" }).click();
  await expect.poll(async () => (await getSession()).run_state, { timeout: 600_000 }).toMatch(/COMPLETE|FAILED/);
  const injected = await getSession();
  expect(injected.run_state).toBe("COMPLETE");
  expect(injected.status).toBe("REVIEW_REQUIRED");
  const injectedResult = injected.results.find((result: { requirement_id: string }) => result.requirement_id === retained.requirement_id);
  expect(injectedResult.source_mode).toBe("generic_review");
  expect(injectedResult.status).toBe("REVIEW");
  expect(injectedResult.status).not.toBe("PASS");
  expect(injectedResult.status).not.toBe("BLOCKER");
  expect(injectedResult.semantic_review.provider.execution_kind).toBe("ACTUAL");
  expect(injected.results.filter((result: { semantic_review?: unknown }) => result.semantic_review)
    .some((result: { status: string }) => ["PASS", "BLOCKER"].includes(result.status))).toBe(false);
  const operationLedger = readOperationLedger(sessionId);
  expect(operationLedger).toEqual({ EXTRACT: 1, PLAN: 0, SEMANTIC: 4 });

  const output = path.resolve("../artifacts/task10");
  const screenshots = path.join(output, "screenshots");
  await fs.mkdir(screenshots, { recursive: true });
  await fs.writeFile(path.join(screenshots, "actual-semantic-missing.png"), missingScreenshot);
  await fs.writeFile(path.join(screenshots, "actual-semantic-positive-recheck.png"), recheckedScreenshot);

  await fs.writeFile(path.join(output, "actual-semantic-e2e.json"), JSON.stringify({
    classification: "ACTUAL",
    baseline: "d90f53ae8e20b8a51b3a4559a3e7e5651dd204a0",
    session_id: sessionId,
    operation_ledger: operationLedger,
    provider: semanticProvider,
    prompt: { version: "task10-semantic-review-v1", sha256: semanticProvider.prompt_sha256 },
    profile_id: positive.generic_profile.profile_id,
    fixture_sha256: {
      positive: crypto.createHash("sha256").update(await fs.readFile(positivePath)).digest("hex"),
      missing: crypto.createHash("sha256").update(await fs.readFile(missingPath)).digest("hex"),
      injection: crypto.createHash("sha256").update(await fs.readFile(injectionPath)).digest("hex"),
    },
    positive: { run_state: positive.run_state, overall_status: positive.status, status: positiveResult.status,
      assessment: positiveResult.semantic_review.assessment, accepted_evidence: positiveResult.semantic_review.evidence },
    missing: { run_state: missing.run_state, overall_status: missing.status, status: missingResult.status,
      assessment: missingResult.semantic_review.assessment, coverage: missingResult.semantic_review.coverage },
    recheck: { run_state: rechecked.run_state, overall_status: rechecked.status, status: recheckedResult.status,
      assessment: recheckedResult.semantic_review.assessment, evidence_fingerprint: recheckedResult.semantic_review.evidence_fingerprint },
    prompt_injection: { run_state: injected.run_state, overall_status: injected.status, status: injectedResult.status,
      assessment: injectedResult.semantic_review.assessment,
      reason_code: injectedResult.semantic_review.reason_code },
    semantic_pass_or_blocker_observed: false,
  }, null, 2), "utf8");
});
