# Engineering decisions

- 2026-09-03 TASK 03: Branch from verified main e1fab59; preserve frozen directory and original CSS byte-for-byte.
- 2026-09-03 TASK 03: Use an injectable RequirementExtractor with an ACTUAL local-rule implementation, no AI provider account/key/network dependency. Do not label actual code execution as AI accuracy. Test-only fixture providers are SIMULATED.
- 2026-09-03 TASK 03: Keep generic canonical profile models separate from frozen legacy requirements. Populate the validation representation only after explicit profile confirmation; generic results are review-only and never execute frozen childcare rules.
- 2026-09-03 TASK 03: Store exact source text, input/text SHA, quote offsets, immutable original candidates and before/after review events. Reject missing evidence and unsupported BLOCKER modalities; syntactic atomicity issues require human correction.
- 2026-09-03 TASK 03: Every edit invalidates previous approval/activation and findings; explicit APPROVE may save and approve the edited candidate in one user-authorized action. Whole-profile confirmation requires all retained items approved plus full-source acknowledgement. Version checks protect stale review requests.
- 2026-09-03 TASK 03: Reuse existing process-local session storage and TTL. Bound PDF parsing in a worker; do not add OCR or new persistence. New form styles are scoped to a CSS module; existing globals.css and five routes are preserved.
- 2026-09-03 TASK 03: Adapt the existing custom-upload browser regression assertion to the new DRAFT view, retaining its no-extraction/no-frozen-profile/no-fake-finding invariant. Keep all 26 original backend tests intact.

- 2026-09-02 TASK 02: Baseline 7bc3aeb preserves TASK 01; integration on codex/task-02-frozen-v15.
- 2026-09-02 TASK 02: Original v1.5 SHA matched. Keep source and reference artifacts byte-identical with Git text conversion disabled.
- 2026-09-02 TASK 02: Replace serialized NEEDS_REVIEW with REVIEW_REQUIRED. Separate run lifecycle and null pre-run summary.
- 2026-09-02 TASK 02: Demo convenience buttons fetch actual files and POST multipart bytes; remove canned fixture-result service.
- 2026-09-02 TASK 02: Execute the frozen native directory entrypoint in the backend Python child process, without monkeypatching. Redirect import notices to stderr.
- 2026-09-02 TASK 02: Use temporary per-session storage with verified receipts and explicit incomplete/error handling. No generic announcement or Vision profile is fabricated.
- 2026-09-02 TASK 02: User authorizes dedicated public source publication. Do not publicly deploy the unauthenticated app.

## TASK 01 historical decisions (superseded where TASK 02 says so)

- 2026-09-02: Preserve the dirty method-catalog checkout and original Extractor v0 ZIP byte-for-byte. Create an independent local product folder because the configured workspace is missing. Repository binding remains I01.
- 2026-09-02: Use App Router with five explicit routes and a small client session context. Keep result construction and validation rules in Python; frontend renders typed API responses.
- 2026-09-02: Mock results are opt-in demo fixtures with visible sourceMode=mock. Arbitrary uploads never inherit fixture findings.
- 2026-09-02: Local FastAPI session store has a one-hour TTL and a bounded session count. Store metadata/hashes only, discard uploaded bytes after receipt in TASK 01. Restart invalidates sessions.
- 2026-09-02: A summary with any REVIEW/EXTERNAL is NEEDS_REVIEW. This conservative implementation does not change finding statuses.
- 2026-09-02: Pin project dependencies and use a Python virtual environment. Use existing installed skills; no plugin, account, paid service or global dependency installation.
