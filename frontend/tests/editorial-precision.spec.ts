import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import type { CheckSession, SemanticAssessment, ValidationResult, VerificationPlanSet } from "../types/check";
import type { ProfileRequirement } from "../types/profile";

const qaStateNames = [
  "01-landing",
  "02-custom-extraction-provisional",
  "03-human-review-selected",
  "04-package-plan-ready",
  "05-package-plan-review-required",
  "06-result-blocker",
  "07-result-ready",
  "08-semantic-related-evidence-review",
  "09-semantic-no-clear-evidence-review",
  "10-evidence-inspector-open",
  "11-actionable-recovery",
  "12-recheck-comparison",
] as const;

const editorialSessionId = "editorial-precision-session";
const editorialStamp = "2026-09-13T00:00:00.000Z";
const backendPlannerErrors = new Set(["PLANNER_UNAVAILABLE", "PLANNER_SCHEMA_REJECTED", "PROCESS_RESTART"]);

function expectBackendReachablePlannerTransition(session: CheckSession) {
  if (session.verification_plan_state === "READY") {
    expect(session.verification_plan, "READY planner state requires a compiled plan").not.toBeNull();
    expect(session.verification_plan_error, "READY planner state clears its error").toBeNull();
    expect(session.source_mode, "READY planner state selects generic_verifier").toBe("generic_verifier");
    return;
  }

  expect(session.verification_plan, `${session.verification_plan_state} planner state has no compiled plan`).toBeNull();
  if (session.verification_plan_state === "REVIEW_REQUIRED") {
    expect(
      backendPlannerErrors.has(session.verification_plan_error ?? ""),
      "REVIEW_REQUIRED planner state requires a backend-emitted error",
    ).toBe(true);
    expect(session.source_mode, "planner failure selects generic_review").toBe("generic_review");
  } else {
    expect(session.verification_plan_error, `${session.verification_plan_state} planner state clears its error`).toBeNull();
  }
}

function confirmedGenericSession(overrides: Partial<CheckSession> = {}): CheckSession {
  const quote = "영상은 60초 이내여야 합니다.";
  const provenance = {
    provider: "SIMULATED browser fixture", model: "fixture", prompt_version: "fixture-v1",
    prompt_sha256: "a".repeat(64), execution_kind: "SIMULATED",
  } as const;
  const requirement: ProfileRequirement = {
    requirement_id: "G001", rule: quote, modality: "MUST", severity: "REVIEW", verifier: "SEMANTIC",
    condition: "", evidence: { source_section: "제출 규격", quote }, confidence: 0.9,
    extraction_status: "CONFIRMED", evidence_start: 0, evidence_end: quote.length, issues: [],
    original: { requirement_id: "G001", rule: quote, modality: "MUST", severity: "REVIEW", verifier: "SEMANTIC", condition: "", evidence: { source_section: "제출 규격", quote }, confidence: 0.9 },
    stage1: provenance, stage2_decision: "KEEP", stage2_reason: "fixture", stage2: provenance, authoritative: true,
  };
  return {
    id: editorialSessionId, created_at: editorialStamp, updated_at: editorialStamp, mode: "custom",
    source_mode: "generic_review", announcement_name: "공고.txt", validation_profile: "generic",
    engine_sha256: null, verification_plan: null, verification_plan_state: "NOT_STARTED", verification_plan_error: null,
    current_job_id: null, current_job: null, run_state: "NOT_STARTED", validation_complete: false, run_error: null,
    requirements: [], files: [], results: [], previous_results: [], status: null, revision: 0, fixture: null,
    generic_profile: {
      profile_type: "generic", profile_id: "profile-editorial", status: "CONFIRMED",
      announcement: { source_type: "TEXT", name: "공고.txt", sha256: "b".repeat(64), text_sha256: "c".repeat(64), text: quote, ingestion_status: "READABLE", page_count: null, notice: "" },
      requirements: [requirement], raw_candidates: [requirement.original], gated_candidate_ids: ["G001"], stage2_reviews: [],
      provider: provenance.provider, execution_kind: "SIMULATED", stage1: provenance, stage2: provenance,
      pipeline_status: "COMPLETE", pipeline_error: null, raw_candidate_count: 1, gated_candidate_count: 1,
      dropped_candidate_count: 0, review_batches: 1, failed_batches: [], overflow: false, overflow_policy: "",
      extraction_complete: true, notices: [], history: [], version: 1, created_at: editorialStamp, updated_at: editorialStamp,
    },
    ...overrides,
  };
}

