# RESULT_CODEX — TASK 02
Date: 2026-09-02 (Asia/Seoul)
Integration acceptance: **PASS**. Public repository created; source push/PR publication is being finalized.
TASK 01 baseline: commit 7bc3aeb37d2e4a5fbc96904409f0187d91ab6a39.
Work branch: codex/task-02-frozen-v15.

## ACTUAL EXECUTION

- Verified the ZIP's original validator SHA before integration; matched the user-specified hash. Verified all six manifest-listed artifact hashes and preserved source/reference bytes.
- Reran TASK 01 frontend typecheck, production build, Playwright and backend pytest before integration edits.
- Created a local baseline commit and main reference, then a separate TASK 02 branch. The unrelated ai-development-methods checkout was not touched.
- Copied original frozen source and manifests to backend/app/validators/frozen_v15/. Stored historical gate reports separately under docs/reference_full_gate/.
- Installed only actual engine imports into the project virtual environment: numpy 2.5.2, opencv-python-headless 5.0.0.93, pypdf 6.16.2, PyMuPDF 1.28.2. Python 3.14.0; FastAPI 0.135.1; Pydantic 2.13.5. Imports passed. Backend-executable ffprobe: 8.1.2-full_build-www.gyan.dev.
- Generated new actual synthetic acceptance fixtures under fixtures/v15/. Historical 12s/8s, 320x180 TASK 01 files were preserved and are not used for v1.5 acceptance.
- Independently audited video container, exact duration, dimensions, ratio, byte size, and extracted PDF section content **before scoring**. Both videos fully decoded.
- Executed the original native validate_case(Path) against both packages. Then executed the same frozen engine through the adapter and real API upload/recheck flow.
- Adapter verifies the fixed requirement profile, uploaded names/sizes/SHA-256, original engine SHA and structured outputs. Worker runs in the same Python environment with UTF-8 and a 180-second timeout. Original code/globals/thresholds were not patched.
- Submission files now live in isolated temporary session directories. The app retains raw output separately; no output JSON is added to the submitted package.
- Demo buttons fetch real file bytes into the browser and POST multipart files. No normal golden-path API response is intercepted or replaced.
- Migrated serialized NEEDS_REVIEW to REVIEW_REQUIRED in Python and TypeScript. The three locked submission states are BLOCKED, REVIEW_REQUIRED and READY. Before validation, status=null and run_state=NOT_STARTED.
- Preserved all five routes and the existing CSS/layout. Updated data labels and prioritized existing result cards by severity.
- Created the dedicated public repository https://github.com/edward321416-maker/final-check and verified visibility/public ownership. It is separate from ai-development-methods.

Actual acceptance outcomes:

| Case | Independent facts | Raw frozen findings | Adapted summary |
| --- | --- | --- | --- |
| Broken | 61.000s; MP4; 1080x1920; 9:16; video 9,550 bytes; one correct-name PDF; application/portrait/description present, privacy absent | R09 BLOCKER, R13 BLOCKER, R19 REVIEW, R20 REVIEW, R21 REVIEW | BLOCKED; 16 adapted results; exactly two blockers |
| Fixed | 45.000s; MP4; 1080x1920; 9:16; video 9,038 bytes; one correct-name PDF; all four sections present | R19 REVIEW, R20 REVIEW, R21 REVIEW | REVIEW_REQUIRED; R09/R13 PASS; zero blockers |

Videos are intentionally simple static construction at 2 fps without audio, permitted by the task's photo-only demo scope. Metadata and output are measured, not simulated.

## ACTUAL TEST

