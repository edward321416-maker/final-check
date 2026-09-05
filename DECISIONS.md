# Engineering decisions

- 2026-09-05 TASK07: FINAL CHECK GO. Use Python `sqlite3` plus application-owned local files behind minimal SessionStore/JobStore/ArtifactStore boundaries; default `FINAL_CHECK_DATA_DIR` is `.final-check/runtime/`.
- 2026-09-05 TASK07: Represent two-stage extraction as one idempotent durable job per session/profile/version/operation. Save Stage1, gate, each Stage2 batch and final checkpoints; restart changes abandoned PENDING/RUNNING to RETRYABLE.
- 2026-09-05 TASK07: Retry only through explicit user action, at most three attempts. Persist safe error categories and provider provenance, never raw stderr, tokens, Codex auth, cookies or browser login data.
- 2026-09-05 TASK07: Preserve the one-hour TTL but protect process-active and PENDING/RUNNING/RETRYABLE sessions. Claim only single-node, single-backend-process durability.
- 2026-09-05 TASK07: Keep TASK06 model/prompts/provider/human confirmation unchanged. No cloud, Redis/Celery, Vision/OCR, benchmark, provider selection or TASK08 generic verifier implementation.

- 2026-09-05 TASK06: FINAL CHECK GO. Two-stage extraction is GO for the local MVP; Stage1 and Stage2 remain provisional until mandatory human confirmation. AI pre-confirmation BLOCKER authority is NOT_ALLOWED.
- 2026-09-05 TASK06: Use existing authenticated Codex CLI through separate provider adapters. Long calls run in a background task and the UI polls status. This is an ACTUAL LOCAL AI PROVIDER, not a production provider selection.
- 2026-09-05 TASK06: Candidate overflow begins above100, Stage2 batches contain50, and500 is the hard ceiling. Preserve completed batches and retry only failed batches; never truncate or silently substitute local rules.
- 2026-09-05 TASK06: Keep generic submission results REVIEW/EXTERNAL only. No Vision/OCR, automatic generic verifier, benchmark/rescoring, deployment or frozen-validator change.
- 2026-09-05 TASK06: One public C03 flow is actual product acceptance, not accuracy measurement. Synthetic safety contracts are SELF and provider faults are SIMULATED.

- 2026-09-04 TASK05: FINAL CHECK GO; local rules STOP AS PRIMARY. One real blind gpt-5.6-sol/high candidate, one frozen prompt, eight isolated sessions, zero tool calls or retries.
- 2026-09-04 TASK05: Measurement PASS; AI-FIRST — STOP for this primary candidate. GATED recall47.98%, precision35.02%, semantic support78.48%, unsupported BLOCKER3. Improvement over local is insufficient for the authorized thresholds.
- 2026-09-04 TASK05: Preserve existing100-candidate cap (C01 rejects117), Gold173, all matching units, scoring policy and source hashes. Do not tune prompts/regex, change Gold, integrate production or begin another task. Full evidence in benchmarks/task05/report/report.md.

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

## TASK 04 measurement decisions

- 2026-09-03: Start from merged TASK03 main 81bf2551; prior prerequisite non-start contributes no benchmark data.
- 2026-09-03: Eight actual scoped announcements; freeze173 Gold before output, preserve original input bytes, no extractor tuning or Gold score adjustment.
- 2026-09-03: Primary denominator is raw candidates; one-to-one complete atomic MATCH only. Same-agent manual scoring and known Gold boundary limitations are disclosed.
- 2026-09-03: Measured recall18.50%, precision15.17%, modality25.00%, semantic support24.17%; FINAL CHECK remains GO. Engineering recommends replacing local rules as primary with a future AI-first comparison plus deterministic evidence gate. Product Lead must review before scope/provider selection.
- 2026-09-03: Keep current product, validator, tests and five-screen UI unchanged. No repeated regex fixes, TASK05, Vision/OCR, provider integration or deployment. Deliver PR without merge.

## TASK 01 historical decisions (superseded where TASK 02 says so)

- 2026-09-02: Preserve the dirty method-catalog checkout and original Extractor v0 ZIP byte-for-byte. Create an independent local product folder because the configured workspace is missing. Repository binding remains I01.
- 2026-09-02: Use App Router with five explicit routes and a small client session context. Keep result construction and validation rules in Python; frontend renders typed API responses.
- 2026-09-02: Mock results are opt-in demo fixtures with visible sourceMode=mock. Arbitrary uploads never inherit fixture findings.
- 2026-09-02: Local FastAPI session store has a one-hour TTL and a bounded session count. Store metadata/hashes only, discard uploaded bytes after receipt in TASK 01. Restart invalidates sessions.
- 2026-09-02: A summary with any REVIEW/EXTERNAL is NEEDS_REVIEW. This conservative implementation does not change finding statuses.
- 2026-09-02: Pin project dependencies and use a Python virtual environment. Use existing installed skills; no plugin, account, paid service or global dependency installation.
