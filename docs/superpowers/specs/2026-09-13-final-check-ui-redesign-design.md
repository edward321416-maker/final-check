# FINAL CHECK — UI Redesign Design

**Status:** USER REVIEW REQUIRED  
**Self-review:** COMPLETED (2026-09-13)  
**Baseline:** `main@9f13866db1f14d917764a7d2865153f7aa6fbf3e`  
**Product decision:** GO  
**Scope:** Frontend information architecture, visual system, interaction design, responsive behavior, and presentation quality  
**Architecture:** Modern AI SaaS base + Evidence Lab identity

## 1. Product goal

Redesign FINAL CHECK so a first-time user or competition judge can understand the product in seconds and can trace every important state back to evidence.

The UI must communicate the product model accurately:

> AI structures the announcement and finds evidence candidates. Human confirmation establishes the requirement profile. Deterministic verifiers decide only the conditions they can safely measure. Uncertain semantic findings remain REVIEW.

The redesign is not a new verification engine. It is a presentation and workflow refinement over the existing TASK02–TASK10 behavior.

Primary success criteria:

- the landing page explains the value proposition without requiring product knowledge;
- announcement extraction visually connects source text to extracted requirements;
- human review visibly separates AI candidates from human-confirmed rules;
- upload is framed as preparing a submission package for preflight, not as a generic uploader;
- results make `RULE -> EVIDENCE -> VERDICT` the dominant reading order;
- BLOCKER, REVIEW, PASS, and EXTERNAL remain semantically distinct without turning the interface into a red/amber/green dashboard;
- TASK10 evidence is inspectable without allowing AI evidence to appear as automatic compliance approval;
- mobile keeps evidence visible instead of hiding it behind a summary-only view;
- competition screenshots can be captured from real product states without decorative mock data contradicting visible counts.

## 2. Non-goals

This redesign does not change:

- TASK02–TASK10 backend verification semantics;
- any frozen validator, prompt, manifest, or plan hash;
- the Human-confirmed Requirement Profile authority boundary;
- AI authority: AI still cannot produce automatic `PASS`, `BLOCKER`, `READY`, or `BLOCKED` decisions for semantic content;
- TASK08 verifier families or Plan DSL;
- TASK10 eligibility, PDF trust, exact evidence gate, coverage rules, or acknowledgement rules;
- TASK07/TASK09 single-backend-process runtime behavior;
- public hosting architecture;
- OCR, Vision, MP4 semantic understanding, URL verification, or new file types;
- dark mode;
- user accounts, billing, collaboration, or analytics.

No UI work may silently broaden product claims beyond what the current engine actually verifies.

## 3. Existing frontend context

The current frontend is working and should be evolved rather than replaced wholesale.

Observed baseline structure:

- `frontend/app/globals.css` — current paper/pine/lime visual system and shared layout;
- `frontend/components/ui.tsx` — Navigation, Badge, EvidenceBox, FileList, Guard, and common UI helpers;
- `frontend/components/screens.tsx` — Home, Announcement, Upload, Results, and Recheck screen logic;
- `frontend/components/generic-profile.tsx` — text announcement input, AI extraction, review/edit/approve, profile confirmation, and plan compile actions;
- App Router paths `/`, `/announcement`, `/upload`, `/results`, `/recheck`.

Current `.preview` intentionally uses `transform: rotate(1deg)`; the redesign removes this and the broader scrapbook/paper treatment. Existing data fetching, durable polling, mutation, semantic acknowledgement, session recovery, and result authority remain the implementation source of truth.

Implementation may extract focused presentational components from the existing large screen files when that improves clarity, but must not rewrite working session/business logic merely for styling consistency.

## 4. Design principles

### 4.1 Evidence first

The product should make the user ask "what is the evidence?" before "what color is the status?". Status is compact metadata; evidence is the primary explanatory surface.

### 4.2 Truthful progress

Never invent percentages, ETA, or processing stages the backend cannot observe. Loading UI may show only real coarse-grained states supported by current session/job data.

### 4.3 Human authority is visible

AI-extracted requirements are provisional until a person approves them. `AI EXTRACTED` and `HUMAN CONFIRMED` must never look interchangeable.

### 4.4 Deterministic certainty differs from semantic review

A measured 61.0-second video can produce a deterministic BLOCKER. A PDF sentence related to a mandatory content requirement remains REVIEW. Both can share the Evidence Chain grammar while keeping different authority.

