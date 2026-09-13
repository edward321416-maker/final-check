# FINAL CHECK — UI Redesign Design

**Status:** USER REVIEW REQUIRED  
**Self-review:** PENDING  
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
- public judging screenshots can be captured from real product states without decorative mock data contradicting the visible result counts.

## 2. Non-goals

This redesign does not change:

- TASK02–TASK10 backend verification semantics;
- any frozen validator, prompt, manifest, or plan hash;
- the Human-confirmed Requirement Profile authority boundary;
- AI authority: AI still cannot produce automatic `PASS`, `BLOCKER`, `READY`, or `BLOCKED` decisions for semantic content;
- TASK08 verifier families or Plan DSL;
- TASK10 eligibility, PDF trust, evidence exact-match gate, coverage rules, or acknowledgement rules;
- the one-backend-process TASK07/TASK09 runtime model;
- public hosting architecture;
- support for OCR, Vision, MP4 semantic understanding, URL verification, or new file types;
- dark mode;
- user accounts, billing, collaboration, or analytics.

No redesign task may silently broaden product claims beyond what the current engine actually verifies.

## 3. Existing frontend context

The current frontend already has working flows and should be evolved rather than replaced wholesale.

Observed baseline structure includes:

- `frontend/app/globals.css` for the current paper/pine/lime visual system and shared layout;
- `frontend/components/ui.tsx` for Navigation, Badge, evidence, file-list, guard, and common UI primitives;
- `frontend/components/screens.tsx` for Home, Announcement, Upload, Results, and Recheck screen logic;
- `frontend/components/generic-profile.tsx` for text announcement input, AI extraction, review/edit/approve, profile confirmation, and plan compile actions;
- App Router paths for `/`, `/announcement`, `/upload`, `/results`, and `/recheck`.

Current `.preview` intentionally uses `transform: rotate(1deg)`; the redesign removes this and other scrapbook/paper styling. Existing data-fetching, durable polling, mutation, acknowledgement, and session recovery behavior remain the implementation source of truth.

The implementation may extract focused presentational components from the existing large screen files when that improves clarity, but must not rewrite working session/business logic merely for style consistency.

## 4. Design principles

### 4.1 Evidence first

The product should make the user ask "what is the evidence?" before "what color is the status?". Status is compact metadata; evidence is the main explanatory surface.

### 4.2 Truthful progress

Never invent completion percentages or model stages the backend cannot observe. Loading UI may show only real coarse-grained states supported by current session/job data.

### 4.3 Human authority is visible

AI-extracted requirements must look provisional until a person approves them. `AI EXTRACTED` and `HUMAN CONFIRMED` are different states and must never be visually interchangeable.

### 4.4 Deterministic certainty is visually different from semantic review

A measured 61.0-second video can produce a deterministic BLOCKER. A PDF sentence that appears related to a mandatory content requirement remains REVIEW. Both can use the same evidence-chain layout while keeping their authority different.

### 4.5 Quiet by default, detail on demand

The default interface is neutral and scan-friendly. Provenance hashes, prompt IDs, offsets, and low-level diagnostic fields remain available but are moved behind secondary disclosure or the Evidence Inspector.

### 4.6 Reference successful product patterns, do not clone them

Use proven interaction ideas as references:

- Linear: quiet product surfaces, split list/detail inspection, compact navigation;
- Vercel: deployment/preflight status hierarchy and restrained use of status color;
- GitHub Checks / review UI: check -> annotation -> source context traceability;
- Stripe Radar: clear Block / Review / Allow conceptual separation without full-surface color fills;
- Sentry: summary first, deep evidence/trace inspection on demand.

FINAL CHECK keeps its own evidence-first identity and Korean-first product copy.

## 5. Visual system

### 5.1 Base palette

Use a white SaaS foundation:

- page background: white or very light neutral gray;
- primary text: near-black neutral;
- secondary text: cool neutral gray;
- borders: low-contrast neutral gray;
- primary signature color: Electric Blue;
- cards: white with subtle border and minimal elevation.

Electric Blue is reserved for:

- primary CTA;
- active step;
- keyboard/focus ring;
- selected/interactive evidence relationship;
- source-to-evidence trace;
- selected tabs and controls.

Electric Blue must not mean PASS.

### 5.2 Status colors

Status color remains separate from brand color:

- `BLOCKER`: red;
- `REVIEW`: amber;
- `PASS`: green;
- `EXTERNAL`: cool gray / blue-gray.

Cards remain neutral. Use a compact status chip plus an approximately 3px leading status indicator. BLOCKER may receive a very faint red surface tint, but no state receives a fully saturated card background.

### 5.3 Typography

- Primary: Pretendard, with existing system fallbacks retained.
- Product/body text: proportional sans serif.
- Monospace only for IDs, hashes, page/character locators, durations when shown as machine evidence, and technical provenance.
- Avoid decorative uppercase tracking except for very small metadata labels.

### 5.4 Shape and elevation

- Product frames and major cards: approximately 12–16px radius.
- Controls: moderate radius, not pill-heavy by default.
- Border: 1px neutral.
- Shadow: soft and restrained; product screenshots should appear crisp rather than floating heavily.
- Remove intentional tilt/rotation from product preview surfaces.

## 6. Brand mark and header

### 6.1 Logo

Use a `Scan Corners + Check` mark with the `FINAL CHECK` wordmark.

The symbol should use a small number of open scan-corner strokes around a central check; it must not become a closed checkbox icon. The mark is Electric Blue on light surfaces. The header uses symbol + wordmark; favicon/small contexts may use the symbol only.

No complex illustration or gradient logo is required.

### 6.2 Landing product header

Landing header structure:

- left: brand mark + `FINAL CHECK`;
- center: compact navigation such as `How it works`, `Evidence-first`, `검증 방식`;
- right: primary CTA `제출 전 검사 시작하기`.

The center navigation is for the landing page only. Once the user enters the app flow, navigation noise is reduced and the app header + stepper become dominant.

## 7. Information architecture and routes

The landing page is not a numbered verification step.

Target app stepper:

1. `공고`
2. `요구사항 검토`
3. `제출파일`
4. `결과`
5. `재검사`

To make the approved five-step model truthful, add a dedicated frontend requirement-review route:

- `/` — landing/start, outside the numbered stepper;
- `/announcement` — Step 01, announcement ingestion/extraction workspace;
- `/requirements` — Step 02, Human Review and profile confirmation;
- `/upload` — Step 03, submission package workspace;
- `/results` — Step 04, results and evidence;
- `/recheck` — Step 05, revised package comparison/recheck.

This is a frontend workflow split only. It reuses existing profile/session endpoints and does not add a new backend authority boundary.

The current combined `GenericProfileReview` behavior should be separated presentation-wise:

- extraction/job state and source-to-candidate mapping belong on `/announcement`;
- edit/approve/delete/full-source acknowledgement/profile confirmation/plan compile belong on `/requirements`.

If the session is not ready for a later step, existing Guard behavior remains fail-closed and provides an actionable recovery route.

## 8. App shell and segmented stepper

Use a Wide App Canvas rather than full-bleed dashboard chrome.

Recommended max widths:

- landing content: 1240–1280px;
- normal app screens: 1200–1240px;
- Results / Evidence: up to 1320px;
- desktop horizontal padding: 24–32px;
- narrow screens: single-column layout.

Segmented Stepper behavior:

- one thin horizontal row;
- each step includes `01`, `02`, etc. plus Korean step name;
- current step: Electric Blue text and approximately 2px underline;
- completed step: small check indicator and neutral/dark text;
- future disabled step: neutral gray;
- no large circles or checkout-style progress line;
- keyboard focus remains visible;
- current step uses `aria-current="step"`.

## 9. Landing page

### 9.1 Hero

Use a Split Hero, approximately 48% copy / 52% product proof.

Primary copy:

> **제출 버튼을 누르기 전, 마지막 확인.**
>
> FINAL CHECK가 공고의 요구사항을 구조화하고, 실제 제출파일에서 놓친 조건과 근거를 찾아줍니다.

