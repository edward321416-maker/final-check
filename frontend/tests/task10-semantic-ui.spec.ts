import { expect, test, type Page } from "@playwright/test";

const sessionId = "task10-ui-session";
const stamp = "2026-09-09T00:00:00.000Z";

function baseSession(overrides: Record<string, unknown> = {}) {
  return {
    id: sessionId, created_at: stamp, updated_at: stamp, mode: "custom",
    source_mode: "generic_review", announcement_name: "공고.txt", validation_profile: "generic", engine_sha256: null,
    generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
    verification_plan: null, verification_plan_state: "REVIEW_REQUIRED", verification_plan_error: null,
    current_job_id: null, current_job: null, run_state: "NOT_STARTED", validation_complete: false, run_error: null,
    requirements: [], files: [{ name: "submission.pdf", size_bytes: 100, media_type: "application/pdf", sha256: "a".repeat(64) }],
    results: [], previous_results: [], status: "REVIEW_REQUIRED", revision: 1, fixture: null,
    ...overrides,
  };
}

function semanticResult(overrides: Record<string, unknown> = {}) {
  return {
    id: "G001:semantic", requirement_id: "G001", status: "REVIEW", title: "내용 요구사항", explanation: "명확한 관련 근거 후보를 찾지 못했습니다.",
    action: "원문과 공고문을 직접 대조하세요.", announcement_evidence: { source: "공고", locator: "p.1", excerpt: "필수 내용" },
    submission_evidence: null, source_mode: "generic_review", verification_plan_id: null, checker_type: null, measured_fact: null, expected_constraint: null,
    semantic_review: { assessment: "NO_CLEAR_EVIDENCE", coverage: "FULL", reason_code: null, evidence: [], evidence_fingerprint: "old", provider: null },
    ...overrides,
  };
}

async function openWithSession(page: Page, current: () => object, readiness: { ack_required: boolean; eligible_requirement_count: number; reason_code: string | null } = { ack_required: false, eligible_requirement_count: 0, reason_code: "NOT_GENERIC" }) {
  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), sessionId);
  await page.route("**/api/sessions/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/semantic-readiness")) return route.fulfill({ contentType: "application/json", body: JSON.stringify(readiness) });
    if (path.endsWith(`/sessions/${sessionId}`)) return route.fulfill({ contentType: "application/json", body: JSON.stringify(current()) });
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"detail":"missing mock"}' });
  });
  await page.goto("/upload");
}

test("does not block deterministic-only preflight with a semantic acknowledgement", async ({ page }) => {
  await openWithSession(page, () => baseSession());
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
});

test("requires the semantic text acknowledgement before preflight", async ({ page }) => {
  await openWithSession(page, () => baseSession(), { ack_required: true, eligible_requirement_count: 1, reason_code: null });
  await expect(page.getByText("AI 내용 검토 안내", { exact: true })).toBeVisible();
  const acknowledgement = page.getByRole("checkbox", { name: "PDF에서 추출된 전체 텍스트가 AI 내용 검토에 사용되는 것을 확인했습니다." });
  await expect(acknowledgement).toBeVisible();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
  await acknowledgement.check();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
});

test("uses deterministic-only activity copy when no semantic review is eligible", async ({ page }) => {
  await openWithSession(page, () => baseSession({ run_state: "RUNNING" }));
  await expect(page.getByText("객관적 제출 조건을 확인하고 있습니다.", { exact: true })).toBeVisible();
  await expect(page.getByLabel("제출파일")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
});

test("polls a running semantic validation and routes only after completion", async ({ page }) => {
  const running = baseSession({ run_state: "RUNNING", results: [] });
  const complete = baseSession({ run_state: "COMPLETE", results: [semanticResult()] });
  let gets = 0;
  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), sessionId);
  await page.route("**/api/sessions/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/semantic-readiness")) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ack_required: true, eligible_requirement_count: 1, reason_code: null }) });
    if (path.endsWith("/validate")) return route.fulfill({ contentType: "application/json", body: JSON.stringify(running) });
    if (path.endsWith(`/sessions/${sessionId}`)) {
      gets += 1;
      const value = gets === 1 ? baseSession() : gets > 2 ? complete : baseSession({ run_state: "RUNNING" });
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(value) });
    }
    return route.abort();
  });
  await page.goto("/upload");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page.getByText("객관적 조건과 PDF 내용 근거를 확인하고 있습니다.", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/results$/);
  expect(gets).toBeGreaterThan(1);
});