### 4.5 Quiet by default, detail on demand

The default interface is neutral and scan-friendly. Hashes, prompt IDs, offsets, and low-level diagnostics remain available behind secondary disclosure or the Evidence Inspector.

### 4.6 Reference proven patterns without cloning them

Reference interaction patterns from:

- Linear — quiet product surfaces, list/detail inspection, compact navigation;
- Vercel — deployment/preflight status hierarchy and restrained status color;
- GitHub Checks/review — check -> annotation -> source-context traceability;
- Stripe Radar — clear Block / Review / Allow conceptual separation without full-surface color fills;
- Sentry — summary first, deeper evidence/trace inspection on demand.

FINAL CHECK keeps a distinct Korean-first, evidence-first identity.

## 5. Visual system

### 5.1 Base palette

Use a white SaaS foundation:

- page background: white or very light neutral gray;
- primary text: near-black neutral;
- secondary text: cool neutral gray;
- borders: low-contrast neutral gray;
- signature color: Electric Blue;
- cards: white with subtle border and minimal elevation.

Electric Blue is reserved for primary CTA, active step, focus ring, selected evidence relationship, source/evidence trace, active tab, and selected controls. It must not mean PASS.

### 5.2 Status colors

- `BLOCKER`: red;
- `REVIEW`: amber;
- `PASS`: green;
- `EXTERNAL`: cool gray / blue-gray.

Cards remain neutral. Use a compact status chip plus an approximately 3px leading indicator. BLOCKER may receive a very faint red tint, but no state gets a fully saturated card background.

### 5.3 Typography

- Primary: Pretendard with existing system fallbacks.
- Product/body text: proportional sans serif.
- Monospace only for IDs, hashes, page/character locators, durations shown as machine evidence, and technical provenance.
- Avoid decorative uppercase tracking except very small metadata labels.

### 5.4 Shape and elevation

- major cards/product frames: approximately 12–16px radius;
- controls: moderate radius, not pill-heavy;
- border: 1px neutral;
- shadow: soft and restrained;
- remove intentional rotation/tilt from product surfaces.

## 6. Brand mark and header

### 6.1 Logo

Use a `Scan Corners + Check` symbol with the `FINAL CHECK` wordmark.

The mark uses a small number of open scan-corner strokes around a central check; it must not become a closed checkbox icon. The symbol is Electric Blue on light surfaces. Header uses symbol + wordmark; favicon/small contexts may use symbol only.

No complex illustration or gradient logo is required.

### 6.2 Product Header

Landing header:

- left: brand mark + `FINAL CHECK`;
- center: compact navigation such as `How it works`, `Evidence-first`, `검증 방식`;
- right: primary CTA `제출 전 검사 시작하기`.

Inside the app flow, remove the center landing navigation and prioritize brand + Segmented Stepper. Avoid duplicate navigation chrome.

## 7. Information architecture and routes

The landing page is not a numbered verification step.

Target app stepper:

1. `공고`
2. `요구사항 검토`
3. `제출파일`
4. `결과`
5. `재검사`

Add a dedicated frontend requirement-review route so the approved five-step model is truthful:

- `/` — landing/start, outside numbered stepper;
- `/announcement` — Step 01, announcement ingestion/extraction workspace;
- `/requirements` — Step 02, Human Review and profile confirmation;
- `/upload` — Step 03, submission package workspace;
- `/results` — Step 04, results and evidence;
- `/recheck` — Step 05, revised-package comparison/recheck.

This is a frontend workflow split only. It reuses existing profile/session endpoints and introduces no new backend authority boundary.

The current combined `GenericProfileReview` behavior is separated presentation-wise:

- extraction/job state and source-to-candidate mapping belong on `/announcement`;
- edit/approve/delete/full-source acknowledgement/profile confirmation/plan compile belong on `/requirements`.

### 7.1 Session-mode behavior

The route split must not fabricate AI stages for demo/frozen sessions.

**Custom/generic session:**

- `/announcement` shows real ingestion/extraction state and extracted candidates;
- once candidates are available, CTA advances to `/requirements`;
- `/requirements` owns Human Review, confirmation, and plan compile;
- `/upload` becomes available after the current authoritative prerequisites are satisfied.

**Demo/frozen session:**

- `/announcement` shows the frozen announcement requirements/source evidence as a read-only product example and must not label them as a live AI extraction if no live extraction occurred;
- `/requirements` shows a read-only or already-confirmed requirement review summary sufficient to explain the Human Review concept without creating fake edits/AI jobs;
- the demo continues to `/upload` using the existing frozen validator behavior.

