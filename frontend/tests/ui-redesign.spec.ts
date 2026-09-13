import { expect, test, type Page } from "@playwright/test";

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

async function openWithSession(
  page: Page,
  session: object,
  path: string,
  readiness = { ack_required: false, eligible_requirement_count: 0, reason_code: "NOT_GENERIC" },
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

test("confirmed generic profile can enter upload when planner is REVIEW_REQUIRED", async ({ page }) => {
  const session = baseSession({
    validation_profile: "generic", verification_plan_state: "REVIEW_REQUIRED",
    generic_profile: { status: "CONFIRMED", execution_kind: "ACTUAL", requirements: [], extraction_complete: true },
  });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("heading", { level: 1, name: /제출/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /요구사항 검토로 돌아가기/ })).toHaveCount(0);
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
    requirements: [requirement], raw_candidates: [requirement.original], gated_candidate_ids: ["G001"],
    stage2_reviews: [], provider: provenance.provider, execution_kind: "SIMULATED", stage1: provenance, stage2: provenance,
    pipeline_status: "COMPLETE", pipeline_error: null, raw_candidate_count: 1, gated_candidate_count: 1,
    dropped_candidate_count: 0, review_batches: 1, failed_batches: [], overflow: false, overflow_policy: "",
    extraction_complete: true, notices: [], history: [], version: 1, created_at: stamp, updated_at: stamp,
  };
  const session = baseSession({ generic_profile: profile });
  await openWithSession(page, session, "/announcement");
  await expect(page.getByRole("button", { name: "Profile 확정" })).toHaveCount(0);
  await page.getByRole("button", { name: "요구사항 G001" }).click();
  await expect(page.getByRole("region", { name: "공고 원문" }).locator("mark")).toHaveText(quote);
  await page.goto("/requirements");

  await page.getByRole("button", { name: "요구사항 G001" }).click();
  const sourcePane = page.getByRole("region", { name: "공고 원문" });
  await expect(sourcePane.locator("mark")).toHaveText(quote);
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(inspector.getByLabel("요구사항 문장")).toHaveValue(quote);
  await expect(inspector.getByRole("button", { name: "항목 승인" })).toBeVisible();
});