function editorialResult(
  status: "BLOCKER" | "REVIEW" | "PASS" | "EXTERNAL",
  requirementId: string,
  title: string,
): ValidationResult {
  return {
    id: requirementId,
    requirement_id: requirementId,
    status,
    title,
    explanation: `${status} 판정 근거입니다.`,
    action: "해당 항목을 확인하세요.",
    announcement_evidence: { source: "공고문.pdf", locator: "11/16", excerpt: `${title} 공고 근거` },
    submission_evidence: { source: "submission.pdf", locator: "11/16", excerpt: `${title} 제출파일 근거` },
    source_mode: "generic_verifier",
    verification_plan_id: `P-${requirementId}`,
    checker_type: "PDF_PAGE_COUNT",
    measured_fact: "11 pages",
    expected_constraint: "<= 16 pages",
    semantic_review: null,
  };
}

function provisionalGenericSession(): CheckSession {
  const base = confirmedGenericSession();
  const requirement = base.generic_profile!.requirements[0];
  return {
    ...base,
    generic_profile: {
      ...base.generic_profile!,
      status: "DRAFT",
      requirements: [{ ...requirement, extraction_status: "EXTRACTED", authoritative: false }],
    },
  };
}

function verifiedPlanSet(): VerificationPlanSet {
  const quote = "영상은 60초 이내여야 합니다.";
  return {
    plan_set_id: "plan-set-editorial",
    profile_id: "profile-editorial",
    profile_version: 1,
    announcement_sha256: "b".repeat(64),
    announcement_text_sha256: "c".repeat(64),
    confirmed_requirements_sha256: "f".repeat(64),
    planner_provenance: {
      provider: "SIMULATED browser fixture",
      model: "fixture",
      prompt_version: "fixture-plan-v1",
      prompt_sha256: "9".repeat(64),
      execution_kind: "SIMULATED",
    },
    plan_schema_version: "task08-verification-plan-v1",
    created_at: editorialStamp,
    plans: [{
      plan_id: "P-G001",
      requirement_id: "G001",
      planner_disposition: "CANDIDATE",
      checker_type: "VIDEO_METADATA",
      status: "VERIFIED",
      gate_reasons: [],
      target_selector: { kind: "UNIQUE_EXTENSION", value: ".mp4" },
      constraint: { field: "duration_seconds", operator: "LTE", value: 60, unit: "seconds" },
      parameter_provenance: {
        evidence_quote: quote,
        evidence_start: 0,
        evidence_end: quote.length,
        source_substring: "60초 이내",
        normalized_value: 60,
        operator: "LTE",
      },
      planner_reason: "Deterministic fixture plan for a human-confirmed duration rule.",
    }],
  };
}

function packageSession(planState: "READY" | "REVIEW_REQUIRED"): CheckSession {
  const base = confirmedGenericSession();
  const extracted = base.generic_profile!.requirements[0];
  const deterministicRequirement: ProfileRequirement = {
    ...extracted,
    modality: "MUST",
    severity: "BLOCKER",
    verifier: "DETERMINISTIC",
    condition: "always",
  };
  return {
    ...base,
    source_mode: planState === "READY" ? "generic_verifier" : "generic_review",
    verification_plan: planState === "READY" ? verifiedPlanSet() : null,
    verification_plan_state: planState,
    verification_plan_error: planState === "REVIEW_REQUIRED" ? "PLANNER_UNAVAILABLE" : null,
    files: [{ name: "submission.mp4", size_bytes: 2048, media_type: "video/mp4", sha256: "d".repeat(64) }],
    generic_profile: { ...base.generic_profile!, requirements: [deterministicRequirement] },
  };
}

function singleResultSession(result: ValidationResult, status: "BLOCKED" | "REVIEW_REQUIRED" | "READY"): CheckSession {
  const base = result.source_mode === "generic_verifier" ? packageSession("READY") : confirmedGenericSession();
  return {
    ...base,
    source_mode: result.source_mode,
    verification_plan: result.source_mode === "generic_verifier" ? verifiedPlanSet() : null,
    verification_plan_state: result.source_mode === "generic_verifier" ? "READY" : "NOT_STARTED",
    verification_plan_error: null,
    run_state: "COMPLETE",
    validation_complete: status !== "REVIEW_REQUIRED",
    status,
    revision: 1,
    files: result.source_mode === "generic_verifier"
      ? [{ name: "submission.mp4", size_bytes: 4096, media_type: "video/mp4", sha256: "e".repeat(64) }]
      : [{ name: "submission.pdf", size_bytes: 4096, media_type: "application/pdf", sha256: "e".repeat(64) }],
    results: [result],
  };
}