The same visual system may serve both modes, but labels must describe what actually occurred.

### 7.2 Step readiness and guards

The stepper is navigation plus state communication, not a way to bypass workflow guards.

- Step 01 requires an active session/announcement context.
- Step 02 is enabled when the session has real candidate/frozen requirement data appropriate to its mode.
- Step 03 is enabled only when the existing product contract considers the requirement/profile/plan state ready for package validation; demo uses its existing frozen readiness path.
- Step 04 requires completed results.
- Step 05 requires prior results/recheck context.

If a user reaches a later route without prerequisites, preserve fail-closed Guard behavior and provide a specific link to the missing prior step rather than always returning to Home.

## 8. App shell and Segmented Stepper

Use a Wide App Canvas rather than full-bleed dashboard chrome.

Recommended max widths:

- landing: 1240–1280px;
- normal app screens: 1200–1240px;
- Results/Evidence: up to 1320px;
- desktop horizontal padding: 24–32px;
- narrow screens: single column.

Stepper behavior:

- thin horizontal row;
- `01`, `02`, etc. + Korean step name;
- current step: Electric Blue text + approximately 2px underline;
- completed: small check + neutral/dark text;
- future disabled: neutral gray;
- no large circles or checkout-style connector line;
- visible keyboard focus;
- current step uses `aria-current="step"`.

## 9. Landing page

### 9.1 Split Hero

Approximately 48% copy / 52% product proof.

Primary copy:

> **제출 버튼을 누르기 전, 마지막 확인.**
>
> FINAL CHECK가 공고의 요구사항을 구조화하고, 실제 제출파일에서 놓친 조건과 근거를 찾아줍니다.

Primary CTA: `제출 전 검사 시작하기`  
Secondary: `어떻게 작동하나요?`

Trust statement:

> AI는 근거를 찾고, 확실한 조건은 코드가 검증합니다.

The hero must not claim every announcement requirement can be automatically checked.

The primary CTA should move the user into the real start path or start chooser already supported by the product; it must not begin a fake validation animation.

### 9.2 Mini Product Window

The right side is a compact product proof, not an angled decorative mockup.

Demonstrate the real result grammar:

- internally consistent counts such as `1 BLOCKER / 1 REVIEW / 3 PASS`;
- deterministic example: `영상 60초 이내 -> 61.0s -> BLOCKER`;
- semantic example: `기대효과 포함 -> proposal.pdf p.2 -> REVIEW`.

Static example data must be clearly example/demo content and must never contradict the visible rows.

### 9.3 Three-step Product Story

Alternating layout:

- 01 text left / product frame right — 공고 읽기;
- 02 product frame left / text right — 기준 확정;
- 03 text left / product frame right — 제출물 검증.

Step 03 may receive slightly greater visual weight because evidence-backed preflight is the differentiator.

Use Clean Product Frames:

- no browser address-bar chrome;
- 1px neutral border;
- 12–16px radius;
- restrained shadow;
- actual FINAL CHECK UI/state whenever available;
- readable at competition screenshot scale.

## 10. Step 01 — Split Extraction Workspace

Desktop:

- left ~45%: `Announcement Source`;
- right ~55%: `Extracted Requirements`.

Show extraction as transformation, not verdict.

Candidate rows/cards may show requirement ID, modality, verifier family, concise rule, source locator, and provisional state `AI EXTRACTED` or equivalent. Do not show submission PASS/BLOCKER here.

Interaction:

- selecting/focusing a requirement highlights its exact source evidence;
- source evidence can highlight its mapped requirement only when the current stored mapping supports it;
- use subtle Electric Blue highlight/trace;
- if exact mapping is unavailable, do not fabricate it; show stored section + exact quote instead.

During extraction, use Truthful Step Activity based only on real pipeline/session states.

## 11. Step 02 — Compact Review List + Inspector

Desktop:

- left ~65%: compact requirement list;
- right ~35%: selected-item Inspector.

List prioritizes rule summary, modality, verifier, confirmation state.

Inspector order:

1. AI/provisional state;
2. exact announcement evidence;
3. editable structured requirement fields;
4. verifier classification;
5. issues/warnings;
6. actions: save edit, needs review, approve, delete.

Primary visual story:

`AI EXTRACTED -> SOURCE EVIDENCE -> HUMAN CONFIRMED`

`항목 승인` means the announcement requirement is confirmed as authoritative; it never means the submitted package already satisfies it.

Full-source acknowledgement and Profile confirmation remain explicit. Plan compilation remains after Profile confirmation. Low-level provenance/history moves to secondary disclosure.

## 12. Step 03 — Preflight Package Workspace

Desktop:

- left 60–65%: `Submission Package`;
- right 35–40%: `What will be checked`.

### 12.1 Submission Package

Show file selection/drop area, current package files, file type, size, and metadata such as page count/duration only when actually known.

Before validation, file rows must not show final PASS/BLOCKER. Neutral readiness language is allowed only when derived from real backend/session readiness.

### 12.2 What will be checked

Summarize confirmed profile/plan in user language, e.g. file presence, PDF page count, video duration, PDF content evidence.

Where reliable, show derived counts such as:

> 4개 자동 검사 · 1개 AI 근거 검토

Never hard-code production counts that can diverge from the current plan.

Primary CTA:

> Preflight 검사 실행

TASK10 acknowledgement copy remains explicit whenever a semantic AI call can actually occur.

## 13. Truthful processing states

Replace spinner-only long waits with Truthful Step Activity when the backend exposes a real stage.

Allowed examples include only states supported by current data, such as source prepared, extraction running/completed, durable job batch progress where exposed, package ready, validation run started, semantic review running, or results committed.

Rules:

- no fake `%`;
- no guessed ETA;
- no client-only stage names that imply nonexistent backend work;
- restart/restored/failed state is represented truthfully;
- failed runs remain actionable and never masquerade as completion.

## 14. Step 04 — Results and Evidence

### 14.1 Hybrid Summary

Top summary:

- left: overall state + one-line explanation + reliable checked time when available;
- right: compact BLOCKER / REVIEW / PASS / EXTERNAL counts.

READY copy remains scoped:

> 자동 확인 가능한 필수 조건을 충족했습니다.

Do not imply all competition requirements are proven satisfied.

### 14.2 Status Tabs

Directly below summary:

- `전체`;
- `BLOCKER`;
- `REVIEW`;
- `PASS`;
- `EXTERNAL`.

Include counts; default `전체`. Default ordering: BLOCKER -> REVIEW -> PASS -> EXTERNAL. Active tab uses Electric Blue; status chips retain status colors.

### 14.3 Three-column Evidence Chain

Desktop reading order:

- RULE ~25%;
- EVIDENCE ~50%;
- VERDICT ~25%.

Deterministic example:

`영상 60초 이내 -> duration 61.0s -> BLOCKER`

Semantic example:

`기대효과 포함 -> proposal.pdf · p.2 -> REVIEW`

Cards stay neutral. Hover/focus may reveal a subtle Electric Blue trace linking the three zones. The trace is an affordance, not persistent decoration.

### 14.4 Neutral Card + Status Chip

Use compact chip + leading status indicator + neutral surface. BLOCKER may receive a faint red tint. Status must remain understandable without color alone.

## 15. Evidence Inspector — Right Side Drawer

Selecting a result opens a right-side Evidence Inspector while preserving list context.

Desktop: right drawer.  
Narrow/mobile: full-width sheet/panel.

Evidence-first Hybrid order:

1. compact status + assessment label;
2. `공고 요구사항`;
3. `제출파일 근거`;
4. locator such as `proposal.pdf · p.2 · chars 5:43`;
5. exact evidence quote;
6. `왜 REVIEW인가` or corresponding explanation;
7. collapsed `기술 세부 보기` for hashes/provider/prompt/provenance when available.

TASK10 wording may use:

> REVIEW · Related evidence found
>
> 관련 근거 후보는 확인됐지만 최종 충족 여부는 직접 확인이 필요합니다.

For semantic findings, the Drawer must never provide an action that converts AI evidence directly into automatic PASS/BLOCKER authority.

Drawer behavior:

- accessible close button;
- Escape closes;
- correct focus management;
- background context remains recognizable;
- subtle slide/fade only.

## 16. Step 05 — Recheck

Recheck reuses Upload + Results language rather than becoming a separate design system.

Emphasize revised package, prior/current result changes, evidence changes even when REVIEW remains REVIEW, and deterministic changes such as 61s BLOCKER -> 45s PASS.

Existing recheck fingerprint/change logic remains authoritative.

