import { expect, test, type Page } from "@playwright/test";
import { recoveryHref } from "../lib/workflow";

const sessionId = "ui-redesign-session";
const stamp = "2026-09-13T00:00:00.000Z";

function baseSession(overrides: Record<string, unknown> = {}) {
  return {
    id: sessionId, created_at: stamp, updated_at: stamp, mode: "custom",
    source_mode: "unavailable", announcement_name: "공고.txt", validation_profile: null,
    engine_sha256: null, generic_profile: null, verification_plan: null,
    verification_plan_state: "NOT_STARTED", verification_plan_error: null,
    current_job_id: null, current_job: null, run_state: "NOT_STARTED",
    validation_complete: false, run_error: null, requirements: [], files: [],
    results: [], previous_results: [], status: null, revision: 0, fixture: null,
    ...overrides,
  };
}

function result(
  status: "BLOCKER" | "REVIEW" | "PASS" | "EXTERNAL",
  id: string,
  title: string,
  overrides: Record<string, unknown> = {},
) {
  return {
    id,
    requirement_id: id,
    status,
    title,
    explanation: `${status} 설명`,
    action: "확인하세요.",
    announcement_evidence: { source: "공고", locator: "p.1", excerpt: `${title} 공고 근거` },
    submission_evidence: { source: "submission.mp4", locator: "duration", excerpt: "61.0s" },
    source_mode: "generic_verifier",
    verification_plan_id: "P1",
    checker_type: "VIDEO_METADATA",
    measured_fact: "61.0s",
    expected_constraint: "<= 60 seconds",
    semantic_review: null,
    ...overrides,
  };
}

async function openWithSession(
  page: Page,
  session: object,
  path: string,
  readiness: { ack_required: boolean; eligible_requirement_count: number; reason_code: string | null }
    = { ack_required: false, eligible_requirement_count: 0, reason_code: "NOT_GENERIC" },
) {
  await page.addInitScript(([key, id]) => sessionStorage.setItem(key, id), ["final-check-session-id-v2", sessionId]);
  await page.route("**/api/sessions/**", route => {
    const url = new URL(route.request().url()).pathname;
    if (url.endsWith("/semantic-readiness")) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(readiness) });
    }
    if (url.endsWith(`/sessions/${sessionId}`)) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(session) });
    }
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"detail":"missing mock"}' });
  });
  await page.goto(path);
}

test("landing is outside the numbered workflow", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "검사 단계" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "How it works" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Evidence-first" })).toBeVisible();
});

test("landing uses approved copy and internally consistent example counts", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." })).toBeVisible();
  await expect(page.getByText("AI는 근거를 찾고, 확실한 조건은 코드가 검증합니다.", { exact: true })).toBeVisible();
  const preview = page.getByRole("region", { name: "Preflight 결과 예시" });
  await expect(preview.getByText("1 BLOCKER", { exact: true })).toBeVisible();
  await expect(preview.getByText("1 REVIEW", { exact: true })).toBeVisible();
  await expect(preview.getByText("3 PASS", { exact: true })).toBeVisible();
  await expect(preview).toContainText("61.0s");
  await expect(preview).toContainText("proposal.pdf · p.2");
  await expect(page.getByText("모든 BLOCKER는", { exact: false })).toHaveCount(0);
});

test("landing product proof is not intentionally tilted", async ({ page }) => {
  await page.goto("/");
  const transform = await page.getByRole("region", { name: "Preflight 결과 예시" }).evaluate(el => getComputedStyle(el).transform);
  expect(transform).toBe("none");
});

test("reduced motion disables nonessential product transitions", async ({ page }) => {
  await page.goto("/");
  const frame = page.locator(".product-frame").first();
  const normalSeconds = await frame.evaluate(element => parseFloat(getComputedStyle(element).transitionDuration));
  expect(normalSeconds).toBeGreaterThanOrEqual(0.12);
  expect(normalSeconds).toBeLessThanOrEqual(0.2);

  await page.emulateMedia({ reducedMotion: "reduce" });
  const reducedSeconds = await frame.evaluate(element => parseFloat(getComputedStyle(element).transitionDuration));
  expect(reducedSeconds).toBeLessThanOrEqual(0.001);
});