test("ignores a stale semantic completion after the active session is replaced", async ({ page }) => {
  const oldSessionId = "old-review-session";
  const newSessionId = "new-review-session";
  const oldRunning = baseSession({ id: oldSessionId, announcement_name: "이전 세션 공고.txt", run_state: "RUNNING", results: [] });
  const oldComplete = baseSession({ id: oldSessionId, announcement_name: "이전 세션 공고.txt", run_state: "COMPLETE",
    results: [semanticResult({ title: "오래된 세션 결과" })] });
  const newSession = baseSession({ id: newSessionId, mode: "demo", source_mode: "validator", announcement_name: "새 세션 공고.txt",
    validation_profile: "frozen_v15", generic_profile: null, files: [], run_state: "NOT_STARTED", results: [],
    requirements: [{ id: "R01", title: "새 세션 동결 요구사항", description: "새 세션 확인", verifier: "DETERMINISTIC",
      announcement_evidence: { source: "동결 공고", locator: "R01", excerpt: "동결 근거" } }],
  });
  let oldSessionGets = 0;
  let releaseOldCompletion!: () => void;
  const oldCompletionHeld = new Promise<void>(resolve => { releaseOldCompletion = resolve; });
  let markOldPollStarted!: () => void;
  const oldPollStarted = new Promise<void>(resolve => { markOldPollStarted = resolve; });

  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), oldSessionId);
  await page.route("**/api/**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith("/semantic-readiness")) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ack_required: true, eligible_requirement_count: 1, reason_code: null }) });
    }
    if (request.method() === "GET" && path.endsWith(`/sessions/${oldSessionId}`)) {
      oldSessionGets += 1;
      if (oldSessionGets === 1) return route.fulfill({ contentType: "application/json", body: JSON.stringify(oldRunning) });
      markOldPollStarted();
      await oldCompletionHeld;
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(oldComplete) });
    }
    if (request.method() === "POST" && path.endsWith("/api/sessions")) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(newSession) });
    }
    if (request.method() === "POST" && path.endsWith(`/sessions/${newSessionId}/demo-announcement`)) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(newSession) });
    }
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"detail":"missing mock"}' });
  });

  await page.goto("/upload");
  await expect(page.getByText("객관적 조건과 PDF 내용 근거를 확인하고 있습니다.", { exact: true })).toBeVisible();
  await oldPollStarted;
  await page.getByRole("link", { name: /FINAL CHECK/ }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.getByRole("button", { name: "demo 검사 시작하기" }).click();
  await expect(page).toHaveURL(/\/announcement$/);
  await expect(page.getByText("새 세션 동결 요구사항", { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("final-check-session-id-v2"))).toBe(newSessionId);

  releaseOldCompletion();
  await page.waitForTimeout(250);

  expect(oldSessionGets).toBe(2);
  expect(await page.evaluate(() => sessionStorage.getItem("final-check-session-id-v2"))).toBe(newSessionId);
  await expect(page).toHaveURL(/\/announcement$/);
  await expect(page.getByText("오래된 세션 결과", { exact: true })).toHaveCount(0);
  await expect(page.getByText("새 세션 동결 요구사항", { exact: true })).toBeVisible();
});

test("retries a transient running-session poll failure and routes after a later completion", async ({ page }) => {
  const running = baseSession({ run_state: "RUNNING", results: [] });
  const complete = baseSession({ run_state: "COMPLETE", results: [semanticResult()] });
  let gets = 0;
  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), sessionId);
  await page.route("**/api/sessions/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/semantic-readiness")) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ack_required: true, eligible_requirement_count: 1, reason_code: null }) });
    if (path.endsWith("/validate")) return route.fulfill({ contentType: "application/json", body: JSON.stringify(running) });
    if (path.endsWith(`/sessions/${sessionId}`)) {
      gets += 1;
      if (gets === 1) return route.fulfill({ contentType: "application/json", body: JSON.stringify(baseSession()) });
      if (gets === 2) return route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"temporary poll failure"}' });
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(complete) });
    }
    return route.abort();
  });
  await page.goto("/upload");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page.getByText("객관적 조건과 PDF 내용 근거를 확인하고 있습니다.", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/results$/);
  expect(gets).toBe(3);
});

