# FINAL CHECK UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign FINAL CHECK into the approved White SaaS + Electric Blue evidence-first product UI while preserving every TASK02–TASK10 authority, safety, polling, acknowledgement, and verification contract.

**Architecture:** Keep the backend and session contracts unchanged. Split the current combined frontend flow into a route-aware shell plus dedicated Announcement Extraction, Human Review, Submission Package, Results/Evidence, and Recheck presentation units. Centralize five-step route readiness in a pure workflow helper, preserve existing mutation/polling logic, and add an accessible Evidence Inspector over the existing result data.

**Tech Stack:** Next.js 16.3.4 App Router, React 19.2.8, TypeScript 5.9 strict mode, CSS, Playwright 1.62.1, existing FastAPI backend, existing local ChatGPT-authenticated Codex CLI runtime.

**Spec:** `docs/superpowers/specs/2026-09-13-final-check-ui-redesign-design.md`

**Normative audit:** `docs/superpowers/specs/2026-09-13-final-check-ui-redesign-audit.md`

## Global Constraints

- Audited backend baseline: `main@9f13866db1f14d917764a7d2865153f7aa6fbf3e`. If `origin/main` has advanced when execution starts, compare it with this baseline and stop for Product Lead review if contracts relevant to this plan changed.
- TASK02–TASK10 backend verification semantics, frozen hashes, Plan DSL, AI authority, Human-confirmation boundary, semantic eligibility, exact evidence gate, and acknowledgement rules do not change.
- Do not add backend work merely for presentation. No pre-run media metadata endpoint, new result status, new verifier family, new AI call, OCR/Vision/URL verification, or persistence schema change.
- Semantic findings remain `REVIEW`; AI never directly produces automatic `PASS`, `BLOCKER`, `READY`, or `BLOCKED` authority.
- Custom Step 03 readiness is `validation_profile === "generic" && generic_profile?.status === "CONFIRMED"`; Verification Plan `READY` is capability information, not a global gate.
- Demo Step 03 readiness is `validation_profile === "frozen_v15"`.
- Before validation, `SubmissionFile` UI may use only `name`, `size_bytes`, `media_type`, and `sha256`. Page count and duration may appear only when actual Results evidence supplies them.
- Preserve semantic acknowledgement reset, stale-session polling cancellation, reload polling resume, transient poll retry, mutation locks, failed-run recovery, and semantic REVIEW-to-REVIEW evidence-fingerprint comparison.
- `/` is outside the numbered workflow. App steps are `/announcement`, `/requirements`, `/upload`, `/results`, `/recheck`.
- Demo/frozen requirements must never be labelled as live `AI EXTRACTED` results.
- Results default order is `BLOCKER -> REVIEW -> PASS -> EXTERNAL`.
- Never use `CheckSession.updated_at` as a “last checked” timestamp.
- Electric Blue is brand/action/focus/evidence-trace color, never PASS color.
- Mobile keeps Evidence visible with `RULE -> EVIDENCE -> VERDICT` vertical stacking.
- Motion is subtle and nonessential; `prefers-reduced-motion` is mandatory.
- Existing public judging runtime stays untouched until a separate review runtime, all regressions, ACTUAL flows, screenshots, and Product Lead gate pass.
- Product AI configuration remains `gpt-5.6-sol` / reasoning `high`; UI work must not alter it.

## Execution isolation

Before Task 1, use `superpowers:using-git-worktrees`. Fetch `origin/main` and `origin/ui-redesign-design`; create isolated branch/worktree `ui-redesign` from `origin/ui-redesign-design`. Do not switch, stop, or delete the worktree/process currently serving the public judging URL.

Recommended controller for Tasks 1–5 and 7: **`gpt-5.6-sol`, reasoning `high`**. Task 6 mechanical CSS work may use **`gpt-5.6-sol`, reasoning `medium`**, but its review and the final gate return to `high`.

---

### Task 1: Lock the five-step workflow and route-aware product shell

**Files:**
- Create: `frontend/lib/workflow.ts`
- Create: `frontend/components/app-chrome.tsx`
- Create: `frontend/app/requirements/page.tsx`
- Create: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/components/ui.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/golden-path.spec.ts`

**Interfaces:**
- Consumes: `CheckSession`, `useSession()`, `usePathname()`.
- Produces:
  - `type WorkflowStep = "announcement" | "requirements" | "upload" | "results" | "recheck"`
  - `WORKFLOW_STEPS`
  - `canEnterStep(session, step)`
  - `isStepComplete(session, step)`
  - `recoveryHref(session, step)`
  - `AppChrome`
  - real `/requirements` route with an initial truthful read-only requirements summary that Task 3 enhances into the editable Inspector.

- [ ] **Step 1: Write workflow/chrome tests first**

Create `frontend/tests/ui-redesign.spec.ts` with a helper that also intercepts semantic readiness so upload tests never leak to a real backend session:

```ts
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
  await expect(page.getByRole("heading", { name: /제출/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /요구사항 검토로 돌아가기/ })).toHaveCount(0);
});

test("unconfirmed custom profile fails closed from upload to requirements", async ({ page }) => {
  const session = baseSession({ generic_profile: { status: "REVIEW_REQUIRED" } });
  await openWithSession(page, session, "/upload");
  await expect(page.getByRole("link", { name: /요구사항 검토/ })).toHaveAttribute("href", "/requirements");
});
```

Production types stay strict; test doubles may be structurally partial because they are JSON fixtures, but production code must not weaken `CheckSession`.

- [ ] **Step 2: Prove the old UI fails these tests**

From `frontend/`:

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts --project=desktop
```

Expected: FAIL because landing still shows the old Stepper and `/requirements` does not exist.