test("landing and app workspaces do not overflow the viewport", async ({ page }) => {
  await page.goto("/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);

  const session = baseSession({
    validation_profile: "generic",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
  });
  await openWithSession(page, session, "/upload");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
});

test("deep links recover to the nearest available workflow step", async ({ page }) => {
  await openWithSession(page, baseSession(), "/requirements");
  await expect(page.getByRole("link", { name: "공고 단계로 돌아가기" })).toHaveAttribute("href", "/announcement");

  await openWithSession(page, baseSession({ generic_profile: { status: "REVIEW_REQUIRED" } }), "/upload");
  await expect(page.getByRole("link", { name: "요구사항 검토로 돌아가기" })).toHaveAttribute("href", "/requirements");

  await openWithSession(page, baseSession({
    validation_profile: "generic",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
  }), "/results");
  await expect(page.getByRole("link", { name: "제출파일 단계로 돌아가기" })).toHaveAttribute("href", "/upload");
});

test("recheck recovery returns to existing results", () => {
  const session = baseSession({ results: [result("REVIEW", "G001", "내용 요구사항")] });
  expect(recoveryHref(session as Parameters<typeof recoveryHref>[0], "recheck")).toBe("/results");
});

test("confirmed generic profile can enter upload when planner is REVIEW_REQUIRED", async ({ page }) => {
  const session = baseSession({
    validation_profile: "generic", verification_plan_state: "REVIEW_REQUIRED",
    generic_profile: { status: "CONFIRMED", execution_kind: "ACTUAL", requirements: [], extraction_complete: true },
  });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("heading", { level: 1, name: /제출/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /요구사항 검토로 돌아가기/ })).toHaveCount(0);
});

test("preflight scope comes from the verified plan and semantic readiness", async ({ page }) => {
  const confirmedSession = baseSession({
    validation_profile: "generic",
    source_mode: "generic_verifier",
    verification_plan_state: "READY",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
    verification_plan: {
      plan_set_id: "plan-set", profile_id: "profile", profile_version: 1,
      announcement_sha256: "a".repeat(64), announcement_text_sha256: "b".repeat(64),
      confirmed_requirements_sha256: "c".repeat(64),
      planner_provenance: { provider: "Codex CLI", model: "gpt-5.6-sol", prompt_version: "task08", prompt_sha256: "d".repeat(64), execution_kind: "ACTUAL" },
      plan_schema_version: "task08-verification-plan-v1", created_at: stamp,
      plans: [{
        plan_id: "P1", requirement_id: "G001", planner_disposition: "CANDIDATE", checker_type: "VIDEO_METADATA", status: "VERIFIED", gate_reasons: [],
        target_selector: { kind: "UNIQUE_EXTENSION", value: ".mp4" },
        constraint: { field: "duration_seconds", operator: "<=", value: 60, unit: "seconds" },
        parameter_provenance: { evidence_quote: "60초 이내", evidence_start: 0, evidence_end: 6, source_substring: "60초 이내", normalized_value: 60, operator: "<=" },
        planner_reason: "deterministic video duration",
      }],
    },
    files: [
      { name: "submission.mp4", size_bytes: 1024, media_type: "video/mp4", sha256: "e".repeat(64) },
      { name: "proposal.pdf", size_bytes: 2048, media_type: "application/pdf", sha256: "f".repeat(64) },
    ],
  });
  await openWithSession(page, confirmedSession, "/upload", { ack_required: true, eligible_requirement_count: 1, reason_code: null });
  const scope = page.getByRole("region", { name: "이번 검사" });
  await expect(scope).toContainText("영상 길이");
  await expect(scope).toContainText("PDF 내용 근거");
  await expect(scope).toContainText("1개 자동 검사");
  await expect(scope).toContainText("1개 AI 근거 검토");
  const packagePane = page.getByRole("region", { name: "제출 패키지" });
  await expect(packagePane).not.toContainText("61.0s");
  await expect(packagePane).not.toContainText("45.0s");
  await expect(packagePane).not.toContainText("페이지 수:");
});