## 17. Actionable Recovery States

Use specific recovery copy when the cause is known.

### PDF text unavailable

> **PDF 내용을 읽을 수 없습니다**  
> 이 파일에서는 텍스트를 추출하지 못해 내용 검토를 실행하지 않았습니다.
>
> `다른 PDF 업로드` / `수동으로 검토`

### Semantic AI failure

> **AI 검토를 완료하지 못했습니다**  
> 자동 PASS/BLOCKER로 처리하지 않았습니다. 이 항목은 REVIEW 상태로 남습니다.
>
> `다시 시도` / `근거 직접 확인`

### Missing prerequisite

Explain which prior step is incomplete and link to that exact step.

Technical diagnostics may live behind a details disclosure.

## 18. Responsive behavior

### Wide desktop

- Wide App Canvas;
- three-column Evidence Chain;
- split extraction;
- review list + inspector;
- right Evidence Drawer.

### Medium/narrow desktop or tablet

Reduce gaps/padding before collapsing. Two-pane layouts stack when each pane no longer remains readable. Stepper stays understandable without tiny labels.

### Mobile/narrow

Evidence becomes Vertical Evidence Stack:

`RULE`

`EVIDENCE`

`VERDICT`

A short Electric Blue trace may preserve relationship. Evidence must not disappear merely to save space.

Other transformations:

- Split Extraction -> source then extracted requirements;
- Human Review -> list then full-width inspector/sheet;
- Preflight Package -> package then check scope;
- Evidence Drawer -> full-width sheet;
- split Hero -> copy then proof;
- alternating Product Story -> linear vertical story.

Avoid horizontal scrolling for core Evidence workflows.

## 19. Motion

Use Subtle Product Motion:

- button/card hover: ~120–160ms;
- step state: short fade;
- evidence trace: subtle hover/focus reveal;
- Evidence Drawer: ~180–220ms slide + fade;
- status update: color/fade only;
- hero Mini Product Window: one restrained initial fade-up allowed.

Do not use parallax, continuous floating, bouncing status icons, aggressive scale, long stagger sequences, or animation that delays evidence reading.

Honor `prefers-reduced-motion` by removing nonessential movement.

## 20. Accessibility

- visible Electric Blue keyboard focus;
- status meaning not color-only;
- semantic HTML / existing ARIA retained or improved;
- stepper uses `aria-current` and disabled semantics;
- status filters use accessible tab/button semantics;
- drawer manages focus and Escape;
- busy/disabled controls remain explicit;
- practical text/chip contrast;
- evidence quotes remain selectable text;
- reduced motion honored.

## 21. Component architecture guidance

Favor focused presentational components while keeping domain/session behavior stable.

Suggested responsibilities, names not mandatory:

- `BrandMark` / `ProductHeader`;
- `AppStepper`;
- `LandingHero` / `MiniProductWindow` / `ProductStory`;
- `ExtractionWorkspace`;
- `RequirementReviewList` / `RequirementInspector`;
- `SubmissionPackage` / `CheckScopeSummary`;
- `TruthfulActivity`;
- `ResultsSummary` / `StatusTabs`;
- `EvidenceChainCard`;
- `EvidenceDrawer`;
- `ActionableRecovery`.

Rules:

- API/domain actions remain in existing screen/profile/session layers unless extraction is required to keep files understandable;
- presentational components receive typed data and callbacks;
- do not duplicate status computation in CSS/UI components;
- do not infer backend state client-side when an authoritative field exists;
- do not create a parallel frontend result model that can drift from current profile/result types.

## 22. Testing and regression requirements

The redesign is complete only if semantics and presentation both pass.

### Existing behavior

- frontend typecheck;
- production build;
- existing Playwright/browser suite;
- public first-visit flow where applicable;
- TASK10 semantic acknowledgement + polling behavior;
- recheck behavior;
- Guard/recovery behavior.

### New/updated UI behavior

- landing CTA enters the real flow;
- landing sample counts are internally consistent;
- `/announcement` never presents extraction candidates as submission PASS/BLOCKER;
- `/requirements` preserves edit / needs-review / approve / delete / profile-confirm / plan-compile behavior for custom sessions;
- demo/frozen labels never imply a live AI extraction that did not occur;
- step readiness matches actual session prerequisites;
- status tabs filter correctly;
- Evidence Drawer renders exact locator/quote and opens/closes accessibly;
- semantic evidence remains REVIEW;
- mobile Evidence Chain renders Rule -> Evidence -> Verdict vertically;
- core workflows avoid horizontal overflow;
- `prefers-reduced-motion` removes nonessential motion;
- keyboard focus reaches tabs, review actions, result rows, and Drawer close.

