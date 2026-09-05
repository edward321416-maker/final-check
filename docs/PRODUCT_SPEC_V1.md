# FINAL CHECK — AI Submission Preflight
Version: 1.3 | TASK 07 durability instructions supplied 2026-09-05.

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
Custom announcement sessions never inherit this frozen profile. TASK 03 uses the separate generic profile layer below.
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
Session/profile/job metadata and application-owned announcement/submission/raw artifacts persist across backend process restart until replacement or safe expiry (one hour). PENDING/RUNNING/RETRYABLE jobs and process-active sessions are not expired.
100 concurrent stored sessions; one upload/run at a time per session; maximum 8 files, 320 MiB per file, 350 MiB package transport.
These are local resource limits, not modifications to the frozen 300MB rule.
Production storage, multi-worker coordination, public app deployment and arbitrary announcement extraction remain outside TASK 02.

## Prior gate context
User-reported independent extractor PASS and frozen 39-package Final Full Gate PASS are reference history.
The exact historical 39-case corpus is absent from this handoff; do not claim reproduction.
Technical Kill Test is closed. TASK 02 executes new local fixtures and integration invariants only.

## TASK 03 generic announcement contract
Keep the same five screens. Text/PDF input lives on Home; extraction, evidence and human review live within Announcement Analysis.
Flow: input → extraction → draft profile → per-item review/edit/delete/approval → explicit whole-profile confirmation → upload/validation orchestration.
Requirement extraction statuses: EXTRACTED, NEEDS_REVIEW, CONFIRMED, UNSUPPORTED. Profile statuses: DRAFT, REVIEW_REQUIRED, CONFIRMED.
No provider may automatically confirm an item or profile. Each retained item needs an explicit user approval; profile confirmation requires acknowledgement that the entire source was reviewed.
Canonical fields: requirement_id, rule, modality, severity, verifier, condition, evidence.source_section, evidence.quote, confidence.
Modality: MUST/MUST_NOT/SHOULD/MAY/INFO. Severity: BLOCKER/REVIEW/INFO/EXTERNAL. Verifier: DETERMINISTIC/SEMANTIC/VISION_SEMANTIC/URL_CHECK/EXTERNAL.
Every candidate needs nonblank exact source evidence, anchored to source-text character offsets. Reject missing or rewritten quotes. SHOULD/MAY/INFO + BLOCKER is a schema error. Compound candidates are split by supported syntax or held for atomicity review; flagged items cannot be approved until edited.
The provider interface is injectable. Default local-rules-v1 executes deterministic Korean keyword/line heuristics; it is **not an AI model**. Its output is actual local execution, with uncalibrated confidence 0.5 and no independent accuracy claim.
The original input SHA-256, extracted-text SHA-256, full text, source type/name, profile ID/version and review history preserve provenance. Exact substring matching is not proof of semantic entailment; a human must review wording, modality, conditions and omissions.
Generic profile mutations invalidate its activation and prior results. Optimistic version checks reject stale approval. Stored profile JSON is available in the session response and preserved in the generic run envelope.
Only CONFIRMED generic profiles populate the validation handoff. Their automatic submission verifiers are not implemented: results are REVIEW/EXTERNAL, validation_complete=false, engine_sha256=null, never fake PASS/BLOCKER/READY. Confirmation means requirements reviewed, not submission verified.
Input bounds: UTF-8 text, 100,000 characters; announcement uploads up to 10 MiB; PDF up to 50 pages with a 30-second parsing worker timeout. A PDF with a textless page is VISION_REQUIRED and generates zero candidates. Invalid/encrypted/oversized sources use unreadable/unsupported paths. Embedded image contents and complex PDF reading order are not interpreted.
Generic profiles inherit the existing single-process, temporary-session lifetime. No paid provider, OAuth, Vision, production hosting, R19 change or historical benchmark claim is added.

## TASK 07 durable runtime contract

TASK07 supersedes the TASK03 temporary-session sentence above. The default local
MVP persists canonical JSON metadata in SQLite and artifacts under
`FINAL_CHECK_DATA_DIR` (default `.final-check/runtime/`). An abandoned PENDING or
RUNNING AI job becomes RETRYABLE on startup and resumes only from its latest durable two-stage
checkpoint after explicit retry. Completed Stage1 and Stage2 batches are not
repeated. Retry is bounded to three attempts, and provider failure cannot confirm
a profile or produce PASS/READY. This is single-node durability; multi-worker,
cloud deployment and production provider selection remain unsupported.
Correct delivery claim: **Generic announcement requirement-profile pipeline is integrated and executable.** General accuracy is for TASK 04 independent evaluation.