test("preflight remains available when the automatic plan requires review", async ({ page }) => {
  const session = baseSession({
    validation_profile: "generic",
    source_mode: "generic_review",
    verification_plan: null,
    verification_plan_state: "REVIEW_REQUIRED",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
  });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("heading", { level: 1, name: /제출/ })).toBeVisible();
  const scope = page.getByRole("region", { name: "이번 검사" });
  await expect(scope).toContainText("자동 검사 계획이 확정되지 않았습니다.");
  await expect(scope).toContainText("REVIEW/수동 검토");
});

test("unconfirmed custom profile fails closed from upload to requirements", async ({ page }) => {
  const session = baseSession({ generic_profile: { status: "REVIEW_REQUIRED" } });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("link", { name: /요구사항 검토/ })).toHaveAttribute("href", "/requirements");
});

test("requirements Inspector highlights only the exact stored evidence offsets", async ({ page }) => {
  const text = "앞문장 기대효과를 포함해야 합니다. 뒷문장";
  const quote = "기대효과를 포함해야 합니다.";
  const start = text.indexOf(quote);
  const end = start + quote.length;
  const provenance = {
    provider: "SIMULATED browser fixture", model: "fixture", prompt_version: "fixture-v1",
    prompt_sha256: "a".repeat(64), execution_kind: "SIMULATED",
  };
  const requirement = {
    requirement_id: "G001", rule: quote, modality: "MUST", severity: "REVIEW", verifier: "SEMANTIC",
    condition: "", evidence: { source_section: "본문", quote }, confidence: 0.5,
    extraction_status: "EXTRACTED", evidence_start: start, evidence_end: end, issues: [],
    original: { requirement_id: "G001", rule: quote, modality: "MUST", severity: "REVIEW", verifier: "SEMANTIC", condition: "", evidence: { source_section: "본문", quote }, confidence: 0.5 },
    stage1: provenance, stage2_decision: "KEEP", stage2_reason: "fixture", stage2: provenance, authoritative: false,
  };
  const profile = {
    profile_type: "generic", profile_id: "profile-1", status: "REVIEW_REQUIRED",
    announcement: { source_type: "TEXT", name: "공고.txt", sha256: "b".repeat(64), text_sha256: "c".repeat(64), text, ingestion_status: "READABLE", page_count: null, notice: "" },
    requirements: [
      requirement,
      { ...requirement, requirement_id: "G002", extraction_status: "CONFIRMED", authoritative: true, original: { ...requirement.original, requirement_id: "G002" } },
      { ...requirement, requirement_id: "G003", extraction_status: "NEEDS_REVIEW", original: { ...requirement.original, requirement_id: "G003" } },
      { ...requirement, requirement_id: "G004", extraction_status: "UNSUPPORTED", original: { ...requirement.original, requirement_id: "G004" } },
    ], raw_candidates: [requirement.original], gated_candidate_ids: ["G001"],
    stage2_reviews: [], provider: provenance.provider, execution_kind: "SIMULATED", stage1: provenance, stage2: provenance,
    pipeline_status: "COMPLETE", pipeline_error: null, raw_candidate_count: 1, gated_candidate_count: 1,
    dropped_candidate_count: 0, review_batches: 1, failed_batches: [], overflow: false, overflow_policy: "",
    extraction_complete: true, notices: [], history: [], version: 1, created_at: stamp, updated_at: stamp,
  };
  const session = baseSession({ generic_profile: profile });
  await openWithSession(page, session, "/announcement");
  await expect(page.getByRole("button", { name: "Profile 확정" })).toHaveCount(0);
  for (const [id, label] of [["G001", "AI EXTRACTED"], ["G002", "HUMAN CONFIRMED"], ["G003", "NEEDS REVIEW"], ["G004", "UNSUPPORTED"]]) {
    await expect(page.getByRole("article", { name: `요구사항 ${id}`, exact: true })).toContainText(label);
  }
  await page.getByRole("button", { name: "요구사항 G001" }).click();
  await expect(page.getByRole("region", { name: "공고 원문" }).locator("mark")).toHaveText(quote);
  await page.goto("/requirements");
  for (const [id, label] of [["G001", "AI EXTRACTED"], ["G002", "HUMAN CONFIRMED"], ["G003", "NEEDS REVIEW"], ["G004", "UNSUPPORTED"]]) {
    await expect(page.getByRole("article", { name: `요구사항 ${id}`, exact: true })).toContainText(label);
  }

  await page.getByRole("button", { name: "요구사항 G001" }).click();
  const sourcePane = page.getByRole("region", { name: "공고 원문" });
  await expect(sourcePane.locator("mark")).toHaveText(quote);
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(inspector.getByLabel("요구사항 문장")).toHaveValue(quote);
  await expect(inspector.getByRole("button", { name: "항목 승인" })).toBeVisible();
});