- [ ] **Step 3: Implement the pure workflow helper**

Create `frontend/lib/workflow.ts`:

```ts
import type { CheckSession } from "@/types/check";

export type WorkflowStep = "announcement" | "requirements" | "upload" | "results" | "recheck";
export interface WorkflowStepDefinition { key: WorkflowStep; href: string; label: string; number: string }

export const WORKFLOW_STEPS: readonly WorkflowStepDefinition[] = [
  { key: "announcement", href: "/announcement", label: "공고", number: "01" },
  { key: "requirements", href: "/requirements", label: "요구사항 검토", number: "02" },
  { key: "upload", href: "/upload", label: "제출파일", number: "03" },
  { key: "results", href: "/results", label: "결과", number: "04" },
  { key: "recheck", href: "/recheck", label: "재검사", number: "05" },
] as const;

function hasRequirementData(session: CheckSession): boolean {
  if (session.mode === "demo") return session.validation_profile === "frozen_v15" && session.requirements.length > 0;
  const profile = session.generic_profile;
  return Boolean(profile && (profile.requirements.length > 0 || profile.extraction_complete));
}

function canUpload(session: CheckSession): boolean {
  if (session.validation_profile === "frozen_v15") return true;
  return session.validation_profile === "generic" && session.generic_profile?.status === "CONFIRMED";
}

export function canEnterStep(session: CheckSession | null, step: WorkflowStep): boolean {
  if (!session?.announcement_name) return false;
  if (step === "announcement") return true;
  if (step === "requirements") return hasRequirementData(session);
  if (step === "upload") return canUpload(session);
  if (step === "results") return session.run_state === "COMPLETE" && session.results.length > 0;
  return session.results.length > 0 || session.previous_results.length > 0 || session.revision > 0;
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

`verification_plan_state` must not appear in `canUpload()`.

- [ ] **Step 4: Implement route-aware Product Header and Segmented Stepper**

Create `frontend/components/app-chrome.tsx` as a client component. It must:

- render Scan Corners + Check + `FINAL CHECK` on every route;
- on `/`, render `How it works`, `Evidence-first`, `검증 방식`, and the primary CTA but no numbered Stepper;
- on app routes, hide landing links and render the five steps from `WORKFLOW_STEPS`;
- derive enabled/completed state only from the workflow helper;
- set `aria-current="step"` only on the active enabled step.

Core structure:

```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/components/session-provider";
import { WORKFLOW_STEPS, canEnterStep, isStepComplete } from "@/lib/workflow";

export function Brand() {
  return <Link href="/" className="brand" aria-label="FINAL CHECK 홈">
    <span className="scan-check" aria-hidden="true"><span>✓</span></span><span>FINAL CHECK</span>
  </Link>;
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const { session } = useSession();
  const landing = path === "/";
  return <>
    <header className={`site-header ${landing ? "landing-header" : "app-header"}`}>
      <Brand />
      {landing && <>
        <nav className="product-nav" aria-label="제품 소개">
          <Link href="#how-it-works">How it works</Link>
          <Link href="#evidence-first">Evidence-first</Link>
          <Link href="#verification">검증 방식</Link>
        </nav>
        <Link className="button primary" href="#start-check">제출 전 검사 시작하기</Link>
      </>}
    </header>
    <div className={path === "/results" ? "shell shell-results" : "shell"}>
      {!landing && <nav aria-label="검사 단계" className="step-nav">
        {WORKFLOW_STEPS.map(step => {
          const active = path === step.href;
          const enabled = canEnterStep(session, step.key);
          const complete = isStepComplete(session, step.key);
          const content = <><span className="step-num">{complete ? "✓" : step.number}</span><span>{step.label}</span></>;
          return enabled
            ? <Link key={step.key} href={step.href} className={`step${active ? " active" : ""}`} aria-current={active ? "step" : undefined}>{content}</Link>
            : <span key={step.key} className="step disabled" aria-disabled="true">{content}</span>;
        })}
      </nav>}
      <main id="main">{children}</main>
      <footer className="site-footer"><strong>FINAL CHECK</strong><span>확신은, 근거에서 시작됩니다.</span></footer>
    </div>
  </>;
}
```

Modify `layout.tsx` to keep `SessionProvider` and place `<AppChrome>{children}</AppChrome>` inside it. Remove the old static header/Navigation duplication.

- [ ] **Step 5: Add route-specific fail-closed `WorkflowGuard`**

In `ui.tsx`:

```tsx
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

- [ ] **Step 6: Add `/requirements` with a truthful read-only first slice**

Create:

```tsx
// frontend/app/requirements/page.tsx
import { RequirementsScreen } from "@/components/screens";
export default function Requirements() { return <RequirementsScreen />; }
```

For Task 1, `RequirementsScreen` must already be real and truthful: for demo show frozen requirement titles/evidence read-only; for custom show extracted requirement titles/state read-only and explain that the next implementation task provides edit/approve Inspector. Do not display fabricated AI history, verdicts, or submission status. Task 3 replaces/enhances this view in the same branch before final review.

- [ ] **Step 7: Apply shell visual tokens**

Introduce:

```css
:root {
  --bg:#f8fafc; --surface:#fff; --ink:#101828; --muted:#667085; --line:#e4e7ec;
  --blue:#2563eb; --blue-soft:#eff6ff;
  --red:#b42318; --red-bg:#fff6f5; --amber:#b54708; --amber-bg:#fffaeb;
  --green:#067647; --green-bg:#ecfdf3; --external:#475467; --external-bg:#f2f4f7;
}
.shell { max-width:1240px; margin:0 auto; padding:0 32px; }
.shell-results { max-width:1320px; }
.step-nav { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border-bottom:1px solid var(--line); }
.step { border-bottom:2px solid transparent; }
.step.active { color:var(--blue); border-bottom-color:var(--blue); background:transparent; }
```

