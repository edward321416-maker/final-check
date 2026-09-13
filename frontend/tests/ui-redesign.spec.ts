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