Primary CTA:

> 제출 전 검사 시작하기

Secondary action:

> 어떻게 작동하나요?

Trust statement:

> AI는 근거를 찾고, 확실한 조건은 코드가 검증합니다.

The hero must not claim that every announcement requirement can be automatically checked.

### 9.2 Hero proof window

The right side uses a compact Mini Product Window, not an angled decorative mockup.

The preview should demonstrate the real result grammar:

- compact counts such as `1 BLOCKER / 1 REVIEW / 3 PASS`;
- deterministic example: `영상 60초 이내 -> 61.0s -> BLOCKER`;
- semantic example: `기대효과 포함 -> proposal.pdf p.2 -> REVIEW`.

Visible counts and visible sample rows must never contradict each other. If sample data is static, label it clearly as an example and keep the counts internally consistent.

### 9.3 Three-step product story

Below the hero, use an alternating product-story sequence:

- 01 text left / product frame right: 공고 읽기;
- 02 product frame left / text right: 기준 확정;
- 03 text left / product frame right: 제출물 검증.

Step 03 may have slightly more visual weight because evidence-backed preflight is the product differentiator.

Actual product screenshots use a Clean Product Frame:

- no browser address-bar chrome;
- 1px neutral border;
- 12–16px radius;
- restrained shadow;
- UI large enough to read at judging screenshot scale.

## 10. Step 01 — Split Extraction Workspace

Desktop layout:

- left approximately 45%: `Announcement Source`;
- right approximately 55%: `Extracted Requirements`.

The screen should show AI extraction as transformation, not as a verdict.

Each candidate requirement may show:

- requirement ID;
- modality, such as `MUST` / `MUST_NOT`;
- verifier family;
- concise rule;
- source section / locator;
- provisional state `AI EXTRACTED` or equivalent.

Do not show submission `PASS` or `BLOCKER` in this stage.

Interaction:

- selecting or focusing a requirement highlights its exact source evidence in the announcement pane;
- selecting a source evidence region highlights the corresponding requirement when a reliable mapping already exists in current data;
- source linkage uses a subtle Electric Blue highlight, not a permanent workflow diagram;
- if exact mapping is unavailable, do not fabricate one; show the stored source section / exact quote instead.

During extraction, use Truthful Step Activity based only on real pipeline/session states. Do not invent percentage completion.

## 11. Step 02 — Compact Review List + Inspector

Desktop layout:

- left approximately 65%: compact requirement list;
- right approximately 35%: selected-item Inspector.

### 11.1 List

Each row should prioritize:

- rule summary;
- modality;
- verifier;
- confirmation state.

The list is for scanning, not for exposing every provenance field.

### 11.2 Inspector

Selected requirement detail order:

1. AI/provisional state;
2. exact announcement evidence;
3. editable structured requirement fields;
4. verifier classification;
5. issues/warnings;
6. actions: save edit, needs review, approve, delete.

Primary visual story:

`AI EXTRACTED -> SOURCE EVIDENCE -> HUMAN CONFIRMED`

`항목 승인` means the announcement requirement has been confirmed as authoritative. It must never read as if the submission already satisfies that requirement.

Full-source acknowledgement and Profile confirmation remain explicit. Plan compilation remains after profile confirmation. Low-level provenance/history stays available through secondary disclosure.

## 12. Step 03 — Preflight Package Workspace

Desktop layout:

- left 60–65%: `Submission Package`;
- right 35–40%: `What will be checked`.

### 12.1 Submission Package

Show:

- drop/select files;
- current package files;
- file type;
- size;
- available metadata such as page count or duration only when actually known from the current pipeline;
- package limits and supported types where useful.

Before validation, file rows must not display final `PASS` or `BLOCKER`. They may use neutral preparation language such as `검사 가능`, `확인 필요`, or actual readiness states already supported by the backend.

### 12.2 What will be checked

Summarize the confirmed profile/plan in user language, for example:

- 파일 존재 여부;
- PDF 페이지 수;
- 영상 길이;
- PDF 내용 근거.

Where counts are reliable, show a concise summary such as:

> 4개 자동 검사 · 1개 AI 근거 검토

The summary must be derived from the actual confirmed plan/readiness rather than decorative hard-coded numbers in production.

Primary CTA:

> Preflight 검사 실행

TASK10 acknowledgement copy remains explicit whenever an actual semantic AI call can occur.

## 13. Truthful processing states

Replace generic spinner-only long-running states with Truthful Step Activity when the backend exposes a real stage.

Example announcement flow may render states corresponding to actual observed pipeline/job values such as:

- source prepared;
- AI extraction running/completed;
- evidence gate/review batch processing when current backend state can distinguish it;
- review candidates ready.

Example semantic flow may render only states the current backend can truthfully expose, such as:

- package ready;
- run started;
- semantic review running;
- results committed.

Rules:

- no fake `%` progress;
- no guessed remaining time;
- no client-only stage names that imply backend work not actually occurring;
- on restart recovery, represent restored/failed durable state truthfully;
- a failed run remains actionable and does not visually masquerade as completion.

## 14. Step 04 — Results and Evidence

Results is the visual center of the redesign.

### 14.1 Hybrid Summary

Top summary:

- left: overall state and one-line explanation;
- optional last-checked time if reliable;
- right: compact counts for BLOCKER / REVIEW / PASS / EXTERNAL.

READY copy must stay scoped, for example:

> 자동 확인 가능한 필수 조건을 충족했습니다.

Do not imply all competition requirements have been proven satisfied.

### 14.2 Status Tabs

Place directly below the summary:

- `전체`;
- `BLOCKER`;
- `REVIEW`;
- `PASS`;
- `EXTERNAL`.

Include counts. Default is `전체`.

Default result ordering:

1. BLOCKER
2. REVIEW
3. PASS
4. EXTERNAL

The active tab uses Electric Blue underline/active treatment. Status labels retain their own status colors.

### 14.3 Three-column Evidence Chain

Desktop reading order:

- RULE: approximately 25%;
- EVIDENCE: approximately 50%;
- VERDICT: approximately 25%.

Deterministic example:

`영상 60초 이내 -> duration 61.0s -> BLOCKER`

Semantic example:

`기대효과 포함 -> proposal.pdf · p.2 -> REVIEW`

Cards remain neutral. On hover/focus of an evidence relationship, a subtle Electric Blue trace may connect/emphasize the three zones. The trace is an interaction affordance, not always-visible decoration.

### 14.4 Status card treatment

Use Neutral Card + Status Chip:

- compact chip;
- leading status indicator;
- neutral surface;
- faint BLOCKER tint only when useful;
- status icon/text must remain understandable without color alone.

## 15. Evidence Inspector — Right Side Drawer

Selecting an evidence result opens a right-side Evidence Inspector while preserving the result list context.

Desktop: right drawer.  
Narrow/mobile: full-width sheet/panel.

Use Evidence-first Hybrid order:

1. compact status + assessment label;
2. `공고 요구사항`;
3. `제출파일 근거`;
4. prominent locator, e.g. `proposal.pdf · p.2 · chars 5:43`;
5. exact evidence quote;
6. explanation such as `왜 REVIEW인가`;
7. collapsed `기술 세부 보기` for hashes/provider/prompt/provenance where available.

TASK10 example wording:

> REVIEW · Related evidence found
>
> 관련 근거 후보는 확인됐지만 최종 충족 여부는 직접 확인이 필요합니다.

For semantic findings, the drawer must never offer an action that converts AI evidence directly into automatic PASS/BLOCKER authority.

Drawer behavior:

- close button is keyboard accessible;
- Escape closes;
- focus is managed correctly;
- background context remains visually recognizable;
- opening/closing uses subtle product motion only.

## 16. Step 05 — Recheck

Recheck retains the same visual language as Upload + Results rather than becoming a separate design system.

The screen should emphasize:

- revised submission package;
- prior vs current result changes;
- evidence/status changes even when both runs remain REVIEW;
- deterministic changes, e.g. 61s BLOCKER -> 45s PASS, without implying unrelated requirements changed.

