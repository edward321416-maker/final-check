# FINAL CHECK UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign FINAL CHECK into the approved White SaaS + Electric Blue evidence-first product UI while preserving every TASK02–TASK10 authority, safety, polling, acknowledgement, and verification contract.

**Architecture:** Keep the backend and session contracts unchanged. Split the current combined frontend flow into a route-aware shell plus dedicated Announcement Extraction, Human Review, Submission Package, Results/Evidence, and Recheck presentation units. Centralize five-step route readiness in a pure workflow helper, preserve existing mutation/polling logic, and add an accessible Evidence Inspector drawer over the existing result data.

**Tech Stack:** Next.js 16.3.4 App Router, React 19.2.8, TypeScript 5.9 strict mode, CSS, Playwright 1.62.1, existing FastAPI backend, existing local ChatGPT-authenticated Codex CLI runtime.

**Spec:** `docs/superpowers/specs/2026-09-13-final-check-ui-redesign-design.md`

**Normative audit:** `docs/superpowers/specs/2026-09-13-final-check-ui-redesign-audit.md`

## Global Constraints

- Baseline runtime contract is `main@9f13866db1f14d917764a7d2865153f7aa6fbf3e`; implementation must start from the approved docs branch based on that baseline unless Product Lead explicitly approves rebasing onto a newer main.
- TASK02–TASK10 backend verification semantics, frozen hashes, Plan DSL, AI authority, Human-confirmation boundary, semantic eligibility, exact evidence gate, and acknowledgement rules do not change.
- Do not modify backend code merely to make the redesign easier. In particular, do not add pre-run media metadata, new statuses, new verifier families, new AI calls, OCR/Vision/URL verification, or persistence changes.
- Semantic findings remain `REVIEW`; AI never directly produces `PASS`, `BLOCKER`, `READY`, or `BLOCKED` authority.
- Custom Step 03 readiness is `validation_profile === "generic" && generic_profile?.status === "CONFIRMED"`; Verification Plan `READY` is capability information, not a universal gate.
- Demo Step 03 readiness is `validation_profile === "frozen_v15"`.
- `SubmissionFile` pre-run UI may use only `name`, `size_bytes`, `media_type`, and `sha256`; page count and video duration appear only when actual result evidence provides them.
- Preserve semantic acknowledgement reset, stale-session polling cancellation, reload polling resume, transient poll retry, mutation lock behavior, and failed-run recovery.
- Preserve semantic REVIEW-to-REVIEW evidence-fingerprint comparison.
- `/` is outside the numbered Stepper. App steps are `/announcement`, `/requirements`, `/upload`, `/results`, `/recheck`.
- Demo/frozen requirements must never be labelled as live `AI EXTRACTED` results.
- Results default order is `BLOCKER -> REVIEW -> PASS -> EXTERNAL`.
- Do not label `updated_at` as a validation time.
- Electric Blue is brand/action/focus/evidence-trace color, never PASS color.
- Mobile keeps Evidence visible using `RULE -> EVIDENCE -> VERDICT` vertical stacking.
- Motion is subtle and nonessential; respect `prefers-reduced-motion`.
- Existing public judging runtime is not replaced until all local/review-runtime gates and Product Lead review pass.
- Product AI configuration remains `gpt-5.6-sol` / reasoning `high`; UI work must not alter provider/runtime configuration.

## Execution isolation

Before Task 1 implementation, use the `superpowers:using-git-worktrees` skill. Fetch `origin/main` and `origin/ui-redesign-design`. Confirm `origin/main` still points to the audited baseline or stop for Product Lead review if main moved in a way that changes contracts. Create an isolated implementation branch/worktree named `ui-redesign` from `origin/ui-redesign-design`. Do **not** switch or delete the worktree currently serving the public judging URL.

Recommended controller for all implementation tasks: **`gpt-5.6-sol`, reasoning `high`**. Task 6 mechanical CSS cleanup may use `medium`, but the task-level review and final gate return to `high`.

---

### Task 1: Lock the five-step workflow and route-aware product shell

**Files:**
- Create: `frontend/lib/workflow.ts`
- Create: `frontend/components/app-chrome.tsx`
- Create: `frontend/app/requirements/page.tsx`
- Create: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/components/ui.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/golden-path.spec.ts`

**Interfaces:**
- Consumes: `CheckSession` from `frontend/types/check.ts`, `useSession()` from `frontend/components/session-provider.tsx`, `usePathname()` from Next.js.
- Produces:
  - `type WorkflowStep = "announcement" | "requirements" | "upload" | "results" | "recheck"`
  - `const WORKFLOW_STEPS: readonly WorkflowStepDefinition[]`
  - `function canEnterStep(session: CheckSession | null, step: WorkflowStep): boolean`
  - `function recoveryHref(session: CheckSession | null, step: WorkflowStep): string`
  - `function isStepComplete(session: CheckSession | null, step: WorkflowStep): boolean`
  - `AppChrome({ children }: { children: React.ReactNode })`
  - `/requirements` route that initially renders the exported Requirements screen once Task 3 supplies it; until then it may render an explicit guarded placeholder component from `ui.tsx`, not fake review data.

- [ ] **Step 1: Write workflow/chrome tests that fail against the current UI**

Add to `frontend/tests/ui-redesign.spec.ts` a mocked-session helper and these assertions:

```ts
import { expect, test, type Page } from "@playwright/test";

const sessionId = "ui-redesign-session";
const stamp = "2026-09-13T00:00:00.000Z";

function baseSession(overrides: Record<string, unknown> = {}) {
  return {
    id: sessionId,
    created_at: stamp,
    updated_at: stamp,
    mode: "custom",
    source_mode: "unavailable",
    announcement_name: "공고.txt",
    validation_profile: null,
    engine_sha256: null,
    generic_profile: null,
    verification_plan: null,
    verification_plan_state: "NOT_STARTED",
    verification_plan_error: null,
    current_job_id: null,
    current_job: null,
    run_state: "NOT_STARTED",
    validation_complete: false,
    run_error: null,
    requirements: [],
    files: [],
    results: [],
    previous_results: [],
    status: null,
    revision: 0,
    fixture: null,
    ...overrides,
  };
}

async function openWithSession(page: Page, session: object, path: string) {
  await page.addInitScript(([key, id]) => sessionStorage.setItem(key, id), ["final-check-session-id-v2", sessionId]);
  await page.route(`**/api/sessions/${sessionId}`, route =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(session) }));
  await page.goto(path);
}

test("landing is outside the numbered workflow and uses product navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "검사 단계" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "How it works" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Evidence-first" })).toBeVisible();
});

test("custom confirmed profile can enter upload even when planner is REVIEW_REQUIRED", async ({ page }) => {
  const session = baseSession({
    validation_profile: "generic",
    verification_plan_state: "REVIEW_REQUIRED",
    generic_profile: { status: "CONFIRMED" },
  });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("heading", { name: /제출/ })).toBeVisible();
  await expect(page.getByText(/요구사항 검토로 돌아가/)).toHaveCount(0);
});

test("unconfirmed custom profile fails closed from upload to requirements", async ({ page }) => {
  const session = baseSession({
    validation_profile: null,
    generic_profile: { status: "REVIEW_REQUIRED" },
  });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("link", { name: /요구사항 검토/ })).toHaveAttribute("href", "/requirements");
});
```

For the compact `generic_profile` test doubles, include the complete required shape only where rendering accesses it; if the route guard returns before rendering workspace content, `{ status: ... }` is sufficient at runtime and may be cast inside the test fixture helper rather than weakening production types.

- [ ] **Step 2: Build and run the targeted tests to prove the old shell fails**

Run from `frontend/`:

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts --project=desktop
```

