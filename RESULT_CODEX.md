# RESULT_CODEX — TASK 03
Date: 2026-09-03 (Asia/Seoul). Base: main e1fab59c83185ad1ddf438046a5ae9f12cf17789.
Branch: codex/task-03-generic-requirement-profile.

## TASK 03 STATUS

**PASS — integration acceptance (all 10 gates).**
Generic announcement requirement-profile pipeline is integrated and executable.
This is not a claim that FINAL CHECK accurately understands every competition announcement.
GitHub delivery is recorded below once actually published. The unchanged TASK 02 report is retained below and in [its baseline archive](artifacts/task02-baseline/RESULT_CODEX_TASK02.md).

## ACTUAL EXECUTION

- Verified the real checkout, origin, clean main, fetched origin/main (0 ahead / 0 behind), read project policy/source-of-truth documents and stack metadata before code changes.
- Created the requested branch; preserved frozen source/manifests/reference artifacts, fixtures and existing globals.css. No unrelated repository was modified.
- Added separate generic Python/TypeScript schemas supporting all requested canonical fields, modality/severity/verifier enums, four extraction states and three profile states.
- Added an injectable RequirementExtractor boundary and executable local-rules-v1. It uses Korean keywords and clause/line patterns, no remote calls or AI model. Actual execution and uncalibrated confidence are visibly labelled.
- Implemented exact quote/offset and source-text hash validation, NO EVIDENCE → NO RULE, SHOULD/MAY/INFO + BLOCKER schema rejection, compound-rule review gates and explicit user-only approval.
- Text input and UTF-8 TXT/PDF uploads preserve source SHA, text SHA, exact source text, source type/name and profile identity. PDF parsing runs in a bounded local worker. Scanned/unreadable input creates no requirements.
- Added edit/delete/NEEDS_REVIEW/APPROVE controls inside the existing Announcement Analysis screen. Before/after history and original candidates preserve provenance. Version checks reject stale edits. Whole-profile confirmation requires every retained item approved and a full-source-review acknowledgement.
- Generic profile changes invalidate activation and prior findings. Only CONFIRMED profiles populate the canonical validation handoff. Frozen and generic branches remain distinct.
- Generic orchestration verifies uploaded-byte receipts, then returns REVIEW/EXTERNAL with validation_complete=false and engine_sha256=null. No generic submission verifier is fabricated, and the frozen engine is never repurposed for a generic profile.
- Preserved the five routes and original global layout/CSS. Added only scoped form styles and truthful provider/result labels.
- Generated actual new text-PDF and raster-only PDF bytes; checked their text layers with pypdf separately from application PyMuPDF parsing. No new dependency, account, OAuth, paid API or plugin installation was needed.

## ACTUAL TEST

All commands below were actually executed locally on Windows. Paths are relative to the specified working directory.

| Working directory / command | Actual result |
| --- | --- |
| backend: `.venv/Scripts/python.exe -X utf8 -m pytest -q --junitxml=../artifacts/task03/backend-baseline.xml` | Original **26 passed**, 16.77s, one existing Starlette deprecation warning |
| frontend: `npm run test:smoke` before edits | Original **8 passed**, 21.7s |
| root: `backend/.venv/Scripts/python.exe -X utf8 scripts/generate_announcement_fixtures.py` | PASS; actual text PDF and raster-only PDF, second-parser content checks passed |
| backend: `.venv/Scripts/python.exe -X utf8 -c "from app.main import app; print('API import OK:', len(app.routes))"` | API import PASS |
| backend: `.venv/Scripts/python.exe -X utf8 -m pytest -q --junitxml=../artifacts/task03/backend-tests.xml` | **47 passed**, 10.01s; original 26 plus 21 new cases; one existing warning |
| frontend: `npm run typecheck` | PASS, exit 0 |
| frontend: `npm run build` | PASS, exit 0; five product routes preserved |
| frontend: `npm run test:smoke` after final UI changes | **14 passed**, 22.2s; 0 failed, skipped or flaky; original 8 plus 6 new desktop/mobile cases |
| root: `git diff --check` | PASS |
| root: `git diff --cached --check` | PASS after normalizing generated-log whitespace |
| Frozen directory before/after SHA-256 comparison | PASS, all four files unchanged |