function deterministicVideoResult(status: "BLOCKER" | "PASS"): ValidationResult {
  const duration = status === "BLOCKER" ? 61 : 45;
  return {
    id: "G001",
    requirement_id: "G001",
    status,
    title: "영상 길이",
    explanation: status === "BLOCKER" ? "영상이 60초를 초과했습니다." : "영상이 60초 이내입니다.",
    action: status === "BLOCKER" ? "영상을 60초 이내로 줄이세요." : "추가 조치가 필요하지 않습니다.",
    announcement_evidence: { source: "공고.txt", locator: "제출 규격", excerpt: "영상은 60초 이내여야 합니다." },
    submission_evidence: { source: "submission.mp4", locator: "ffprobe", excerpt: `duration_seconds=${duration}.0` },
    source_mode: "generic_verifier",
    verification_plan_id: "P-G001",
    checker_type: "VIDEO_METADATA",
    measured_fact: `duration_seconds=${duration}.0; expected LTE 60 SECONDS`,
    expected_constraint: "duration_seconds <= 60 seconds",
    semantic_review: null,
  };
}

function semanticReviewResult(assessment: SemanticAssessment): ValidationResult {
  const related = assessment === "RELATED_EVIDENCE_FOUND";
  const result = editorialResult("REVIEW", "G001", "기대효과를 구체적으로 작성");
  return {
    ...result,
    source_mode: "generic_review",
    checker_type: null,
    verification_plan_id: null,
    measured_fact: null,
    expected_constraint: null,
    submission_evidence: related
      ? { source: "submission.pdf", locator: "2", excerpt: "참여자의 접근성을 높이고 지역 협력의 지속성을 강화합니다." }
      : null,
    semantic_review: {
      assessment,
      coverage: "FULL",
      reason_code: related ? null : "NO_CLEAR_EVIDENCE",
      evidence: related
        ? [{ source: "submission.pdf", locator: "2", excerpt: "참여자의 접근성을 높이고 지역 협력의 지속성을 강화합니다." }]
        : [],
      evidence_fingerprint: related ? "1".repeat(64) : "2".repeat(64),
      provider: {
        provider: "SIMULATED browser fixture",
        model: "fixture",
        prompt_version: "fixture-semantic-v1",
        prompt_sha256: "3".repeat(64),
        execution_kind: "SIMULATED",
      },
    },
  };
}

function failedRunSession(): CheckSession {
  return {
    ...packageSession("READY"),
    run_state: "FAILED",
    run_error: "검사 작업이 중단되었습니다. 현재 제출 패키지를 확인한 뒤 다시 실행하세요.",
    status: "REVIEW_REQUIRED",
    validation_complete: false,
    results: [],
  };
}

async function openQaSession(page: Page, routePath: string, session: CheckSession) {
  await page.unroute("**/api/sessions/**");
  await openConfirmedGenericSession(page, routePath, session);
}

async function captureQa(page: Page, project: string, state: typeof qaStateNames[number]) {
  const directory = path.resolve("../artifacts/editorial-precision/screenshots", project);
  await fs.mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, `${state}.png`), fullPage: true });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow, `${state} must not overflow horizontally`).toBe(false);
}

type QaScenario = {
  name: typeof qaStateNames[number];
  render: (page: Page) => Promise<void>;
};

