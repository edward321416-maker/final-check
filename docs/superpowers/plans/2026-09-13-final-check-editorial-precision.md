# FINAL CHECK Editorial Precision v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine FINAL CHECK from the merged White SaaS UI into the approved Editorial Precision visual system: predominantly black/white/neutral, blue used sparingly, evidence-first alignment, and deterministic integer-pixel visual tokens across all production screens.

**Architecture:** Keep all TASK02–TASK10 behavior, routing, session logic, Human confirmation, acknowledgement, polling, and verifier authority unchanged. Implement the refinement as a presentation-layer change centered on a canonical token file, a deterministic CSS-token audit, targeted CSS/markup simplification, and desktop/mobile visual QA. Existing product components remain the behavioral source of truth; changes to TSX are limited to visual grouping/copy structure where CSS alone cannot express the approved editorial hierarchy.

**Tech Stack:** Next.js 16.3.4 App Router, React 19.2.8, TypeScript 5.9 strict mode, plain CSS/CSS Modules, Node.js built-in test runner for the token auditor, Playwright 1.62.1, existing FastAPI backend and existing local ChatGPT-authenticated Codex CLI for ACTUAL regressions.

**Spec:** `docs/superpowers/specs/2026-09-13-final-check-editorial-precision-design.md`

## Global Constraints

