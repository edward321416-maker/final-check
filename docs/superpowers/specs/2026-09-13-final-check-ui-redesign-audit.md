# FINAL CHECK — UI Redesign Contract Audit

**Status:** USER APPROVED / AUDITED  
**Audit date:** 2026-09-13  
**Runtime baseline:** `main@9f13866db1f14d917764a7d2865153f7aa6fbf3e`  
**Design spec:** `docs/superpowers/specs/2026-09-13-final-check-ui-redesign-design.md`  
**Design spec reviewed at:** `f168a6a5cf9cff22c6175a47e20edd9efff5ceae`  
**Decision:** GO WITH CORRECTIONS

This audit is a normative addendum to the approved UI redesign design. Where this document conflicts with the design spec, **this audit wins**. The purpose is to prevent a presentation-only redesign from changing TASK02–TASK10 authority, safety, runtime, or API behavior.

## 1. Sources checked

The audit compared the approved UI design against the current implementation and contracts, including:

- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/announcement/page.tsx`
- `frontend/app/upload/page.tsx`
- `frontend/app/results/page.tsx`
- `frontend/app/recheck/page.tsx`
- `frontend/app/globals.css`
- `frontend/components/ui.tsx`
- `frontend/components/screens.tsx`
- `frontend/components/generic-profile.tsx`
- `frontend/components/profile.module.css`
- `frontend/components/session-provider.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/poll-session.ts`
- `frontend/types/check.ts`
- `frontend/types/profile.ts`
- `frontend/package.json`
- `frontend/playwright.config.ts`
- frontend Playwright regression and ACTUAL AI tests for TASK06, TASK08, TASK09, and TASK10
- `backend/app/api/profiles.py`
- `backend/app/api/routes.py`
- `.github/workflows/ci.yml`

## 2. Audit conclusion

The approved visual direction and information architecture are compatible with the existing product. **No backend feature or API contract change is required.** The redesign can proceed as a frontend-focused implementation provided the corrections below are treated as hard constraints.

## 3. Normative corrections

### C01 — Step 03 readiness must not require a READY Verification Plan

The design spec describes Step 03 as available when the requirement/profile/plan state is ready. That wording is too restrictive.

Actual contract:

- demo/frozen may validate when `validation_profile === "frozen_v15"`;
- custom/generic may validate after Human confirmation when `generic_profile.status === "CONFIRMED"` and `validation_profile === "generic"`;
- `verification_plan_state === "READY"` is **not** a global prerequisite for package validation;
- a planner failure or `REVIEW_REQUIRED` plan state must not prevent semantic/manual REVIEW paths from continuing.

Therefore the frontend workflow helper must treat Verification Plan state as **capability/scope information**, not a universal gate.

Required rule:

```ts
const canEnterUpload = session.validation_profile === "frozen_v15"
  || (session.validation_profile === "generic" && session.generic_profile?.status === "CONFIRMED");