const qaScenarios: readonly QaScenario[] = [
  {
    name: "01-landing",
    render: async page => {
      await page.goto("/");
      await page.getByRole("link", { name: "제출 전 검사 시작하기" }).first().focus();
    },
  },
  {
    name: "02-custom-extraction-provisional",
    render: async page => {
      await openQaSession(page, "/announcement", provisionalGenericSession());
      await page.getByRole("button", { name: "요구사항 G001" }).focus();
    },
  },
  {
    name: "03-human-review-selected",
    render: async page => {
      await openQaSession(page, "/requirements", provisionalGenericSession());
      await page.getByRole("button", { name: "항목 승인" }).focus();
    },
  },
  {
    name: "04-package-plan-ready",
    render: async page => {
      await openQaSession(page, "/upload", packageSession("READY"));
      await page.getByRole("button", { name: "Preflight 실행하기" }).focus();
    },
  },
  {
    name: "05-package-plan-review-required",
    render: async page => {
      await openQaSession(page, "/upload", packageSession("REVIEW_REQUIRED"));
      await page.getByRole("button", { name: "Preflight 실행하기" }).focus();
    },
  },
  {
    name: "06-result-blocker",
    render: async page => {
      const blocker = deterministicVideoResult("BLOCKER");
      await openQaSession(page, "/results", singleResultSession(blocker, "BLOCKED"));
      await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).focus();
    },
  },
  {
    name: "07-result-ready",
    render: async page => {
      const pass = deterministicVideoResult("PASS");
      await openQaSession(page, "/results", singleResultSession(pass, "READY"));
      await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).focus();
    },
  },
  {
    name: "08-semantic-related-evidence-review",
    render: async page => {
      await openQaSession(page, "/results", singleResultSession(semanticReviewResult("RELATED_EVIDENCE_FOUND"), "REVIEW_REQUIRED"));
      await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).focus();
    },
  },
  {
    name: "09-semantic-no-clear-evidence-review",
    render: async page => {
      await openQaSession(page, "/results", singleResultSession(semanticReviewResult("NO_CLEAR_EVIDENCE"), "REVIEW_REQUIRED"));
      await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).focus();
    },
  },
  {
    name: "10-evidence-inspector-open",
    render: async page => {
      await openQaSession(page, "/results", singleResultSession(semanticReviewResult("RELATED_EVIDENCE_FOUND"), "REVIEW_REQUIRED"));
      await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).click();
      const drawer = page.getByRole("dialog", { name: "Evidence Inspector" });
      await expect(drawer).toBeVisible();
      await drawer.evaluate(async node => Promise.all(node.getAnimations().map(animation => animation.finished)));
      await page.evaluate(() => window.scrollTo(0, 0));
    },
  },
  {
    name: "11-actionable-recovery",
    render: async page => {
      await openQaSession(page, "/upload", failedRunSession());
      await page.getByRole("button", { name: "Preflight 실행하기" }).focus();
    },
  },
  {
    name: "12-recheck-comparison",
    render: async page => {
      const current = semanticReviewResult("RELATED_EVIDENCE_FOUND");
      const session = {
        ...singleResultSession(current, "REVIEW_REQUIRED"),
        revision: 2,
        previous_results: [semanticReviewResult("NO_CLEAR_EVIDENCE")],
      };
      await openQaSession(page, "/results", session);
      await page.getByRole("link", { name: /수정 후 재검사/ }).first().focus();
    },
  },
];

test("visual QA matrix declares all required states", () => {
  expect(qaScenarios.map(scenario => scenario.name)).toEqual(qaStateNames);
});

test("visual QA fixtures use backend-reachable transition pairs", () => {
  const extracted = provisionalGenericSession();
  expect.soft(
    [extracted.generic_profile?.status, extracted.generic_profile?.history.length],
    "successful retained extraction with no history finalizes as DRAFT",
  ).toEqual(["DRAFT", 0]);

  const planReview = packageSession("REVIEW_REQUIRED");
  expect.soft(
    [planReview.verification_plan_state, planReview.verification_plan_error],
    "planner failure must use a backend-emitted error",
  ).toEqual(["REVIEW_REQUIRED", "PLANNER_UNAVAILABLE"]);

  for (const state of ["08", "09", "10", "12"] as const) {
    const semantic = singleResultSession(semanticReviewResult("RELATED_EVIDENCE_FOUND"), "REVIEW_REQUIRED");
    expect.soft(
      [semantic.verification_plan_state, semantic.verification_plan_error],
      `semantic state ${state} retains the Task10 NOT_STARTED/null plan pair`,
    ).toEqual(["NOT_STARTED", null]);
  }

  const failed = failedRunSession();
  expect.soft(
    [failed.run_state, failed.status, failed.validation_complete, failed.results],
    "backend failed-run transition clears results and requires review",
  ).toEqual(["FAILED", "REVIEW_REQUIRED", false, []]);
});

test("focused evidence action clears the next-action copy", async ({ page }) => {
  await openQaSession(page, "/results", singleResultSession(semanticReviewResult("NO_CLEAR_EVIDENCE"), "REVIEW_REQUIRED"));
  const button = page.getByRole("button", { name: /G001 .*근거 자세히 보기/ });
  await button.focus();
  const action = page.locator(".result-card .action-line");
  const [actionBox, buttonBox] = await Promise.all([action.boundingBox(), button.boundingBox()]);
  expect(actionBox).not.toBeNull();
  expect(buttonBox).not.toBeNull();
  expect(
    buttonBox!.y - (actionBox!.y + actionBox!.height),
    "button box needs one space-2 beyond the next-action copy so its 7px focus outline cannot overlap",
  ).toBeGreaterThanOrEqual(8);
});

