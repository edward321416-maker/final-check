# FINAL CHECK — AI Submission Preflight
Version: 1.1 | TASK 02 product instructions supplied 2026-09-02.

## Ownership and source of truth
ChatGPT planning: Product / Business Lead. Codex: AI / Engineering Lead.
This file is the product implementation source of truth; the dedicated FINAL CHECK GitHub repository is the shared project record.
Do not attach this product to ai-development-methods. Record undecided product choices in IMPLEMENTATION_ISSUES.md.

## Product
“공고문과 실제 제출파일을 넣으면, AI가 제출 전에 탈락요인을 찾아주고 각 판정의 근거까지 보여준다.”

## Locked golden path and scope
Home → Announcement Analysis → Submission Upload → Preflight Results → Recheck.
Routes remain /, /announcement, /upload, /results, /recheck. Recheck returns to Results.
Preserve TASK 01 styling/layout. No login, payments, collaboration, admin, analytics dashboard, automatic submission, new verticals or incidental SaaS features.
Frontend Next.js + TypeScript. Backend FastAPI + Python. Never rewrite the frozen validator in another language.

## Locked finding and submission contracts
FindingStatus: BLOCKER, REVIEW, PASS, EXTERNAL.
Every BLOCKER requires nonblank announcement evidence and submission evidence.
SubmissionStatus: **BLOCKED, REVIEW_REQUIRED, READY**.
TASK 02 explicitly replaces serialized NEEDS_REVIEW with REVIEW_REQUIRED.
Before validation, status is null; run_state independently records NOT_STARTED, RUNNING, COMPLETE or FAILED.
Incomplete or failed execution cannot READY. Any REVIEW/EXTERNAL prevents READY.
R20 licensing and R21 AI provenance have no automated verification: REVIEW/EXTERNAL only; no unsupported PASS or BLOCKER.

## R19 lock
PHOTO_ONLY suspicion, Ken Burns, pan, zoom and ambiguous motion → REVIEW.
Confident actual motion → no R19 issue.
Never automatically emit R19 BLOCKER. Preserve frozen thresholds and policies byte-for-byte.

## Frozen source
Original validator_v1_5.py SHA-256:
4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11
Store immutable source/manifests under backend/app/validators/frozen_v15/.
Application input/output adaptation belongs in v15_adapter.py. No source reformat, function rename or threshold edit.

## Current supported validation profile
The provided engine contains a fixed childcare short-form competition profile, R05–R17 and R19–R21, including the literal team name 테스트어린이집.
The application uses its SOURCE_RULES as handoff announcement excerpts. They are not newly extracted from an original announcement PDF.
Arbitrary announcement extraction is unavailable; custom announcement sessions cannot inherit this profile.
Demo selection downloads actual fixture bytes to the browser and uploads them through the same multipart submission endpoint used by file selection.
Actual files are hashed, held in an isolated temporary session package and executed by the original Python validator.
Review findings and factual measurements are shown with both source references; raw engine output is retained separately.

## New TASK 02 demo acceptance
Old fixtures/demo-broken and demo-fixed (12s/8s, 320x180) remain historical skeleton fixtures only.
New fixtures/v15/demo-broken: one correctly named PDF containing application, portrait and description sections but missing privacy; correct MP4 filename, 1080x1920, 9:16, under 300MB, exactly 61 seconds.
Expected raw: R09/R13 BLOCKER; R19/R20/R21 REVIEW; no unintended technical blocker.
New fixtures/v15/demo-fixed: privacy restored; video 45 seconds; same other properties.
Expected raw: R09/R13 BLOCKER absent; submission REVIEW_REQUIRED, never READY.
Independently audit actual file properties before scoring. Do not use invalid fixture ground truth to score the validator.

## Vision boundary
Image-only PDF triggers the frozen engine's VISION_PENDING requests.
No actual vision provider is integrated. Map pending concepts to REVIEW and mark validation incomplete; never invent PASS.
This limitation must be visible in the UI.

## Runtime limits
Loopback-only local service; no cloud upload or new provider call.
Session metadata, temporary submission files and raw results last until replacement, expiry (one hour), or shutdown. Restart invalidates sessions.
100 concurrent stored sessions; one upload/run at a time per session; maximum 8 files, 320 MiB per file, 350 MiB package transport.
These are local resource limits, not modifications to the frozen 300MB rule.
Production storage, multi-worker coordination, public app deployment and arbitrary announcement extraction remain outside TASK 02.

## Prior gate context
User-reported independent extractor PASS and frozen 39-package Final Full Gate PASS are reference history.
The exact historical 39-case corpus is absent from this handoff; do not claim reproduction.
Technical Kill Test is closed. TASK 02 executes new local fixtures and integration invariants only.