- Implementation baseline is merged `main@d71ddba79d78c1aa1e4963c792e7a8c6b72023c1` (PR #15 merge commit). If `origin/main` advances before execution, compare the new main against this baseline and stop for Product Lead review if frontend/API contracts relevant to this plan changed.
- This is a visual-system refinement only. Do not change backend product code, TASK02–TASK10 verification semantics, Human-confirmation authority, semantic REVIEW-only authority, Plan DSL, upload readiness, semantic acknowledgement, polling/stale-session protection, recheck fingerprint comparison, frozen hashes, or public-runtime architecture.
- Keep the five-step IA exactly: `/announcement` → `/requirements` → `/upload` → `/results` → `/recheck`; `/` remains outside the numbered workflow.
- Use the approved neutral palette: `#FFFFFF`, `#FAFAF9`, `#0A0A0A`, `#525252`, `#737373`, `#A3A3A3`, `#E5E5E5`, `#D4D4D4`; approved accent: `#3157FF`, hover `#2447E6`, soft `#F4F6FF`; approved semantic colors from the spec only.
- Blue is limited to primary CTA, active step, focus ring, selected evidence relationship, source/evidence trace, selected control/tab when needed, and the brand mark. It must not become the page atmosphere and never means PASS.
- Approved type pairs only: `56/64`, `48/56`, `40/48`, `32/40`, `24/32`, `20/28`, `16/24`, `14/20`, `12/16`, `11/16` px. No unitless/fractional line-height and no `clamp()`/`vw` typography.
- Approved font weights only: `400`, `500`, `600`, `700`. Approved letter spacing only: `0px`, `-1px`, `1px`.
- Approved visible spacing tokens only: `0`, `4`, `8`, `12`, `16`, `24`, `32`, `48`, `64`, `80`, `96`, `120` px. Layout calculations using `%`, `fr`, `vw`, `vh`, `min()`, `max()`, `clamp()`, and `calc()` are exempt when they are geometry rather than visible spacing.
- Approved radius tokens only: `0`, `4`, `8`, `12` px. Approved border widths only: `1`, `2`, `3` px.
- Ordinary product surfaces have no shadow. Evidence Inspector/modal overlays may use only `--shadow-overlay: 0 16px 48px rgba(10, 10, 10, 0.12)`.
- Body/application copy defaults to `14/20`; meaningful supporting copy may use `16/24`; `11/16` is restricted to tertiary/technical metadata.
- Do not add a left sidebar or reopen information architecture merely because the approved visual mockup used one. The user approved its visual language, not a navigation rewrite.
- Do not reintroduce card-heavy colored metric blocks. Results must read primarily as `RULE → EVIDENCE → VERDICT` rows separated by rules/whitespace.
- Preserve the exact Unicode code-point evidence-offset fix and its non-BMP/repeated-quote regression tests.
- Preserve all existing semantic acknowledgement, stale-session polling cancellation, reload polling resume, transient retry, failed-run recovery, planner fallback, and REVIEW→REVIEW evidence-fingerprint tests.
- Existing public judging runtime must not be stopped, restarted, or swapped until Product Lead explicitly authorizes deployment after final review.

## Execution Isolation

At execution time use `superpowers:using-git-worktrees`. Prefer a new branch/worktree named `editorial-precision-v2` from current `origin/main`, not the old merged `ui-redesign` worktree. Copy/read this spec and plan from the approved planning branch if they are not yet on main. Do not reuse or delete the worktree that serves the public judging URL.

Recommended controller for Tasks 1–7: **`gpt-5.6-sol`, reasoning `high`**. Task 3 is mostly mechanical CSS normalization and may use `medium` for implementation, but every task review and the final whole-branch review return to `high`.

---

## File Structure Lock

Create or modify only the following product surfaces unless a failing test proves one additional frontend file is required:

- `frontend/app/visual-tokens.css` — canonical visual tokens only.
- `frontend/app/globals.css` — shared layout and component presentation; consumes tokens but does not define arbitrary palette/type/spacing values.
- `frontend/components/profile.module.css` — form/review-specific presentation; consumes canonical tokens.
- `frontend/components/landing.tsx` — minimal markup changes only if needed to express editorial grouping.
- `frontend/components/app-chrome.tsx` — shell markup only if a class/semantic wrapper is needed; workflow logic must not change.
- `frontend/components/announcement-workspace.tsx` — no behavior changes; visual grouping only if needed.
- `frontend/components/requirements-workspace.tsx` — no mutation/version logic changes; visual grouping only if needed.
- `frontend/components/preflight-package.tsx` — no upload/ack/poll logic changes; visual grouping only if needed.
- `frontend/components/results-workspace.tsx` — approved result-summary/editorial-row markup and copy hierarchy.
- `frontend/components/evidence-drawer.tsx` — no focus-trap/keyboard logic changes; presentation wrappers only if needed.
- `frontend/components/screens.tsx` — result page title/copy only if required by the approved hierarchy; UploadScreen state machine stays untouched.
- `frontend/scripts/visual-token-audit.mjs` — deterministic production-style audit engine.
- `frontend/scripts/visual-token-audit.test.mjs` — Node built-in unit tests for the audit engine.
- `frontend/tests/editorial-precision.spec.ts` — Playwright visual-contract assertions and QA-state screenshots.
- Existing focused tests under `frontend/tests/` — selector/copy updates only where the visual refinement intentionally changes presentation.
- `frontend/package.json` — visual audit scripts.
- `.github/workflows/ci.yml` — add the visual-token audit gate after dependencies install and before typecheck.

Do not add a component library, Tailwind, CSS-in-JS, a design-token package, or another frontend dependency.

---

### Task 1: Add the canonical editorial tokens and deterministic audit engine

**Files:**
- Create: `frontend/app/visual-tokens.css`
- Create: `frontend/scripts/visual-token-audit.mjs`
- Create: `frontend/scripts/visual-token-audit.test.mjs`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: approved token values from the spec.
- Produces:
  - CSS custom properties in `visual-tokens.css`.
  - `auditCssText(source, filename)` returning an array of `{ file, property, value, reason }` findings.
  - `collectProductionCssFiles(frontendRoot)` returning production `.css`/`.module.css` files under `app/` and `components/`, excluding `.next` and generated artifacts.
  - CLI mode `node scripts/visual-token-audit.mjs --check` that exits `1` on findings and `0` when clean.
  - package scripts `test:visual-tokens` and `audit:visual-tokens`.

- [ ] **Step 1: Write failing unit tests for the audit rules**

Create `frontend/scripts/visual-token-audit.test.mjs` using Node's built-in test runner:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { auditCssText } from "./visual-token-audit.mjs";

function reasons(css) {
  return auditCssText(css, "fixture.css").map(item => item.reason);
}

test("rejects unapproved visual values", () => {
  const result = reasons(`
    .x {
      font-size: 13px;
      line-height: 1.65;
      padding: 18px;
      gap: 10px;
      border-radius: 14px;
      border-width: 4px;
      font-weight: 650;
      letter-spacing: .4px;
      color: #2563eb;
    }
  `);
  assert(result.some(reason => reason.includes("font-size")));
  assert(result.some(reason => reason.includes("line-height")));
  assert(result.some(reason => reason.includes("spacing")));
  assert(result.some(reason => reason.includes("radius")));
  assert(result.some(reason => reason.includes("border width")));
  assert(result.some(reason => reason.includes("font weight")));
  assert(result.some(reason => reason.includes("letter spacing")));
  assert(result.some(reason => reason.includes("raw color")));
});

test("rejects interpolated typography", () => {
  const result = reasons(`.hero { font-size: clamp(40px, 4vw, 56px); line-height: 1.2; }`);
  assert(result.some(reason => reason.includes("responsive typography")));
});

test("accepts token-based declarations and layout calculations", () => {
  const findings = auditCssText(`
    .ok {
      font-size: var(--type-body-size);
      line-height: var(--type-body-line);
      padding: var(--space-4) var(--space-6);
      gap: var(--space-3);
      border-radius: var(--radius-1);
      border-width: var(--border-1);
      color: var(--text-primary);
      width: min(100%, 1240px);
      grid-template-columns: .82fr 1fr;
      opacity: .65;
    }
  `, "fixture.css");
  assert.deepEqual(findings, []);
});
```

- [ ] **Step 2: Run the test to verify RED**

From `frontend/`:

```bash
node --test scripts/visual-token-audit.test.mjs
```

Expected: FAIL because `visual-token-audit.mjs` does not exist.

- [ ] **Step 3: Create the canonical token file**

Create `frontend/app/visual-tokens.css` with exactly these canonical roles and scales:

```css
:root {
  --page: #FFFFFF;
  --surface: #FFFFFF;
  --surface-subtle: #FAFAF9;
  --text-primary: #0A0A0A;
  --text-secondary: #525252;
  --text-muted: #737373;
  --text-faint: #A3A3A3;
  --border-subtle: #E5E5E5;
  --border-strong: #D4D4D4;

  --accent: #3157FF;
  --accent-hover: #2447E6;
  --accent-soft: #F4F6FF;

  --status-blocker: #C62828;
  --status-blocker-soft: #FFF6F5;
  --status-review: #A15C00;
  --status-review-soft: #FFF9EB;
  --status-pass: #17824B;
  --status-pass-soft: #F0FBF5;
  --status-external: #737373;
  --status-external-soft: #F5F5F5;

  --type-display-lg-size: 56px;
  --type-display-lg-line: 64px;
  --type-display-md-size: 48px;
  --type-display-md-line: 56px;
  --type-heading-1-size: 40px;
  --type-heading-1-line: 48px;
  --type-heading-2-size: 32px;
  --type-heading-2-line: 40px;
  --type-heading-3-size: 24px;
  --type-heading-3-line: 32px;
  --type-heading-4-size: 20px;
  --type-heading-4-line: 28px;
  --type-body-lg-size: 16px;
  --type-body-lg-line: 24px;
  --type-body-size: 14px;
  --type-body-line: 20px;
  --type-small-size: 12px;
  --type-small-line: 16px;
  --type-micro-size: 11px;
  --type-micro-line: 16px;

  --space-0: 0px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;
  --space-9: 80px;
  --space-10: 96px;
  --space-11: 120px;

  --radius-0: 0px;
  --radius-1: 4px;
  --radius-2: 8px;
  --radius-3: 12px;
  --border-1: 1px;
  --border-2: 2px;
  --border-3: 3px;

  --shadow-overlay: 0 16px 48px rgba(10, 10, 10, 0.12);
}
```

No compatibility palette aliases such as `--blue`, `--ink`, or `--line` are permanent. If a short-lived alias is needed while Tasks 2–5 migrate CSS, mark it inside a clearly delimited `/* TEMPORARY MIGRATION ALIASES — REMOVE IN TASK 6 */` block and remove it before the audit gate is enabled.

- [ ] **Step 4: Implement the audit engine**

Create `frontend/scripts/visual-token-audit.mjs`. The engine must:

```js
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TYPE = new Set([11, 12, 14, 16, 20, 24, 32, 40, 48, 56]);
const LINE = new Set([16, 20, 24, 28, 32, 40, 48, 56, 64]);
const SPACE = new Set([0, 4, 8, 12, 16, 24, 32, 48, 64, 80, 96, 120]);
const RADIUS = new Set([0, 4, 8, 12]);
const BORDER = new Set([0, 1, 2, 3]);
const WEIGHTS = new Set([400, 500, 600, 700]);
const LETTER = new Set([-1, 0, 1]);
const COLOR_FILE = "visual-tokens.css";

const SPACING_PROPERTIES = new Set([
  "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
  "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
  "gap", "row-gap", "column-gap", "inset", "top", "right", "bottom", "left",
  "scroll-margin", "scroll-margin-top", "scroll-margin-right", "scroll-margin-bottom", "scroll-margin-left",
]);

function pxNumbers(value) {
  return [...value.matchAll(/(-?\d+(?:\.\d+)?)px/g)].map(match => Number(match[1]));
}

function usesVariableOrLayoutExpression(value) {
  return /var\(|calc\(|min\(|max\(/.test(value);
}

function add(findings, file, property, value, reason) {
  findings.push({ file, property, value: value.trim(), reason });
}
```

Then implement `auditCssText()` with these rules:

1. Strip comments before scanning.
2. Parse rule blocks with `/([^{}]+)\{([^{}]*)\}/g`; nested `@media` content is still discovered by subsequent block matches after stripping the outer at-rule text.
3. Parse declarations with `/([\w-]+)\s*:\s*([^;]+);/g`.
4. Allow `var(...)` for visual-token properties.
5. `font-size`: reject `clamp`, `vw`, unitless numbers, fractional px, and px values outside `TYPE`.
6. `line-height`: reject unitless/fractional values and px values outside `LINE`; allow `var(...)` only.
7. `SPACING_PROPERTIES`: inspect every px number in shorthands; reject fractional px and values outside `SPACE`. Permit `auto`, percentages, and layout expressions only when no fixed non-token px occurs.
8. `border-radius`: every px number must be in `RADIUS`.
9. `border-width`, `border-top-width`, `border-right-width`, `border-bottom-width`, `border-left-width`, and width portions of border shorthands must be in `BORDER`.
10. `font-weight`: numeric values must be in `WEIGHTS`; `normal` maps to 400, `bold` maps to 700; reject all others.
11. `letter-spacing`: permit `normal`, `var(...)`, `-1px`, `0px`, `1px`; reject fractional/other values.
12. For production CSS except `visual-tokens.css`, reject raw `#hex`, `rgb()`, `rgba()`, `hsl()`, `hsla()` values; require `var(...)`, `transparent`, `currentColor`, `inherit`, or `none`.
13. Reject `box-shadow` outside `visual-tokens.css` unless the value is exactly `var(--shadow-overlay)` or `none`.
14. For selectors containing `.scan-check`, `.dot`, `.alert-symbol`, `.drawer-close`, `.file-icon`, or `.upload-glyph`, audit fixed `width`, `height`, `min-width`, and `min-height` px values against `SPACE`; layout widths elsewhere are exempt.
15. Reject production `font:` shorthand so size/line/weight cannot bypass the explicit property audit. Migrate all shorthand declarations to explicit properties in later tasks.

Export `auditCssText` and `collectProductionCssFiles`. CLI `--check` recursively scans `frontend/app/**/*.css` and `frontend/components/**/*.css` and prints one line per finding:

```text
frontend/app/globals.css :: font-size=13px :: unapproved font-size token
```

Exit `1` when findings exist.

- [ ] **Step 5: Import tokens without attempting the full migration yet**

At the first line of `frontend/app/globals.css` add:

```css
@import "./visual-tokens.css";
```

If the old `:root` block is still required until Task 2, keep it temporarily but do not enable the repository-wide audit in CI yet.

- [ ] **Step 6: Add package scripts**

Modify `frontend/package.json`:

```json
"test:visual-tokens": "node --test scripts/visual-token-audit.test.mjs",
"audit:visual-tokens": "node scripts/visual-token-audit.mjs --check"
```

Do not add dependencies.

- [ ] **Step 7: Run the audit-engine unit tests**

```bash
npm run test:visual-tokens
```

Expected: PASS. Then run the repo scan once only as a baseline inventory:

```bash
npm run audit:visual-tokens
```

Expected at Task 1: FAIL with current legacy values such as `15px`, `1.65`, `650`, fractional letter spacing, non-token spacing/radius, raw colors, and card shadows. Record the finding count in the SDD ledger; this failure is expected until Task 6 and must not be "fixed" with broad allowlists.

- [ ] **Step 8: Commit Task 1**

```bash
git add frontend/app/visual-tokens.css frontend/app/globals.css frontend/scripts/visual-token-audit.mjs frontend/scripts/visual-token-audit.test.mjs frontend/package.json
git commit -m "feat(ui): add editorial visual token foundation"
```

---

### Task 2: Convert the app shell and landing to Editorial Precision

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/landing.tsx`
- Modify: `frontend/components/app-chrome.tsx` only if a semantic wrapper/class is required
- Create: `frontend/tests/editorial-precision.spec.ts`
- Modify: `frontend/tests/task09-public-first-visit.spec.ts` only for intentional copy/selector changes

**Interfaces:**
- Consumes: token variables from Task 1 and existing landing/session-start behavior.
- Produces: editorial landing/header/stepper visual contract without changing demo/custom session creation or workflow navigation.

- [ ] **Step 1: Write failing computed-style tests for the landing and shell**

Create `frontend/tests/editorial-precision.spec.ts` and reuse the existing session helper pattern from `ui-redesign.spec.ts`. Add:

```ts
import { test, expect } from "@playwright/test";

test("landing uses the approved editorial type, white canvas, and no card shadow", async ({ page }) => {
  await page.goto("/");
  const body = page.locator("body");
  await expect(body).toHaveCSS("background-color", "rgb(255, 255, 255)");

  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  await expect(hero).toHaveCSS("font-size", "56px");
  await expect(hero).toHaveCSS("line-height", "64px");
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
});
```

Add a mobile token-switch test:

```ts
test("landing switches display typography at mobile without interpolated sizes", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile");
  await page.goto("/");
  const hero = page.getByRole("heading", { level: 1, name: "제출 버튼을 누르기 전, 마지막 확인." });
  expect(["32px", "40px"]).toContain(await hero.evaluate(node => getComputedStyle(node).fontSize));
  expect(["40px", "48px"]).toContain(await hero.evaluate(node => getComputedStyle(node).lineHeight));
});
```

- [ ] **Step 2: Run RED**

```bash
npm run build
npx playwright test tests/editorial-precision.spec.ts --project=desktop
```

Expected: FAIL because current body is blue-gray, hero uses `clamp(...)`, product frame has shadow/radius 16, and CTA geometry is 8px/13px.

- [ ] **Step 3: Migrate base/body/header/stepper tokens**

In `globals.css`:

```css
body {
  margin: var(--space-0);
  background: var(--page);
  color: var(--text-primary);
  font-family: "Pretendard", "Noto Sans KR", "Malgun Gothic", sans-serif;
  font-size: var(--type-body-size);
  line-height: var(--type-body-line);
}

.site-header {
  max-width: 1240px;
  padding: var(--space-5) var(--space-6);
  margin: 0 auto;
  gap: var(--space-6);
}

.product-nav {
  gap: var(--space-6);
  font-size: var(--type-body-size);
  line-height: var(--type-body-line);
  font-weight: 400;
}

.step {
  padding: var(--space-4) var(--space-4);
  gap: var(--space-3);
  border-bottom: var(--border-2) solid transparent;
  font-size: var(--type-small-size);
  line-height: var(--type-small-line);
  font-weight: 500;
}

.step.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: transparent;
}
```

Do not add filled step bubbles or a sidebar.

- [ ] **Step 4: Convert the hero and product proof**

Use discrete type tokens:

```css
.landing-hero {
  grid-template-columns: minmax(0, .92fr) minmax(0, 1fr);
  gap: var(--space-8);
  padding: var(--space-11) 0 var(--space-10);
}
.hero h1 {
  max-width: 620px;
  margin: var(--space-5) 0;
  font-size: var(--type-display-lg-size);
  line-height: var(--type-display-lg-line);
  font-weight: 700;
  letter-spacing: -1px;
}
.hero-description {
  max-width: 600px;
  font-size: var(--type-body-lg-size);
  line-height: var(--type-body-lg-line);
  color: var(--text-secondary);
}
.product-frame {
  background: var(--surface);
  border: var(--border-1) solid var(--border-subtle);
  border-radius: var(--radius-2);
  box-shadow: none;
}
```

At desktop/tablet/mobile breakpoints switch the hero explicitly to `48/56`, `40/48`, or `32/40` tokens. Do not use `clamp()` for type.

- [ ] **Step 5: Reduce decorative blue and card styling in landing story**

- `eyebrow`, story numbers, and metadata default to neutral/muted; blue is reserved for actual selection/trace.
- `source-sample mark` may use `var(--accent-soft)`.
- Story frames use white surface + hairline border + 0/4/8 radius, no shadow.
- `status-text` keeps semantic colors, not accent blue.
- Replace all `font:` shorthand with explicit family/size/line/weight declarations.

No session-start logic changes in `landing.tsx`. Markup changes are permitted only to add wrappers/classes needed for spacing/dividers.

- [ ] **Step 6: Verify desktop/mobile and public-first-visit selectors**

```bash
npm run typecheck
npm run build
npx playwright test tests/editorial-precision.spec.ts tests/task09-public-first-visit.spec.ts --project=desktop
npx playwright test tests/editorial-precision.spec.ts --project=mobile
```

Expected: PASS; no horizontal overflow.

- [ ] **Step 7: Commit Task 2**

```bash
git add frontend/app/globals.css frontend/components/landing.tsx frontend/components/app-chrome.tsx frontend/tests/editorial-precision.spec.ts frontend/tests/task09-public-first-visit.spec.ts
git commit -m "feat(ui): apply editorial shell and landing"
```

---

### Task 3: Normalize shared controls, forms, evidence blocks, and page typography

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/profile.module.css`
- Modify: `frontend/components/ui.tsx` only if class names/semantic wrappers are required
- Modify: `frontend/tests/editorial-precision.spec.ts`
- Modify: `frontend/tests/ui-redesign.spec.ts` only for intentional presentational selectors

**Interfaces:**
- Consumes: canonical tokens and existing shared `Badge`, `EvidenceBox`, `FileList`, `PageTitle`, `ModeNote`, `ErrorNotice`, `WorkflowGuard` behavior.
- Produces: one editorial shared-component grammar used by Tasks 4–5.

- [ ] **Step 1: Add failing shared-component style tests**

Add a mocked session route and assert:

```ts
test("shared buttons, inputs, panels, and evidence use the editorial control grammar", async ({ page }) => {
  await openConfirmedGenericSession(page, "/requirements");

  const primary = page.getByRole("button", { name: /Profile 확정|자동 검사 계획 생성/ }).first();
  if (await primary.count()) {
    await expect(primary).toHaveCSS("border-radius", "4px");
    await expect(primary).toHaveCSS("font-size", "14px");
    await expect(primary).toHaveCSS("line-height", "20px");
  }

  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(inspector).toHaveCSS("box-shadow", "none");
  expect(["0px", "4px", "8px"]).toContain(await inspector.evaluate(node => getComputedStyle(node).borderRadius));
});
```

Add a form-control test that opens an editable requirement and checks input/textarea `border-radius: 4px`, `font-size: 14px`, `line-height: 20px`.

- [ ] **Step 2: Run RED**

```bash
npx playwright test tests/editorial-precision.spec.ts --project=desktop -g "shared|form|control"
```

Expected: FAIL because current forms use 8px radius and inherited 12px/1.7 styles; panels/evidence use mixed radii and shaded surfaces.

- [ ] **Step 3: Migrate shared buttons/badges/evidence/panels**

Use this target grammar:

```css
.button {
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: var(--border-1) solid transparent;
  border-radius: var(--radius-1);
  font-size: var(--type-body-size);
  line-height: var(--type-body-line);
  font-weight: 600;
}
.button.primary { background: var(--accent); color: var(--surface); }
.button.primary:hover:not(:disabled) { background: var(--accent-hover); }
.button.secondary { background: var(--surface); color: var(--text-primary); border-color: var(--border-strong); }
.badge {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-1);
  font-size: var(--type-micro-size);
  line-height: var(--type-micro-line);
  font-weight: 600;
}
.panel,
.review-list,
.review-inspector,
.package-panel,
.scope-panel,
.source-pane,
.candidate-list {
  background: var(--surface);
  box-shadow: none;
}
.evidence {
  background: transparent;
  border: 0;
  border-radius: var(--radius-0);
  padding: var(--space-0);
}
```

Keep semantic status text colors. Soft status backgrounds may remain only on compact badges.

- [ ] **Step 4: Normalize `PageTitle`, `ModeNote`, footer, file rows, and empty/recovery states**

- Page title: `32/40` desktop, `24/32` narrow.
- Page description: `14/20` or `16/24` only.
- ModeNote becomes a neutral utility strip with `1px` rule, no blue-filled surface.
- File rows use divider lines and white surface.
- Empty/recovery states rely on type + rules; do not add shadows.

- [ ] **Step 5: Normalize profile forms**

In `profile.module.css`:

```css
.form { display: grid; gap: var(--space-3); margin: var(--space-4) 0; }
.form label { display: grid; gap: var(--space-2); font-size: var(--type-small-size); line-height: var(--type-small-line); font-weight: 600; }
.form input,
.form select,
.form textarea {
  width: 100%;
  padding: var(--space-3);
  border: var(--border-1) solid var(--border-strong);
  border-radius: var(--radius-1);
  background: var(--surface);
  color: var(--text-primary);
  font-size: var(--type-body-size);
  line-height: var(--type-body-line);
}
.fields { gap: var(--space-3); }
.actions { gap: var(--space-2); }
.source { font-size: var(--type-small-size); line-height: var(--type-small-line); }
.provenance { font-size: var(--type-micro-size); line-height: var(--type-micro-line); }
```

No unitless line-height or raw colors.

- [ ] **Step 6: Run targeted regression**

```bash
npm run typecheck
npm run build
npx playwright test tests/editorial-precision.spec.ts tests/ui-redesign.spec.ts --project=desktop
npx playwright test tests/editorial-precision.spec.ts --project=mobile
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add frontend/app/globals.css frontend/components/profile.module.css frontend/components/ui.tsx frontend/tests/editorial-precision.spec.ts frontend/tests/ui-redesign.spec.ts
git commit -m "feat(ui): normalize editorial controls and typography"
```

---

### Task 4: Flatten Announcement, Human Review, and Submission Package workspaces

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/announcement-workspace.tsx` only for visual grouping/classes if needed
- Modify: `frontend/components/requirements-workspace.tsx` only for visual grouping/classes if needed
- Modify: `frontend/components/preflight-package.tsx` only for visual grouping/classes if needed
- Modify: `frontend/tests/editorial-precision.spec.ts`
- Re-run: `frontend/tests/generic-profile.spec.ts`
- Re-run: `frontend/tests/task10-semantic-ui.spec.ts`

**Interfaces:**
- Consumes existing extraction exact-offset behavior, Human Review mutation/version behavior, UploadScreen state machine, semantic readiness/acknowledgement, and plan fallback.
- Produces editorial two-column/list-detail/file-sheet presentation without altering any mutation or validation contract.

- [ ] **Step 1: Add failing workspace-specific style assertions**

Add tests for:

```ts
test("extraction and review read as editorial columns rather than cards", async ({ page }) => {
  await openExtractedSession(page, "/announcement");
  const source = page.getByRole("region", { name: "공고 원문" });
  await expect(source).toHaveCSS("box-shadow", "none");
  expect(["0px", "4px", "8px"]).toContain(await source.evaluate(node => getComputedStyle(node).borderRadius));

  await page.goto("/requirements");
  const list = page.getByRole("region", { name: "요구사항 목록" });
  const inspector = page.getByRole("region", { name: "요구사항 Inspector" });
  await expect(list).toHaveCSS("box-shadow", "none");
  await expect(inspector).toHaveCSS("box-shadow", "none");
});
```

Add an upload test for confirmed generic profile with planner `REVIEW_REQUIRED` that checks the workspace is still accessible and the scope panel is white/no shadow; keep the existing readiness assertion.

- [ ] **Step 2: Run RED**

```bash
npx playwright test tests/editorial-precision.spec.ts --project=desktop -g "extraction|review|package|workspace"
```

Expected: FAIL on current rounded/tinted panel treatment while behavior assertions continue to pass.

- [ ] **Step 3: Refine extraction workspace**

- Preserve `splitEvidenceText()` exactly; do not touch code-point slicing.
- Prefer independent white columns with whitespace and a `1px` divider instead of card shadows/tinted panels.
- Source highlight uses `var(--accent-soft)` plus optionally a `2px` accent rule.
- Candidate rows use hairline dividers.
- `AI EXTRACTED`, `NEEDS_REVIEW`, `CONFIRMED`, `UNSUPPORTED` remain truthful text labels; do not promote them to large blue pills.

- [ ] **Step 4: Refine Human Review list + Inspector**

- Review rows: white, `1px` bottom border, minimal selected edge/underline using accent.
- Inspector: white, at most `8px` radius, no ordinary shadow.
- Source evidence: typography + subtle accent highlight, not tinted card stacks.
- Form controls use Task 3 tokens.
- `Profile 확정` remains the only dominant CTA; edit/secondary remain monochrome; delete stays danger text.
- Keep `profile.version`, `dirtyId`, acknowledgement reset, exact evidence offsets, mutation bodies, and plan compilation logic byte-for-byte unless a selector wrapper requires moving markup without logic changes.

- [ ] **Step 5: Refine Submission Package and scope**

- File area resembles a review sheet: rows + dividers, no colored cards.
- `이번 검사` is a typographic checklist; no dashboard-like tinted box.
- Demo fixture selectors may use a `1px` selected border and restrained `accent-soft` only when selected.
- Semantic acknowledgement remains explicit and readable; do not shrink below `14/20` body copy.
- Running/failure copy stays unchanged.
- Do not show pre-run duration/page count.

- [ ] **Step 6: Run behavior + style regressions**

```bash
npm run typecheck
npm run build
npx playwright test tests/editorial-precision.spec.ts tests/generic-profile.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop
npx playwright test tests/editorial-precision.spec.ts tests/generic-profile.spec.ts --project=mobile
```

Expected: PASS, including non-BMP/repeated-quote offset tests, acknowledgement, stale poll cancellation, reload resume, transient retry, and Plan `REVIEW_REQUIRED` upload availability.

- [ ] **Step 7: Commit Task 4**

```bash
git add frontend/app/globals.css frontend/components/announcement-workspace.tsx frontend/components/requirements-workspace.tsx frontend/components/preflight-package.tsx frontend/tests/editorial-precision.spec.ts
git commit -m "feat(ui): flatten editorial review workspaces"
```

---

### Task 5: Recompose Results and Evidence Inspector around RULE → EVIDENCE → VERDICT

**Files:**
- Modify: `frontend/components/results-workspace.tsx`
- Modify: `frontend/components/evidence-drawer.tsx` only for presentation wrappers/classes; focus logic remains unchanged
- Modify: `frontend/components/screens.tsx` for result page heading copy only
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tests/editorial-precision.spec.ts`
- Re-run/update selectors only: `frontend/tests/golden-path.spec.ts`, `frontend/tests/task10-semantic-ui.spec.ts`

**Interfaces:**
- Consumes: `STATUS_PRIORITY`, `resultChanged`, `semanticPresentationCopy`, backend result statuses/evidence.
- Produces: editorial result summary and row presentation while keeping existing filtering, status ordering, recheck comparison, semantic copy, and Evidence Inspector keyboard behavior.

- [ ] **Step 1: Add failing result-summary and row-style tests**

Use a completed mixed-status mock and assert:

```ts
test("results use editorial summary counts instead of colored metric cards", async ({ page }) => {
  await openCompletedSession(page, "/results");
  const summary = page.getByRole("region", { name: "전체 검사 상태" });
  await expect(summary).toContainText("01");
  await expect(summary).toContainText("BLOCKER");
  await expect(summary).toContainText("REVIEW");
  await expect(summary).toHaveCSS("box-shadow", "none");
});

test("result rows are divider-led evidence chains", async ({ page }) => {
  await openCompletedSession(page, "/results");
  const card = page.getByTestId("result-card").first();
  await expect(card.getByText("RULE", { exact: true })).toBeVisible();
  await expect(card.getByText("EVIDENCE", { exact: true })).toBeVisible();
  await expect(card.getByText("VERDICT", { exact: true })).toBeVisible();
  await expect(card).toHaveCSS("box-shadow", "none");
  expect(["0px", "4px"]).toContain(await card.evaluate(node => getComputedStyle(node).borderRadius));
});
```

Add drawer style assertion: white background, `1px` left border, shadow equals the canonical overlay shadow; preserve existing Escape/focus trap/opener restore tests.

- [ ] **Step 2: Run RED**

```bash
npx playwright test tests/editorial-precision.spec.ts tests/golden-path.spec.ts --project=desktop -g "result|evidence|drawer"
```

Expected: FAIL on current result banner/card visual treatment.

- [ ] **Step 3: Make the page title editorial and stable**

In `ResultsScreen`, change only presentation copy:

```tsx
<PageTitle
  step="04 / PREFLIGHT RESULTS"
  title="Preflight Result"
  description="제출 전 점검이 완료되었습니다. 판정별 근거와 필요한 조치를 확인하세요."
/>
```

Do not derive a fake checked timestamp from `updated_at`.

- [ ] **Step 4: Simplify the result summary markup**

Keep dynamic `title` logic but present it as supporting copy. Replace card-like metrics with plain count items:

```tsx
<div className="result-summary-counts" aria-label="판정 요약">
  {STATUSES.map(status => <span key={status} className={`summary-status summary-${status.toLowerCase()}`}>
    <b>{String(counts[status]).padStart(2, "0")}</b>
    <span>{status}</span>
  </span>)}
</div>
```

CSS target:

```css
.result-banner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-6);
  padding: var(--space-7) 0;
  border: 0;
  border-bottom: var(--border-1) solid var(--border-subtle);
  border-radius: var(--radius-0);
  background: transparent;
  box-shadow: none;
}
.result-summary-counts span {
  background: transparent;
  border: 0;
  border-left: var(--border-3) solid currentColor;
  border-radius: var(--radius-0);
  padding: 0 0 0 var(--space-3);
}
```

Status color appears only on the marker/text.

- [ ] **Step 5: Flatten Evidence Chain rows**

`result-card` becomes a row with hairline separators and no full-card semantic fill/shadow. Desktop keeps three columns; mobile stacks vertically. Inside result rows, `EvidenceBox` presentation is unboxed via descendant CSS.

Keep:

- BLOCKER → REVIEW → PASS → EXTERNAL ordering;
- filter tabs and counts;
- semantic max-three evidence candidates;
- `RELATED_EVIDENCE_FOUND` wording remains REVIEW, not satisfied;
- `NO_CLEAR_EVIDENCE` coverage-aware wording remains unchanged;
- REVIEW→REVIEW evidence fingerprint comparison remains visible.

- [ ] **Step 6: Refine Evidence Inspector without touching keyboard logic**

- white background;
- `1px` left border using `var(--border-subtle)`;
- `box-shadow: var(--shadow-overlay)` only;
- source locator `11/16` monospace;
- evidence blocks use typography/dividers, not stacked tinted cards;
- technical details remain collapsed.

Do not modify the `useEffect`, Escape handling, Tab focus cycling, body overflow restoration, or opener focus restoration in `evidence-drawer.tsx`.

- [ ] **Step 7: Run result/semantic/accessibility regression**

```bash
npm run typecheck
npm run build
npx playwright test tests/editorial-precision.spec.ts tests/golden-path.spec.ts tests/task10-semantic-ui.spec.ts --project=desktop
npx playwright test tests/editorial-precision.spec.ts tests/golden-path.spec.ts --project=mobile
```

Expected: PASS, including broken/fixed demo expectations, semantic REVIEW-only assertions, drawer Escape/focus trap/focus restore, and recheck evidence fingerprint changes.

- [ ] **Step 8: Commit Task 5**

```bash
git add frontend/components/results-workspace.tsx frontend/components/evidence-drawer.tsx frontend/components/screens.tsx frontend/app/globals.css frontend/tests/editorial-precision.spec.ts frontend/tests/golden-path.spec.ts frontend/tests/task10-semantic-ui.spec.ts
git commit -m "feat(ui): recompose editorial evidence results"
```

---

### Task 6: Complete token migration and turn the visual audit into a CI gate

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/app/visual-tokens.css`
- Modify: `frontend/components/profile.module.css`
- Modify: `frontend/scripts/visual-token-audit.mjs`
- Modify: `frontend/scripts/visual-token-audit.test.mjs`
- Modify: `frontend/package.json`
- Modify: `.github/workflows/ci.yml`
- Modify: `frontend/tests/editorial-precision.spec.ts`

**Interfaces:**
- Consumes: all visual migrations from Tasks 2–5.
- Produces: zero visual-token audit findings and a CI-enforced design-system contract.

- [ ] **Step 1: Run the repo audit and capture the remaining RED inventory**

```bash
npm run audit:visual-tokens
```

Expected before cleanup: FAIL if any legacy raw colors, non-token size/spacing/radius/border, `font:` shorthand, unitless/fractional typography, arbitrary font weight/letter spacing, or ordinary card shadow remains.

Do not add broad allowlists to make the scan green.

- [ ] **Step 2: Remove all temporary compatibility aliases and remaining raw values**

Search production styles:

```bash
rg -n "#([0-9a-fA-F]{3,8})\b|rgba?\(|hsla?\(|font:|font-size:\s*(13|15|17|22|23|27)px|font-weight:\s*(650|800|900)|letter-spacing:\s*[-.]?[0-9]*\.[0-9]+px|line-height:\s*[0-9]+\.[0-9]+|border-radius:\s*(14|16)px" app components -g "*.css"
```

Every production hit must be removed or replaced with an approved token. The only raw palette/shadow definitions belong in `visual-tokens.css`.

- [ ] **Step 3: Validate the token file itself**

Extend the audit unit test to read `app/visual-tokens.css` and assert required canonical values exactly:

```js
const required = new Map([
  ["--page", "#FFFFFF"],
  ["--text-primary", "#0A0A0A"],
  ["--accent", "#3157FF"],
  ["--status-blocker", "#C62828"],
  ["--status-review", "#A15C00"],
  ["--status-pass", "#17824B"],
  ["--shadow-overlay", "0 16px 48px rgba(10, 10, 10, 0.12)"],
]);
```

Fail if a required token is missing or changed.

- [ ] **Step 4: Make the repo audit GREEN**

```bash
npm run test:visual-tokens
npm run audit:visual-tokens
```

Expected: both PASS and audit reports `0 findings`.

- [ ] **Step 5: Add the CI gate**

In `.github/workflows/ci.yml`, frontend job after `npm ci` and before typecheck:

```yaml
      - name: Audit visual tokens
        working-directory: frontend
        run: npm run audit:visual-tokens
```

Do not alter backend CI.

- [ ] **Step 6: Add whole-page token/overflow/reduced-motion browser assertions**

In `editorial-precision.spec.ts`, add:

```ts
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
```

Keep the existing drawer/recovery/mobile overflow assertions.

- [ ] **Step 7: Run full non-ACTUAL frontend regression**

```bash
npm run test:visual-tokens
npm run audit:visual-tokens
npm run typecheck
npm run build
npm run test:smoke
```

Expected: visual audit 0 findings; all non-ACTUAL Playwright tests PASS with only the explicitly gated ACTUAL tests skipped.

- [ ] **Step 8: Commit Task 6**

```bash
git add frontend/app/globals.css frontend/app/visual-tokens.css frontend/components/profile.module.css frontend/scripts/visual-token-audit.mjs frontend/scripts/visual-token-audit.test.mjs frontend/package.json frontend/tests/editorial-precision.spec.ts .github/workflows/ci.yml
git commit -m "test(ui): enforce editorial visual tokens"
```

---

### Task 7: Run the 12-state visual QA matrix, ACTUAL authority regression, and final review gate

**Files:**
- Create: `artifacts/editorial-precision/visual-qa-matrix.json` (generated evidence; do not commit unless repository policy explicitly tracks it)
- Create: `artifacts/editorial-precision/screenshots/desktop/*.png` and `mobile/*.png` (generated evidence; do not commit by default)
- Modify tests only if a visual-intent selector changed while semantic assertion remains identical.
- Do not modify backend product behavior.

**Interfaces:**
- Consumes: complete Editorial Precision frontend, existing mock/session helpers, TASK08 ACTUAL and TASK10 ACTUAL tests.
- Produces: 24 visual QA screenshots (12 states × desktop/mobile), exact visual audit evidence, full regression evidence, ACTUAL authority evidence, and a final independent review report.

- [ ] **Step 1: Build a deterministic visual QA state matrix in Playwright**

Extend `editorial-precision.spec.ts` with a screenshot helper:

```ts
async function captureQa(page, project, state) {
  const dir = `../artifacts/editorial-precision/screenshots/${project}`;
  await page.screenshot({ path: `${dir}/${state}.png`, fullPage: true });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow, `${state} must not overflow horizontally`).toBe(false);
}
```

Capture these exact state names on both configured projects:

1. `01-landing`
2. `02-custom-extraction-provisional`
3. `03-human-review-selected`
4. `04-package-plan-ready`
5. `05-package-plan-review-required`
6. `06-result-blocker`
7. `07-result-ready`
8. `08-semantic-related-evidence-review`
9. `09-semantic-no-clear-evidence-review`
10. `10-evidence-inspector-open`
11. `11-actionable-recovery`
12. `12-recheck-comparison`

Use deterministic mocked sessions for visual-state capture where real AI is unnecessary. Every mock must use the exact current `CheckSession` contract and must not fabricate a status combination the backend could never produce.

- [ ] **Step 2: Run the 24-state screenshot matrix**

Use an isolated review runtime on ports distinct from the public runtime and a dedicated data directory:

```bash
npx playwright test tests/editorial-precision.spec.ts --project=desktop
npx playwright test tests/editorial-precision.spec.ts --project=mobile
```

Expected: PASS; 24 named state screenshots captured with no horizontal overflow.

- [ ] **Step 3: Perform the human visual QA review against the checklist**

For every state record in `visual-qa-matrix.json`:

```json
{
  "state": "06-result-blocker",
  "desktop": {
    "color_hierarchy": "PASS",
    "type_hierarchy": "PASS",
    "spacing_rhythm": "PASS",
    "alignment": "PASS",
    "status_restraint": "PASS",
    "evidence_legibility": "PASS",
    "contrast": "PASS",
    "focus_visibility": "PASS",
    "overflow": "PASS"
  },
  "mobile": { "same_keys": "PASS" },
  "finding": null
}
```

A reviewer may record LOW cosmetic observations, but unresolved HIGH or MEDIUM findings block Product Lead review. Any fix requires a scoped re-run of the affected states and the visual-token audit.

- [ ] **Step 4: Run backend/secret/frontend full regression**

Repository root/backend/frontend as appropriate:

```bash
cd backend
python -m pytest -q
cd ..
python scripts/scan_secrets.py
cd frontend
npm ci
npm run test:visual-tokens
npm run audit:visual-tokens
npm run typecheck
npm run build
npm run test:smoke
```

Expected: backend remains at the current repository count with zero failures; secret scan PASS; visual audit 0 findings; typecheck/build PASS; all non-ACTUAL browser tests PASS.

- [ ] **Step 5: Run TASK08 ACTUAL**

Using the same production-like Codex provider configuration and a fresh isolated data directory:

```bash
TASK08_ACTUAL_AI=1 npx playwright test tests/task08-actual-ai.spec.ts --project=desktop
```

Required preserved evidence:

- actual extraction retains the 60-second rule;
- plan is VERIFIED `VIDEO_METADATA`;
- actual 61s MP4 → BLOCKER/BLOCKED;
- actual 45s MP4 → PASS/READY;
- same PlanSet reused;
- operation ledger remains `EXTRACT=1 / PLAN=1 / SEMANTIC=0`.

- [ ] **Step 6: Run TASK10 ACTUAL**

```bash
TASK10_ACTUAL_AI=1 npx playwright test tests/task10-actual-semantic.spec.ts --project=desktop
```

Required preserved evidence:

- positive PDF → `REVIEW / RELATED_EVIDENCE_FOUND` with exact locally grounded excerpt;
- missing evidence → REVIEW and never BLOCKER;
- prompt injection → REVIEW and never PASS/BLOCKER;
- REVIEW→REVIEW evidence fingerprint change remains visible;
- semantic PASS/BLOCKER observed = 0;
- operation ledger remains `EXTRACT=1 / PLAN=0 / SEMANTIC=4`.

- [ ] **Step 7: Independent whole-branch review**

Dispatch a fresh `gpt-5.6-sol / high` reviewer over `origin/main...HEAD`. Review separately for:

1. Editorial Precision spec compliance.
2. Token audit correctness and bypass risk.
3. Accidental behavior/authority changes.
4. Accessibility regressions.
5. Visual QA matrix completeness.
6. Test weakening/skipping.
7. Backend/frozen-contract diff.

Required final finding gate: `BLOCKER 0 / HIGH 0 / MEDIUM 0`. LOW findings must be either fixed or explicitly adjudicated as nonblocking cosmetic issues before Product Lead review.

- [ ] **Step 8: Commit only real source/test fixes from review**

If review fixes are needed, create one or more scoped commits and re-run the relevant token audit/tests. Do not commit generated screenshot artifacts unless explicitly approved.

Suggested final source commit message if needed:

```bash
git commit -m "fix(ui): close editorial precision review findings"
```

- [ ] **Step 9: Publish through a new PR and wait for fresh CI**

Because PR #15 is already merged, do not reuse it. Push branch `editorial-precision-v2` normally and open one non-draft PR to `main` with title:

```text
FINAL CHECK Editorial Precision v2 — visual system refinement
```

PR body must state:

- visual-only scope;
- no backend authority change;
- canonical token scales;
- visual audit 0 findings;
- desktop/mobile 12-state matrix status;
- full regression counts;
- TASK08/TASK10 ACTUAL preserved;
- public judging runtime not yet switched;
- `MERGE NOT YET AUTHORIZED`.

Wait for a fresh CI run from the exact PR head. Required: frontend token audit SUCCESS, frontend typecheck/build SUCCESS, backend SUCCESS, secret scan SUCCESS.

- [ ] **Step 10: Stop for Product Lead review**

Final report format:

```text
EDITORIAL PRECISION V2 GATE

BRANCH
- base SHA:
- head SHA:
- commits:
- backend product-code diff: YES/NO

VISUAL TOKENS
- unit tests:
- repo audit findings:
- palette drift:
- typography drift:
- spacing drift:
- radius/border drift:

VISUAL QA
- desktop states: 12/12
- mobile states: 12/12
- HIGH findings:
- MEDIUM findings:
- LOW findings:

REGRESSION
- backend:
- secret scan:
- typecheck:
- build:
- Playwright:

TASK08 ACTUAL
- 61s:
- 45s:
- PlanSet reuse:
- ledger:

TASK10 ACTUAL
- positive:
- missing:
- injection:
- recheck fingerprint:
- semantic PASS/BLOCKER:
- ledger:

FINAL REVIEW
- verdict:
- BLOCKER:
- HIGH:
- MEDIUM:
- LOW:

PR / CI
- PR:
- exact head:
- CI run:
- backend:
- frontend:

PUBLIC RUNTIME
- current URL healthy: YES/NO
- switched: NO

ACTION
- PRODUCT LEAD REVIEW REQUESTED — MERGE NOT YET AUTHORIZED
```

Do not merge or switch the public runtime in this task.

---

## Plan Self-Review Record

### Spec coverage

- Color system and scarce accent: Tasks 1–6.
- Integer typography/line-height/weights/letter spacing: Tasks 1–3 and 6.
- Integer spacing/radius/border: Tasks 1–6.
- No ordinary shadows / overlay-only shadow: Tasks 1, 2, 3, 5, 6.
- Landing editorial hierarchy: Task 2.
- Five-step shell preserved: Tasks 2–7, with explicit no-sidebar constraint.
- Extraction/Human Review/Package editorial flattening: Task 4.
- RULE→EVIDENCE→VERDICT results and status restraint: Task 5.
- Evidence Inspector presentation with keyboard logic preserved: Task 5.
- Responsive/reduced-motion/overflow: Tasks 2, 6, 7.
- Deterministic visual-token audit and CI enforcement: Tasks 1 and 6.
- 12-state desktop/mobile visual QA: Task 7.
- TASK08/TASK10 behavioral authority regression: Task 7.
- Public runtime protection and new-PR gate: Task 7.

### Placeholder scan

The plan contains no TBD/TODO/"implement later" placeholders. Every task names concrete files, commands, expected RED/GREEN behavior, and commit boundaries.

### Type/interface consistency

- `CheckSession`, `FindingStatus`, `ValidationResult`, and existing workspace props remain unchanged.
- The plan does not introduce new backend types or result states.
- `auditCssText` and `collectProductionCssFiles` are defined in Task 1 and reused only by Task 6.
- `editorial-precision.spec.ts` is created in Task 2 and extended in Tasks 3–7.
- Existing UploadScreen state-machine functions remain in `screens.tsx` and are never moved.
- Existing EvidenceDrawer keyboard/focus implementation remains behaviorally unchanged.

## Completion Definition

Editorial Precision v2 is implementation-complete only when the deterministic visual audit reports zero findings, all 24 desktop/mobile QA states are reviewed, all standard/ACTUAL regressions preserve authority, final reviewer has no unresolved BLOCKER/HIGH/MEDIUM finding, fresh PR CI is green, and Product Lead has reviewed the evidence. A visually cleaner branch that weakens Human confirmation, semantic REVIEW-only authority, acknowledgement/polling safety, exact evidence offsets, recheck comparison, or frozen hashes is **not complete**.