test("mobile source content does not create a blank 420px pane", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile", "mobile-only stacked workspace assertion");
  await openQaSession(page, "/announcement", provisionalGenericSession());
  const sourceHeading = page.getByRole("heading", { name: "Announcement Source" });
  const extractedHeading = page.getByRole("heading", { name: "Extracted Requirements" });
  const [sourceHeadingBox, extractedHeadingBox] = await Promise.all([sourceHeading.boundingBox(), extractedHeading.boundingBox()]);
  expect(sourceHeadingBox).not.toBeNull();
  expect(extractedHeadingBox).not.toBeNull();
  expect(
    extractedHeadingBox!.y - (sourceHeadingBox!.y + sourceHeadingBox!.height),
    "stacked source content and grid spacing should remain compact",
  ).toBeLessThanOrEqual(180);
});

test("captures the 12-state editorial visual QA matrix", async ({ page }, info) => {
  for (const scenario of qaScenarios) {
    await test.step(scenario.name, async () => {
      await scenario.render(page);
      await captureQa(page, info.project.name, scenario.name);
    });
  }
});

function completedMixedStatusSession() {
  return confirmedGenericSession({
    source_mode: "generic_verifier",
    verification_plan: verifiedPlanSet(),
    verification_plan_state: "READY",
    run_state: "COMPLETE",
    validation_complete: true,
    status: "BLOCKED",
    revision: 1,
    results: [
      editorialResult("EXTERNAL", "G004", "외부 확인"),
      editorialResult("PASS", "G003", "파일 형식"),
      editorialResult("REVIEW", "G002", "내용 요구사항"),
      editorialResult("BLOCKER", "G001", "페이지 수"),
    ],
  });
}

async function openConfirmedGenericSession(
  page: Page,
  path: string,
  session = confirmedGenericSession(),
  readiness: { ack_required: boolean; eligible_requirement_count: number; reason_code: string | null } = {
    ack_required: false,
    eligible_requirement_count: 0,
    reason_code: "NOT_ELIGIBLE",
  },
) {
  expectBackendReachablePlannerTransition(session);
  await page.addInitScript(([key, id]) => sessionStorage.setItem(key, id), ["final-check-session-id-v2", editorialSessionId]);
  await page.route("**/api/sessions/**", route => {
    const url = new URL(route.request().url()).pathname;
    if (url.endsWith("/semantic-readiness")) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(readiness) });
    }
    if (url.endsWith(`/sessions/${editorialSessionId}`)) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(session) });
    }
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"detail":"missing mock"}' });
  });
  await page.goto(path);
}

test("results use editorial summary counts instead of colored metric cards", async ({ page }) => {
  await openConfirmedGenericSession(page, "/results", completedMixedStatusSession());
  await expect(page.getByRole("heading", { name: "Preflight Result" })).toBeVisible();
  await expect(page.getByText("제출 전 점검이 완료되었습니다. 판정별 근거와 필요한 조치를 확인하세요.", { exact: true })).toBeVisible();
  const summary = page.getByRole("region", { name: "전체 검사 상태" });
  await expect(summary).toContainText("01");
  await expect(summary).toContainText("BLOCKER");
  await expect(summary).toContainText("REVIEW");
  await expect(summary).toHaveCSS("box-shadow", "none");
  await expect(summary).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
});

test("result rows are divider-led evidence chains", async ({ page }, info) => {
  await openConfirmedGenericSession(page, "/results", completedMixedStatusSession());
  const card = page.getByTestId("result-card").first();
  await expect(card.getByText("RULE", { exact: true })).toBeVisible();
  await expect(card.getByText("EVIDENCE", { exact: true })).toBeVisible();
  await expect(card.getByText("VERDICT", { exact: true })).toBeVisible();
  await expect(card).toHaveCSS("box-shadow", "none");
  await expect(card).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
  expect(["0px", "4px"]).toContain(await card.evaluate(node => getComputedStyle(node).borderRadius));
  const columns = await card.evaluate(node => getComputedStyle(node).gridTemplateColumns.trim().split(/\s+/).length);
  expect(columns).toBe(info.project.name === "mobile" ? 1 : 3);
});