Expected before implementation: FAIL because the landing still renders `검사 단계`, `/requirements` does not exist, and upload guard logic is not five-step aware.

- [ ] **Step 3: Implement the pure workflow contract**

Create `frontend/lib/workflow.ts` with an explicit, auditable mapping:

```ts
import type { CheckSession } from "@/types/check";

export type WorkflowStep = "announcement" | "requirements" | "upload" | "results" | "recheck";

export interface WorkflowStepDefinition {
  key: WorkflowStep;
  href: string;
  label: string;
  number: string;
}

export const WORKFLOW_STEPS: readonly WorkflowStepDefinition[] = [
  { key: "announcement", href: "/announcement", label: "공고", number: "01" },
  { key: "requirements", href: "/requirements", label: "요구사항 검토", number: "02" },
  { key: "upload", href: "/upload", label: "제출파일", number: "03" },
  { key: "results", href: "/results", label: "결과", number: "04" },
  { key: "recheck", href: "/recheck", label: "재검사", number: "05" },
] as const;

function hasRequirementData(session: CheckSession): boolean {
  return session.mode === "demo"
    ? session.validation_profile === "frozen_v15" && session.requirements.length > 0
    : Boolean(session.generic_profile && (
        session.generic_profile.requirements.length > 0
        || session.generic_profile.extraction_complete
      ));
}

function canUpload(session: CheckSession): boolean {
  if (session.validation_profile === "frozen_v15") return true;
  return session.validation_profile === "generic"
    && session.generic_profile?.status === "CONFIRMED";
}

export function canEnterStep(session: CheckSession | null, step: WorkflowStep): boolean {
  if (!session?.announcement_name) return false;
  if (step === "announcement") return true;
  if (step === "requirements") return hasRequirementData(session);
  if (step === "upload") return canUpload(session);
  if (step === "results") return session.results.length > 0 && session.run_state === "COMPLETE";
  return session.previous_results.length > 0 || session.results.length > 0 || session.revision > 0;
}

export function isStepComplete(session: CheckSession | null, step: WorkflowStep): boolean {
  if (!session) return false;
  if (step === "announcement") return hasRequirementData(session);
  if (step === "requirements") return canUpload(session);
  if (step === "upload") return session.run_state === "COMPLETE" && session.results.length > 0;
  if (step === "results") return session.results.length > 0;
  return session.revision > 1;
}

export function recoveryHref(session: CheckSession | null, step: WorkflowStep): string {
  if (!session?.announcement_name) return "/";
  if (step === "requirements") return "/announcement";
  if (step === "upload") return session.mode === "custom" ? "/requirements" : "/announcement";
  if (step === "results") return canUpload(session) ? "/upload" : recoveryHref(session, "upload");
  if (step === "recheck") return session.results.length > 0 ? "/results" : recoveryHref(session, "results");
  return "/";
}
```

Do not include `verification_plan_state === "READY"` in `canUpload()`.

- [ ] **Step 4: Implement route-aware Product Header and Segmented Stepper**

Create `frontend/components/app-chrome.tsx` as a client component. Required behavior:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/components/session-provider";
import { WORKFLOW_STEPS, canEnterStep, isStepComplete } from "@/lib/workflow";

export function Brand() {
  return <Link href="/" className="brand" aria-label="FINAL CHECK 홈">
    <span className="scan-check" aria-hidden="true"><span>✓</span></span>
    <span>FINAL CHECK</span>
  </Link>;
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session } = useSession();
  const landing = pathname === "/";
  return <>
    <header className={landing ? "site-header landing-header" : "site-header app-header"}>
      <Brand />
      {landing ? <>
        <nav className="product-nav" aria-label="제품 소개">
          <Link href="#how-it-works">How it works</Link>
          <Link href="#evidence-first">Evidence-first</Link>
          <Link href="#verification">검증 방식</Link>
        </nav>
        <Link className="button primary" href="#start-check">제출 전 검사 시작하기</Link>
      </> : null}
    </header>
    <div className={pathname === "/results" ? "shell shell-results" : "shell"}>
      {!landing ? <nav aria-label="검사 단계" className="step-nav">
        {WORKFLOW_STEPS.map(step => {
          const active = pathname === step.href;
          const enabled = canEnterStep(session, step.key);
          const complete = isStepComplete(session, step.key);
          const content = <><span className="step-num">{complete ? "✓" : step.number}</span><span>{step.label}</span></>;
          return enabled
            ? <Link key={step.key} href={step.href} className={`step${active ? " active" : ""}`} aria-current={active ? "step" : undefined}>{content}</Link>
            : <span key={step.key} className="step disabled" aria-disabled="true">{content}</span>;
        })}
      </nav> : null}
      <main id="main">{children}</main>
      <footer className="site-footer"><strong>FINAL CHECK</strong><span>확신은, 근거에서 시작됩니다.</span></footer>
    </div>
  </>;
}
```

Modify `frontend/app/layout.tsx` to keep `SessionProvider` server-safe and place `<AppChrome>{children}</AppChrome>` inside it. Remove the old static header/Navigation duplication.

- [ ] **Step 5: Add a workflow-aware Guard without weakening existing fail-closed behavior**

Modify `frontend/components/ui.tsx` so route screens can declare the required step:

```tsx
import { canEnterStep, recoveryHref, type WorkflowStep } from "@/lib/workflow";

export function WorkflowGuard({ step, children }: { step: WorkflowStep; children: ReactNode }) {
  const { session, loading, recoveryError } = useSession();
  if (loading) return <div className="empty" role="status">검사 세션을 불러오는 중입니다…</div>;
  if (!canEnterStep(session, step)) {
    const href = recoveryHref(session, step);
    const label = href === "/requirements" ? "요구사항 검토로 돌아가기"
      : href === "/announcement" ? "공고 단계로 돌아가기"
      : href === "/upload" ? "제출파일 단계로 돌아가기"
      : href === "/results" ? "결과로 돌아가기"
      : "홈으로 돌아가기";
    return <section className="empty" aria-label="단계 준비 필요">
      <h1>이 단계를 아직 진행할 수 없습니다</h1>
      <p>{recoveryError || "앞 단계의 확인을 완료한 뒤 다시 진행해 주세요."}</p>
      <Link className="button primary" href={href}>{label}</Link>
    </section>;
  }
  return <>{children}</>;
}
```

Keep the old `Guard` temporarily only if existing code still needs it during this task; remove it after all routes migrate in later tasks.

- [ ] **Step 6: Add `/requirements` route without fake state**

Create `frontend/app/requirements/page.tsx`:

```tsx
import { RequirementsScreen } from "@/components/screens";
export default function Requirements() { return <RequirementsScreen />; }
```

Add a temporary `RequirementsScreen` in `screens.tsx` that uses `<WorkflowGuard step="requirements">` and truthful copy such as `요구사항 검토 화면을 준비했습니다.` with no fabricated requirements. Task 3 replaces this temporary body with the actual review workspace in the same commit series; do not merge Task 1 alone to production.

- [ ] **Step 7: Apply the shell-only visual baseline**

In `globals.css`, introduce the new neutral/blue variables and shell geometry without yet redesigning every inner screen:

```css
:root {
  --bg:#f8fafc;
  --surface:#ffffff;
  --ink:#101828;
  --muted:#667085;
  --line:#e4e7ec;
  --blue:#2563eb;
  --blue-soft:#eff6ff;
  --red:#b42318;
  --red-bg:#fff6f5;
  --amber:#b54708;
  --amber-bg:#fffaeb;
  --green:#067647;
  --green-bg:#ecfdf3;
  --external:#475467;
  --external-bg:#f2f4f7;
}
.shell { max-width:1240px; margin:0 auto; padding:0 32px; }
.shell-results { max-width:1320px; }
.step-nav { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border-bottom:1px solid var(--line); }
.step { border-bottom:2px solid transparent; }
.step.active { color:var(--blue); border-bottom-color:var(--blue); background:transparent; }
```

Remove old green active-step treatment from the shell. Full visual-token cleanup happens in Task 2/6.

- [ ] **Step 8: Update the demo golden path for the added Human Review step**

Change the demo start sequence in `frontend/tests/golden-path.spec.ts` so it asserts:

```ts
await flow.start();
await page.getByRole("link", { name: /요구사항 검토/ }).click();
await expect(page).toHaveURL(/\/requirements$/);
await expect(page.getByText(/동결|확인된 요구사항/)).toBeVisible();
await page.getByRole("link", { name: /제출파일/ }).click();
await expect(page).toHaveURL(/\/upload$/);
```

The demo Human Review screen is read-only; do not simulate edits or fake AI jobs.

- [ ] **Step 9: Run the targeted workflow regression**

Run from `frontend/`:

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop
```

