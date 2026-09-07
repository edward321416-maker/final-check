# TASK 08 — Typed Verifier Compiler and Deterministic Checker MVP

## Product boundary

TASK08 converts a human-confirmed generic requirement profile into a closed,
versioned verification plan. The AI planner proposes typed data only. A
deterministic grounding gate decides whether that proposal can run, and checker
code measures application-owned submission bytes. The AI cannot issue PASS,
BLOCKER, READY or BLOCKED.

```text
CONFIRMED profile
→ isolated AI planner
→ typed candidates
→ deterministic grounding gate
→ VERIFIED / REVIEW_ONLY / EXTERNAL PlanSet
→ actual PDF/MP4 inspection
→ evidence-backed finding
→ generic readiness policy
```

The existing `generic_review` lane remains REVIEW/EXTERNAL only. The new
`generic_verifier` lane may issue PASS/BLOCKER only from a VERIFIED plan with
both announcement and submission evidence.

## Planner isolation and provenance

`VerificationPlanner` is a provider boundary. The local implementation uses the
existing ChatGPT-authenticated Codex CLI with `gpt-5.6-sol` and high reasoning.
It runs in an ephemeral directory with read-only sandboxing, web and tools
disabled, no repository context, and a copied authentication file that is
deleted after the call. Only the confirmed profile, announcement text, exact
evidence, modality, severity, verifier and condition enter the request.
Submission names, sizes, bytes, prior results and benchmark data do not.

Planner prompt version: `task08-planner-v1`.

Prompt SHA-256:
`096fd93cd2c3770cd49dcdbe6131e0abda4ea8b3e074728dc7b45e219f36a4a6`.

Plan schema version: `task08-verification-plan-v1`.

The planner schema cannot emit VERIFIED. Provider, model, prompt version, prompt
hash and execution kind are injected by the application after structured output
validation.

## Closed plan language

The seven checker families are:

- `FILE_PRESENCE`
- `FILE_COUNT`
- `FILE_NAME`
- `FILE_TYPE`
- `FILE_SIZE`
- `PDF_PAGE_COUNT`
- `VIDEO_METADATA`

Selectors are limited to `EXACT_NAME`, `UNIQUE_EXTENSION`,
`ALL_BY_EXTENSION` and `ALL_FILES`. Filename operations are limited to exact,
prefix, suffix and contains literals. Numeric comparison is limited to EQ, LT,
LTE, GT and GTE with typed units. Arbitrary regex, code, shell, SQL, URL calls,
imports, executable names, ffprobe options and filesystem paths are outside the
schema.

## Deterministic authorization gate

Automatic execution requires all of the following:

- The profile and requirement are human-confirmed and authoritative.
- The verifier is DETERMINISTIC and modality is MUST or MUST_NOT.
- The condition is exactly `always`.
- The planner returned exactly one schema-valid candidate per confirmed rule.
- Evidence quote and offsets match the confirmed source.
- Parameter substring, normalized value and comparison operator are grounded in
  that evidence.
- The checker/constraint/selector combination belongs to the closed set.
- The source names the target sufficiently for the selector.
- No unsupported qualifier such as excluded cover or appendix was discarded.

Failure of any gate produces REVIEW_ONLY. EXTERNAL requirements remain
EXTERNAL. The checker resolves `UNIQUE_EXTENSION` only when exactly one actual
file matches; zero or multiple matches produce REVIEW.

## Deterministic inspection

The generic engine rehashes application-owned bytes and compares the inventory
with stored upload receipts before it runs. It does not use the frozen validator
metadata helper.

- PDF type uses the signature and pypdf parsing. PDF page count uses pypdf.
  Parser failure returns REVIEW.
- MP4 type and video metadata use a closed ffprobe command assembled only by
  application code. Unavailable, timed-out, malformed or unreadable ffprobe
  output returns REVIEW.
- File size uses actual bytes. A decimal MB versus binary MiB boundary that
  changes the result returns REVIEW.
- Every definite PASS or violation records the measured fact and actual file
  evidence.

An automatic BLOCKER additionally requires an authoritative confirmed mandatory
rule with severity BLOCKER, deterministic verifier and an unconditional,
definite violation. Other violations remain REVIEW. READY is possible only when
every mandatory rule has a definite PASS; advisory SHOULD/MAY/INFO results do
not block readiness.

## Persistence and invalidation

The PlanSet persists inside the TASK07 SQLite-backed `CheckSession`. It binds to
profile ID/version, announcement bytes SHA, extracted-text SHA and a canonical
hash of the confirmed requirements. Any binding change invalidates it. Changing
only the submission reuses the same PlanSet and reruns checker code without
another planner call. A backend restart reconstructs a completed PlanSet; an
abandoned RUNNING planner state becomes REVIEW_REQUIRED and must be retried
explicitly.

## Product flow

After confirming the requirement profile, the user selects **자동 검사 계획
생성**. The summary labels each plan as 자동 검사 가능, 검토 필요 or 외부 확인,
and shows the checker, expected constraint and source quote. The UI states that
AI proposes a plan and has no verdict authority. Current MVP automatic file
support is PDF / MP4.

## Actual acceptance evidence

The ACTUAL local product E2E used this exact excerpt from the public C01 source:

`- 전체 길이 60초 이내 영상(최소 길이 제한 없음)`

Actual TASK06 Stage1 and Stage2 retained the duration rule. After operator
confirmation, the actual TASK08 planner proposed VIDEO_METADATA with
`DURATION_SECONDS LTE 60 SECONDS`; the deterministic gate authorized it. The
same persisted PlanSet measured a real 61-second test MP4 as BLOCKER/BLOCKED and
a real 45-second test MP4 as PASS/READY. Both results contain source and
submission evidence. Evidence is under `artifacts/task08/`.

Earlier full C01/C02 attempts ended in existing TASK06 Stage1 malformed output,
and one excerpt attempt encountered a transient provider-unavailable result.
The passing acceptance therefore claims the exact public excerpt flow, not
full-announcement coverage. It is product acceptance, not an accuracy
benchmark.

## Verification and limits

- Backend: 134 passed.
- Standard browser suite: 16 passed, 4 opt-in actual-AI cases skipped.
- Separate actual TASK08 product E2E: 1 passed.
- Separate existing TASK06 actual-AI regression: 1 passed.
- TypeScript typecheck and production build: PASS.
- Gold count/hash and frozen Validator hash: unchanged.

This local MVP does not verify semantics, imagery, OCR, URLs or additional file
formats. It does not claim production provider availability, multiple-worker
coordination, public deployment, universal rule coverage or benchmark accuracy.
