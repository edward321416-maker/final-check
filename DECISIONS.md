# Engineering decisions

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