Expected: PASS; landing has no numbered Stepper, `/requirements` exists, and confirmed generic upload does not depend on planner READY.

- [ ] **Step 10: Commit Task 1**

```bash
git add frontend/lib/workflow.ts frontend/components/app-chrome.tsx frontend/app/requirements/page.tsx frontend/app/layout.tsx frontend/components/ui.tsx frontend/app/globals.css frontend/components/screens.tsx frontend/tests/ui-redesign.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): add five-step workflow shell"
```

---

### Task 2: Replace the legacy landing with the approved evidence-first product story

**Files:**
- Create: `frontend/components/landing.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/task09-public-first-visit.spec.ts`

**Interfaces:**
- Consumes: existing `request`, `sessionRequest`, `TextAnnouncementInput`, session `update`, and router behavior used by current HomeScreen.
- Produces: `LandingScreen` with the same real demo/custom session-start behavior, anchors `#how-it-works`, `#evidence-first`, `#verification`, and `#start-check` consumed by Product Header links.

- [ ] **Step 1: Add failing landing truthfulness and brand tests**

Extend `ui-redesign.spec.ts`:

```ts
test("landing uses the approved message and an internally consistent example window", async ({ page }) => {
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

test("landing preview has no intentional rotation", async ({ page }) => {
  await page.goto("/");
  const transform = await page.getByRole("region", { name: "Preflight 결과 예시" }).evaluate(el => getComputedStyle(el).transform);
  expect(transform).toBe("none");
});
```

- [ ] **Step 2: Run the landing tests and confirm they fail on the old preview**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts --project=desktop -g "landing"
```

Expected: FAIL on hero wording/counts/rotation/product header anchors.

- [ ] **Step 3: Extract the real session-start logic into `LandingScreen` without changing requests**

Create `frontend/components/landing.tsx`. Preserve the current `POST /sessions`, `demo-announcement`, uploaded announcement, and `TextAnnouncementInput` behavior. The component must not create a fake validation run.

Use the approved hero structure:

```tsx
<section className="hero landing-hero">
  <div className="hero-copy">
    <span className="eyebrow">AI SUBMISSION PREFLIGHT</span>
    <h1>제출 버튼을 누르기 전, 마지막 확인.</h1>
    <p className="hero-description">FINAL CHECK가 공고의 요구사항을 구조화하고, 실제 제출파일에서 놓친 조건과 근거를 찾아줍니다.</p>
    <div className="hero-actions">
      <a className="button primary large" href="#start-check">제출 전 검사 시작하기</a>
      <a className="button secondary" href="#how-it-works">어떻게 작동하나요?</a>
    </div>
    <p className="trust-line">AI는 근거를 찾고, 확실한 조건은 코드가 검증합니다.</p>
  </div>
  <section className="product-frame mini-product" aria-label="Preflight 결과 예시">
    <div className="mini-summary"><span>1 BLOCKER</span><span>1 REVIEW</span><span>3 PASS</span></div>
    <div className="mini-chain"><strong>영상 60초 이내</strong><span>61.0s</span><b className="status-text blocker">BLOCKER</b></div>
    <div className="mini-chain"><strong>기대효과 포함</strong><span>proposal.pdf · p.2</span><b className="status-text review">REVIEW</b></div>
    <small>EXAMPLE · 실제 판정 구조를 축약한 예시</small>
  </section>
</section>
```

Below it, add the three alternating product-story sections with static UI fragments that only illustrate already-existing product behavior. The fragments must be clearly illustrative and must not expose invented live metrics.

- [ ] **Step 4: Implement the real start section and scoped evidence claim**

Give the custom/demo inputs an anchor `id="start-check"`. Use the scoped principle copy exactly:

> 자동 판정 가능한 항목은 공고 근거와 실제 측정/제출 근거를 연결하고, 의미 판단은 REVIEW로 남깁니다.

Keep the disclosure that custom announcement text is used by the local ChatGPT-authenticated Codex CLI. Keep existing limits/copy that are still contract-true.

- [ ] **Step 5: Replace old landing CSS with Clean Product Frame styling**

Remove `.preview { transform:rotate(1deg) }` and old lime/pine hero treatments. Add restrained styles:

```css
.product-frame { background:var(--surface); border:1px solid var(--line); border-radius:16px; box-shadow:0 18px 45px rgba(16,24,40,.08); }
.landing-hero { grid-template-columns:minmax(0,.92fr) minmax(0,1fr); gap:64px; padding:88px 0 72px; }
.mini-chain { display:grid; grid-template-columns:1fr minmax(120px,1.2fr) auto; gap:16px; align-items:center; border-top:1px solid var(--line); padding:16px 0; }
.trust-line { margin-top:18px; font-size:13px; color:var(--muted); }
```

No gradient logo, parallax, bounce, or infinite animation.

- [ ] **Step 6: Update public first-visit selector without weakening the ngrok test**

In `task09-public-first-visit.spec.ts`, update the hero selector from `/제출 버튼을 누르기 전/` to the approved exact heading while keeping the ngrok interstitial handling and screenshot behavior unchanged.

- [ ] **Step 7: Verify landing desktop and mobile**

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/task09-public-first-visit.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts --project=mobile
```

Expected: PASS and no horizontal overflow.

- [ ] **Step 8: Commit Task 2**

```bash
git add frontend/components/landing.tsx frontend/components/screens.tsx frontend/app/globals.css frontend/tests/ui-redesign.spec.ts frontend/tests/task09-public-first-visit.spec.ts
git commit -m "feat(ui): redesign evidence-first landing"
```

---

### Task 3: Split AI extraction from Human Review and build the two approved workspaces

