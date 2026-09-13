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