### Visual regression targets

Capture at least:

- desktop landing;
- desktop extraction workspace;
- desktop Human Review inspector;
- desktop BLOCKER result;
- desktop TASK10 Evidence Drawer;
- one mobile/narrow result state.

Screenshots support regression and competition selection but do not replace interaction tests.

## 23. Competition screenshot targets

The redesigned product should naturally produce:

1. **Landing** — value proposition + product proof.
2. **Announcement -> AI extraction** — split source/candidate workspace.
3. **Human Review** — selected requirement, source evidence, editable rule, human confirmation.
4. **Deterministic validation** — actual 61s MP4 -> BLOCKER/BLOCKED evidence.
5. **TASK10 semantic review** — REVIEW / RELATED_EVIDENCE_FOUND + `proposal.pdf` page/offset evidence in Drawer.

No screenshot may use a mock state that contradicts actual product semantics.

Representative message:

> 공고에서 요구사항 추출 -> 제출파일 사전검수
>
> AI가 공고를 구조화하고, 실제 파일과 문서 근거를 바탕으로 제출 전 실수를 줄입니다.

## 24. Rollout strategy

Implementation occurs on a dedicated UI redesign branch/worktree, not directly on `main` and not by editing the currently serving public runtime in place.

Recommended sequence:

1. visual tokens, app shell, brand, landing;
2. split extraction vs requirement-review presentation while preserving existing calls;
3. package workspace;
4. Results Evidence Chain, tabs, Drawer;
5. responsive/recovery/motion polish;
6. full frontend regression plus relevant locked-contract checks;
7. fresh public ACTUAL run on review runtime/build before switching judging runtime;
8. retain prior known-good public runtime path until redesigned build is verified.

Do not delete the existing public-runtime branch/worktree merely because the redesign branch is complete.

## 25. Acceptance criteria

The redesign is acceptable only when all are true:

- landing communicates AI Submission Preflight rather than generic AI/upload tooling;
- legacy paper/pine/lime/tilted-preview identity is removed from redesigned surfaces;
- Electric Blue is interaction/brand color, never PASS color;
- Product Header, Scan Corners + Check, Segmented Stepper, and Wide App Canvas are consistent;
- landing uses Split Hero + Mini Product Window + alternating Product Story + Clean Product Frames;
- app IA exposes separate `공고` and `요구사항 검토` steps without fabricating live AI stages for demo sessions;
- Step 01 uses Split Extraction Workspace;
- Step 02 uses Compact Review List + Inspector;
- Step 03 uses Preflight Package Workspace;
- long-running states use truthful activity, not fake percentages;
- Results use Hybrid Summary + Status Tabs + three-column Evidence Chain;
- result cards use Neutral Card + Status Chip;
- evidence detail uses an Evidence-first Right Side Drawer;
- mobile uses Vertical Evidence Stack and keeps evidence visible;
- failures use Actionable Recovery States;
- motion is subtle and reduced-motion compliant;
- backend authority/verification contracts remain unchanged;
- required regression/typecheck/build/browser checks pass before merge;
- the five competition screenshot states can be captured from a verified build.

## 26. Self-review record

Completed against the brainstorming architectural checklist:

- **Placeholder scan:** no `TBD`/`TODO` or unresolved design placeholder remains.
- **Internal consistency:** landing is outside the numbered app flow; separate `/requirements` route makes the approved five-step Stepper consistent with the approved Split Extraction + Human Review screens.
- **Mode consistency:** demo/frozen behavior is explicitly separated from live custom/generic AI extraction so the UI cannot falsely imply an AI action occurred.
- **Authority consistency:** deterministic PASS/BLOCKER and semantic REVIEW boundaries are unchanged throughout all screens.
- **Scope check:** this remains one frontend redesign effort; no backend feature expansion is required.
- **Ambiguity check:** step readiness, demo handling, CTA behavior, responsive collapse, status color meaning, evidence disclosure, and rollout boundaries are explicit enough for one implementation plan.

## 27. Product decision

**GO.**

This is a presentation/UX refinement, not feature expansion. It should be the final major frontend polish pass before competition submission unless verification discovers a submission-blocking usability or correctness defect.