**Files:**
- Create: `frontend/components/announcement-workspace.tsx`
- Create: `frontend/components/requirements-workspace.tsx`
- Modify: `frontend/components/generic-profile.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/components/profile.module.css`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/generic-profile.spec.ts`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/task06-actual-ai.spec.ts`
- Modify: `frontend/tests/task08-plan-ui.spec.ts`
- Modify: `frontend/tests/task08-actual-ai.spec.ts`
- Modify: `frontend/tests/task09-public-actual.spec.ts`
- Modify: `frontend/tests/task10-actual-semantic.spec.ts`

**Interfaces:**
- Consumes: existing profile mutations/endpoints exactly as implemented: `/extract`, `/requirements/{id}/review`, `/profile/confirm`, `/verification-plan/compile`.
- Produces:
  - `AnnouncementWorkspace()` for Step 01;
  - `RequirementsWorkspace()` for Step 02;
  - exact source-span helper `splitEvidenceText(text: string, start: number, end: number, quote: string): { before: string; match: string; after: string } | null`;
  - selected requirement state local to the two workspaces; no backend selection state.

- [ ] **Step 1: Rewrite generic-profile UI tests to require the new route split**

Update `generic-profile.spec.ts` so extraction stays on `/announcement` and review actions occur only after navigation to `/requirements`:

```ts
await page.goto("/announcement");
await page.getByRole("button", { name: "요구사항 추출 실행" }).click();
await expect(page.getByText(/추출된 요구사항/)).toBeVisible();
await page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
await expect(page).toHaveURL(/\/requirements$/);
const card = page.getByRole("button", { name: /요구사항 G001/ });
await card.click();
await expect(page.getByRole("region", { name: "요구사항 Inspector" })).toBeVisible();
```

Add an assertion that Step 01 does **not** expose `Profile 확정`, while Step 02 does.

Add an exact-highlight test using a mocked profile whose `announcement.text` is `앞문장 기대효과를 포함해야 합니다. 뒷문장` and whose evidence offset points exactly at `기대효과를 포함해야 합니다.`. Assert the matching span renders in `<mark>` after selecting the requirement.

- [ ] **Step 2: Run the split-workspace tests and confirm failure**

```bash
npm run build
npx playwright test tests/generic-profile.spec.ts tests/ui-redesign.spec.ts --project=desktop
```

Expected: FAIL because review controls are still embedded on `/announcement` and `/requirements` has no real workspace.

- [ ] **Step 3: Isolate `TextAnnouncementInput` and exact source splitting**

Keep `TextAnnouncementInput` in `generic-profile.tsx` with the existing request path unchanged. Export a pure helper either from `announcement-workspace.tsx` or a small adjacent function:

```ts
export function splitEvidenceText(text: string, start: number, end: number, quote: string) {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > text.length) return null;
  const match = text.slice(start, end);
  if (match !== quote) return null;
  return { before: text.slice(0, start), match, after: text.slice(end) };
}
```

No fuzzy matching or `indexOf` fallback for repeated quotes.

- [ ] **Step 4: Build `AnnouncementWorkspace` as the 45/55 Split Extraction Workspace**

For custom sessions:

- left: full announcement source in a scrollable `Announcement Source` pane;
- right: extraction state and compact candidate list;
- selecting/focusing a candidate highlights the exact source span using `splitEvidenceText`;
- if exact mapping fails, show source section + quote without highlight;
- extraction button/polling uses the existing `/extract` behavior;
- truthful activity derives only from `pipeline_status` and `current_job.stage/status`;
- after extraction data exists, show `요구사항 검토로 이동` linking to `/requirements`.

Render activity labels with a small translation function, for example:

```ts
const jobStageCopy = {
  NOT_STARTED: "AI 요구사항 추출 준비",
  STAGE1_COMPLETE: "요구사항 후보 생성 완료",
  GATE_COMPLETE: "근거 게이트 완료",
  STAGE2_BATCH_N_COMPLETE: "의미 검토 배치 처리 중",
  FINALIZED: "검토 후보 준비 완료",
} as const;
```

Do not show percentages or remaining time.

For demo/frozen sessions, render the frozen requirement/evidence list read-only with labels `동결 공고 요구사항` and `Validator v1.5 예시`; do not render `AI EXTRACTED`.

- [ ] **Step 5: Build `RequirementsWorkspace` as Compact Review List + Inspector**

For custom sessions, keep all existing mutation semantics and version checks. Replace one-card-per-full-form layout with:

- 65% selectable compact list;
- 35% selected-item Inspector;
- Inspector contains exact source evidence, fields, Stage2 reason/issues, and actions;
- selected item draft is keyed by `requirement_id:profile.version` so backend version updates reset stale drafts;
- changing a field marks that item dirty and resets full-source acknowledgement;
- `항목 승인` remains requirement authority approval, not submission compliance;
- full-source acknowledgement and `Profile 확정` remain explicit;
- after confirmation, plan summary/compile is shown in the Inspector/sidebar area;
- `제출파일 선택하기` is enabled once profile confirmation produces `validation_profile="generic"`, regardless of planner READY/REVIEW_REQUIRED.

Keep mutation bodies identical to current semantics:

```ts
await sessionRequest(sid, `requirements/${id}/review`, {
  expected_version: profile.version,
  action,
  requirement,
});
```

and:

```ts
await sessionRequest(sid, "profile/confirm", {
  expected_version: profile.version,
  reviewed_full_source: true,
});
```

For demo/frozen sessions, render a read-only summary explaining that these are already frozen/verified example requirements. Provide a real link to `/upload`; no fake editable fields or AI history.

- [ ] **Step 6: Replace `AnnouncementScreen` and temporary `RequirementsScreen` bodies**

`AnnouncementScreen` becomes:

```tsx
export function AnnouncementScreen() {
  return <WorkflowGuard step="announcement"><AnnouncementWorkspace /></WorkflowGuard>;
}
```

`RequirementsScreen` becomes:

```tsx
export function RequirementsScreen() {
  return <WorkflowGuard step="requirements"><RequirementsWorkspace /></WorkflowGuard>;
}
```

Update PageTitle labels to Step 01 and Step 02 respectively.

- [ ] **Step 7: Migrate ACTUAL and planner UI tests through `/requirements`**

For `task06-actual-ai.spec.ts`, after extraction completes, navigate:

```ts
await page.getByRole("link", { name: "요구사항 검토로 이동" }).click();
await expect(page).toHaveURL(/\/requirements$/);
```

Then keep the existing edit/delete/approve/full-source confirm assertions against the new Inspector/list selectors.

For TASK08/TASK09 ACTUAL tests that perform profile operations by direct API calls, after `page.reload()` navigate explicitly to `/requirements` before asserting the plan summary if the UI is expected there, then continue to `/upload`. Do not alter operation-ledger expectations.

For TASK10 ACTUAL semantic test, direct API setup remains valid; after reload, navigate to `/requirements` only if the UI needs the confirmation state, otherwise go directly to `/upload` because the API-confirmed profile is already authoritative. Do not introduce an extra PLAN call: TASK10 operation ledger must remain `{ EXTRACT: 1, PLAN: 0, SEMANTIC: 4 }` in that test.

- [ ] **Step 8: Apply workspace visual layout and responsive collapse**

Add styles:

```css
.extraction-workspace { display:grid; grid-template-columns:minmax(0,.82fr) minmax(0,1fr); gap:20px; }
.review-workspace { display:grid; grid-template-columns:minmax(0,1.85fr) minmax(320px,1fr); gap:20px; }
.source-pane,.review-list,.review-inspector { background:var(--surface); border:1px solid var(--line); border-radius:14px; }
.source-highlight { background:var(--blue-soft); color:var(--ink); border-radius:4px; padding:1px 2px; }
@media (max-width: 900px) {
  .extraction-workspace,.review-workspace { grid-template-columns:1fr; }
}
```

Keep the current form labels and native controls accessible; switch green focus colors in `profile.module.css` to `var(--blue)`.

- [ ] **Step 9: Run focused extraction/review regression**

```bash
npm run typecheck
npm run build
npx playwright test tests/generic-profile.spec.ts tests/ui-redesign.spec.ts tests/task08-plan-ui.spec.ts --project=desktop
```

Expected: PASS.

- [ ] **Step 10: Commit Task 3**

```bash
git add frontend/components/announcement-workspace.tsx frontend/components/requirements-workspace.tsx frontend/components/generic-profile.tsx frontend/components/screens.tsx frontend/components/profile.module.css frontend/app/globals.css frontend/tests/generic-profile.spec.ts frontend/tests/ui-redesign.spec.ts frontend/tests/task06-actual-ai.spec.ts frontend/tests/task08-plan-ui.spec.ts frontend/tests/task08-actual-ai.spec.ts frontend/tests/task09-public-actual.spec.ts frontend/tests/task10-actual-semantic.spec.ts
git commit -m "feat(ui): split extraction and human review"
```

---

### Task 4: Turn upload/recheck into the truthful Preflight Package Workspace

**Files:**
- Create: `frontend/components/preflight-package.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/components/ui.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/task10-semantic-ui.spec.ts`
- Modify: `frontend/tests/golden-path.spec.ts`

**Interfaces:**
- Consumes: `CheckSession`, `SemanticReadiness`, current `UploadScreen` callbacks and polling state.
- Produces `PreflightPackageWorkspace` presentation props while `UploadScreen` remains the owner of package mutation, acknowledgement, validation start, AbortController generation, and polling.

Use this presentation interface:

```ts
interface PreflightPackageWorkspaceProps {
  session: CheckSession;
  recheck: boolean;
  busy: boolean;
  readiness: SemanticReadiness | null;
  acknowledged: boolean;
  selected: File[];
  error: string;
  pollError: string;
  onSelectFiles(event: React.ChangeEvent<HTMLInputElement>): void;
  onUpload(): void;
  onChooseDemo(caseName: "demo-broken" | "demo-fixed"): void;
  onAcknowledge(value: boolean): void;
  onValidate(): void;
}
```

- [ ] **Step 1: Add failing package-scope tests**

Extend `ui-redesign.spec.ts` using a confirmed generic session with a plan containing one VERIFIED `VIDEO_METADATA` plan and semantic readiness with one eligible requirement. Assert:

```ts
await openWithSession(page, confirmedSession, "/upload");
await expect(page.getByRole("region", { name: "제출 패키지" })).toBeVisible();
const scope = page.getByRole("region", { name: "이번 검사" });
await expect(scope).toContainText("영상 길이");
await expect(scope).toContainText("PDF 내용 근거");
await expect(scope).toContainText("1개 자동 검사");
await expect(scope).toContainText("1개 AI 근거 검토");
await expect(page.getByText(/페이지 수:|duration|초$/, { exact: false })).toHaveCount(0);
```

Add an assertion that `verification_plan_state="REVIEW_REQUIRED"` with a confirmed generic profile still renders the workspace and a REVIEW/manual-scope explanation rather than redirecting.

- [ ] **Step 2: Run targeted upload tests to confirm the old layout fails**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop -g "preflight|semantic|acknowledgement|poll"
```

Expected: at least package-scope/layout assertions fail; existing semantic safety tests must still pass before refactor where selectors are unchanged.

- [ ] **Step 3: Extract only presentation; preserve UploadScreen state machine**

Move package markup to `preflight-package.tsx`. Do **not** move or rewrite these functions/effects unless necessary for props wiring:

- `loadReadiness()`
- `resumePolling()`
- polling generation/AbortController refs
- both `useEffect` blocks controlling cleanup/resume
- `choose()`
- `upload()`
- `validate()`
- acknowledgement reset behavior

The new left pane is `Submission Package`; right pane is `이번 검사`.

- [ ] **Step 4: Derive the What-will-be-checked summary from real contracts**

Compute deterministic scope only from `session.verification_plan?.plans` with status `VERIFIED`. Map checker types to user copy with an exhaustive record:

```ts
const CHECKER_LABEL: Record<CheckerType, string> = {
  FILE_PRESENCE: "파일 존재 여부",
  FILE_COUNT: "파일 개수",
  FILE_NAME: "파일명",
  FILE_TYPE: "파일 형식",
  FILE_SIZE: "파일 크기",
  PDF_PAGE_COUNT: "PDF 페이지 수",
  VIDEO_METADATA: "영상 길이/메타데이터",
};
```

Semantic scope count is `readiness?.eligible_requirement_count ?? 0`.

Render counts only from those actual values. If plan state is `REVIEW_REQUIRED`, show `자동 검사 계획을 확정하지 못한 항목은 REVIEW로 남습니다.` and continue to permit package validation when the confirmed profile contract allows it.

- [ ] **Step 5: Keep pre-run file rows contract-true**

`FileList` may display:

- name;
- size;
- MIME type;
- neutral selected/received state.

It must not display page count, duration, PASS, or BLOCKER before validation. Do not infer type solely from filename for user claims when the server media type is available.

- [ ] **Step 6: Replace spinner-only long-run copy with truthful run activity**

For validation, derive only from `run_state` and whether semantic acknowledgement/readiness indicates semantic work can occur. Safe copy:

- `RUNNING` + eligible semantic count > 0: `객관적 조건과 PDF 내용 근거를 확인하고 있습니다.`
- `RUNNING` + no semantic eligible requirement: `객관적 제출 조건을 확인하고 있습니다.`
- `FAILED`: show `run_error` through Actionable Recovery.

Do not claim which internal semantic substage is executing because `CheckSession` does not expose it.

- [ ] **Step 7: Implement Actionable Recovery without hiding raw safety reason**

For `pollError`/`run_error`, render a clear heading and safe next action while retaining technical reason when it is the only exact diagnostic, e.g.:

```tsx
<section className="recovery-state" role="alert" aria-label="검사 복구 안내">
  <strong>검사를 완료하지 못했습니다</strong>
  <p>{pollError}</p>
  <p>현재 제출 패키지를 확인한 뒤 다시 실행할 수 있습니다.</p>
</section>
```

`PACKAGE_CHANGED_DURING_RUN` must remain observable because existing TASK10 tests depend on it.

- [ ] **Step 8: Update semantic UI tests only for intentional copy/selector changes**

Preserve all existing assertions covering:

- deterministic-only path has no acknowledgement checkbox;
- semantic path requires acknowledgement;
- running semantic validation polls to completion;
- stale completion cannot replace active session;
- transient poll failure retries;
- failed semantic poll remains actionable;
- reload resumes polling.

Update the expected running text to the new truthful copy rather than deleting these tests.

- [ ] **Step 9: Run package/polling regression desktop and mobile**

```bash
npm run typecheck
npm run build
npx playwright test tests/task10-semantic-ui.spec.ts tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: PASS with no horizontal overflow and no acknowledgement/polling regression.

