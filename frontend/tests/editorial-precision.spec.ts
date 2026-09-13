import { test, expect, type Page } from "@playwright/test";

const editorialSessionId = "editorial-precision-session";
const editorialStamp = "2026-09-13T00:00:00.000Z";

function confirmedGenericSession() {
  const quote = "영상은 60초 이내여야 합니다.";
  const provenance = {
    provider: "SIMULATED browser fixture", model: "fixture", prompt_version: "fixture-v1",
    prompt_sha256: "a".repeat(64), execution_kind: "SIMULATED",
  };
  const requirement = {
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
  };
}

async function openConfirmedGenericSession(page: Page, path: string) {
  await page.addInitScript(([key, id]) => sessionStorage.setItem(key, id), ["final-check-session-id-v2", editorialSessionId]);
  await page.route("**/api/sessions/**", route => {
    const url = new URL(route.request().url()).pathname;
    if (url.endsWith(`/sessions/${editorialSessionId}`)) {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(confirmedGenericSession()) });
    }
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"detail":"missing mock"}' });
  });
  await page.goto(path);
}

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
  for (const control of [inspector.getByLabel("요구사항 문장"), inspector.getByLabel("exact evidence quote")]) {
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