test("evidence drawer uses the canonical editorial overlay treatment", async ({ page }) => {
  await openConfirmedGenericSession(page, "/results", completedMixedStatusSession());
  await page.getByRole("button", { name: /G001 .*근거 자세히 보기/ }).click();
  const drawer = page.getByRole("dialog", { name: "Evidence Inspector" });
  await expect(drawer).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(drawer).toHaveCSS("border-left-width", "1px");
  const shadows = await drawer.evaluate(node => {
    const probe = document.createElement("div");
    probe.style.boxShadow = "var(--shadow-overlay)";
    document.body.appendChild(probe);
    const canonical = getComputedStyle(probe).boxShadow;
    probe.remove();
    return { actual: getComputedStyle(node).boxShadow, canonical };
  });
  expect(shadows.actual).toBe(shadows.canonical);
  await expect(drawer.locator(".evidence small").first()).toHaveCSS("font-family", "monospace");
});

test("extraction and review read as editorial columns rather than cards", async ({ page }) => {
  await openConfirmedGenericSession(page, "/announcement");
  const source = page.getByRole("region", { name: "공고 원문" });
  const candidates = page.getByRole("region", { name: "AI 추출 후보" });
  await expect(source).toHaveCSS("box-shadow", "none");
  await expect(source).toHaveCSS("border-radius", "0px");
  await expect(candidates).toHaveCSS("border-radius", "0px");
  await expect(source.locator(".source-highlight")).toHaveCSS("background-color", "rgb(244, 246, 255)");

  const selectedCandidate = candidates.locator(".requirement-candidate.selected");
  await expect(selectedCandidate).toHaveCSS("border-left-width", "2px");
  await expect(selectedCandidate.locator("button")).toHaveCSS("background-color", "rgb(255, 255, 255)");

  await page.goto("/requirements");
  const list = page.getByRole("region", { name: "요구사항 목록" });
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(list).toHaveCSS("box-shadow", "none");
  await expect(inspector).toHaveCSS("box-shadow", "none");
  await expect(list).toHaveCSS("border-radius", "0px");
  await expect(inspector).toHaveCSS("border-radius", "0px");
  await expect(inspector.locator(".inspector-source pre")).toHaveCSS("background-color", "rgb(255, 255, 255)");

  const selectedRequirement = list.locator(".requirement-row.selected");
  await expect(selectedRequirement).toHaveCSS("border-left-width", "2px");
  await expect(selectedRequirement.locator("button")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(inspector.getByRole("button", { name: "항목 승인" })).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(inspector.getByRole("button", { name: "항목 삭제" })).toHaveCSS("color", "rgb(198, 40, 40)");
});

test("confirmed generic review-required package stays accessible and reads as a file sheet", async ({ page }) => {
  const session = confirmedGenericSession({
    verification_plan_state: "REVIEW_REQUIRED",
    verification_plan_error: "PLANNER_UNAVAILABLE",
    files: [{ name: "submission.pdf", size_bytes: 2048, media_type: "application/pdf", sha256: "d".repeat(64) }],
  });
  await openConfirmedGenericSession(page, "/upload", session);

  await expect(page.getByRole("heading", { name: "제출 패키지" })).toBeVisible();
  const packagePanel = page.getByRole("region", { name: "제출 패키지" });
  const scope = page.getByRole("region", { name: "이번 검사" });
  await expect(packagePanel).toHaveCSS("box-shadow", "none");
  await expect(packagePanel).toHaveCSS("border-radius", "0px");
  await expect(scope).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(scope).toHaveCSS("box-shadow", "none");
  await expect(scope).toHaveCSS("border-radius", "0px");
  await expect(scope.locator(".scope-summary")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(scope.locator(".scope-summary")).toHaveCSS("border-radius", "0px");
  await expect(page.getByText("자동 검사 계획이 확정되지 않았습니다.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
  await expect(page.getByText(/(?:예상|소요).*(?:분|초)|\d+\s*페이지/)).toHaveCount(0);
});

test("semantic acknowledgement keeps readable editorial body copy", async ({ page }) => {
  const session = confirmedGenericSession({
    verification_plan_state: "REVIEW_REQUIRED",
    verification_plan_error: "PLANNER_UNAVAILABLE",
    files: [{ name: "submission.pdf", size_bytes: 2048, media_type: "application/pdf", sha256: "e".repeat(64) }],
  });
  await openConfirmedGenericSession(page, "/upload", session, {
    ack_required: true,
    eligible_requirement_count: 1,
    reason_code: null,
  });

  const acknowledgement = page.locator(".semantic-acknowledgement");
  await expect(acknowledgement.locator("p")).toHaveCSS("font-size", "14px");
  await expect(acknowledgement.locator("p")).toHaveCSS("line-height", "20px");
  await expect(acknowledgement.locator("label")).toHaveCSS("font-size", "14px");
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
  await page.getByRole("checkbox").check();
  await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeEnabled();
});

test("landing uses the approved editorial type, white canvas, and no card shadow", async ({ page }, info) => {
  await page.goto("/");
  const body = page.locator("body");
  await expect(body).toHaveCSS("background-color", "rgb(255, 255, 255)");

  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  await expect(hero).toHaveCSS("font-size", info.project.name === "mobile" ? "32px" : "56px");
  await expect(hero).toHaveCSS("line-height", info.project.name === "mobile" ? "40px" : "64px");
  await expect(hero).toHaveCSS("font-weight", "700");

  const frame = page.getByRole("region", { name: "Preflight 결과 예시" });
  await expect(frame).toHaveCSS("box-shadow", "none");
  await expect(frame).toHaveCSS("border-radius", "8px");
});

test("primary controls use scarce accent and compact editorial geometry", async ({ page }) => {
  await page.goto("/");
  const cta = page.getByRole("link", { name: "제출 전 검사 시작하기" }).first();
  await expect(cta).toHaveCSS("background-color", "rgb(49, 87, 255)");
  await expect(cta).toHaveCSS("border-radius", "4px");
  await expect(cta).toHaveCSS("font-size", "14px");
  await expect(cta).toHaveCSS("line-height", "20px");
  await expect(cta).toHaveCSS("font-weight", "600");
});

test("shared buttons, panels, and evidence use the editorial control grammar", async ({ page }, info) => {
  await openConfirmedGenericSession(page, "/requirements");

  const primary = page.getByRole("button", { name: /Profile 확정|자동 검사 계획 생성/ }).first();
  await expect(primary).toHaveCSS("border-radius", "4px");
  await expect(primary).toHaveCSS("font-size", "14px");
  await expect(primary).toHaveCSS("line-height", "20px");

  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(inspector).toHaveCSS("box-shadow", "none");
  expect(["0px", "4px", "8px"]).toContain(await inspector.evaluate(node => getComputedStyle(node).borderRadius));
  const evidence = inspector.locator(".evidence");
  await expect(evidence).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
  await expect(evidence).toHaveCSS("border-radius", "0px");
  await expect(evidence).toHaveCSS("padding", "0px");

  const modeNote = page.locator(".mode-note");
  await expect(modeNote).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(modeNote).toHaveCSS("border-radius", "0px");
  const pageTitle = page.locator(".page-heading h1");
  await expect(pageTitle).toHaveCSS("font-size", info.project.name === "mobile" ? "24px" : "32px");
  await expect(pageTitle).toHaveCSS("line-height", info.project.name === "mobile" ? "32px" : "40px");
});

test("editable requirement form controls use compact editorial geometry", async ({ page }) => {
  await openConfirmedGenericSession(page, "/requirements");
  await page.getByRole("button", { name: "요구사항 G001" }).click();

  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  for (const control of [inspector.getByLabel("condition"), inspector.getByLabel("요구사항 문장"), inspector.getByLabel("exact evidence quote")]) {
    await expect(control).toHaveCSS("border-radius", "4px");
    await expect(control).toHaveCSS("font-size", "14px");
    await expect(control).toHaveCSS("line-height", "20px");
  }
});

test("header and five-step shell use the approved compact type and spacing", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/announcement");

  const header = page.locator(".site-header");
  await expect(header).toHaveCSS("padding-top", "24px");
  await expect(header).toHaveCSS("padding-left", "32px");
  await expect(header).toHaveCSS("column-gap", "32px");

  const brand = page.getByRole("link", { name: "FINAL CHECK 홈" });
  await expect(brand).toHaveCSS("column-gap", "8px");
  await expect(brand).toHaveCSS("font-size", "20px");
  await expect(brand).toHaveCSS("line-height", "28px");
  await expect(brand).toHaveCSS("font-weight", "700");
  await expect(brand).toHaveCSS("letter-spacing", "-1px");

  const firstStep = page.getByRole("navigation", { name: "검사 단계" }).locator(".step").first();
  await expect(firstStep).toHaveCSS("padding", "16px");
  await expect(firstStep).toHaveCSS("column-gap", "12px");
  await expect(firstStep).toHaveCSS("font-size", "12px");
  await expect(firstStep).toHaveCSS("line-height", "16px");
  await expect(firstStep).toHaveCSS("font-weight", "500");
});

test("announcement requirement copy uses the canonical small typography pair", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "demo 검사 시작하기" }).click();
  await expect(page).toHaveURL(/\/announcement$/);
  const requirementCopy = page.locator(".requirement > p").first();
  await expect(requirementCopy).toHaveCSS("font-size", "12px");
  await expect(requirementCopy).toHaveCSS("line-height", "16px");
});