The final browser run began **2026-09-03T02:40:42.8Z**, using Desktop Chrome 1440×1000 and existing iPhone 13 Chromium emulation, 2 workers, 0 retries.
The new text golden path actually inputs source text, runs extraction, checks quotes, edits/saves/keeps review, deletes one item, approves every retained item, confirms/reloads the profile, uploads an actual PDF and reaches REVIEW/EXTERNAL results and Recheck. Normal requests are not intercepted. Page/console error collections were empty in the generic and frozen golden paths.
Actual text-PDF and scanned-PDF browser paths ran in both viewports. Captures assert no horizontal overflow. Desktop review/result and mobile scan screenshots were visually inspected.
Backend cases cover every A–J requirement: missing/rewritten evidence, all three forbidden BLOCKER modalities, atomicity rejection, text/PDF/scan, review lifecycle, edited provenance and before/current frozen integrity. Additional guards cover deletion audit, empty confirmation, source/hash tampering, stale versions, provider failure, malformed PDF/timeout and generic fake verdict rejection.

Evidence:
- [Backend JUnit](artifacts/task03/backend-tests.xml) / [backend log](artifacts/task03/backend-tests.log)
- [Browser JSON](artifacts/task03/browser-tests.json) / [browser log](artifacts/task03/browser-tests.log)
- [Typecheck](artifacts/task03/typecheck.log) / [build](artifacts/task03/build.log)
- [Fixture audit](artifacts/task03/announcement-fixture-audit.json)
- [Text extraction profile](artifacts/task03/text-profile-extracted.json)
- [Actual text-PDF profile](artifacts/task03/submission.pdf-profile.json) / [scanned-PDF profile](artifacts/task03/scanned.pdf-profile.json)
- [Confirmed profile and validation handoff](artifacts/task03/confirmed-handoff.json)
- [Ten generic browser screenshots](artifacts/task03/screenshots/) and current frozen-flow captures in artifacts/screenshots/.

## SELF-BENCHMARK

The synthetic announcement, generated PDFs and expected five extraction candidates were authored in this same task. Atomic split, modality and expected-candidate comparisons are **SELF-BENCHMARK**, not independently labelled evaluation.
Execution of real files and code is ACTUAL TEST; that does not convert same-session ground truth into independent accuracy evidence. No recall, precision, general coverage or 90%+ claim is made.

## SIMULATED

- Test-only MockProvider injections explicitly return execution_kind=SIMULATED. They exercise rewritten evidence rejection and compound-rule review, not real AI/model extraction.
- Provider exceptions and PDF timeouts are labelled fault injections. The existing isolated browser outage test injects a 503 response.
- The default application provider is ACTUAL local rules, not MOCK and not an AI model. Generic submission verification is UNSUPPORTED, not simulated PASS/BLOCKER.

## NOT TESTED

- Independent generic extraction accuracy, held-out gold, general competition recall/precision or external-model extraction.
- Actual Vision/OCR/model integration, URL fetching, semantic submission compliance, malware scanning or R19 improvements.
- Historical 39-case reproduction: exact corpus absent; no replacement corpus or prior-score reproduction claim.
- Firefox/WebKit, physical phones, screen-reader audit, production hosting, load testing or multi-worker operation.
- Robust PDF table/reading-order interpretation, embedded image requirements, arbitrary languages/encodings and exhaustive semantic atomicity/entailment.
- Google Sheets/Drive API synchronization; no authenticated API write is claimed. Completion logging is queued privately when publication is complete.

## REGRESSION

- The unchanged original backend suite ran before edits (26 passed) and remains intact in the final 47-test run.
- Original browser suite ran unchanged before edits (8 passed). Final run retains all 8 scenarios. One custom-upload assertion now expects the new DRAFT review UI and still proves no implicit extraction, frozen-profile inheritance or fake findings.
- Actual frozen broken path remains R09/R13 BLOCKER, BLOCKED; fixed clears both blockers with zero remaining blockers and REVIEW_REQUIRED. R19/R20/R21 remain REVIEW. Evidence-first requirements are asserted by the existing tests.
- No frozen source, constants, filename rules, threshold, algorithm, global CSS or route changes.

## SOURCE INTEGRITY

Before SHA-256: **4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11**

After SHA-256: **4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11**