| Executed command/check | Result |
| --- | --- |
| Baseline frontend npm run typecheck | PASS, exit 0 |
| Baseline frontend npm run build | PASS, exit 0 |
| Baseline frontend npm run test:smoke | 8 passed; desktop/mobile Chromium; 11.4s |
| Baseline backend pytest | 16 passed, 1 dependency warning; 1.10s |
| Updated frontend npm run typecheck | PASS, exit 0 |
| Updated frontend npm run build | PASS, exit 0 |
| Updated frontend npm run test:smoke | **8 passed, 0 failed, 0 skipped, 0 flaky**; 35.1s |
| Updated backend pytest | **26 passed, 0 failed**, 1 dependency warning; 16.69s |
| scripts/generate_v15_fixtures.py | PASS; actual PDF/MP4 files generated |
| scripts/audit_v15_fixtures.py | PASS; both intended ground truths independently confirmed before scoring |
| scripts/run_v15_acceptance.py | PASS; broken BLOCKED, fixed REVIEW_REQUIRED |
| Frozen hash, actual imports and ffprobe smoke | PASS |
| pip check | PASS; no broken requirements |
| git diff --check | PASS, exit 0 |

The real browser suite began at 2026-09-02T10:59:56.349Z. Each viewport's golden path asserts real multipart upload twice, original engine SHA, R09/R13 BLOCKER, both evidence sources, R19 REVIEW, BLOCKED, recheck clearing R09/R13, REVIEW_REQUIRED, reload persistence and no horizontal overflow.
It observed zero page exceptions/console errors in the golden path. The separate outage test intentionally injects one 503; it is labelled fault injection, not a real outage claim.
Backend tests prove all seven requested safety invariants, plus actual upload/recheck, source integrity, status contract parity, receipt tampering, expiry cleanup, input boundaries and unknown-profile rejection.
An actual raster-only PDF was generated, confirmed to have no extracted text, and executed through v1.5. The engine returned four VISION_PENDING requests; adapter returned R09/R10/R11 REVIEW, incomplete validation and REVIEW_REQUIRED.
Policy/runtime failure tests use explicitly injected malformed outputs/errors. Their test outcomes were actually executed; they are not claimed as observed native classifications.

Evidence:
- [TASK 01 baseline logs and reports](artifacts/task01-baseline/)
- [Independent fixture audit](artifacts/demo-fixture-audit.json)
- [Broken raw](artifacts/v15-broken-raw.json) / [broken adapted](artifacts/v15-broken-adapted.json)
- [Fixed raw](artifacts/v15-fixed-raw.json) / [fixed adapted](artifacts/v15-fixed-adapted.json)
- [Runtime dependencies](artifacts/v15-runtime-smoke.json)
- [Backend JUnit](artifacts/backend-smoke.xml) / [Playwright report](artifacts/playwright-results.json)
- [Broken UI](artifacts/screenshots/desktop-04-results-broken.png) / [fixed UI](artifacts/screenshots/desktop-06-results-fixed.png)
- Twelve actual desktop/mobile browser screenshots under artifacts/screenshots/. Upload and result screenshots were visually inspected.

## NOT TESTED

- Exact historical 39-case Final Full Gate corpus: **NOT TESTED**. Handoff contains source/policy/reports only; the historical fixture corpus was absent.
- Independent Requirement Extractor blind evaluation: NOT TESTED; no generic extractor implementation was supplied.
- Actual Vision provider or model accuracy: NOT TESTED / no provider connected. No visual result was invented.
- General R19 motion accuracy/recall or a new benchmark: NOT TESTED. The new still-video demo and policy guardrails were tested only.
- Firefox, Safari/WebKit, physical mobile devices, screen-reader audit, load/fuzz testing and public app hosting: NOT TESTED.
- Cross-platform frozen-engine behavior: local Windows execution verified; Linux/macOS runtime not executed.
- Google Sheets/Drive API synchronization: unavailable; task event remains pending outside Git. No new account/OAuth/plugin schema was acquired.
- No claim that prior Full Gate reference scores are reproduced by these new integration tests.

## FAILURES CORRECTED