- [ ] **Step 10: Commit Task 4**

```bash
git add frontend/components/preflight-package.tsx frontend/components/screens.tsx frontend/components/ui.tsx frontend/app/globals.css frontend/tests/ui-redesign.spec.ts frontend/tests/task10-semantic-ui.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): add truthful preflight package workspace"
```

---

### Task 5: Build the Results Evidence Chain, Status Tabs, and accessible Evidence Inspector

**Files:**
- Create: `frontend/components/results-workspace.tsx`
- Create: `frontend/components/evidence-drawer.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/components/ui.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/golden-path.spec.ts`
- Modify: `frontend/tests/task10-semantic-ui.spec.ts`
- Modify: `frontend/tests/ui-redesign.spec.ts`

**Interfaces:**
- Consumes: `ValidationResult`, `FindingStatus`, `CheckSession.status`, `previous_results`, semantic review metadata.
- Produces:
  - `ResultsWorkspace({ session }: { session: CheckSession })`
  - `EvidenceDrawer({ result, open, onClose, opener }: EvidenceDrawerProps)`
  - `STATUS_PRIORITY: Record<FindingStatus, number>` with exact approved order.

- [ ] **Step 1: Add failing Evidence Chain and ordering tests**

Extend `ui-redesign.spec.ts` with a mocked COMPLETE session whose results arrive in the order EXTERNAL, PASS, REVIEW, BLOCKER. Assert default display order:

```ts
const cards = page.locator("[data-testid='result-card']");
await expect(cards.nth(0)).toContainText("BLOCKER");
await expect(cards.nth(1)).toContainText("REVIEW");
await expect(cards.nth(2)).toContainText("PASS");
await expect(cards.nth(3)).toContainText("EXTERNAL");
```

Assert Status Tabs exist with counts and `전체` selected by default.

For a deterministic VIDEO_METADATA result, assert three labelled columns:

```ts
const card = page.getByRole("article", { name: /영상 길이/ });
await expect(card.getByText("RULE", { exact: true })).toBeVisible();
await expect(card.getByText("EVIDENCE", { exact: true })).toBeVisible();
await expect(card.getByText("VERDICT", { exact: true })).toBeVisible();
```

- [ ] **Step 2: Add failing drawer accessibility test**

```ts
test("evidence inspector opens from a result, closes with Escape, and restores focus", async ({ page }) => {
  await openWithSession(page, completedSession, "/results");
  const opener = page.getByRole("button", { name: /근거 자세히 보기/ }).first();
  await opener.focus();
  await opener.click();
  const drawer = page.getByRole("dialog", { name: "Evidence Inspector" });
  await expect(drawer).toBeVisible();
  await expect(drawer).toContainText("공고 요구사항");
  await expect(drawer).toContainText("제출파일 근거");
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(opener).toBeFocused();
});
```

- [ ] **Step 3: Run Results tests and confirm failure**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop -g "result|evidence|drawer|golden"
```

Expected: FAIL on the new chain/drawer/order contract.

- [ ] **Step 4: Implement Results summary, tabs, and approved ordering**

In `results-workspace.tsx`:

```ts
export const STATUS_PRIORITY: Record<FindingStatus, number> = {
  BLOCKER: 0,
  REVIEW: 1,
  PASS: 2,
  EXTERNAL: 3,
};
```

Do not use `updated_at` as a checked time.

READY explanatory copy must be exactly scoped to automatic certainty, e.g.:

> 자동 확인 가능한 필수 조건을 충족했습니다.

Status tabs: `전체`, `BLOCKER`, `REVIEW`, `PASS`, `EXTERNAL`; counts derive from current `session.results`. Use actual `<button>` elements with `aria-pressed` or `role="tab"`/`aria-selected` consistently.

- [ ] **Step 5: Implement neutral Evidence Chain cards**

Each card is an `<article data-testid="result-card">` with 3 desktop columns:

- RULE: title/requirement ID/expected constraint when present;
- EVIDENCE: measured fact + submission evidence + announcement locator summary;
- VERDICT: compact status chip + action/explanation.

Semantic rules:

- if `semantic_review` exists, status displayed is the backend `REVIEW` only;
- `RELATED_EVIDENCE_FOUND` copy says related evidence candidate found, not requirement satisfied;
- `NO_CLEAR_EVIDENCE` with FULL coverage says no clear evidence candidate found, not violation;
- PARTIAL/NONE coverage never implies whole-document absence.

Use existing `semantic_review.evidence.slice(0, 3)` maximum in visible/detail surfaces.

- [ ] **Step 6: Implement Evidence-first Right Side Drawer**

`evidence-drawer.tsx` must render:

1. compact status;
2. `공고 요구사항` with announcement evidence;
3. `제출파일 근거` with source/locator/excerpt or precise no-evidence/manual-review copy;
4. `왜 이 판정인가` explanation;
5. collapsed `기술 세부 보기` with `requirement_id`, `verification_plan_id`, `checker_type`, semantic coverage/assessment/provider prompt metadata when present.

Accessibility implementation requirements:

```tsx
<section
  role="dialog"
  aria-modal="true"
  aria-label="Evidence Inspector"
  tabIndex={-1}
  ref={dialogRef}
  className="evidence-drawer"