test("keeps a failed semantic poll actionable on the upload screen", async ({ page }) => {
  const running = baseSession({ run_state: "RUNNING", results: [] });
  const failed = baseSession({ run_state: "FAILED", run_error: "PACKAGE_CHANGED_DURING_RUN", results: [] });
  let gets = 0;
  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), sessionId);
  await page.route("**/api/sessions/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/semantic-readiness")) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ack_required: true, eligible_requirement_count: 1, reason_code: null }) });
    if (path.endsWith("/validate")) return route.fulfill({ contentType: "application/json", body: JSON.stringify(running) });
    if (path.endsWith(`/sessions/${sessionId}`)) {
      gets += 1;
      const value = gets === 1 ? baseSession() : failed;
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(value) });
    }
    return route.abort();
  });
  await page.goto("/upload");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  await expect(page).toHaveURL(/\/upload$/);
  await expect(page.getByRole("alert", { name: "작업 오류" })).toContainText("PACKAGE_CHANGED_DURING_RUN");
  await expect(page.getByRole("alert", { name: "작업 오류" })).toContainText("현재 제출 패키지를 확인한 뒤 다시 실행할 수 있습니다.");
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
});

test("resumes polling after an upload screen reload", async ({ page }) => {
  let gets = 0;
  await page.addInitScript((id) => sessionStorage.setItem("final-check-session-id-v2", id), sessionId);
  await page.route("**/api/sessions/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/semantic-readiness")) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ack_required: true, eligible_requirement_count: 1, reason_code: null }) });
    if (path.endsWith(`/sessions/${sessionId}`)) {
      gets += 1;
      const value = gets > 3 ? baseSession({ run_state: "COMPLETE", results: [semanticResult()] }) : baseSession({ run_state: "RUNNING" });
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(value) });
    }
    return route.abort();
  });
  await page.goto("/upload");
  await expect(page.getByText("객관적 조건과 PDF 내용 근거를 확인하고 있습니다.", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page).toHaveURL(/\/results$/);
});

test("renders no more than three verified semantic evidence excerpts", async ({ page }) => {
  const evidence = [1, 2, 3, 4].map(pageNumber => ({ source: "submission.pdf", locator: `p.${pageNumber}`, excerpt: `근거 후보 ${pageNumber}` }));
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [semanticResult({ submission_evidence: evidence[0], semantic_review: { assessment: "RELATED_EVIDENCE_FOUND", coverage: "FULL", reason_code: null, evidence, evidence_fingerprint: "new", provider: null } })] }));
  await page.goto("/results");
  const finding = page.getByRole("article", { name: "G001 내용 요구사항" });
  await expect(finding.getByText("추가 근거 후보", { exact: true })).toBeVisible();
  await expect(finding.getByText("근거 후보 1", { exact: true })).toBeVisible();
  await expect(finding.locator(".evidence-label", { hasText: "근거 후보 3" })).toBeVisible();
  await expect(finding.getByText("근거 후보 4", { exact: true })).toHaveCount(0);
});

test("labels a completed full-coverage no-evidence review as no clear evidence, not unexecuted", async ({ page }) => {
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [semanticResult()] }));
  await page.goto("/results");
  const finding = page.getByRole("article", { name: "G001 내용 요구사항" });
  await expect(finding.getByText("제출파일에서 명확한 관련 근거 후보를 찾지 못했습니다. 직접 대조가 필요합니다.", { exact: true })).toBeVisible();
  await expect(finding.getByText("이 항목의 제출파일 검증은 실행되지 않았습니다. 직접 대조가 필요합니다.", { exact: true })).toHaveCount(0);
  await expect(finding.getByText("위반", { exact: false })).toHaveCount(0);
});

test("does not turn partial semantic coverage into a whole-document absence claim", async ({ page }) => {
  const partial = semanticResult({
    submission_evidence: null,
    semantic_review: { assessment: "NO_CLEAR_EVIDENCE", coverage: "PARTIAL", reason_code: null, evidence: [], evidence_fingerprint: "partial", provider: null },
  });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [partial] }));
  await page.goto("/results");
  const finding = page.getByRole("article", { name: "G001 내용 요구사항" });
  await expect(finding.getByText("문서 일부만 확인되어 문서 전체의 관련 근거 유무를 판단할 수 없습니다. 직접 대조가 필요합니다.", { exact: true })).toBeVisible();
  await expect(finding.getByText("제출파일에서 명확한 관련 근거 후보를 찾지 못했습니다. 직접 대조가 필요합니다.", { exact: true })).toHaveCount(0);
});

test("places the Korean semantic-unavailable explanation before its reason code", async ({ page }) => {
  const unavailable = semanticResult({ explanation: "AI 내용 검토를 사용할 수 없어 직접 확인이 필요합니다.", semantic_review: { assessment: null, coverage: "FULL", reason_code: "SEMANTIC_PROVIDER_UNAVAILABLE", evidence: [], evidence_fingerprint: "unavailable", provider: null } });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [unavailable] }));
  await page.goto("/results");
  const finding = page.getByRole("article", { name: "G001 내용 요구사항" });
  await finding.getByRole("button", { name: /근거 자세히 보기/ }).click();
  const drawer = page.getByRole("dialog", { name: "Evidence Inspector" });
  await drawer.getByText("기술 세부 보기", { exact: true }).click();
  const text = await drawer.innerText();
  expect(text.indexOf("AI 내용 검토를 사용할 수 없어 직접 확인이 필요합니다.")).toBeLessThan(text.indexOf("SEMANTIC_PROVIDER_UNAVAILABLE"));
});