test("proof and story metadata use approved editorial tokens", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  const proofHeading = page.locator(".mini-window-heading");
  await expect(proofHeading).toHaveCSS("padding-bottom", "16px");
  await expect(proofHeading).toHaveCSS("font-size", "11px");
  await expect(proofHeading).toHaveCSS("line-height", "16px");
  await expect(proofHeading).toHaveCSS("letter-spacing", "1px");

  const proofMetadata = page.locator(".mini-summary span").first();
  await expect(proofMetadata).toHaveCSS("padding", "4px 8px");
  await expect(proofMetadata).toHaveCSS("font-size", "11px");
  await expect(proofMetadata).toHaveCSS("line-height", "16px");

  const story = page.locator(".story-step").first();
  await expect(story).toHaveCSS("padding", "48px 0px");
  await expect(story.locator("h3")).toHaveCSS("font-size", "24px");
  await expect(story.locator("h3")).toHaveCSS("line-height", "32px");
  await expect(story.locator(".story-frame")).toHaveCSS("padding", "32px");
  await expect(story.locator(".story-frame")).toHaveCSS("gap", "24px");

  const storyMetadata = story.locator(".source-sample > span");
  await expect(storyMetadata).toHaveCSS("font-size", "11px");
  await expect(storyMetadata).toHaveCSS("line-height", "16px");
  await expect(storyMetadata).toHaveCSS("letter-spacing", "1px");
});