- PyMuPDF built-in Korean CID encoding produced PDFs that pypdf could not extract reliably. Independent audit failed before scoring. Embedded the CJK font with Unicode mapping, regenerated and reran audit. This invalid fixture was not counted as a validator failure.
- PyMuPDF's deprecated fitz import emitted a notice to stdout, contaminating child-process JSON. Adapter worker redirects incidental output to stderr while emitting original raw JSON separately. The frozen source was not modified.
- Actual receipt verification initially compared the browser's MIME declaration too. Changed it to compare actual names, byte sizes and SHA-256; MIME declarations are not treated as file identity.
- Two newly authored helper scripts initially landed in the tool's stale workspace. Corrected absolute patch targets and copied them into final-check. Automatic approval review rejected a combined move/delete cleanup with the generic reason "blocked by policy"; duplicate helper copies remain outside this repository under 헬스 해커톤/scripts. No deletion was retried through another tool.
- One Starlette TestClient/httpx deprecation warning remains. PyMuPDF retains the original engine's fitz import warning. Neither prevented successful actual execution.
- Node FORCE_COLOR/NO_COLOR notices are test-runner environment warnings, not frontend runtime errors.

## PRODUCT LIMITATIONS

- **Vision:** pending scanned-PDF sections remain REVIEW and validation_complete=false. This is visible in the mode notice and result explanations.
- **R19 review noise:** both deliberately static videos remain REVIEW. No automatic photo-only BLOCKER exists. No claim about general false-review rates.
- **R20/R21:** licensing and AI provenance remain REVIEW; source-file inspection cannot establish external rights or creation history.
- **Supported announcement:** the supplied frozen engine is a childcare short-form competition profile, with fixed 테스트어린이집 filenames. TASK 02 text's Wanted reference does not match that artifact; the UI identifies the supplied frozen profile rather than claiming Wanted integration.
- **Announcement evidence:** source quotes come from the frozen SOURCE_RULES handoff. Original announcement PDF/URL was not included. No new source location/page number was invented.
- **Semantic boundary:** text-PDF PASS establishes presence of section markers, not document truth, signatures or eligibility.
- **Sessions:** local in-memory metadata and temporary files; one-hour inactivity TTL, replacement/shutdown cleanup and per-session operation lock. No durable or multi-worker service.
- **Uploads:** 8 files, 320 MiB each, 350 MiB aggregate transport. These local limits allow normal <=300MB inputs but are not frozen threshold changes. Extension admission is not malware scanning.
- **Deployment:** source repository is public; application remains loopback-only. No public application hosting, login, payment, dashboard or automatic submission was added.
- Other Product questions are tracked in IMPLEMENTATION_ISSUES.md; no UI redesign or source rewrite was performed.

## SOURCE INTEGRITY

- Expected SHA-256: **4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11**
- Actual SHA-256: **4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11**
- Match: **YES**; source size 15,851 bytes.
- Original source modified/reformatted/renamed internally: **NO**.
- Original ZIP SHA-256: d4aa135bc36565845c0fe3b00779a2c353a708d43f05764bd74f7a0d87f46fa7.
- Source and all six manifest-listed reference artifacts were checked again after tests.
- [Hash evidence](artifacts/source-integrity.json). Git disables text conversion on frozen/reference artifacts.
- Runtime adaptation is solely in the adapter; the service calls it and never patches engine constants or algorithms.

## GITHUB PUBLICATION

GITHUB_PUBLICATION = PENDING_PUSH
Dedicated public repository ownership and visibility were verified under edward321416-maker/final-check.
Baseline main and the integration branch will be pushed, then a normal PR will carry the tested integration.

## CHANGED FILES

Core changes:
- backend/app/validators/v15_adapter.py; new frozen_v15/ original artifacts.
- backend/app/api/routes.py, main.py, models/schemas.py, services/{sessions,demo,policy}.py.
- backend/requirements.txt, requirements.lock.txt and tests/test_smoke.py.
- frontend/types/check.ts, lib/api.ts, components/{screens,session-provider,ui}.tsx, app/layout.tsx and tests/golden-path.spec.ts.
- scripts/generate_v15_fixtures.py, audit_v15_fixtures.py and run_v15_acceptance.py.
- New actual fixtures/v15/ package and source/reference/audit/raw/adapted/test evidence.
- Product/validator/demo/README/decision/issue/task/execution/sync documents and .gitattributes.
- frontend/app/globals.css was not changed.
A full TASK 02 diff is relative to baseline 7bc3aeb; the previous TASK 01 report is retained in artifacts/task01-baseline/RESULT_CODEX_TASK01.md.