- [ ] **Step 8: Update demo golden path for the five-step UI**

After demo start, require `/announcement -> /requirements -> /upload`. On `/requirements`, assert truthful frozen/read-only wording, not `AI EXTRACTED`.

- [ ] **Step 9: Verify and commit Task 1**

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop
```

Expected: PASS.

```bash
git add frontend/lib/workflow.ts frontend/components/app-chrome.tsx frontend/app/requirements/page.tsx frontend/app/layout.tsx frontend/components/ui.tsx frontend/components/screens.tsx frontend/app/globals.css frontend/tests/ui-redesign.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): add five-step workflow shell"
```

---

### Task 2: Replace the legacy landing with the evidence-first product story

**Files:**
- Create: `frontend/components/landing.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/task09-public-first-visit.spec.ts`

**Interfaces:**
- Consumes existing real demo/custom start requests and `TextAnnouncementInput`.
- Produces `LandingScreen` plus anchors `#how-it-works`, `#evidence-first`, `#verification`, `#start-check`.

- [ ] **Step 1: Add failing landing tests**

```ts
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
```

- [ ] **Step 2: Verify failure**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts --project=desktop -g "landing"
```

Expected: FAIL against old preview/copy.

- [ ] **Step 3: Implement `LandingScreen` while preserving real start behavior**

Keep the current `POST /sessions`, `demo-announcement`, announcement file upload, and text start flows unchanged. Hero structure:

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

- [ ] **Step 4: Add three-step alternating story and real start section**

Add sections with IDs matching Product Header anchors. Use the approved workflow copy: `01 공고 읽기`, `02 기준 확정`, `03 제출물 검증`. Product-frame examples may illustrate existing behavior only. Give the real input area `id="start-check"`.

Use the scoped claim exactly:

> 자동 판정 가능한 항목은 공고 근거와 실제 측정/제출 근거를 연결하고, 의미 판단은 REVIEW로 남깁니다.

- [ ] **Step 5: Replace legacy tilted/paper landing CSS**

```css
.product-frame { background:var(--surface); border:1px solid var(--line); border-radius:16px; box-shadow:0 18px 45px rgba(16,24,40,.08); }
.landing-hero { grid-template-columns:minmax(0,.92fr) minmax(0,1fr); gap:64px; padding:88px 0 72px; }
.mini-chain { display:grid; grid-template-columns:1fr minmax(120px,1.2fr) auto; gap:16px; align-items:center; border-top:1px solid var(--line); padding:16px 0; }
.trust-line { margin-top:18px; font-size:13px; color:var(--muted); }
```

Remove `.preview` rotation and old lime/pine hero emphasis. No gradient logo, bounce, parallax, or infinite animation.

- [ ] **Step 6: Update the public first-visit hero selector and verify**

Keep ngrok interstitial behavior unchanged; update only the approved heading selector.

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/task09-public-first-visit.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts --project=mobile
```

Expected: PASS and no horizontal overflow.

- [ ] **Step 7: Commit Task 2**

```bash
git add frontend/components/landing.tsx frontend/components/screens.tsx frontend/app/globals.css frontend/tests/ui-redesign.spec.ts frontend/tests/task09-public-first-visit.spec.ts
git commit -m "feat(ui): redesign evidence-first landing"
```

---

### Task 3: Split AI extraction from Human Review

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
- Consumes existing `/extract`, `/requirements/{id}/review`, `/profile/confirm`, `/verification-plan/compile` contracts unchanged.
- Produces `AnnouncementWorkspace`, `RequirementsWorkspace`, and `splitEvidenceText(text,start,end,quote)`.

- [ ] **Step 1: Rewrite profile UI tests around `/announcement -> /requirements`**

After extraction, assert Step 01 has no `Profile 확정`, then click `요구사항 검토로 이동`, assert `/requirements`, select `요구사항 G001`, and assert `요구사항 Inspector` contains the edit/approve controls.

Add an exact-highlight fixture:

```ts
const text = "앞문장 기대효과를 포함해야 합니다. 뒷문장";
const quote = "기대효과를 포함해야 합니다.";
const start = text.indexOf(quote); // fixture construction only; production code must not use fuzzy/indexOf recovery
const end = start + quote.length;
```

Mock the profile with `evidence_start:start`, `evidence_end:end`, `evidence.quote:quote`; after selecting G001 assert the source pane contains `mark` with exactly `quote`.

- [ ] **Step 2: Verify the current combined screen fails**

```bash
npm run build
npx playwright test tests/generic-profile.spec.ts tests/ui-redesign.spec.ts --project=desktop
```

Expected: FAIL on route split/Inspector/highlight.

- [ ] **Step 3: Implement exact stored-offset source splitting**

```ts
export function splitEvidenceText(text: string, start: number, end: number, quote: string) {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > text.length) return null;
  const match = text.slice(start, end);
  if (match !== quote) return null;
  return { before: text.slice(0, start), match, after: text.slice(end) };
}
```

If this returns null, render stored source section + exact quote without a highlighted source span. No production fuzzy matching.

- [ ] **Step 4: Build Step 01 Split Extraction Workspace**

Custom layout: left ~45% full source, right ~55% extraction/candidate list. Candidate select/focus highlights its exact stored span. Extraction execution/polling keeps current request/version semantics.

Truthful activity translation may use only actual values:

```ts
const jobStageCopy = {
  NOT_STARTED: "AI 요구사항 추출 준비",
  STAGE1_COMPLETE: "요구사항 후보 생성 완료",
  GATE_COMPLETE: "근거 게이트 완료",
  STAGE2_BATCH_N_COMPLETE: "의미 검토 배치 처리 중",
  FINALIZED: "검토 후보 준비 완료",
} as const;
```

Use `pipeline_status` and `current_job.status/stage`; no percent or ETA.

Demo/frozen Step 01 is read-only and labelled `동결 공고 요구사항` / `Validator v1.5 예시`; never `AI EXTRACTED`.

- [ ] **Step 5: Build Step 02 Compact Review List + Inspector**

Custom layout: left ~65% compact list, right ~35% Inspector. Preserve existing draft/version semantics, dirty-item acknowledgement reset, edit/needs-review/approve/delete actions, full-source acknowledgement, profile confirmation, plan compile, provenance/history disclosure.

Mutation payloads remain:

```ts
await sessionRequest(sid, `requirements/${id}/review`, { expected_version: profile.version, action, requirement });
await sessionRequest(sid, "profile/confirm", { expected_version: profile.version, reviewed_full_source: true });
```

After confirmation, `제출파일 선택하기` is available even when planner state is `REVIEW_REQUIRED`; the planner state changes scope/copy, not the upload gate.

Demo/frozen Step 02 is a truthful read-only/already-confirmed summary with a link to `/upload`.

- [ ] **Step 6: Wire screens and responsive CSS**

```tsx
export function AnnouncementScreen() {
  return <WorkflowGuard step="announcement"><AnnouncementWorkspace /></WorkflowGuard>;
}
export function RequirementsScreen() {
  return <WorkflowGuard step="requirements"><RequirementsWorkspace /></WorkflowGuard>;
}
```

CSS:

```css
.extraction-workspace { display:grid; grid-template-columns:minmax(0,.82fr) minmax(0,1fr); gap:20px; }
.review-workspace { display:grid; grid-template-columns:minmax(0,1.85fr) minmax(320px,1fr); gap:20px; }
.source-pane,.review-list,.review-inspector { background:var(--surface); border:1px solid var(--line); border-radius:14px; }
.source-highlight { background:var(--blue-soft); color:var(--ink); border-radius:4px; padding:1px 2px; }
@media (max-width:900px) { .extraction-workspace,.review-workspace { grid-template-columns:1fr; } }
```

Switch `profile.module.css` focus color to `var(--blue)`.

- [ ] **Step 7: Migrate existing ACTUAL/planner tests without changing ledgers**

- TASK06 UI actions after extraction occur on `/requirements`.
- TASK08/TASK09 direct-API setup may navigate to `/requirements` for plan summary, then `/upload`.
- TASK10 direct-API profile confirmation may go directly to `/upload`; do not add a planner call. Its operation ledger must remain `{ EXTRACT: 1, PLAN: 0, SEMANTIC: 4 }`.

- [ ] **Step 8: Verify and commit Task 3**

```bash
npm run typecheck
npm run build
npx playwright test tests/generic-profile.spec.ts tests/ui-redesign.spec.ts tests/task08-plan-ui.spec.ts --project=desktop
```

Expected: PASS.

```bash
git add frontend/components/announcement-workspace.tsx frontend/components/requirements-workspace.tsx frontend/components/generic-profile.tsx frontend/components/screens.tsx frontend/components/profile.module.css frontend/app/globals.css frontend/tests/generic-profile.spec.ts frontend/tests/ui-redesign.spec.ts frontend/tests/task06-actual-ai.spec.ts frontend/tests/task08-plan-ui.spec.ts frontend/tests/task08-actual-ai.spec.ts frontend/tests/task09-public-actual.spec.ts frontend/tests/task10-actual-semantic.spec.ts
git commit -m "feat(ui): split extraction and human review"
```

---

### Task 4: Build the truthful Preflight Package Workspace

**Files:**
- Create: `frontend/components/preflight-package.tsx`
- Modify: `frontend/components/screens.tsx`
- Modify: `frontend/components/ui.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/ui-redesign.spec.ts`
- Modify: `frontend/tests/task10-semantic-ui.spec.ts`
- Modify: `frontend/tests/golden-path.spec.ts`

**Interfaces:**
- Consumes `CheckSession`, `SemanticReadiness`, `CheckerType`, current UploadScreen callbacks/polling state.
- Produces a presentational `PreflightPackageWorkspace`; `UploadScreen` stays owner of package mutation, semantic acknowledgement, validation start, AbortController generation, and polling.

- [ ] **Step 1: Add failing package-scope tests with explicit fixture data**

Construct a confirmed session inside the test:

```ts
const confirmedSession = baseSession({
  validation_profile: "generic",
  source_mode: "generic_verifier",
  verification_plan_state: "READY",
  generic_profile: { status: "CONFIRMED", requirements: [], extraction_complete: true },
  verification_plan: {
    plan_set_id: "plan-set", profile_id: "profile", profile_version: 1,
    announcement_sha256: "a".repeat(64), announcement_text_sha256: "b".repeat(64),
    confirmed_requirements_sha256: "c".repeat(64),
    planner_provenance: { provider:"Codex CLI", model:"gpt-5.6-sol", prompt_version:"task08", prompt_sha256:"d".repeat(64), execution_kind:"ACTUAL" },
    plan_schema_version: "task08-verification-plan-v1", created_at: stamp,
    plans: [{
      plan_id:"P1", requirement_id:"G001", planner_disposition:"CANDIDATE", checker_type:"VIDEO_METADATA", status:"VERIFIED", gate_reasons:[],
      target_selector:{ kind:"UNIQUE_EXTENSION", value:".mp4" },
      constraint:{ field:"duration_seconds", operator:"<=", value:60, unit:"seconds" },
      parameter_provenance:{ evidence_quote:"60초 이내", evidence_start:0, evidence_end:6, source_substring:"60초 이내", normalized_value:60, operator:"<=" },
      planner_reason:"deterministic video duration",
    }],
  },
});
await openWithSession(page, confirmedSession, "/upload", { ack_required:true, eligible_requirement_count:1, reason_code:null });
const scope = page.getByRole("region", { name:"이번 검사" });
await expect(scope).toContainText("영상 길이");
await expect(scope).toContainText("PDF 내용 근거");
await expect(scope).toContainText("1개 자동 검사");
await expect(scope).toContainText("1개 AI 근거 검토");
```