```

Do not add a stricter frontend gate than the backend `/validate` contract.

### C02 — No invented pre-run PDF page count or video duration

Current `SubmissionFile` contains only:

```ts
interface SubmissionFile {
  name: string;
  size_bytes: number;
  media_type: string;
  sha256: string;
}
```

The redesign must **not** add backend work solely to populate pre-run page count or duration. Before validation, the package workspace may show only data already known from the current contract: filename, size, media type, package membership, and real readiness/scope state.

Measured page count/duration belongs in Results only when produced by actual verification evidence such as `measured_fact` or `submission_evidence`.

### C03 — Landing sample must be internally consistent and claims must be scoped

Current landing preview says `2개의 BLOCKER` while the visible rows show one BLOCKER and one REVIEW. The redesign must remove that contradiction.

The approved Mini Product Window may use a clearly labelled example such as:

- `1 BLOCKER`
- `1 REVIEW`
- `3 PASS`
- `영상 60초 이내 -> 61.0s -> BLOCKER`
- `기대효과 포함 -> proposal.pdf p.2 -> REVIEW`

The current phrase `모든 BLOCKER는 공고문과 제출파일, 두 곳의 근거를 함께 보여줍니다.` is broader than the product can guarantee. Replace it with a scoped claim such as:

> 자동 판정 가능한 항목은 공고 근거와 실제 측정/제출 근거를 연결하고, 의미 판단은 REVIEW로 남깁니다.

### C04 — Results default status order changes only in the frontend

Approved order:

`BLOCKER -> REVIEW -> PASS -> EXTERNAL`

Current frontend order places EXTERNAL before PASS. Update frontend sorting and relevant tests only. Do not change backend result semantics or result generation order as a hidden contract.

### C05 — Landing and app chrome require route-aware presentation

Current `RootLayout` renders the same header and step navigation on every route. The redesign requires `/` to be outside the numbered Stepper and to use Product Header navigation, while app routes use the compact app shell plus Segmented Stepper.

Preferred low-risk implementation:

- keep `RootLayout` as the server layout;
- add a focused client `AppChrome`/route-aware shell using `usePathname()`;
- do not introduce route groups unless implementation evidence shows they are necessary.

### C06 — Source highlighting must use stored exact offsets, never fuzzy inference

`ProfileRequirement` already provides:

- `evidence_start`
- `evidence_end`
- `evidence.quote`
- `evidence.source_section`

and the profile contains full announcement text.

The Split Extraction Workspace may highlight the exact stored `[evidence_start, evidence_end)` span after validating bounds and, where practical, that the slice matches the stored quote. If the mapping is invalid or unavailable, fall back to the stored source section + exact quote. Do not add fuzzy matching.

### C07 — Truthful Step Activity may use only real pipeline/job/run states

Real fields include:

- `generic_profile.pipeline_status`
- `current_job.status`
- `current_job.stage`
- `current_job.completed_stage2_batches`
- `run_state`

Real job stages are:

`NOT_STARTED | STAGE1_COMPLETE | GATE_COMPLETE | STAGE2_BATCH_N_COMPLETE | FINALIZED`

The UI may translate these to plain Korean, but must not create fake percentages, ETA, or unobservable stages.

### C08 — Do not label `updated_at` as “last checked”

`CheckSession.updated_at` changes on ordinary session saves, not only completed validation. Therefore Results should omit “last checked” unless a true validation timestamp already exists in a reliable contract. This redesign does not add one.

### C09 — Preserve UploadScreen polling and acknowledgement safety

The current upload/validation flow contains safety-critical behavior:

- semantic readiness lookup;
- acknowledgement reset when package/session changes;
- explicit acknowledgement only when required;
- AbortController/generation protection against stale session completion;
- resume polling after reload;
- transient poll retry;
- re-fetch after failed validate request;
- RUNNING mutation protection.

The redesign may extract presentation components, but must preserve these behaviors and their regression tests.

### C10 — Preserve semantic REVIEW-to-REVIEW recheck comparison

TASK10 recheck may remain `REVIEW` while the semantic assessment/evidence fingerprint changes. The Results redesign must preserve the existing comparison behavior and must not reduce recheck comparison to status-only differences.

### C11 — No backend change is required for the approved UI

Do not modify TASK02–TASK10 backend behavior to make the UI easier to build. In particular, do not add:

- pre-run media metadata endpoints;
- new semantic authority;
- new verifier families;
- new result statuses;
- new AI calls;
- OCR/Vision/URL verification;
- persistence schema changes.

If implementation unexpectedly appears to require one of these, stop and return to Product Lead review before changing backend code.

### C12 — Demo/frozen screens must not fake AI extraction

A demo/frozen session has frozen requirements from Validator v1.5, not a live Stage1/Stage2 extraction.

Therefore:

- demo `/announcement` uses truthful labels such as `동결 공고 요구사항` / `검증 예시`;
- demo `/requirements` may show a read-only/already-confirmed Human Review concept screen;
- never show `AI EXTRACTED` for a requirement unless live extraction actually occurred.

### C13 — `/requirements` route requires regression migration

Adding `/requirements` changes the UI path but not the backend workflow. Existing tests that currently perform extraction, Human Review, confirmation, and plan compilation on `/announcement` must be updated to follow:

`/announcement -> /requirements -> /upload`.

At minimum review/update:

- `frontend/tests/golden-path.spec.ts`
- `frontend/tests/generic-profile.spec.ts`
- `frontend/tests/task06-actual-ai.spec.ts`
- `frontend/tests/task08-plan-ui.spec.ts`
- `frontend/tests/task08-actual-ai.spec.ts`
- `frontend/tests/task09-public-actual.spec.ts`
- `frontend/tests/task10-actual-semantic.spec.ts`
- `frontend/tests/task10-semantic-ui.spec.ts` where route/chrome selectors change.

### C14 — Guards must remain fail-closed but become route-specific

The current Guard is coarse. The redesign may improve recovery copy and destination, but later routes must never become reachable merely because the Stepper visually enables them.

Preferred recovery destinations:

- no active announcement/session -> `/`;
- Step 02 unavailable -> `/announcement`;
- Step 03 custom profile not confirmed -> `/requirements`;
- Results unavailable -> `/upload`;
- Recheck unavailable -> `/results` when prior results exist, otherwise the nearest valid earlier step.

### C15 — Right Side Drawer accessibility is a release requirement

Evidence Inspector must support:

- actual button semantics for opening/closing;
- accessible name/title;
- Escape closes;
- keyboard focus moves into the drawer on open;
- focus is contained while modal/drawer semantics require it;
- closing restores focus to the opener;
- mobile uses a full-width sheet without hiding evidence content;
- `prefers-reduced-motion` removes nonessential transitions.

### C16 — Current public runtime must not be replaced during development

The judging URL currently depends on the existing local runtime. UI implementation must occur in an isolated branch/worktree and a separate review runtime first. Do not switch the current public judging runtime until:

- typecheck/build pass;
- frontend Playwright regression passes on desktop and mobile;
- TASK08 deterministic ACTUAL path remains valid;
- TASK10 ACTUAL semantic path remains REVIEW-only;
- five competition screenshot states have been reviewed;
- final Product Lead approval is given.

## 4. Contract invariants to verify after implementation

The final UI branch must demonstrate all of the following without backend semantic changes:

1. Semantic findings never render as automatic PASS/BLOCKER.
2. Human confirmation still establishes the authoritative profile.
3. A custom confirmed profile can reach upload even if the Verification Planner is REVIEW_REQUIRED.
4. Missing semantic acknowledgement cannot start a semantic AI run.
5. Deterministic-only flows require no semantic acknowledgement and create no semantic AI call.
6. 61s actual MP4 remains BLOCKER/BLOCKED under the same verified plan.
7. 45s actual MP4 remains PASS/READY under the same verified plan.
8. TASK10 positive evidence remains REVIEW/RELATED_EVIDENCE_FOUND.
9. TASK10 absence remains REVIEW/NO_CLEAR_EVIDENCE when FULL coverage permits that assessment.
10. Prompt-injection fixture never obtains semantic PASS/BLOCKER authority.
11. Recheck comparison still detects semantic evidence-state changes even when status stays REVIEW.
12. Frozen validator/prompt/manifest hashes remain unchanged.

## 5. Audit decision

**GO WITH CORRECTIONS.**

The visual redesign is safe to implement as a frontend architectural refactor. C01–C16 are mandatory implementation constraints. Any implementation that requires changing backend authority, verification semantics, AI call boundaries, or frozen hashes must stop for renewed design review.