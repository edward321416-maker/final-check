# TASK10 evidence-backed content review

Status: **Local implementation and verification complete; public ACTUAL NOT TESTED; DO NOT MERGE pending Product Lead review.**

TASK10 adds a parallel semantic review lane for human-confirmed mandatory content requirements. It does not expand AI verdict authority. Deterministic TASK08 checks remain the only automatic `PASS` / `BLOCKER` path; every TASK10 semantic outcome is `REVIEW`, and a mandatory semantic review keeps the overall submission at `REVIEW_REQUIRED`.

## Supported path

- Exactly one submitted, trusted, text-readable PDF is eligible for semantic review.
- The application verifies the upload receipt and actual PDF type, extracts page-aware text locally, and sends the complete bounded extracted text to the existing ChatGPT-authenticated Codex CLI only after explicit acknowledgement.
- Original PDF bytes are not sent to AI as a file. MP4 contents are not sent for semantic analysis.
- The provider returns evidence candidates only. Local code accepts a quote only when its document/page identifiers resolve to the current extraction and the quote is an exact substring of that page text; local code computes the offsets.
- Related evidence and full-coverage no-clear-evidence outcomes both remain `REVIEW`. For `MUST_NOT`, related text is also review-only.
- A recheck performs a fresh semantic review and can report an evidence-state or evidence-fingerprint change even though both results remain `REVIEW`.

## Completeness and safety limits

- Maximum one semantic PDF, 50 pages, 100,000 extracted characters, 50 eligible semantic requirements, and three evidence candidates per requirement.
- Limits are fail-closed completeness gates; input is not silently truncated.
- `PARTIAL` text coverage may show accepted positive evidence but cannot claim that evidence is absent from the whole document. `NONE`, encrypted, parser-failed, ambiguous, missing, or fake-PDF targets remain safe `REVIEW` paths without an AI call.
- Submission text is untrusted data. Prompt-injection text cannot add a verdict field, bypass the closed response schema, or create semantic `PASS`, `BLOCKER`, `READY`, or `BLOCKED` authority.
- Fabricated, rewritten, wrong-page, or stale-package quotes are rejected before trusted evidence is exposed.
- Provider, schema, guard, or transport failure degrades only the semantic item to `REVIEW`; valid deterministic findings are preserved.

## Unsupported scope

TASK10 v0.1 does not provide OCR, Vision, image understanding, MP4 semantic analysis, URL checking, semantic PASS/BLOCKER decisions, semantic caching, multi-PDF role resolution, truncated whole-document analysis, a paid API-key provider, multi-worker coordination, cloud failover, or a production SLA.

## Runtime and verification status

The supported implementation is the current single-node, single-backend-process local runtime using the existing authenticated Codex CLI. The documented TASK09 ngrok URL returned HTTP 404 during the one permitted read-only health check on 2026-09-10 KST. No public service was started, replaced, or redeployed, so TASK09 public ACTUAL and TASK10 public ACTUAL are **NOT TESTED**, not PASS.

If separately restored and authorized, the existing judge topology still depends on the host PC and network remaining online, one local backend process, ngrok Free transfer/request limits and first-visit behavior, and public upload limits of 16 MiB per file / 24 MiB per package / eight files. It has no cloud failover or production SLA.

Fresh local acceptance on implementation HEAD `a87c2eb9637154b278c15fdaa2586693fbd14c86` passed the full backend suite, focused TASK10 suite, standard Playwright suite, TypeScript check, production build, guarded TASK08 ACTUAL regression, and TASK10 ACTUAL positive/missing/recheck/prompt-injection flow. Exact commands, counts, session IDs, prompt provenance, hashes, and limits are recorded in `artifacts/task10/RESULT_CODEX_TASK10.md`.