Also assert the **file-list/package pane** does not show `61.0s`, `45.0s`, or `페이지 수:` before validation.

Create a second fixture by overriding `verification_plan:null`, `verification_plan_state:"REVIEW_REQUIRED"`, `source_mode:"generic_review"`; assert it still enters upload and explains that uncompiled deterministic items remain REVIEW/manual scope.

- [ ] **Step 2: Verify layout tests fail before refactor**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop -g "preflight|semantic|acknowledgement|poll"
```

- [ ] **Step 3: Extract presentation only; preserve current UploadScreen state machine**

`PreflightPackageWorkspace` receives:

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
  onSelectFiles: (event: ChangeEvent<HTMLInputElement>) => void;
  onUpload: () => void;
  onChooseDemo: (caseName: "demo-broken" | "demo-fixed") => void;
  onAcknowledge: (value: boolean) => void;
  onValidate: () => void;
}
```

Import `type ChangeEvent` from React. Keep `loadReadiness`, `resumePolling`, generation/AbortController refs, cleanup/resume effects, `choose`, `upload`, `validate`, acknowledgement resets, and re-fetch-after-error behavior in `UploadScreen` unless a move is mechanically necessary and covered by tests.

- [ ] **Step 4: Derive `이번 검사` only from actual plan/readiness**

```ts
const CHECKER_LABEL: Record<CheckerType, string> = {
  FILE_PRESENCE:"파일 존재 여부", FILE_COUNT:"파일 개수", FILE_NAME:"파일명",
  FILE_TYPE:"파일 형식", FILE_SIZE:"파일 크기", PDF_PAGE_COUNT:"PDF 페이지 수",
  VIDEO_METADATA:"영상 길이/메타데이터",
};
```

Deterministic count = plans with `status === "VERIFIED"`. Semantic count = `readiness?.eligible_requirement_count ?? 0`. Never hard-code production counts.

When planner is `REVIEW_REQUIRED`, copy states that automatic plan was not established and affected items remain REVIEW/manual. Validation stays available if Global Constraints permit it.

- [ ] **Step 5: Keep pre-run file rows truthful**

Show filename, server-reported MIME type, size, and neutral received/selected state only. No page count, duration, PASS, or BLOCKER before a run.

- [ ] **Step 6: Render truthful run activity and actionable failure**

Safe copy:

- RUNNING + semantic eligible > 0: `객관적 조건과 PDF 내용 근거를 확인하고 있습니다.`
- RUNNING + semantic eligible == 0: `객관적 제출 조건을 확인하고 있습니다.`
- FAILED: show `run_error` plus `현재 제출 패키지를 확인한 뒤 다시 실행할 수 있습니다.`

Keep `PACKAGE_CHANGED_DURING_RUN` visible as an exact diagnostic. Do not invent semantic substages.

- [ ] **Step 7: Preserve every TASK10 polling/ack test**

Update selectors/copy only; retain coverage for deterministic-no-ack, required ack, background polling, stale completion isolation, transient retry, failed poll, and reload resume.

- [ ] **Step 8: Verify desktop/mobile and commit Task 4**

```bash
npm run typecheck
npm run build
npx playwright test tests/task10-semantic-ui.spec.ts tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: PASS.

```bash
git add frontend/components/preflight-package.tsx frontend/components/screens.tsx frontend/components/ui.tsx frontend/app/globals.css frontend/tests/ui-redesign.spec.ts frontend/tests/task10-semantic-ui.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): add truthful preflight package workspace"
```

---

### Task 5: Build Results Evidence Chain, Status Tabs, and accessible Evidence Inspector

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
- Consumes existing `ValidationResult`, `FindingStatus`, session status/results/previous_results, semantic metadata.
- Produces `ResultsWorkspace`, `EvidenceDrawer`, and `STATUS_PRIORITY`.

- [ ] **Step 1: Add explicit result fixtures and failing order/chain tests**

In `ui-redesign.spec.ts`:

```ts
function result(status: "BLOCKER"|"REVIEW"|"PASS"|"EXTERNAL", id: string, title: string, overrides: Record<string, unknown> = {}) {
  return {
    id, requirement_id:id, status, title, explanation:`${status} 설명`, action:"확인하세요.",
    announcement_evidence:{ source:"공고", locator:"p.1", excerpt:`${title} 공고 근거` },
    submission_evidence:{ source:"submission.mp4", locator:"duration", excerpt:"61.0s" },
    source_mode:"generic_verifier", verification_plan_id:"P1", checker_type:"VIDEO_METADATA",
    measured_fact:"61.0s", expected_constraint:"<= 60 seconds", semantic_review:null,
    ...overrides,
  };
}
const completedSession = baseSession({
  validation_profile:"generic", generic_profile:{ status:"CONFIRMED", requirements:[], extraction_complete:true },
  run_state:"COMPLETE", status:"BLOCKED",
  results:[
    result("EXTERNAL","G004","외부 확인"), result("PASS","G003","파일 형식"),
    result("REVIEW","G002","내용 요구사항", { checker_type:null, measured_fact:null }),
    result("BLOCKER","G001","영상 길이"),
  ],
});
await openWithSession(page, completedSession, "/results");
const cards = page.locator("[data-testid='result-card']");
await expect(cards.nth(0)).toContainText("BLOCKER");
await expect(cards.nth(1)).toContainText("REVIEW");
await expect(cards.nth(2)).toContainText("PASS");
await expect(cards.nth(3)).toContainText("EXTERNAL");
```

Assert tabs `전체/BLOCKER/REVIEW/PASS/EXTERNAL` with actual counts, plus `RULE`, `EVIDENCE`, `VERDICT` in the deterministic card.

- [ ] **Step 2: Add failing drawer keyboard/focus test using the same `completedSession`**

```ts
const opener = page.getByRole("button", { name:/근거 자세히 보기/ }).first();
await opener.focus();
await opener.click();
const drawer = page.getByRole("dialog", { name:"Evidence Inspector" });
await expect(drawer).toBeVisible();
await expect(drawer).toContainText("공고 요구사항");
await expect(drawer).toContainText("제출파일 근거");
await page.keyboard.press("Escape");
await expect(drawer).toBeHidden();
await expect(opener).toBeFocused();
```

- [ ] **Step 3: Verify failure**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=desktop -g "result|evidence|inspector|golden"
```