Existing recheck fingerprint/change logic remains authoritative.

## 17. Actionable recovery states

Use specific recovery copy instead of generic `오류가 발생했습니다` when the cause is known.

Examples:

### PDF text unavailable

> **PDF 내용을 읽을 수 없습니다**  
> 이 파일에서는 텍스트를 추출하지 못해 내용 검토를 실행하지 않았습니다.
>
> Actions: `다른 PDF 업로드` / `수동으로 검토`

### Semantic AI run failure

> **AI 검토를 완료하지 못했습니다**  
> 자동 PASS/BLOCKER로 처리하지 않았습니다. 이 항목은 REVIEW 상태로 남습니다.
>
> Actions: `다시 시도` / `근거 직접 확인`

### Missing prerequisite

Explain which prior step is incomplete and link to that step rather than sending all users generically to Home.

Technical diagnostics may be placed behind a details disclosure where useful.

## 18. Responsive behavior

Primary breakpoints should follow content needs rather than device labels.

### Wide desktop

- full Wide App Canvas;
- three-column Evidence Chain;
- split extraction workspace;
- review list + inspector;
- right-side Evidence Drawer.

### Medium/narrow desktop or tablet

- reduce gaps/padding before collapsing structure;
- two-pane layouts may become stacked when each pane no longer remains readable;
- stepper remains compact and horizontally understandable without forcing tiny text.

### Mobile / narrow

Evidence results become a Vertical Evidence Stack:

`RULE`

`EVIDENCE`

`VERDICT`

A short Electric Blue trace may preserve the relationship. Evidence must not disappear merely to save space.

Other transformations:

- Split Extraction -> source then extracted requirements in one column;
- Human Review -> list then full-width inspector/sheet;
- Preflight Package -> package then check scope;
- Evidence Drawer -> full-width sheet;
- landing split hero -> copy then proof window;
- alternating product story -> linear vertical story.

Avoid horizontal scrolling for the core Evidence Chain.

## 19. Motion

Use Subtle Product Motion only:

- button/card hover: approximately 120–160ms;
- step state: short fade;
- evidence trace: subtle hover/focus reveal;
- Evidence Drawer: approximately 180–220ms slide + fade;
- status update: color/fade, no bounce;
- hero Mini Product Window: one restrained initial fade-up is allowed.

Do not use:

- parallax;
- continuous floating;
- bouncing success icons;
- aggressive scaling;
- long stagger sequences;
- animation that delays evidence reading.

Honor `prefers-reduced-motion` by removing nonessential transitions and movement.

## 20. Accessibility

The redesign must preserve or improve accessibility:

- visible keyboard focus with Electric Blue focus ring;
- status meaning is not color-only;
- semantic HTML and existing ARIA labels are retained or improved;
- stepper exposes `aria-current` and disabled state correctly;
- tabs use appropriate tab/list semantics or equally clear accessible button semantics;
- drawer traps/manages focus appropriately and closes via Escape;
- buttons have disabled state and busy text where needed;
- body text and status chips meet practical contrast requirements;
- exact evidence quotes remain selectable/readable text;
- reduced motion is respected.

## 21. Component architecture guidance

Implementation should favor focused presentational components while keeping session/domain behavior stable.

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

- domain/API calls remain in the existing screen/profile/session layer unless extraction is necessary to keep files understandable;
- presentational components receive typed data and callbacks;
- do not duplicate status computation in CSS/UI components;
- do not infer backend state client-side when an authoritative field already exists;
- do not create a parallel frontend result model that can drift from `ValidationResult` / current profile types.

## 22. Testing and regression requirements

The redesign is complete only if product semantics and presentation both pass.

Required verification categories:

### Existing behavior

- frontend typecheck;
- production build;
- existing browser/Playwright suite;
- public first-visit flow where still applicable;
- existing TASK10 semantic acknowledgement and polling behavior;
- recheck behavior;
- guard/recovery behavior.

### New/updated UI behavior