test("wide landing uses only approved hero spacing", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto("/");
  await expect(page.locator(".landing-hero")).toHaveCSS("padding", "96px 0px 80px");
});

test("tablet landing switches to approved discrete spacing and type", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 1000 });
  await page.goto("/");
  const hero = page.locator(".landing-hero");
  await expect(hero).toHaveCSS("column-gap", "32px");
  await expect(hero.locator("h1")).toHaveCSS("font-size", "48px");
  await expect(hero.locator("h1")).toHaveCSS("line-height", "56px");
  await expect(page.locator(".story-step").first()).toHaveCSS("column-gap", "32px");
});

test("mobile shell keeps tokenized step geometry", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/announcement");

  const brand = page.getByRole("link", { name: "FINAL CHECK 홈" });
  await expect(brand).toHaveCSS("font-size", "20px");
  await expect(brand).toHaveCSS("line-height", "28px");

  const firstStep = page.getByRole("navigation", { name: "검사 단계" }).locator(".step").first();
  await expect(firstStep).toHaveCSS("padding", "12px 4px");
  await expect(firstStep).toHaveCSS("column-gap", "8px");
  await expect(firstStep).toHaveCSS("font-size", "12px");
  await expect(firstStep).toHaveCSS("line-height", "16px");
  await expect(firstStep.locator(".step-num")).toHaveCSS("width", "24px");
  await expect(firstStep.locator(".step-num")).toHaveCSS("height", "24px");
});

test("landing switches display typography at mobile without interpolated sizes", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile");
  await page.goto("/");
  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  expect(["32px", "40px"]).toContain(await hero.evaluate(node => getComputedStyle(node).fontSize));
  expect(["40px", "48px"]).toContain(await hero.evaluate(node => getComputedStyle(node).lineHeight));
});

test("landing does not overflow the viewport", async ({ page }) => {
  await page.goto("/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
});

test("major surfaces remain monochrome-first and overflow-safe", async ({ page }) => {
  await page.goto("/");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(255, 255, 255)");
});

test("reduced motion keeps visual refinement nonessential", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const duration = await page.locator(".product-frame").first().evaluate(el => getComputedStyle(el).transitionDuration);
  expect(["0s", "0.001s", "0.000001s"]).toContain(duration);
});