- [ ] **Step 4: Implement Hybrid Summary, Status Tabs, and exact priority**

```ts
export const STATUS_PRIORITY: Record<FindingStatus, number> = { BLOCKER:0, REVIEW:1, PASS:2, EXTERNAL:3 };
```

Counts derive from current results. Default tab is `전체`. Do not display `updated_at` as a check time. READY copy is scoped: `자동 확인 가능한 필수 조건을 충족했습니다.`

- [ ] **Step 5: Implement neutral 3-column Evidence Chain**

Each `<article data-testid="result-card">` has desktop columns:

- RULE: title/requirement/expected constraint;
- EVIDENCE: measured fact + submission evidence + announcement locator summary;
- VERDICT: compact status chip + explanation/action.

Semantic rendering rules:

- semantic status remains backend REVIEW;
- `RELATED_EVIDENCE_FOUND` = related evidence candidate, never “satisfied”;
- `NO_CLEAR_EVIDENCE` FULL = no clear evidence candidate, never “violation”;
- PARTIAL/NONE never implies whole-document absence;
- display at most three accepted semantic evidence excerpts.

- [ ] **Step 6: Implement Evidence-first Right Side Inspector**

`EvidenceDrawer` renders status, 공고 요구사항, 제출파일 근거, why/explanation, then collapsed technical details (`requirement_id`, plan/checker IDs, semantic coverage/assessment/provider metadata when present).

Dialog root:

```tsx
<section role="dialog" aria-modal="true" aria-label="Evidence Inspector" tabIndex={-1} ref={dialogRef} className="evidence-drawer">
```

On open, remember the opener and move focus into the drawer. Keydown handler closes on Escape and cycles Tab/Shift+Tab through drawer focusables. On close, remove listeners and restore opener focus. Provide real close and `근거 자세히 보기` buttons; do not rely on arbitrary card clicks.

- [ ] **Step 7: Preserve semantic recheck comparison**

Move existing comparison logic without reducing it to status-only comparison. Existing TASK10 assertion `내용 근거 상태가 변경되었습니다.` must continue to pass when REVIEW remains REVIEW but assessment/evidence fingerprint changes.

- [ ] **Step 8: Apply desktop/mobile styling**

```css
.result-card { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,2fr) minmax(180px,1fr); border:1px solid var(--line); border-left:3px solid var(--status-color); border-radius:14px; background:var(--surface); }
.evidence-trace { opacity:0; transition:opacity 140ms ease; }
.result-card:hover .evidence-trace,.result-card:focus-within .evidence-trace { opacity:1; }
.evidence-drawer { position:fixed; inset:0 0 0 auto; width:min(520px,92vw); background:var(--surface); z-index:50; overflow:auto; }
@media (max-width:760px) { .result-card { grid-template-columns:1fr; } .evidence-drawer { width:100vw; } }
```

Each status class sets `--status-color`; Electric Blue trace remains independent.

- [ ] **Step 9: Preserve golden/TASK10 semantic assertions and verify**

Golden path still proves broken demo R09/R13 BLOCKER, R19 REVIEW, fixed R09/R13 PASS, no BLOCKER after fixed recheck, and fixed frozen overall remains REVIEW_REQUIRED due R19. TASK10 retains max-three evidence, NO_CLEAR_EVIDENCE wording, semantic change comparison, and no semantic PASS/BLOCKER.

```bash
npm run typecheck
npm run build
npx playwright test tests/golden-path.spec.ts tests/task10-semantic-ui.spec.ts tests/ui-redesign.spec.ts --project=desktop
npx playwright test tests/golden-path.spec.ts tests/ui-redesign.spec.ts --project=mobile
```

Expected: PASS.

- [ ] **Step 10: Commit Task 5**

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
- Consumes Tasks 1–5 components.
- Produces final responsive/a11y/recovery behavior only; no data-contract changes.

- [ ] **Step 1: Add failing reduced-motion, overflow, and deep-link recovery tests**

```ts
test("reduced motion disables nonessential product transitions", async ({ page }) => {
  await page.emulateMedia({ reducedMotion:"reduce" });
  await page.goto("/");
  const seconds = await page.locator(".product-frame").first().evaluate(el => parseFloat(getComputedStyle(el).transitionDuration));
  expect(seconds).toBeLessThanOrEqual(0.001);
});
```