test("demo requirements Inspector uses padded content and action groups", async ({ page }) => {
  const demo = baseSession({
    mode: "demo", validation_profile: "frozen_v15", source_mode: "validator",
    requirements: [{
      id: "R01", title: "동결 요구사항", description: "Validator v1.5 예시",
      verifier: "DETERMINISTIC",
      announcement_evidence: { source: "동결 공고", locator: "R01", excerpt: "동결 근거" },
    }],
  });
  await openWithSession(page, demo, "/requirements");
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(inspector.locator(".workspace-body")).toContainText("실시간 AI 추출 결과가 아닙니다.");
  await expect(inspector.locator(".workspace-actions").getByRole("link", { name: "제출파일 선택하기" })).toBeVisible();
});

test("results use the audited priority, counted status tabs, and evidence chain", async ({ page }, testInfo) => {
  const completedSession = baseSession({
    validation_profile: "generic",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
    run_state: "COMPLETE",
    status: "BLOCKED",
    results: [
      result("EXTERNAL", "G004", "외부 확인"),
      result("PASS", "G003", "파일 형식"),
      result("REVIEW", "G002", "내용 요구사항", { checker_type: null, measured_fact: null }),
      result("BLOCKER", "G001", "영상 길이"),
    ],
  });
  await openWithSession(page, completedSession, "/results");

  const cards = page.locator("[data-testid='result-card']");
  await expect(cards).toHaveCount(4);
  await expect(cards.nth(0)).toContainText("BLOCKER");
  await expect(cards.nth(1)).toContainText("REVIEW");
  await expect(cards.nth(2)).toContainText("PASS");
  await expect(cards.nth(3)).toContainText("EXTERNAL");
  for (const tab of ["전체 4", "BLOCKER 1", "REVIEW 1", "PASS 1", "EXTERNAL 1"]) {
    await expect(page.getByRole("button", { name: tab, exact: true })).toBeVisible();
  }
  await expect(cards.nth(0).getByText("RULE", { exact: true })).toBeVisible();
  await expect(cards.nth(0).getByText("EVIDENCE", { exact: true })).toBeVisible();
  await expect(cards.nth(0).getByText("VERDICT", { exact: true })).toBeVisible();
  const columns = await cards.nth(0).evaluate(element => getComputedStyle(element).gridTemplateColumns.trim().split(/\s+/).length);
  expect(columns).toBe(testInfo.project.name === "mobile" ? 1 : 3);
});

test("Evidence Inspector traps focus, closes with Escape, and restores its opener", async ({ page }, testInfo) => {
  const completedSession = baseSession({
    validation_profile: "generic",
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
    run_state: "COMPLETE",
    status: "BLOCKED",
    results: [result("BLOCKER", "G001", "영상 길이")],
  });
  await openWithSession(page, completedSession, "/results");

  const opener = page.getByRole("button", { name: /근거 자세히 보기/ }).first();
  await opener.focus();
  await opener.click();
  const drawer = page.getByRole("dialog", { name: "Evidence Inspector" });
  await expect(drawer).toBeVisible();
  await expect(drawer).toContainText("공고 요구사항");
  await expect(drawer).toContainText("제출파일 근거");
  if (testInfo.project.name === "mobile") {
    const box = await drawer.boundingBox();
    expect(box?.width).toBeCloseTo(page.viewportSize()?.width ?? 0, 3);
  }

  const close = drawer.getByRole("button", { name: "Evidence Inspector 닫기" });
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect.poll(() => drawer.evaluate(element => element.contains(document.activeElement))).toBe(true);
  await page.keyboard.press("Tab");
  await expect.poll(() => drawer.evaluate(element => element.contains(document.activeElement))).toBe(true);
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(opener).toBeFocused();
});