test("reports a REVIEW evidence change without a fake status transition", async ({ page }) => {
  const previous = semanticResult();
  const current = semanticResult({ submission_evidence: { source: "submission.pdf", locator: "p.7", excerpt: "관련 근거" }, semantic_review: { assessment: "RELATED_EVIDENCE_FOUND", coverage: "FULL", reason_code: null, evidence: [{ source: "submission.pdf", locator: "p.7", excerpt: "관련 근거" }], evidence_fingerprint: "new", provider: null } });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [current], previous_results: [previous] }));
  await page.goto("/results");
  const comparison = page.getByRole("region", { name: "재검사 비교" });
  await expect(comparison).toContainText("내용 근거 상태가 변경되었습니다.");
  await expect(comparison).toContainText("이전: 명확한 근거 후보 미발견");
  await expect(comparison).toContainText("현재: p.7 관련 근거 후보 발견");
});

test("keeps PARTIAL coverage explicit in a REVIEW-to-REVIEW fingerprint comparison", async ({ page }) => {
  const partialReview = {
    assessment: "NO_CLEAR_EVIDENCE", coverage: "PARTIAL", reason_code: null, evidence: [], provider: null,
  };
  const previous = semanticResult({ semantic_review: { ...partialReview, evidence_fingerprint: "partial-old" } });
  const current = semanticResult({ semantic_review: { ...partialReview, evidence_fingerprint: "partial-new" } });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [current], previous_results: [previous] }));
  await page.goto("/results");
  const comparison = page.getByRole("region", { name: "재검사 비교" });
  await expect(comparison).toContainText("내용 근거 상태가 변경되었습니다.");
  await expect(comparison).toContainText("현재: 문서 일부만 확인되어 관련 근거 후보 유무 판단 불가");
  await expect(comparison.getByText("현재: 명확한 근거 후보 미발견", { exact: true })).toHaveCount(0);
});

test("keeps NONE coverage explicit in a REVIEW-to-REVIEW reason comparison", async ({ page }) => {
  const noCoverage = {
    assessment: "NO_CLEAR_EVIDENCE", coverage: "NONE", evidence: [], evidence_fingerprint: "none", provider: null,
  };
  const previous = semanticResult({ semantic_review: { ...noCoverage, reason_code: "PDF_TEXT_UNAVAILABLE" } });
  const current = semanticResult({ semantic_review: { ...noCoverage, reason_code: "SEMANTIC_PROVIDER_UNAVAILABLE" } });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [current], previous_results: [previous] }));
  await page.goto("/results");
  const comparison = page.getByRole("region", { name: "재검사 비교" });
  await expect(comparison).toContainText("내용 근거 상태가 변경되었습니다.");
  await expect(comparison).toContainText("현재: 문서 내용 검토 미실행/사용 불가로 관련 근거 후보 유무 판단 불가");
  await expect(comparison.getByText("현재: 명확한 근거 후보 미발견", { exact: true })).toHaveCount(0);
});

test("keeps status-change comparison intact", async ({ page }) => {
  const previous = semanticResult({ status: "BLOCKER" });
  const current = semanticResult({ status: "PASS" });
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", results: [current], previous_results: [previous] }));
  await page.goto("/results");
  const comparison = page.getByRole("region", { name: "재검사 비교" });
  await expect(comparison).toContainText("1개 판정 변경");
  await expect(comparison).toContainText("BLOCKER");
  await expect(comparison).toContainText("PASS");
});

test("describes READY as deterministic readiness without claiming every REVIEW blocks it", async ({ page }) => {
  await openWithSession(page, () => baseSession({ run_state: "COMPLETE", status: "READY", validation_complete: true, results: [semanticResult()] }));
  await page.goto("/results");
  const banner = page.getByRole("region", { name: "전체 검사 상태" });
  await expect(banner).toContainText("자동 확인 가능한 필수 조건을 충족했습니다.");
  await expect(banner).toContainText("자동 확인 가능한 필수 조건의 결과와 남아 있는 REVIEW 항목을 함께 확인하세요.");
  await expect(banner).not.toContainText("REVIEW와 EXTERNAL을 직접 확인하기 전에는 제출 준비 완료로 판단하지 않습니다.");
});