For desktop/mobile screenshots assert:

```ts
expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
```

Add deep-link cases proving missing prerequisites recover to `/`, `/announcement`, `/requirements`, `/upload`, or `/results` according to `recoveryHref()`.

- [ ] **Step 2: Verify expected failures**

```bash
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

- [ ] **Step 3: Normalize Electric Blue focus and subtle motion**

```css
:is(button,a,summary,input,select,textarea,[tabindex]):focus-visible { outline:3px solid color-mix(in srgb,var(--blue) 55%,white); outline-offset:3px; }
.button,.result-card,.product-frame,.evidence-drawer { transition-duration:140ms; transition-timing-function:ease; }
.evidence-drawer { transition-duration:200ms; }
@media (prefers-reduced-motion:reduce) {
  *,*::before,*::after { scroll-behavior:auto !important; transition-duration:.001s !important; animation-duration:.001s !important; animation-iteration-count:1 !important; }
}
```

No continuous decorative motion.

- [ ] **Step 4: Complete responsive rules**

- below 900px: extraction/review/package workspaces one column;
- below 760px: Evidence Chain vertical; drawer full width;
- Stepper wraps/stacks label under number without page overflow;
- landing hero one column;
- landing center nav may hide on narrow screens but primary start path stays reachable;
- file/hash/locator strings use `overflow-wrap:anywhere`.

- [ ] **Step 5: Align framework error/404/loading states with Actionable Recovery**

`error.tsx` keeps `reset` and Home actions and says the user can retry; `not-found.tsx` links Home; `loading.tsx` remains generic `화면을 준비하고 있습니다…` rather than inventing AI stages.

Use this error structure:

```tsx
<section className="recovery-state empty" role="alert">
  <h1>화면을 불러오지 못했습니다</h1>
  <p>현재 검사 상태는 가능한 범위에서 유지됩니다. 다시 시도하거나 홈에서 새 검사를 시작할 수 있습니다.</p>
  <button className="button primary" onClick={reset}>다시 시도</button>
  <a className="button secondary" href="/">홈으로</a>
</section>
```

- [ ] **Step 6: Remove unreferenced legacy paper/pine/lime/rotation CSS after repository search**

Delete only selectors/tokens proven unused after Tasks 1–5. Preserve any compatibility selector still referenced by components/tests until its consumer is migrated. Final CSS must have one coherent White SaaS token system.

- [ ] **Step 7: Verify and commit Task 6**

```bash
npm run typecheck
npm run build
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts tests/generic-profile.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop
npx playwright test tests/ui-redesign.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: PASS, no horizontal overflow, reduced-motion passes.

```bash
git add frontend/app/globals.css frontend/components/profile.module.css frontend/app/error.tsx frontend/app/not-found.tsx frontend/app/loading.tsx frontend/tests/ui-redesign.spec.ts frontend/tests/golden-path.spec.ts
git commit -m "feat(ui): finish responsive and recovery polish"
```

---

### Task 7: Full contract regression, ACTUAL verification, screenshots, and review-runtime gate

**Files:**
- Modify only test selectors/copy assertions if the UI changed while product semantics remain identical.
- Do not modify backend product behavior.
- Save generated evidence under existing `artifacts/` conventions; do not commit generated artifacts unless repository policy already tracks that exact artifact class.

**Interfaces:**
- Consumes complete redesigned frontend.
- Produces regression evidence for TASK08/TASK10 authority and five competition screenshot states.

- [ ] **Step 1: Confirm frontend-only implementation scope**

From repo root:

```bash
git diff origin/main...HEAD -- backend
git diff --name-only origin/main...HEAD
```

Expected: no backend product-code diff; changed files are approved docs/frontend only.

- [ ] **Step 2: Run backend regression and secret scan**

From `backend/`:

```bash
python -m pytest -q
```

From repo root:

```bash
python scripts/scan_secrets.py
```

Expected: all backend tests PASS; secret scan PASS.

- [ ] **Step 3: Run frontend CI-equivalent gates**

From `frontend/`:

```bash
npm ci
npm run typecheck
npm run build
```

Expected: exit 0.

- [ ] **Step 4: Run full Playwright smoke suite**

```bash
npm run test:smoke
```

Expected: all non-ACTUAL tests pass on configured desktop/mobile projects; ACTUAL tests are skipped unless their explicit flags are set. Inspect `../artifacts/playwright-results.json` for exact pass/skip/fail counts.

- [ ] **Step 5: Re-run TASK08 ACTUAL deterministic path**

Use the same existing production-like local environment that previously passed TASK08: `FINAL_CHECK_AI_PROVIDER=codex`, `FINAL_CHECK_AI_MODEL=gpt-5.6-sol`, `FINAL_CHECK_AI_REASONING=high`, existing `FINAL_CHECK_DATA_DIR`, and `TASK08_ACTUAL_AI=1`.

```bash
npx playwright test tests/task08-actual-ai.spec.ts --project=desktop
```

Required: actual 60s rule extraction; VERIFIED VIDEO_METADATA plan; 61s BLOCKER/BLOCKED; 45s PASS/READY; same PlanSet; ledger `{ EXTRACT:1, PLAN:1, SEMANTIC:0 }`.

- [ ] **Step 6: Re-run TASK10 ACTUAL semantic path**

With existing Codex provider config and `TASK10_ACTUAL_AI=1`:

```bash
npx playwright test tests/task10-actual-semantic.spec.ts --project=desktop
```

Required: positive = REVIEW/RELATED_EVIDENCE_FOUND with locally grounded excerpt; missing = REVIEW and never BLOCKER; injection = REVIEW and never PASS/BLOCKER; recheck fingerprint/assessment change preserved; ledger `{ EXTRACT:1, PLAN:0, SEMANTIC:4 }`; semantic PASS/BLOCKER observed = false.

