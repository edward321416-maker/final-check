# Task 2 Report: Editorial Shell and Landing

## Model fields

- Requested model: `gpt-5.6-sol`
- Requested reasoning effort: `high`
- Observed model: `UNKNOWN`
- Observed reasoning effort: `UNKNOWN`

## Scope and outcome

- Converted the shared body, header, five-step navigation, landing hero, proof frame, story frames, controls, and landing metadata to the approved Editorial Precision tokens.
- Replaced interpolated hero/story display typography with discrete `56/64`, `48/56`, `40/48`, and `32/40` breakpoints.
- Removed ordinary landing-frame shadows, reduced decorative accent use, and retained semantic BLOCKER/REVIEW colors.
- Added computed-style coverage for the white canvas, display typography, proof geometry, scarce accent control geometry, discrete mobile typography, and horizontal overflow.
- Did not modify `frontend/components/landing.tsx`, `frontend/components/app-chrome.tsx`, or `frontend/tests/task09-public-first-visit.spec.ts`; existing semantic markup and behavior were sufficient.
- No backend, session-start, navigation, five-step IA, authority, readiness, acknowledgement, polling, recheck, evidence, or hash behavior changed.

## RED evidence

1. `npm run build`
   - PASS.
2. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts --project=desktop`
   - The first invocation was invalid RED evidence because the build replaced Next assets while the existing process still served the prior manifest; the page rendered without CSS. The isolated runtime was stopped and restarted with the manifest-guarded SDD scripts.
   - Valid rerun: FAIL as expected, `2 failed, 1 skipped`.
   - Body received `rgb(248, 250, 252)` instead of `rgb(255, 255, 255)`.
   - Primary CTA received `rgb(37, 99, 235)` instead of `rgb(49, 87, 255)`.

## GREEN evidence

1. `npm run typecheck`
   - PASS.
2. `$env:API_ORIGIN='http://127.0.0.1:8410'; npm run build`
   - PASS; nine static routes generated.
3. Rebuilt runtime restart using `.superpowers/sdd/2026-09-13-final-check-editorial-precision/stop-review-runtime.ps1` and `start-review-runtime.ps1`
   - PASS; only manifest-matched review processes were stopped. Backend healthy on `127.0.0.1:8410`; frontend healthy on `127.0.0.1:3410`; data remained under the SDD runtime directory.
4. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts tests/task09-public-first-visit.spec.ts --project=desktop`
   - PASS: `3 passed, 2 skipped`.
   - Skips: the mobile-only typography test; TASK09 public-first-visit, which explicitly requires `TASK09_FIRST_VISIT=1` and a public ngrok URL.
5. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts --project=mobile`
   - PASS: `4 passed`.
   - Includes the mobile discrete-type check and no-horizontal-overflow assertion.
6. `git diff --check`
   - PASS.
7. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/ui-redesign.spec.ts --project=desktop --project=mobile`
   - PASS: `44 passed`.
   - Confirms preserved landing copy, focus indicators, reduced motion, desktop/mobile overflow, five-step recovery/navigation, readiness routing, evidence offsets, status semantics, and inspector keyboard behavior.

## Modified files

- `frontend/app/globals.css`
- `frontend/tests/editorial-precision.spec.ts`
- `.superpowers/sdd/2026-09-13-final-check-editorial-precision/task-2-report.md`

## Unresolved issues / limits

- The public ngrok first-visit path was `NOT TESTED` because this task was restricted to the isolated local runtime and forbade touching ngrok/public runtime state. Its existing test remained unchanged and self-skipped.
- Runtime helper host compatibility is asymmetric in this environment: PowerShell 7 auto-converts manifest timestamps during `ConvertFrom-Json`, so the stop script reports a false start-time mismatch; Windows PowerShell 5.1 runs the guarded stop successfully. Conversely, the start script health check succeeds under PowerShell 7 but not Windows PowerShell 5.1. The scripts were not modified because they are outside Task 2 scope.

## Fix round 1

### Review target

- Reviewed Task 2 head: `874c17bf1802239884b3cd18fa1fe8ab64c75a0d`.
- Review verdict: `CHANGES REQUESTED` for incomplete integer-token normalization and missing responsive/shell coverage.
- Requested model: `gpt-5.6-sol`.
- Requested reasoning effort: `high`.
- Observed model: `UNKNOWN`.
- Observed reasoning effort: `UNKNOWN`.

### RED before fix

1. `npm run audit:visual-tokens`
   - FAIL as expected. It reported Task 2 shell/landing violations including brand `22px/900`, step metadata `9px/1.7/.4px`, CTA weight `700`, proof/story metadata, wide `84px`, tablet `36px`, and mobile step `7px/1px/10px` values.
2. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts --project=desktop --reporter=line`
   - FAIL as expected: `6 failed, 2 passed, 1 skipped` on the unchanged reviewed runtime.
   - Independent failures observed CTA weight `700` instead of `600`, brand gap `10px` instead of `8px`, proof heading bottom padding `18px` instead of `16px`, wide hero bottom padding `84px` instead of `80px`, tablet gap `36px` instead of `32px`, and mobile brand size `19px` instead of `20px`.

### Fix applied

- Normalized every Task 2 base, header, stepper, landing hero, proof, story, start/demo, legend, badge, and footer declaration to the approved type, spacing, radius, border, weight, color, and letter-spacing tokens.
- Set primary controls to the normative `14/20` pair at weight `600`.
- Replaced the wide, tablet, and mobile exceptions with approved `80/96`, `32`, `12/4`, `8`, and `12/16` token values.
- Removed the unused `.step small` declaration rather than retaining prohibited metadata values for markup that the five-step shell does not render.
- Added computed-style regressions for the header/brand/stepper, representative proof and story metadata, CTA weight, and explicit 1600px, 1440px, 900px, and 390px viewport states.
- No JSX, session, workflow, IA, navigation, readiness, polling, evidence, authority, or backend code changed.

### GREEN after fix

1. `npm run typecheck`
   - PASS.
2. `$env:API_ORIGIN='http://127.0.0.1:8410'; npm run build`
   - PASS; nine static routes generated.
3. Manifest-guarded isolated runtime restart with the SDD stop/start scripts
   - PASS; frontend `127.0.0.1:3410`, backend `127.0.0.1:8410`, SDD-local data directory.
4. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts --project=desktop --reporter=line`
   - PASS: `8 passed, 1 skipped` (mobile-only assertion).
5. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts tests/task09-public-first-visit.spec.ts --project=desktop --reporter=line`
   - PASS: `8 passed, 2 skipped` (mobile-only assertion and explicitly gated public-ngrok TASK09 test).
6. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/editorial-precision.spec.ts --project=mobile --reporter=line`
   - PASS: `9 passed`.
7. `$env:FINAL_CHECK_BASE_URL='http://127.0.0.1:3410'; npx playwright test tests/ui-redesign.spec.ts --project=desktop --project=mobile --reporter=line`
   - PASS: `44 passed`.
8. `npm run audit:visual-tokens`
   - Overall repository result remains FAIL because later-screen selectors are still pending their owning tasks. The first remaining violation is `.alert-symbol` (`27px` and `44px` result-status styling), followed by `.mode-note` and later workflow-screen declarations; the preceding Task 2 base/shell/landing block is clean.
9. `git diff --check`
   - PASS.

### Remaining limit

- Public-ngrok first visit remains `NOT TESTED` by task constraint; no public runtime or ngrok state was touched.