>
```

On open:

- store the opener element;
- focus the dialog or first close button;
- add keydown listener for Escape and Tab;
- cycle Tab/Shift+Tab inside focusable controls;
- on close remove listener and restore opener focus.

Render a backdrop button/element with an accessible close action. Do not make arbitrary result card clicks the only way to open; include a real button labelled `근거 자세히 보기`.

- [ ] **Step 7: Preserve recheck semantic fingerprint comparison**

When moving current comparison logic out of `screens.tsx`, copy the existing semantic assessment/evidence fingerprint comparison behavior exactly. Add/retain a TASK10 UI assertion that a REVIEW→REVIEW change with a different semantic fingerprint still renders `내용 근거 상태가 변경되었습니다.`.

- [ ] **Step 8: Implement desktop chain and mobile vertical stack CSS**

```css
.result-card { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,2fr) minmax(180px,1fr); border:1px solid var(--line); border-left:3px solid var(--status-color); border-radius:14px; background:var(--surface); }
.evidence-trace { opacity:0; transition:opacity 140ms ease; }
.result-card:hover .evidence-trace,.result-card:focus-within .evidence-trace { opacity:1; }
.evidence-drawer { position:fixed; inset:0 0 0 auto; width:min(520px,92vw); background:var(--surface); z-index:50; overflow:auto; }
@media (max-width: 760px) {
  .result-card { grid-template-columns:1fr; }
  .evidence-drawer { width:100vw; }
}
```

Use status-specific custom properties/classes; Electric Blue trace remains separate from status color.

- [ ] **Step 9: Update golden/TASK10 selectors, not semantics**

Golden path must still assert:

- broken demo has two BLOCKERs;
- R09 and R13 BLOCKER;
- R19 REVIEW;
- fixed recheck has no BLOCKER;
- R09/R13 PASS;
- overall fixed frozen demo remains `REVIEW_REQUIRED` because R19 still needs review;
- filters work after reload.

TASK10 semantic UI must still assert maximum three evidence excerpts, NO_CLEAR_EVIDENCE copy, recheck semantic change, and no semantic PASS/BLOCKER.

- [ ] **Step 10: Run Results/Evidence regression desktop and mobile**

```bash
npm run typecheck
npm run build
npx playwright test tests/golden-path.spec.ts tests/task10-semantic-ui.spec.ts tests/ui-redesign.spec.ts --project=desktop
npx playwright test tests/golden-path.spec.ts tests/ui-redesign.spec.ts --project=mobile
```

Expected: PASS; drawer keyboard test passes and no mobile horizontal overflow.

- [ ] **Step 11: Commit Task 5**

```bash
git add frontend/components/results-workspace.tsx frontend/components/evidence-drawer.tsx frontend/components/screens.tsx frontend/components/ui.tsx frontend/app/globals.css frontend/tests/golden-path.spec.ts frontend/tests/task10-semantic-ui.spec.ts frontend/tests/ui-redesign.spec.ts
git commit -m "feat(ui): add evidence chain and inspector"
```

---

### Task 6: Finish responsive, motion, focus, loading, and recovery polish

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/profile.module.css`
- Modify: `frontend/app/error.tsx`
- Modify: `frontend/app/not-found.tsx`
- Modify: `frontend/app/loading.tsx`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/golden-path.spec.ts`

**Interfaces:**
- Consumes all new UI components from Tasks 1–5.
- Produces final responsive and accessibility behavior without new data contracts.

- [ ] **Step 1: Add failing narrow-layout, reduced-motion, and recovery assertions**

In `ui-redesign.spec.ts` add:

```ts
test("reduced motion disables nonessential product transitions", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const duration = await page.locator(".product-frame").first().evaluate(el => getComputedStyle(el).transitionDuration);
  expect(duration === "0s" || duration === "0.001s").toBe(true);
});
```

In the existing screenshot capture helper, retain:

```ts
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
expect(overflow).toBe(false);
```

Add deep-link recovery assertions for `/requirements`, `/upload`, `/results`, and `/recheck` with missing prerequisites so each links to the nearest valid step defined by `recoveryHref()`.

- [ ] **Step 2: Run mobile/recovery tests and confirm missing polish failures**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: FAIL where reduced-motion or new route-specific recovery is not yet complete.

- [ ] **Step 3: Normalize global focus states and subtle motion**

Use Electric Blue focus throughout:

```css
:is(button,a,summary,input,select,textarea,[tabindex]):focus-visible {
  outline:3px solid color-mix(in srgb, var(--blue) 55%, white);
  outline-offset:3px;
}
.button,.result-card,.product-frame,.evidence-drawer { transition-duration:140ms; transition-timing-function:ease; }
.evidence-drawer { transition-duration:200ms; }
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { scroll-behavior:auto !important; transition-duration:.001ms !important; animation-duration:.001ms !important; animation-iteration-count:1 !important; }
}
```

Do not add parallax, bounce, scale loops, or decorative continuous motion.

- [ ] **Step 4: Complete responsive breakpoints**

Ensure:

- `< 900px`: extraction/review/package workspaces become one column;
- `< 760px`: Evidence Chain becomes vertical stack; drawer becomes full width;
- Stepper stays readable without horizontal page overflow; short Korean labels may stack under the number;
- landing split hero becomes one column;
- header center product nav may collapse/hide at narrow widths while keeping the primary CTA/start path reachable;
- file names and hash/locator strings use `overflow-wrap:anywhere`.

- [ ] **Step 5: Make framework error/404/loading states match Actionable Recovery**

Update:

`error.tsx`:

```tsx
<section className="recovery-state empty" role="alert">
  <h1>화면을 불러오지 못했습니다</h1>
  <p>현재 검사 상태는 가능한 범위에서 유지됩니다. 다시 시도하거나 홈에서 새 검사를 시작할 수 있습니다.</p>
  <button className="button primary" onClick={reset}>다시 시도</button>
  <a className="button secondary" href="/">홈으로</a>
</section>
```

`not-found.tsx` keeps a concise route recovery link. `loading.tsx` stays a truthful generic page-loading status and does not invent AI stages.

- [ ] **Step 6: Remove leftover legacy paper/pine/lime/rotation styling that is no longer referenced**

Delete dead selectors and colors after confirming via repository search they are unused. Keep compatibility aliases only when existing tests/components still reference them. The goal is one coherent White SaaS token system, not parallel old/new themes.

- [ ] **Step 7: Run desktop + mobile UI regression**

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts tests/generic-profile.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: PASS; no horizontal overflow; reduced-motion assertion passes.

- [ ] **Step 8: Commit Task 6**

```bash
git add frontend/app/globals.css frontend/components/profile.module.css frontend/app/error.tsx frontend/app/not-found.tsx frontend/app/loading.tsx frontend/tests/ui-redesign.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): finish responsive and recovery polish"
```

---

### Task 7: Full contract regression, ACTUAL verification, screenshots, and review-runtime gate

**Files:**
- Modify only if failures reveal UI-test selector drift: frontend test files already touched above.
- Do not modify backend behavior as part of this task.
- Generated evidence stays under existing `artifacts/` conventions and should not be committed unless repository policy already tracks that artifact.

**Interfaces:**
- Consumes the complete redesigned frontend.
- Produces evidence that existing TASK08/TASK10 ACTUAL authority and five competition screenshot states survive the redesign.

- [ ] **Step 1: Confirm no unintended backend or frozen-contract changes**

Run from repository root:

```bash
git diff origin/main...HEAD -- backend
```

Expected: no backend product-code diff for the UI redesign.

Then inspect the changed-file list:

```bash
git diff --name-only origin/main...HEAD
```

Expected: frontend + approved docs only, unless a test artifact policy explicitly requires another file.

- [ ] **Step 2: Run backend regression and secret scan**

From `backend/` using the existing project virtual environment:

```bash
python -m pytest -q
```

Expected: all existing backend tests PASS.

From repository root:

```bash
python scripts/scan_secrets.py
```

Expected: PASS with no live credential patterns.

- [ ] **Step 3: Run frontend CI-equivalent gates**

From `frontend/`:

```bash
npm ci
npm run typecheck
npm run build
```

Expected: all commands exit 0.

- [ ] **Step 4: Run the complete Playwright suite on both configured projects**

From `frontend/` after production build:

```bash
npm run test:smoke
```

Expected: all non-ACTUAL tests PASS; ACTUAL tests remain explicitly skipped unless their environment flags are set. Review `../artifacts/playwright-results.json` for failures/skips rather than inferring from console summary alone.

- [ ] **Step 5: Run TASK08 ACTUAL deterministic verifier path with the existing Codex provider**

Use the same local production-like environment that previously passed TASK08, including `FINAL_CHECK_AI_PROVIDER=codex`, `FINAL_CHECK_AI_MODEL=gpt-5.6-sol`, `FINAL_CHECK_AI_REASONING=high`, and the existing data directory required by operation-ledger checks. Set `TASK08_ACTUAL_AI=1`, then run only:

```bash
npx playwright test tests/task08-actual-ai.spec.ts --project=desktop
```

Required evidence:

- actual extraction retained the 60-second rule;
- plan is VERIFIED `VIDEO_METADATA`;
- 61s file remains BLOCKER/BLOCKED;
- 45s file remains PASS/READY;
- same PlanSet reused;
- operation ledger remains `{ EXTRACT: 1, PLAN: 1, SEMANTIC: 0 }`.

Do not change product logic to repair a visual selector failure; update only the test selector when the semantic assertion remains identical.

- [ ] **Step 6: Run TASK10 ACTUAL semantic path**

With the same provider configuration and `TASK10_ACTUAL_AI=1`, run:

```bash
npx playwright test tests/task10-actual-semantic.spec.ts --project=desktop
```

Required evidence:

- positive PDF remains `REVIEW / RELATED_EVIDENCE_FOUND` with locally grounded excerpt;
- missing evidence remains REVIEW and never BLOCKER;
- prompt injection remains REVIEW and never PASS/BLOCKER;
- recheck fingerprint/assessment changes remain visible;
- operation ledger remains `{ EXTRACT: 1, PLAN: 0, SEMANTIC: 4 }` for that test;
- semantic PASS/BLOCKER observed remains false.

- [ ] **Step 7: Capture the five competition screenshots from real product states**

Capture at desktop width from the redesigned review runtime:

1. Landing: Split Hero + Mini Product Window.
2. Step 01: Split Extraction Workspace with real custom extraction result/source evidence.
3. Step 02: Human Review with selected requirement Inspector showing source evidence and Human confirmation boundary.
4. Step 04 deterministic: actual 61s MP4 result showing BLOCKER/BLOCKED Evidence Chain.
5. Step 04 semantic: TASK10 positive PDF result with `REVIEW / RELATED_EVIDENCE_FOUND`; open Evidence Inspector showing real page locator/excerpt.

Save to a dedicated non-secret artifact directory, for example:

```text
artifacts/ui-redesign/screenshots/01-landing.png
artifacts/ui-redesign/screenshots/02-extraction.png
artifacts/ui-redesign/screenshots/03-human-review.png
artifacts/ui-redesign/screenshots/04-blocker.png
artifacts/ui-redesign/screenshots/05-semantic-evidence.png
```

Screenshot 4 and 5 must use actual tested states, not the landing static example.

- [ ] **Step 8: Start a separate review runtime; do not replace the judging runtime**

Start backend/frontend for the `ui-redesign` worktree on separate local ports or a separate temporary tunnel/domain. Verify `/api/health` returns `status=ok` under production-like configuration. Do not stop the existing process/tunnel serving `https://uncoy-joelle-macrodont.ngrok-free.dev` during this review.