- [ ] **Step 7: Capture five competition screenshots from real product states**

Save:

```text
artifacts/ui-redesign/screenshots/01-landing.png
artifacts/ui-redesign/screenshots/02-extraction.png
artifacts/ui-redesign/screenshots/03-human-review.png
artifacts/ui-redesign/screenshots/04-blocker.png
artifacts/ui-redesign/screenshots/05-semantic-evidence.png
```

Required states:

1. Landing Split Hero + Mini Product Window.
2. Real custom extraction showing source + candidate relationship.
3. Human Review with selected Inspector and source evidence.
4. Actual 61s deterministic BLOCKER/BLOCKED Evidence Chain.
5. TASK10 positive PDF `REVIEW / RELATED_EVIDENCE_FOUND` with open Evidence Inspector showing actual locator/excerpt.

Screenshots 4–5 must not use static landing demo content.

- [ ] **Step 8: Start a separate review runtime and keep judging runtime alive**

Use separate ports and/or a temporary review tunnel/domain for the `ui-redesign` worktree. Verify review `/api/health` returns `status=ok` with production-like configuration. Do not stop or replace `https://uncoy-joelle-macrodont.ngrok-free.dev` yet.

Human review matrix: landing desktop/mobile; all five steps; planner READY; planner REVIEW_REQUIRED with confirmed profile; deterministic BLOCKER/PASS; semantic related/no-clear-evidence; drawer keyboard behavior; actionable failure.

- [ ] **Step 9: Verify frozen hashes did not change**

Existing locked checks must retain:

```text
Frozen Validator 4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11
Gold manifest 035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89
TASK06 Stage1 52b226089eddf6fb109ab07f676110c7dea48c602397a7d6c283384e3be4d7f4
TASK06 Stage2 be838b1ef8d57f921147a3dfb993fa3237fb56dd766b825c883b644aa131163f
TASK08 Planner 096fd93cd2c3770cd49dcdbe6131e0abda4ea8b3e074728dc7b45e219f36a4a6
```

A mismatch is STOP; never update an expected hash for this UI redesign.

- [ ] **Step 10: Produce final review evidence and stop before public swap**

PR/review evidence must include: branch/head SHA, backend test result/count, typecheck/build, Playwright pass/skip counts, TASK08 ACTUAL outcome+ledger, TASK10 ACTUAL outcome+ledger, five screenshot paths, `backend semantic changes: none`, `public judging runtime: not switched yet`.

Product Lead must issue explicit `GO`, `MODIFY`, or `STOP` before merge/public runtime swap.

If only intentional selector/copy test fixes were needed after the final run:

```bash
git add frontend/tests
git commit -m "test(ui): complete redesign regression gate"
```

Do not merge or swap public runtime in this plan without that final Product Lead decision.

---

## Plan self-review record

### Spec and audit coverage

- Brand/tokens/Product Header/Segmented Stepper/Wide Canvas: Tasks 1–2, 6.
- Split Hero/Mini Product Window/3-step story/Clean Product Frames: Task 2.
- Split Extraction + exact source evidence + truthful processing: Task 3.
- Compact Review List + Inspector + Human authority: Task 3.
- Preflight Package Workspace + plan fallback + acknowledgement/polling safety: Task 4.
- Hybrid Summary/Status Tabs/neutral cards/approved order/Evidence Chain: Task 5.
- Right Side Evidence Inspector + keyboard/focus + technical detail: Task 5.
- Mobile Evidence vertical stack, reduced motion, recovery: Tasks 5–6.
- Audit C01 plan-not-global-gate: Tasks 1, 3, 4.
- C02 no invented media metadata: Task 4.
- C03 truthful sample/claims: Task 2.
- C04 status order: Task 5.
- C05 route-aware chrome: Task 1.
- C06 exact offsets: Task 3.
- C07 truthful stage data: Tasks 3–4.
- C08 no updated_at check time: Task 5.
- C09 polling/ack: Task 4 and Task 7.
- C10 semantic fingerprint: Task 5 and Task 7.
- C11 no backend feature changes: Global Constraints + Task 7.
- C12 demo does not fake AI: Tasks 1 and 3.
- C13 route regression migration: Tasks 1, 3, 7.
- C14 fail-closed guards: Tasks 1 and 6.
- C15 drawer accessibility: Tasks 5 and 6.
- C16 separate review runtime: Task 7.
- Five competition screenshots: Task 7.

### Self-review corrections applied

- Mocked workflow tests intercept `/semantic-readiness`; they cannot accidentally fail by contacting a nonexistent backend session.
- Reduced-motion CSS and its assertion use compatible seconds-based values.
- Task 4 defines `confirmedSession` data before using it.
- Task 5 defines result fixtures and `completedSession` before using them.
- Task 1 uses a truthful minimal read-only `/requirements` slice rather than an undefined screen body.
- Production source highlighting is exact-offset only; `indexOf` appears only in deterministic test-fixture construction.

### Type consistency

- Workflow helpers consume existing `CheckSession` only.
- Package workspace consumes existing `CheckSession`, `SemanticReadiness`, and `CheckerType` only.
- Results uses existing `ValidationResult`/semantic metadata only.
- No task creates a backend field/status/endpoint.

## Completion definition

Implementation is complete only after Tasks 1–7 and final Product Lead evidence review. A visually polished branch that weakens Human confirmation, semantic REVIEW-only authority, acknowledgement, polling safety, planner fallback, recheck fingerprint comparison, or frozen hashes is **not complete**.