- landing CTA enters the real flow;
- landing sample counts are internally consistent;
- `/announcement` extraction states never show submission PASS/BLOCKER;
- `/requirements` preserves edit / needs-review / approve / delete / profile-confirm / plan-compile actions;
- stepper enable/disable rules match actual session readiness;
- result status tabs filter correctly;
- Evidence Drawer opens/closes and renders exact evidence locator/quote;
- semantic evidence remains REVIEW in UI;
- mobile Evidence Chain renders Rule -> Evidence -> Verdict vertically;
- responsive layouts do not introduce horizontal scrolling for core workflows;
- `prefers-reduced-motion` disables nonessential motion;
- keyboard focus can reach and operate tabs, review actions, result cards, and drawer close.

### Visual regression targets

Capture representative screenshots for at least:

- desktop landing;
- desktop extraction workspace;
- desktop human review inspector;
- desktop BLOCKER result;
- desktop TASK10 Evidence Drawer;
- one narrow/mobile result state.

The screenshot set is for regression and competition-submission selection, not a substitute for interaction tests.

## 23. Competition screenshot targets

The redesigned product should naturally produce these five submission images:

1. **Landing** — value proposition + real product proof.
2. **Announcement -> AI extraction** — split source/candidate workspace.
3. **Human Review** — selected requirement, source evidence, editable rule, human confirmation.
4. **Deterministic validation** — actual 61s MP4 -> BLOCKER/BLOCKED evidence.
5. **TASK10 semantic review** — REVIEW / RELATED_EVIDENCE_FOUND + `proposal.pdf` page/offset evidence in the Drawer.

Suggested captions remain concise and factual. No screenshot should use a mock state that contradicts actual product semantics.

Representative-image message:

> 공고에서 요구사항 추출 -> 제출파일 사전검수
>
> AI가 공고를 구조화하고, 실제 파일과 문서 근거를 바탕으로 제출 전 실수를 줄입니다.

## 24. Rollout strategy

Implementation should occur on a dedicated UI redesign branch/worktree based on the approved baseline, not directly on `main` and not by editing the currently serving public runtime in place.

Recommended rollout:

1. implement visual tokens/app shell and landing;
2. split extraction vs requirement-review presentation while preserving existing backend calls;
3. implement upload/package workspace;
4. implement results Evidence Chain, tabs, and Drawer;
5. implement responsive/recovery/motion polish;
6. run full frontend regression and locked-contract checks relevant to the touched surface;
7. perform a fresh public ACTUAL run on a review deployment/runtime before switching the judging URL/runtime;
8. keep the prior known-good public runtime path available until the redesigned build is verified.

Do not delete the existing public-runtime branch/worktree merely because the redesign branch is complete.

## 25. Acceptance criteria

The UI redesign is acceptable when all are true:

- landing communicates FINAL CHECK as an AI Submission Preflight, not a generic AI chat or upload tool;
- legacy paper/pine/lime/tilted-preview identity is removed from the redesigned surfaces;
- Electric Blue is used as interaction/brand color, not PASS color;
- Product Header, Scan Corners + Check mark, Segmented Stepper, and Wide App Canvas are implemented consistently;
- landing uses Split Hero + Mini Product Window + alternating three-step Product Story + Clean Product Frames;
- app IA exposes separate `공고` and `요구사항 검토` steps;
- announcement uses Split Extraction Workspace;
- human review uses Compact Review List + Inspector;
- upload uses Preflight Package Workspace;
- long-running AI states use truthful activity, not fake percentages;
- results use Hybrid Summary + Status Tabs + three-column Evidence Chain;
- result cards use Neutral Card + Status Chip;
- Evidence detail uses a right-side Evidence-first Drawer;
- mobile uses Vertical Evidence Stack and keeps evidence visible;
- failures use Actionable Recovery States;
- motion is subtle and reduced-motion compliant;
- no backend authority or verification contract changes;
- all required regression/typecheck/build/browser tests pass before merge;
- the five competition screenshot states can be captured from a verified product build.

## 26. Product decision

**GO.**

This redesign is a presentation/UX refinement, not feature expansion. It should be the final major frontend polish pass before competition submission unless testing discovers a submission-blocking usability or correctness defect.