**Identical.** Entire frozen directory: [before](artifacts/task03/frozen-before.json) / [after](artifacts/task03/frozen-after.json). Both measurements were made in this task. Git diff for frozen_v15 and frontend/app/globals.css is empty.

## PRODUCT LIMITATIONS

- Local rules are a narrow, uncalibrated Korean heuristic. Implicit obligations, negations, multi-line context, exceptions, cross-references and applicant-facing scope can be missed or misclassified. Users must review the full source, not only extracted candidates.
- Exact evidence matching proves textual provenance, not semantic entailment. Atomicity checks are conservative syntax checks, not an exhaustive semantic proof. Original clause fragments may need wording edits.
- Provider candidates default to conservative REVIEW/INFO/EXTERNAL severities. User-edited MUST/MUST_NOT BLOCKER severity is allowed in the profile; it still cannot create an unsupported automatic submission BLOCKER.
- CONFIRMED means human-reviewed requirements. Generic compliance verification is not implemented: all results REVIEW/EXTERNAL, summary REVIEW_REQUIRED, validation incomplete. Evidence panels explicitly say submission verification was not run.
- Input limits: 10 MiB announcement, 100,000 text characters, 50 PDF pages, 30-second worker timeout. Any textless PDF page prevents extraction. A readable text layer does not prove that image-based conditions were captured.
- Profiles/history/source bytes remain in the existing local temporary session lifecycle (one-hour inactivity TTL, restart/shutdown expiry), without durable production storage.
- TASK 04 should use independently collected announcements and independently authored gold to assess extraction before any broad product accuracy claim. External provider and generic automatic-verifier selection remain separately scoped.

## FAILURES CORRECTED

The first updated browser run produced **13 passed / 1 failed**: the mobile custom-upload regression searched an English navigation label hidden by the existing responsive CSS. The page snapshot showed the visible Korean label. Changed the selector to that Korean label, preserved all safety assertions, rebuilt and reran the entire suite: **14 passed**. [Original failure log, JSON, snapshot and screenshot](artifacts/task03/first-browser-failure/).
The initial staged whitespace check flagged trailing spaces/blank EOF lines in generated terminal logs and the failure snapshot. Normalized only artifact whitespace; the subsequent staged check passed. Test results, JSON findings and frozen bytes were unchanged.
One existing Starlette TestClient/httpx deprecation warning and Node color-environment notices remain; they did not cause runtime or final test failures.

## CHANGED FILES

- New backend: app/models/profiles.py; app/api/profiles.py; app/services/{announcement_input,extractors,profiles,generic_validation}.py; tests/test_profiles.py.
- Updated backend: app/models/schemas.py, app/api/routes.py, app/main.py. Original backend/tests/test_smoke.py and frozen_v15 directory unchanged.
- New frontend: types/profile.ts; components/generic-profile.tsx and profile.module.css; tests/generic-profile.spec.ts.
- Updated frontend: types/check.ts; components/screens.tsx and ui.tsx; app/layout.tsx; tests/golden-path.spec.ts. Original globals.css unchanged.
- New fixtures/announcements/ and scripts/generate_announcement_fixtures.py.
- Updated product/README/demo/decision/issues/tasks/result/sync documents; baseline archives, fixture audit, profile outputs, test reports and screenshots.
- Full path inventory: [changed-files.txt](artifacts/task03/changed-files.txt). Review the TASK 03 PR diff against main for every change.

## GITHUB DELIVERY

Tests and integration gates passed locally. Commit/push/PR metadata is appended after actual publication; no publication or merge is implied by this local status.

---

# Historical TASK 02 report — unchanged results, not a TASK 03 rerun claim
Date: 2026-09-02 (Asia/Seoul)
Integration acceptance: **PASS**. **GITHUB_PUBLICATION = PUBLISHED**.
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

GITHUB_PUBLICATION = PUBLISHED
- Dedicated public repository: https://github.com/edward321416-maker/final-check.
- TASK 01 baseline and tested TASK 02 source were pushed to the dedicated repository.
- Delivery PR: https://github.com/edward321416-maker/final-check/pull/1. Use the linked PR for live merge state.
- GitHub content API retrieval of the published validator matched the original SHA-256 exactly.
- [Publication verification](artifacts/github-publication.json) records the verified integration commit, public visibility, PR and frozen source hash before the normal PR merge.
- Application hosting remains local; public repository publication does not expose the running API.

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
