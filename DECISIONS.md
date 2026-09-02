# Engineering decisions

- 2026-09-02: Preserve the dirty method-catalog checkout and original Extractor v0 ZIP byte-for-byte. Create an independent local product folder because the configured workspace is missing. Repository binding remains I01.
- 2026-09-02: Use App Router with five explicit routes and a small client session context. Keep result construction and validation rules in Python; frontend renders typed API responses.
- 2026-09-02: Mock results are opt-in demo fixtures with visible sourceMode=mock. Arbitrary uploads never inherit fixture findings.
- 2026-09-02: Local FastAPI session store has a one-hour TTL and a bounded session count. Store metadata/hashes only, discard uploaded bytes after receipt in TASK 01. Restart invalidates sessions.
- 2026-09-02: A summary with any REVIEW/EXTERNAL is NEEDS_REVIEW. This conservative implementation does not change finding statuses.
- 2026-09-02: Pin project dependencies and use a Python virtual environment. Use existing installed skills; no plugin, account, paid service or global dependency installation.