Use the review runtime for a human visual pass of:

- landing at 1440px and mobile width;
- all five app steps;
- custom confirmed profile with planner READY;
- custom confirmed profile with planner REVIEW_REQUIRED;
- deterministic BLOCKER/PASS;
- semantic REVIEW positive/no-evidence;
- drawer keyboard behavior;
- actionable failure state.

- [ ] **Step 9: Run frozen-hash and diff sanity checks already present in the repository**

Run the repository's existing locked-hash/regression checks as they are currently documented/used by CI or task scripts. At minimum verify that no frontend task changed the known frozen values:

```text
Frozen Validator: 4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11
Gold manifest: 035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89
TASK06 Stage1: 52b226089eddf6fb109ab07f676110c7dea48c602397a7d6c283384e3be4d7f4
TASK06 Stage2: be838b1ef8d57f921147a3dfb993fa3237fb56dd766b825c883b644aa131163f
TASK08 Planner: 096fd93cd2c3770cd49dcdbe6131e0abda4ea8b3e074728dc7b45e219f36a4a6
```

If a documented script reports a hash mismatch, stop; do not update an expected hash for a UI redesign.

- [ ] **Step 10: Perform final Product Lead gate before public swap**

Create a concise evidence note in the PR description or review comment containing:

- branch/head SHA;
- backend test count/result;
- frontend typecheck/build result;
- Playwright pass/skip counts;
- TASK08 ACTUAL outcome and ledger;
- TASK10 ACTUAL outcome and ledger;
- five screenshot paths;
- statement `backend semantic changes: none`;
- statement `public judging runtime: not switched yet`.

Product Lead decision must be explicit: `GO`, `MODIFY`, or `STOP`.

- [ ] **Step 11: Commit any final test-selector-only fixes, then stop before public deployment**

If Step 2–10 required no source fixes, no extra commit is needed. If only test selectors/copy assertions changed while semantics stayed identical:

```bash
git add frontend/tests
git commit -m "test(ui): complete redesign regression gate"
```

Do not merge/swap the public runtime as part of this implementation plan without the explicit Product Lead GO after evidence review.

---

## Plan self-review record

### Spec coverage

- White SaaS + Electric Blue visual system: Tasks 1, 2, 6.
- Scan Corners + Check + wordmark: Task 1.
- Product Header / landing outside Stepper: Task 1.
- Segmented five-step Stepper: Task 1.
- Wide App Canvas: Tasks 1, 5.
- Split Hero / Mini Product Window / clean frames / 3-step story: Task 2.
- Split Extraction Workspace and truthful activity: Task 3.
- Compact Review List + Inspector and Human authority: Task 3.
- Preflight Package Workspace / real scope / semantic acknowledgement: Task 4.
- Status Tabs / Hybrid Summary / Neutral result cards / approved ordering: Task 5.
- RULE -> EVIDENCE -> VERDICT chain: Task 5.
- Right Side Evidence Inspector and technical disclosure: Task 5.
- Mobile vertical Evidence chain: Tasks 5, 6.
- Actionable Recovery: Tasks 1, 4, 6.
- Subtle motion / reduced motion / focus: Task 6.
- Competition screenshot set: Task 7.
- Audit C01 plan-not-gate correction: Tasks 1, 4.
- Audit C02 no pre-run page/duration: Task 4.
- Audit C03 truthful sample/claims: Task 2.
- Audit C04 result ordering: Task 5.
- Audit C05 route-aware chrome: Task 1.
- Audit C06 exact offsets/no fuzzy: Task 3.
- Audit C07 truthful stages: Tasks 3, 4.
- Audit C08 no `updated_at` validation timestamp: Task 5.
- Audit C09 polling/ack preservation: Task 4 and Task 7 ACTUAL regression.
- Audit C10 semantic fingerprint recheck: Task 5 and Task 7.
- Audit C11 no backend feature changes: Global Constraints and Task 7 diff gate.
- Audit C12 demo not fake AI: Tasks 1, 3.
- Audit C13 route regression migration: Tasks 1, 3, 7.
- Audit C14 fail-closed recovery: Tasks 1, 6.
- Audit C15 drawer accessibility: Tasks 5, 6.
- Audit C16 separate review runtime/public safety: Task 7.

### Placeholder scan

No `TBD`, `TODO`, deferred implementation placeholders, or unspecified “write tests” steps are permitted by this plan. Each task names exact files, test assertions, commands, and commit boundaries.

### Type/interface consistency

- Workflow helpers consume the existing `CheckSession` contract only.
- Preflight presentation receives the existing `SemanticReadiness` and `CheckSession` without adding API fields.
- Results consumes the existing `ValidationResult` / `SemanticReviewMetadata` fields.
- Exact source highlight consumes existing `evidence_start`, `evidence_end`, `evidence.quote`, and announcement text.
- No plan step adds a backend type or status.

## Completion definition

The UI redesign is implementation-complete only when Tasks 1–7 pass and Product Lead has reviewed the final regression evidence/screenshots. A visually polished branch that weakens Human confirmation, semantic REVIEW-only authority, acknowledgement, polling safety, plan fallback, or frozen hashes is **not complete**.